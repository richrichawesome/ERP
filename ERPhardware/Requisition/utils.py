# Requisition/utils.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
import os
from datetime import datetime, timezone

def generate_requisition_pdf(requisition):
    """
    Generate a professional PDF for the requisition form
    Returns the URL to access the PDF
    """
    try:
        print(f"🔍 PDF Generation Started for REQ-{requisition.req_id}")

        # Create rfs directory if it doesn't exist
        rf_dir = os.path.join(settings.MEDIA_ROOT, 'rfs')
        print(f"📁 RF Directory: {rf_dir}")
        os.makedirs(rf_dir, exist_ok=True)

        
        # Generate filename for RF (Requisition Form)
        filename = f'RF_{requisition.req_id:06d}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join(rf_dir, filename)
        print(f"💾 File path: {filepath}")

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=letter,
            rightMargin=0.75*inch, 
            leftMargin=0.75*inch,
            topMargin=1*inch, 
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Title Style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Header Style
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Normal Style
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            leading=12
        )
        
        # Bold Style
        bold_style = ParagraphStyle(
            'CustomBold',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold',
            leading=12
        )
        
        # ===== TITLE SECTION =====
        title = Paragraph("REQUISITION FORM", title_style)
        elements.append(title)
        
        subtitle = Paragraph("Inventory Replenishment Request", normal_style)
        subtitle.alignment = TA_CENTER
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # ===== REQUISITION INFORMATION SECTION =====
        req_header = Paragraph("Requisition Information", header_style)
        elements.append(req_header)
        
        req_info_data = [
            [
                Paragraph('<b>Requisition ID:</b>', bold_style), 
                Paragraph(f'REQ-{requisition.req_id:06d}', normal_style),
                Paragraph('<b>Status:</b>', bold_style),
                Paragraph('Pending Custodian Approval', normal_style)
            ],
            [
                Paragraph('<b>Requested By:</b>', bold_style), 
                Paragraph(f'{requisition.requested_by.user_fname} {requisition.requested_by.user_lname}', normal_style),
                Paragraph('<b>Branch:</b>', bold_style),
                Paragraph(f'{requisition.branch.branch_name}', normal_style)
            ],
            [
                Paragraph('<b>Date Requested:</b>', bold_style), 
                Paragraph(requisition.req_requested_date.strftime('%B %d, %Y %I:%M %p'), normal_style),
                Paragraph('<b>Requisition Type:</b>', bold_style),
                Paragraph('Inventory Replenishment', normal_style)
            ],
            # In the req_info_data section, add this row:
            [
                Paragraph('<b>Date Required:</b>', bold_style), 
                Paragraph(requisition.req_date_required.strftime('%B %d, %Y'), normal_style),
                Paragraph('<b>Days Until Required:</b>', bold_style),
                Paragraph(str((requisition.req_date_required - timezone.now().date()).days), normal_style)
            ],
        ]
        
        req_info_table = Table(req_info_data, colWidths=[1.2*inch, 2.3*inch, 1*inch, 2*inch])
        req_info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(req_info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # ===== REQUESTED ITEMS SECTION =====
        items_header = Paragraph("Requested Items", header_style)
        elements.append(items_header)
        
        # Items Table Header
        items_data = [[
            Paragraph('<b>#</b>', bold_style),
            Paragraph('<b>Product Name</b>', bold_style),
            Paragraph('<b>Description</b>', bold_style),
            Paragraph('<b>Quantity</b>', bold_style),
            Paragraph('<b>Unit</b>', bold_style)
        ]]
        
        # Add items to table
        for idx, item in enumerate(requisition.items.all(), 1):
            items_data.append([
                Paragraph(str(idx), normal_style),
                Paragraph(item.product.prod_name, normal_style),
                Paragraph(item.product.prod_desc, normal_style),
                Paragraph(str(item.quantity), normal_style),
                Paragraph(item.uom, normal_style)
            ])
        
        items_table = Table(items_data, colWidths=[0.4*inch, 2*inch, 2.5*inch, 0.8*inch, 0.8*inch])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Body rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # ===== NOTES SECTION =====
        if requisition.req_notes:
            notes_header = Paragraph("Additional Notes", header_style)
            elements.append(notes_header)
            
            notes_text = Paragraph(requisition.req_notes, normal_style)
            elements.append(notes_text)
            elements.append(Spacer(1, 0.2*inch))
        
        # ===== APPROVAL SECTION =====
        elements.append(Spacer(1, 0.4*inch))
        
        approval_header = Paragraph("Approval Section", header_style)
        elements.append(approval_header)
        
        approval_data = [
            [
                Paragraph('<b>Requested By:</b>', bold_style),
                '',
                Paragraph('<b>Property Custodian:</b>', bold_style),
                ''
            ],
            ['', '', '', ''],  # Empty row for signatures
            [
                Paragraph(f'{requisition.requested_by.user_fname} {requisition.requested_by.user_lname}', normal_style),
                '',
                '',
                ''
            ],
            [
                Paragraph('Signature over Printed Name', normal_style),
                Paragraph('Date', normal_style),
                Paragraph('Signature over Printed Name', normal_style),
                Paragraph('Date', normal_style)
            ],
        ]
        
        approval_table = Table(approval_data, colWidths=[2*inch, 1.2*inch, 2*inch, 1.2*inch])
        approval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('LINEABOVE', (0, 1), (1, 1), 1, colors.black),
            ('LINEABOVE', (2, 1), (3, 1), 1, colors.black),
            ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]))
        
        elements.append(approval_table)
        
        # ===== FOOTER =====
        elements.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        )
        footer = Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} • StockFlow Inventory System", footer_style)
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        print("✅ PDF built successfully")

        
        # Update the requisition with the RF file path
        requisition.rf_file.name = os.path.join('rfs', filename)
        requisition.save()
        
        print(f"✅ RF file saved: {requisition.rf_file.name}")
        print(f"✅ RF file absolute path: {requisition.rf_file.path}")
        
        # Return the relative URL for accessing the PDF
        rf_relative_url = os.path.join(settings.MEDIA_URL, 'rfs', filename)
        print(f"🌐 RF URL: {rf_relative_url}")
        
        return rf_relative_url
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        raise e