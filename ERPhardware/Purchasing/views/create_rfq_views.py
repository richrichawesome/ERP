from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from Requisition.models import Requisition, RequisitionStatusTimeline
from Purchasing.models import RFQ, RFQ_Item
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from ERP.models import User, Branch
from datetime import datetime


from django.db.models import F, Sum

def create_rfq_multiple(request):
    """Create a single RFQ for multiple approved requisitions"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    
    try:
        user = User.objects.get(pk=user_id)
        if user.role_id != 3:
            return JsonResponse({'success': False, 'error': 'Unauthorized access'}, status=403)
        
        # Get selected requisition IDs from POST
        req_ids = request.POST.getlist('req_ids[]')
        if not req_ids:
            return JsonResponse({'success': False, 'error': 'No requisitions selected'}, status=400)
        
        requisitions = Requisition.objects.filter(req_id__in=req_ids, req_main_status='APPROVED_REQUISITION')
        if not requisitions.exists():
            return JsonResponse({'success': False, 'error': 'No valid approved requisitions found'}, status=400)
        
        with transaction.atomic():
            # Create RFQ linked to multiple requisitions (could create a ManyToMany or use a textual list)
            rfq = RFQ.objects.create(
                rfq_created_by=user  # Or you can choose another field if you want
            )
            
            # Aggregate items across all requisitions
            combined_items = {}
            for req in requisitions:
                for item in req.items.all():
                    key = item.product_id
                    if key in combined_items:
                        combined_items[key]['quantity'] += item.quantity
                        combined_items[key]['requisitions'].append(req.req_id)
                    else:
                        combined_items[key] = {
                            'product': item.product,
                            'quantity': item.quantity,
                            'uom': item.uom,
                            'requisitions': [req.req_id]
                        }
            
            # Create RFQ Items
            for data in combined_items.values():
                RFQ_Item.objects.create(
                    rfq=rfq,
                    product=data['product'],
                    rfq_item_req_qty=data['quantity'],
                    rfq_item_req_uom=data['uom']
                )
            
            # Update substatus for all requisitions and create timeline
            for req in requisitions:
                req.rfq = rfq 
                req.req_substatus = 'RFQ_CREATED'
                req.save()
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status=req.req_main_status,
                    sub_status='RFQ_CREATED',
                    user=user,
                    comment='RFQ created for multiple requisitions'
                )
            
            # Generate PDF for combined RFQ
            pdf_buffer = generate_rfq_pdf_multiple(rfq, combined_items)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="RFQ-{rfq.rfq_id:06d}.pdf"'
            return response
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



def generate_rfq_pdf_multiple(rfq, combined_items):
    """Generate RFQ PDF with Unit Price column blank for supplier"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch,
                            leftMargin=0.75*inch, topMargin=1*inch, bottomMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')
    company_header_style = ParagraphStyle('CompanyHeader', parent=styles['Heading2'], fontSize=12, fontName='Helvetica-Bold')
    
    # Get Branch 1 information
    try:
        branch = Branch.objects.get(branch_id=1)
    except Branch.DoesNotExist:
        branch = None
    
    # Get the user who created the RFQ
    user = rfq.rfq_created_by
    
    # Title at the VERY TOP
    elements.append(Paragraph("REQUEST FOR QUOTATION", title_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Create a table for the header section with two columns
    header_data = [
        [
            # Left column: Company info
            Paragraph("<b>Cagasan Enterprises</b><br/>" + 
                     (f"{branch.branch_address}" if branch else "[Main Branch Address]"), 
                     company_header_style),
            # Right column: RFQ details
            Paragraph(
                f"<b>Date:</b> {rfq.rfq_created_at.strftime('%B %d, %Y')}<br/>" +
                f"<b>Quotation #:</b> RFQ-{rfq.rfq_id:06d}<br/>" +
                f"<b>Contact Number:</b> {(branch.branch_phone if branch else '[Main Branch Contact Number]')}<br/>" +
                f"<b>Created by:</b> {user.user_fname} {user.user_lname}",
                normal_style
            )
        ]
    ]
    
    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (1,0), (1,0), 20),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Horizontal line separator
    elements.append(Paragraph("<hr/>", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # "Quote for" section - Display text only (empty fields for supplier to fill)
    elements.append(Paragraph("<b>Quote for:</b>", bold_style))
    elements.append(Paragraph("<b>Supplier Name:</b> _______________________________", normal_style))
    elements.append(Paragraph("<b>Address:</b> _____________________________________", normal_style))
    elements.append(Paragraph("<b>Contact Person:</b> ______________________________", normal_style))
    elements.append(Paragraph("<b>Contact Number:</b> _____________________________", normal_style))
    elements.append(Paragraph("<b>Email:</b> _______________________________________", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Payment and Delivery Terms - Empty for supplier to fill
    elements.append(Paragraph("<b>Payment Terms:</b> _____________________________", bold_style))
    elements.append(Paragraph("<b>Delivery Terms:</b> _____________________________", bold_style))
    elements.append(Paragraph("<b>Quote Valid Until:</b> _________________________", bold_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Items Table
    data = [[
        Paragraph('<b>#</b>', bold_style),
        Paragraph('<b>Product Name</b>', bold_style),
        Paragraph('<b>Specification</b>', bold_style),
        Paragraph('<b>Quantity</b>', bold_style),
        Paragraph('<b>Unit</b>', bold_style),
        Paragraph('<b>Unit Price</b>', bold_style)
    ]]
    
    for idx, item_data in enumerate(combined_items.values(), 1):
        product = item_data['product']
        specs = product.product_specification_set.all()
        spec_text = ', '.join([f"{s.spec_name}: {s.spec_value}" for s in specs]) if specs.exists() else 'No specifications'
        
        # Get UOM from product if not specified in requisition
        uom = item_data.get('uom', product.prod_unit_of_measure)
        
        data.append([
            str(idx),
            product.prod_name,
            spec_text,
            str(item_data['quantity']),
            uom,
            ''  # Blank Unit Price for supplier to fill
        ])
    
    table = Table(data, colWidths=[0.4*inch, 1.8*inch, 2.8*inch, 0.7*inch, 0.8*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (3,1), (3,-1), 'RIGHT'),  # Align quantity right
        ('ALIGN', (5,1), (5,-1), 'RIGHT'),  # Align unit price right
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    
    
    
    # Footer with generation info
    elements.append(Spacer(1, 0.5*inch))
    current_time = timezone.now() if hasattr(timezone, 'now') else datetime.now()
    footer_text = f"Generated on {current_time.strftime('%B %d, %Y at %I:%M %p')} - StockFlow Inventory System"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer




def preview_rfq_data(request):
    """Generate preview data for RFQ before creating it"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    
    try:
        user = User.objects.get(pk=user_id)
        if user.role_id != 3:
            return JsonResponse({'success': False, 'error': 'Unauthorized access'}, status=403)
        
        # Get selected requisition IDs from POST
        req_ids = request.POST.getlist('req_ids[]')
        if not req_ids:
            return JsonResponse({'success': False, 'error': 'No requisitions selected'}, status=400)
        
        requisitions = Requisition.objects.filter(req_id__in=req_ids, req_main_status='APPROVED_REQUISITION')
        if not requisitions.exists():
            return JsonResponse({'success': False, 'error': 'No valid approved requisitions found'}, status=400)
        
        # Get Branch 1 information
        try:
            branch = Branch.objects.get(branch_id=1)
        except Branch.DoesNotExist:
            branch = None
        
        # Aggregate items across all requisitions
        combined_items = {}
        for req in requisitions:
            for item in req.items.all():
                key = item.product_id
                if key in combined_items:
                    combined_items[key]['quantity'] += item.quantity
                    combined_items[key]['requisitions'].append(req.req_id)
                else:
                    combined_items[key] = {
                        'product': item.product,
                        'quantity': item.quantity,
                        'uom': item.uom,
                        'requisitions': [req.req_id]
                    }
        
        # Prepare preview data
        preview_data = {
            'success': True,
            'branch_info': {
                'address': branch.branch_address if branch else '[Main Branch Address]',
                'phone': branch.branch_phone if branch else '[Main Branch Contact Number]',
            },
            'user_info': {
                'name': f"{user.user_fname} {user.user_lname}",
            },
            'rfq_info': {
                'date': datetime.now().strftime('%B %d, %Y'),
                'requisition_ids': req_ids,
                'requisition_count': len(requisitions),
            },
            'items': []
        }
        
        # Add items to preview data
        for idx, item_data in enumerate(combined_items.values(), 1):
            product = item_data['product']
            specs = product.product_specification_set.all()
            spec_text = ', '.join([f"{s.spec_name}: {s.spec_value}" for s in specs]) if specs.exists() else 'No specifications'
            
            # Get UOM from product if not specified in requisition
            uom = item_data.get('uom', product.prod_unit_of_measure)
            
            preview_data['items'].append({
                'index': idx,
                'product_name': product.prod_name,
                'specification': spec_text,
                'quantity': item_data['quantity'],
                'uom': uom,
                'unit_price': ''  # Empty for supplier to fill
            })
        
        return JsonResponse(preview_data)
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

