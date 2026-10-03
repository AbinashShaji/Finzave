import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_financial_report_pdf(period, health_data):
    """
    Generates a PDF financial report for the given period.
    Returns a bytes object of the PDF content.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles matching FinZave branding
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.black,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        spaceBefore=15,
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    
    # Header
    elements.append(Paragraph("<b>FinZave</b>", title_style))
    elements.append(Paragraph("Personal Financial Report", title_style))
    
    # Convert period_id '2026-07' to 'July 2026'
    try:
        dt = datetime.strptime(period.period_id, '%Y-%m')
        period_str = dt.strftime('%B %Y')
    except Exception:
        period_str = period.period_id
        
    elements.append(Paragraph(f"<b>Period:</b> {period_str}", subtitle_style))
    elements.append(Paragraph(f"<b>Generated Date:</b> {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # Financial Summary
    # ---------------------------------------------------------
    elements.append(Paragraph("<b>Financial Summary</b>", section_header_style))
    
    score_str = "N/A"
    if health_data and health_data.get('score') is not None:
        score_str = f"{health_data['score']}/100"
        
    summary_data = [
        ['Total Income', f"Rs. {period.total_income:,.2f}"],
        ['Total Expenses', f"Rs. {period.total_expenses:,.2f}"],
        ['Net Savings', f"Rs. {period.savings:,.2f}"],
        ['Financial Score', score_str]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))
    
    # ---------------------------------------------------------
    # Income Breakdown
    # ---------------------------------------------------------
    elements.append(Paragraph("<b>Income Breakdown</b>", section_header_style))
    
    income_data = [
        ['Category', 'Amount'],
        ['Fixed Income', f"Rs. {period.fixed_income:,.2f}"],
        ['Variable Income', f"Rs. {period.variable_income:,.2f}"]
    ]
    
    income_table = Table(income_data, colWidths=[300, 150])
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
    ]))
    elements.append(income_table)
    elements.append(Spacer(1, 15))
    
    # ---------------------------------------------------------
    # Expense Breakdown
    # ---------------------------------------------------------
    elements.append(Paragraph("<b>Expense Breakdown</b>", section_header_style))
    
    expense_data = [['Category', 'Amount']]
    if period.categories:
        for cat, amt in period.categories.items():
            expense_data.append([cat, f"Rs. {amt:,.2f}"])
    else:
        expense_data.append(['No expenses recorded', 'Rs. 0.00'])
        
    expense_table = Table(expense_data, colWidths=[300, 150])
    expense_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
    ]))
    elements.append(expense_table)
    elements.append(Spacer(1, 15))
    
    # ---------------------------------------------------------
    # Savings Analysis
    # ---------------------------------------------------------
    elements.append(Paragraph("<b>Savings Analysis</b>", section_header_style))
    
    savings_rate = 0.0
    if period.total_income > 0:
        savings_rate = (period.savings / period.total_income) * 100
        
    elements.append(Paragraph(f"<b>Savings Rate:</b> {savings_rate:,.1f}%", normal_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Your savings rate for this period was {savings_rate:,.1f}%.", normal_style))
    
    # Generate PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
