import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String

# FinZave Brand Colors
FZ_BLACK = colors.HexColor('#0a0a0a')
FZ_WHITE = colors.HexColor('#ffffff')
FZ_RED = colors.HexColor('#e11d48')
FZ_GREEN = colors.HexColor('#16a34a')
FZ_DARK_GRAY = colors.HexColor('#52525b')
FZ_LIGHT_GRAY = colors.HexColor('#e4e4e7')
FZ_GRAY_BG = colors.HexColor('#fafafa')

def create_logo():
    d = Drawing(120, 30)
    
    # The FZ Box
    r = Rect(0, 0, 24, 24, rx=4, ry=4)
    r.fillColor = FZ_BLACK
    r.strokeColor = FZ_BLACK
    d.add(r)
    
    # FZ Text inside box
    s1 = String(4, 6, "FZ", fontName='Helvetica-Bold', fontSize=12, fillColor=FZ_WHITE)
    d.add(s1)
    
    # FinZave Text
    s2 = String(32, 4, "FinZave", fontName='Helvetica-Bold', fontSize=20, fillColor=FZ_BLACK)
    d.add(s2)
    
    return d

def create_header(period_str):
    styles = getSampleStyleSheet()
    subtitle_style = ParagraphStyle('HeaderSubtitle', parent=styles['Normal'], fontSize=12, textColor=FZ_DARK_GRAY, spaceAfter=20, fontName='Helvetica')
    
    right_style = ParagraphStyle('HeaderRight', parent=styles['Normal'], fontSize=10, textColor=FZ_DARK_GRAY, alignment=2, fontName='Helvetica')
    right_bold = ParagraphStyle('HeaderRightBold', parent=styles['Normal'], fontSize=10, textColor=FZ_BLACK, alignment=2, fontName='Helvetica-Bold')
    
    gen_date = datetime.now().strftime('%d %B %Y')
    
    data = [
        [
            create_logo(),
            Paragraph("Reporting Period:", right_style)
        ],
        [
            Paragraph("Personal Financial Report", subtitle_style),
            Paragraph(period_str, right_bold)
        ],
        [
            '',
            Paragraph(f"Generated: {gen_date}", right_style)
        ]
    ]
    
    t = Table(data, colWidths=[4.5*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,-1), (-1,-1), 1.5, FZ_BLACK),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 15),
    ]))
    return t

def create_financial_summary(period, health_data, is_incomplete):
    styles = getSampleStyleSheet()
    label_style = ParagraphStyle('SummaryLabel', parent=styles['Normal'], fontSize=11, textColor=FZ_DARK_GRAY, fontName='Helvetica')
    value_style = ParagraphStyle('SummaryValue', parent=styles['Normal'], fontSize=11, textColor=FZ_BLACK, fontName='Helvetica-Bold', alignment=2)
    
    if is_incomplete:
        savings_val = "Provisional"
        savings_rate_val = "Provisional"
    else:
        savings_val = f"Rs. {period.savings:,.2f}"
        savings_rate = (period.savings / period.total_income * 100) if period.total_income > 0 else 0
        savings_rate_val = f"{savings_rate:.1f}%"
        
    score_str = f"{health_data['score']}/100" if health_data and health_data.get('score') is not None else "N/A"
    
    data = [
        [Paragraph("Total Income", label_style), Paragraph(f"Rs. {period.total_income:,.2f}", value_style)],
        [Paragraph("Total Expenses", label_style), Paragraph(f"Rs. {period.total_expenses:,.2f}", value_style)],
        [Paragraph("Net Savings", label_style), Paragraph(savings_val, value_style)],
        [Paragraph("Savings Rate", label_style), Paragraph(savings_rate_val, value_style)],
        [Paragraph("Financial Score", label_style), Paragraph(score_str, value_style)]
    ]
    
    t = Table(data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, FZ_LIGHT_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    return t

def create_incomplete_warning():
    styles = getSampleStyleSheet()
    warning_title = ParagraphStyle('WarnTitle', parent=styles['Normal'], fontSize=12, textColor=FZ_RED, fontName='Helvetica-Bold', spaceAfter=6)
    warning_text = ParagraphStyle('WarnText', parent=styles['Normal'], fontSize=10, textColor=FZ_BLACK, leading=14)
    
    data = [
        [Paragraph("Tracking Status: Incomplete Month", warning_title)],
        [Paragraph("Expense tracking is incomplete for this period. Savings calculations are provisional until all expenses are recorded.", warning_text)]
    ]
    
    t = Table(data, colWidths=[7.0*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), FZ_GRAY_BG),
        ('BOX', (0,0), (-1,-1), 1, FZ_RED),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
    ]))
    return t

