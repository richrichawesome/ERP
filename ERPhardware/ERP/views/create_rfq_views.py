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
from ERP.models import User
from datetime import datetime


def create_rfq(request, req_id):
    """Create RFQ from approved requisition and generate PDF"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    
    try:
        user = User.objects.get(pk=user_id)
        
        # Verify user is purchase management (role_id == 3)
        if user.role_id != 3:
            return JsonResponse({'success': False, 'error': 'Unauthorized access'}, status=403)
        
        # Get the requisition
        requisition = get_object_or_404(Requisition, req_id=req_id)
        
        # Verify requisition is in correct status
        if requisition.req_main_status != 'APPROVED_REQUISITION':
            return JsonResponse({
                'success': False, 
                'error': 'Requisition must be in APPROVED_REQUISITION status to create RFQ'
            }, status=400)
        
        # Check if RFQ already exists for this requisition
        existing_rfq = RFQ.objects.filter(rfq_created_by=requisition).first()
        if existing_rfq:
            return JsonResponse({
                'success': False, 
                'error': 'RFQ already exists for this requisition'
            }, status=400)
        
        with transaction.atomic():
            # Create RFQ
            rfq = RFQ.objects.create(
                rfq_created_by=requisition
            )
            
            # Create RFQ Items from Requisition Items
            requisition_items = requisition.items.all()
            for item in requisition_items:
                RFQ_Item.objects.create(
                    requisition=requisition,
                    product=item.product,
                    rfq_item_req_qty=item.quantity,
                    rfq_item_req_uom=item.uom
                )
            
            # Update requisition substatus
            requisition.req_substatus = 'RFQ_CREATED'
            requisition.save()
            
            # Create timeline entry
            RequisitionStatusTimeline.objects.create(
                requisition=requisition,
                main_status=requisition.req_main_status,
                sub_status='RFQ_CREATED',
                user=user,
                comment='RFQ created by purchasing staff'
            )
            
            # Generate PDF
            pdf_buffer = generate_rfq_pdf(rfq, requisition)
            
            # Return PDF as download
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="RFQ-{rfq.rfq_id:06d}_REQ-{requisition.req_id:06d}.pdf"'
            return response
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def generate_rfq_pdf(rfq, requisition):
    """Generate PDF for RFQ matching the requisition form design"""
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles (matching requisition form)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#000000'),
        leading=12
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#000000'),
        fontName='Helvetica-Bold',
        leading=12
    )
    
    # Title
    title = Paragraph("REQUEST FOR QUOTATION", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Purchase Request for Materials", normal_style)
    subtitle.alignment = TA_CENTER
    elements.append(subtitle)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # RFQ Information
    rfq_header = Paragraph("RFQ Information", header_style)
    elements.append(rfq_header)
    
    rfq_info_data = [
        [
            Paragraph('<b>RFQ ID:</b>', bold_style),
            Paragraph(f'RFQ-{rfq.rfq_id:06d}', normal_style),
            Paragraph('<b>Status:</b>', bold_style),
            Paragraph('Awaiting Supplier Quotations', normal_style)
        ],
        [
            Paragraph('<b>Requisition ID:</b>', bold_style),
            Paragraph(f'REQ-{requisition.req_id:06d}', normal_style),
            Paragraph('<b>Requisition Type:</b>', bold_style),
            Paragraph(requisition.get_req_type_display(), normal_style)
        ],
        [
            Paragraph('<b>Date Created:</b>', bold_style),
            Paragraph(rfq.rfq_created_at.strftime('%B %d, %Y %I:%M %p'), normal_style),
            Paragraph('<b>Date Required:</b>', bold_style),
            Paragraph(requisition.req_date_required.strftime('%B %d, %Y') if requisition.req_date_required else 'Not specified', normal_style)
        ],
        [
            Paragraph('<b>Requested By:</b>', bold_style),
            Paragraph(f'{requisition.requested_by.user_fname} {requisition.requested_by.user_lname}', normal_style),
            Paragraph('<b>Branch:</b>', bold_style),
            Paragraph(requisition.branch.branch_name, normal_style)
        ],
    ]
    
    rfq_info_table = Table(rfq_info_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 1.8*inch])
    rfq_info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(rfq_info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Requested Materials
    items_header = Paragraph("Requested Materials", header_style)
    elements.append(items_header)
    
    # Items table header
    items_data = [[
        Paragraph('<b>#</b>', bold_style),
        Paragraph('<b>Product Name</b>', bold_style),
        Paragraph('<b>Specification</b>', bold_style),
        Paragraph('<b>Quantity</b>', bold_style),
        Paragraph('<b>Unit</b>', bold_style)
    ]]
    
    # Get RFQ items
    rfq_items = RFQ_Item.objects.filter(requisition=requisition).select_related('product').order_by('rfq_item_id')
    
    for idx, item in enumerate(rfq_items, 1):
        # Get specifications
        specs = item.product.product_specification_set.all()
        if specs.exists():
            spec_text = ', '.join([f"{spec.spec_name}: {spec.spec_value}" for spec in specs])
        else:
            spec_text = 'No specifications'
        
        items_data.append([
            Paragraph(str(idx), normal_style),
            Paragraph(item.product.prod_name, normal_style),
            Paragraph(spec_text, normal_style),
            Paragraph(str(item.rfq_item_req_qty), normal_style),
            Paragraph(item.rfq_item_req_uom, normal_style)
        ])
    
    items_table = Table(items_data, colWidths=[0.4*inch, 1.8*inch, 2.8*inch, 0.7*inch, 0.8*inch])
    items_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),
        
        # Grid and styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Notes Section
    if requisition.req_notes:
        notes_header = Paragraph("Additional Notes", header_style)
        elements.append(notes_header)
        notes_text = Paragraph(requisition.req_notes, normal_style)
        elements.append(notes_text)
        elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    footer = Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} • StockFlow Inventory System",
        footer_style
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer





