def create_professional_table(headers, row_data, col_widths, red_amount=False):
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('TH', parent=styles['Normal'], fontSize=10, textColor=FZ_DARK_GRAY, fontName='Helvetica-Bold')
    row_style = ParagraphStyle('TD', parent=styles['Normal'], fontSize=10, textColor=FZ_BLACK, fontName='Helvetica')
    amt_style = ParagraphStyle('TDAmt', parent=styles['Normal'], fontSize=10, textColor=FZ_RED if red_amount else FZ_BLACK, fontName='Helvetica', alignment=2)
    pct_style = ParagraphStyle('TDPct', parent=styles['Normal'], fontSize=10, textColor=FZ_DARK_GRAY, fontName='Helvetica', alignment=2)
    
    data = [[Paragraph(h, header_style) if i == 0 else Paragraph(h, ParagraphStyle('THR', parent=header_style, alignment=2)) for i, h in enumerate(headers)]]
    
    for row in row_data:
        formatted_row = [Paragraph(row[0], row_style)]
        formatted_row.append(Paragraph(row[1], amt_style))
        if len(row) > 2:
            formatted_row.append(Paragraph(row[2], pct_style))
        data.append(formatted_row)
        
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1.5, FZ_BLACK),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t

def create_footer():
    styles = getSampleStyleSheet()
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=FZ_DARK_GRAY, alignment=1, fontName='Helvetica')
    text = (
        "<b>FinZave | Personal Financial Intelligence</b><br/>"
        "Disclaimer: This report is generated from recorded financial data. "
        "Actual financial decisions should consider changing income, expenses, and market conditions."
    )
    return Paragraph(text, footer_style)

def generate_financial_report_pdf(period, health_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=50, leftMargin=50,
        topMargin=40, bottomMargin=60
    )
    
    elements = []
    styles = getSampleStyleSheet()
    section_header = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=16, textColor=FZ_BLACK, spaceBefore=35, spaceAfter=20, fontName='Helvetica-Bold')
    
    try:
        dt = datetime.strptime(period.period_id, '%Y-%m')
        period_str = dt.strftime('%B %Y')
    except Exception:
        period_str = period.period_id
        
    # Check completeness
    is_incomplete = False
    if period.total_income > 0 and (period.total_expenses == 0 or not period.categories):
        is_incomplete = True
        
    # --- PAGE 1: HEADER & SUMMARY ---
    elements.append(create_header(period_str))
    
    elements.append(Paragraph("Executive Financial Summary", section_header))
    
    if is_incomplete:
        elements.append(create_incomplete_warning())
        elements.append(Spacer(1, 15))
        
    elements.append(create_financial_summary(period, health_data, is_incomplete))
    
    elements.append(PageBreak())
    
    # --- PAGE 2: INCOME & EXPENSES ---
    elements.append(create_header(period_str))
    
    elements.append(Paragraph("Income Breakdown", section_header))
    inc_headers = ['Source', 'Amount']
    inc_data = [
        ['Fixed Income', f"Rs. {period.fixed_income:,.2f}"],
        ['Variable Income', f"Rs. {period.variable_income:,.2f}"]
    ]
    elements.append(create_professional_table(inc_headers, inc_data, [4.5*inch, 2.5*inch]))
    
    elements.append(Paragraph("Expense Analysis", section_header))
    exp_headers = ['Category', 'Amount', 'Percentage']
    exp_data = []
    if period.categories:
        sorted_cats = sorted(period.categories.items(), key=lambda x: x[1], reverse=True)
        for cat, amt in sorted_cats:
            pct = (amt / period.total_expenses * 100) if period.total_expenses > 0 else 0
            exp_data.append([cat, f"Rs. {amt:,.2f}", f"{pct:.1f}%"])
    else:
        exp_data.append(['No expenses recorded', 'Rs. 0.00', '0.0%'])
        
    elements.append(create_professional_table(exp_headers, exp_data, [3.5*inch, 2*inch, 1.5*inch], red_amount=True))
    
    # No Page 3 (Intelligence removed)
    
    # FOOTER Generation
    def add_footer(canvas, doc):
        canvas.saveState()
        footer = create_footer()
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, 25)
        
        # Page Number
        page_num = canvas.getPageNumber()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(FZ_DARK_GRAY)
        canvas.drawRightString(doc.leftMargin + doc.width, 25, f"Page {page_num}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
