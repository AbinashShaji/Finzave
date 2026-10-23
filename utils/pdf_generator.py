"""
Module: utils/pdf_generator.py

Purpose:
Generates comprehensive, professional multi-page Monthly Financial Analysis Reports in PDF format.

Sections:
1. Executive Summary (Reporting period, generation date, totals, net savings, rate, score, category, confidence, narrative summary)
2. Health Score Breakdown (Overall score & category, 4 pillars: Savings 40, Expense Mgmt 25, Stability 20, Spending Control 15, factors)
3. Income Analysis (Fixed vs variable, itemized sources, MoM comparison and percentage change)
4. Expense Analysis (Category totals, amount, % of total expenses, % of income consumed, largest expense callout)
5. Savings and Cash Flow (Net savings, savings rate, MoM comparison of income, expenses, savings)
6. Historical Comparison (Chronological multi-month trajectory for available periods: income, expenses, savings, health score, trends)
7. Financial Insights and Recommendations (Actionable observations from actual transactions, distinguished from recommendations)
8. Financial Goals (Goal name, target amount, current progress, remaining amount, deadline, completion %, status)
9. Methodology and Data Limitations (Calculation definitions, incomplete data notice, statutory disclaimer)
"""
import os
import io
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.pdfgen import canvas

from utils.rule_engine import FinancialPeriod, percentage_change
from analysis.scoring import calculate_health_score
from analysis.services import build_overview, _detect_patterns

# ---------------------------------------------------------------------------
# FONT CONFIGURATION (Unicode Indian Rupee ₹ Support)
# ---------------------------------------------------------------------------
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_OBLIQUE = 'Helvetica-Oblique'

try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    font_candidates_regular = [
        'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf'
    ]
    font_candidates_bold = [
        'C:/Windows/Fonts/arialbd.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'
    ]
    
    reg_path = next((p for p in font_candidates_regular if os.path.exists(p)), None)
    bold_path = next((p for p in font_candidates_bold if os.path.exists(p)), None)
    
    if reg_path and bold_path:
        pdfmetrics.registerFont(TTFont('FinZaveFont', reg_path))
        pdfmetrics.registerFont(TTFont('FinZaveFont-Bold', bold_path))
        FONT_REGULAR = 'FinZaveFont'
        FONT_BOLD = 'FinZaveFont-Bold'
except Exception:
    pass

# ---------------------------------------------------------------------------
# BRAND PALETTE
# ---------------------------------------------------------------------------
FZ_BLACK = colors.HexColor('#0a0a0a')
FZ_WHITE = colors.HexColor('#ffffff')
FZ_RED = colors.HexColor('#e11d48')
FZ_GREEN = colors.HexColor('#16a34a')
FZ_BLUE = colors.HexColor('#2563eb')
FZ_AMBER = colors.HexColor('#d97706')
FZ_DARK_GRAY = colors.HexColor('#27272a')
FZ_MID_GRAY = colors.HexColor('#71717a')
FZ_LIGHT_GRAY = colors.HexColor('#e4e4e7')
FZ_GRAY_BG = colors.HexColor('#f8fafc')
FZ_BORDER = colors.HexColor('#e2e8f0')


def format_inr(amount: Any, decimals: int = 0) -> str:
    """Formats amount into standard Indian currency representation (e.g. ₹1,50,000 or -₹25,000)."""
    if amount is None:
        return 'N/A'
    try:
        val = float(amount)
    except (ValueError, TypeError):
        return 'N/A'
    is_neg = val < 0
    val = abs(val)
    if decimals > 0:
        base_str = f'{val:.{decimals}f}'
        int_part, dec_part = base_str.split('.')
        dec_part = '.' + dec_part
    else:
        int_part = str(int(round(val)))
        dec_part = ''
    if len(int_part) > 3:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        int_part = ','.join(groups) + ',' + last3
    return f'-₹{int_part}{dec_part}' if is_neg else f'₹{int_part}{dec_part}'


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that writes dynamic page totals and repeated running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        # Footer on all pages
        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(FZ_MID_GRAY)
        self.drawString(36, 22, "FinZave | Personal Financial Intelligence — Confidential & Proprietary")
        self.drawRightString(letter[0] - 36, 22, f"Page {self._pageNumber} of {page_count}")
        
        self.setStrokeColor(FZ_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 32, letter[0] - 36, 32)

        # Running header on page 2 onwards
        if self._pageNumber > 1:
            self.setFont(FONT_REGULAR, 8)
            self.setFillColor(FZ_MID_GRAY)
            self.drawString(36, letter[1] - 28, "FinZave Personal Financial Analysis Report")
            period_str = getattr(self, 'report_period_label', '')
            if period_str:
                self.drawRightString(letter[0] - 36, letter[1] - 28, period_str)
            self.line(36, letter[1] - 32, letter[0] - 36, letter[1] - 32)

        self.restoreState()


def create_logo():
    d = Drawing(120, 26)
    r = Rect(0, 0, 22, 22, rx=4, ry=4)
    r.fillColor = FZ_BLACK
    r.strokeColor = FZ_BLACK
    d.add(r)
    s1 = String(3.5, 5.5, "FZ", fontName=FONT_BOLD, fontSize=11, fillColor=FZ_WHITE)
    d.add(s1)
    s2 = String(28, 4, "FinZave", fontName=FONT_BOLD, fontSize=18, fillColor=FZ_BLACK)
    d.add(s2)
    return d


def create_header(period_str):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('RepTitle', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=14, textColor=FZ_BLACK, leading=17)
    right_bold = ParagraphStyle('RepRightBold', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=10, textColor=FZ_BLACK, alignment=2)
    right_sub = ParagraphStyle('RepRightSub', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=8.5, textColor=FZ_MID_GRAY, alignment=2)
    
    gen_date = datetime.now().strftime('%d %B %Y')
    
    data = [
        [
            create_logo(),
            Paragraph(f"Reporting Period: <b>{period_str}</b>", right_bold)
        ],
        [
            Paragraph("Monthly Financial Analysis Report", title_style),
            Paragraph(f"Generated on {gen_date}", right_sub)
        ]
    ]
    
    t = Table(data, colWidths=[3.8*inch, 3.7*inch])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LINEBELOW', (0,-1), (-1,-1), 1.2, FZ_BLACK),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
    ]))
    return t


def create_section_header(title, subtitle=None):
    styles = getSampleStyleSheet()
    elements = []
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontName=FONT_BOLD, fontSize=11.5, textColor=FZ_BLACK, spaceBefore=8, spaceAfter=2, keepWithNext=True)
    elements.append(Paragraph(title, h_style))
    if subtitle:
        sub_style = ParagraphStyle('SecSub', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=8, textColor=FZ_MID_GRAY, spaceAfter=4, keepWithNext=True)
        elements.append(Paragraph(subtitle, sub_style))
    return elements


def generate_financial_report_pdf(
    period: FinancialPeriod,
    health_data: Dict[str, Any],
    historical_periods: Optional[List[FinancialPeriod]] = None,
    overview: Optional[Dict[str, Any]] = None,
    goals: Optional[List[Dict[str, Any]]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    income_sources: Optional[List[Dict[str, Any]]] = None,
    historical_scores: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Renders a comprehensive, multi-page Monthly Financial Analysis Report PDF.
    Preserves existing scoring numbers and data integrity without fabricating metrics.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=45
    )

    try:
        dt = datetime.strptime(period.period_id, '%Y-%m')
        period_str = dt.strftime('%B %Y')
    except Exception:
        period_str = period.period_id

    doc.report_period_label = period_str

    styles = getSampleStyleSheet()
    
    body_style = ParagraphStyle('PBody', fontName=FONT_REGULAR, fontSize=8.5, textColor=FZ_DARK_GRAY, leading=12)
    table_cell = ParagraphStyle('TCell', fontName=FONT_REGULAR, fontSize=8, textColor=FZ_BLACK, leading=11)
    table_cell_bold = ParagraphStyle('TCellB', fontName=FONT_BOLD, fontSize=8, textColor=FZ_BLACK, leading=11)
    table_cell_right = ParagraphStyle('TCellR', fontName=FONT_REGULAR, fontSize=8, textColor=FZ_BLACK, leading=11, alignment=2)
    table_cell_right_bold = ParagraphStyle('TCellRB', fontName=FONT_BOLD, fontSize=8, textColor=FZ_BLACK, leading=11, alignment=2)
    th_style = ParagraphStyle('TH', fontName=FONT_BOLD, fontSize=8, textColor=FZ_WHITE, leading=10)
    th_right = ParagraphStyle('THR', fontName=FONT_BOLD, fontSize=8, textColor=FZ_WHITE, leading=10, alignment=2)

    elements = []

    is_incomplete = (period.status == "incomplete") or (period.total_income > 0 and (period.total_expenses == 0 or not period.categories))
    prev_period = historical_periods[-2] if historical_periods and len(historical_periods) >= 2 else None

    # =========================================================================
    # PAGE 1: EXECUTIVE SUMMARY, HEALTH SCORE BREAKDOWN, CASH FLOW DYNAMICS
    # =========================================================================
    elements.append(create_header(period_str))
    elements.append(Spacer(1, 6))

    # Incomplete Warning if applicable
    if is_incomplete:
        warn_title = ParagraphStyle('WT', fontName=FONT_BOLD, fontSize=9.5, textColor=FZ_RED)
        warn_desc = ParagraphStyle('WD', fontName=FONT_REGULAR, fontSize=8, textColor=FZ_DARK_GRAY, leading=11)
        w_table = Table([
            [Paragraph("<b>Status: Incomplete Monthly Tracking</b>", warn_title)],
            [Paragraph("Expense logging for this month is incomplete. Net savings and health score are calculated provisionally until all expenses are recorded.", warn_desc)]
        ], colWidths=[540])
        w_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff1f2')),
            ('BOX', (0,0), (-1,-1), 1, FZ_RED),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(w_table)
        elements.append(Spacer(1, 6))

    # 1. Executive Summary
    elements.extend(create_section_header("1. Executive Summary", "High-level snapshot of monthly performance and overall financial condition."))
    
    narrative_title_text = overview.get("narrative_title", "Monthly Financial Summary") if overview else "Monthly Financial Summary"
    narrative_body_text = overview.get("narrative_body", "Financial analysis based on recorded income, expenditures, and savings trends.") if overview else "Financial analysis based on recorded income, expenditures, and savings trends."
    
    narrative_title_p = ParagraphStyle('NT', fontName=FONT_BOLD, fontSize=9, textColor=FZ_BLACK, leading=12)
    narrative_body_p = ParagraphStyle('NB', fontName=FONT_REGULAR, fontSize=8, textColor=FZ_DARK_GRAY, leading=11)
    
    n_table = Table([
        [Paragraph(narrative_title_text, narrative_title_p)],
        [Paragraph(narrative_body_text, narrative_body_p)]
    ], colWidths=[540])
    n_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), FZ_GRAY_BG),
        ('BOX', (0,0), (-1,-1), 0.75, FZ_BORDER),
        ('LINELEFT', (0,0), (0,-1), 3, FZ_BLACK),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(n_table)
    elements.append(Spacer(1, 6))

    # Executive KPI Grid (5 Columns)
    hs_score = health_data.get('score')
    score_str = f"{hs_score}/100" if hs_score is not None else "N/A"
    cat_str = health_data.get('category', 'N/A') or 'N/A'
    conf_str = f"{health_data.get('confidence', 'N/A')}%" if health_data.get('confidence') is not None else "N/A"
    
    rate_val = (period.savings_rate * 100) if period.savings_rate is not None else 0.0
    rate_str = f"{rate_val:.1f}%" if period.total_income > 0 else "0.0%"
    if is_incomplete:
        savings_display = "Provisional"
        rate_display = "Provisional"
    else:
        savings_display = format_inr(period.savings)
        rate_display = rate_str

    kpi_hdr = ParagraphStyle('KH', fontName=FONT_BOLD, fontSize=7.5, textColor=FZ_MID_GRAY, alignment=1)
    kpi_val = ParagraphStyle('KV', fontName=FONT_BOLD, fontSize=11, textColor=FZ_BLACK, alignment=1)
    kpi_sub = ParagraphStyle('KS', fontName=FONT_REGULAR, fontSize=7, textColor=FZ_MID_GRAY, alignment=1)
    
    kpi_data = [
        [
            Paragraph("GROSS INCOME", kpi_hdr),
            Paragraph("TOTAL EXPENSES", kpi_hdr),
            Paragraph("NET SAVINGS", kpi_hdr),
            Paragraph("SAVINGS RATE", kpi_hdr),
            Paragraph("HEALTH SCORE", kpi_hdr)
        ],
        [
            Paragraph(format_inr(period.total_income), kpi_val),
            Paragraph(format_inr(period.total_expenses), kpi_val),
            Paragraph(savings_display, kpi_val),
            Paragraph(rate_display, kpi_val),
            Paragraph(score_str, kpi_val)
        ],
        [
            Paragraph(f"Fixed: {format_inr(period.fixed_income)}", kpi_sub),
            Paragraph(f"{(period.total_expenses/period.total_income*100):.0f}% of income" if period.total_income > 0 else "—", kpi_sub),
            Paragraph("Capital Retained" if period.savings >= 0 else "Net Deficit", kpi_sub),
            Paragraph("Target: ≥20.0%", kpi_sub),
            Paragraph(f"{cat_str} ({conf_str} Conf)", kpi_sub)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[108, 108, 108, 108, 108])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), FZ_GRAY_BG),
        ('BOX', (0,0), (-1,-1), 0.75, FZ_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, FZ_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 8))

    # 2. Health Score Breakdown
    elements.extend(create_section_header("2. Health Score Architecture & Pillar Breakdown", "100-point multi-factor model scaled by historical data confidence."))

    pillars = health_data.get('pillars', {})
    adjustments = health_data.get('adjustments', [])
    
    p1 = pillars.get('savings_rate', {})
    p2 = pillars.get('expense_ratio', {})
    p3 = pillars.get('stability_trend', {})
    p4 = pillars.get('spending_control', {})

    def get_adj_reason(idx, fallback):
        if idx < len(adjustments):
            return adjustments[idx].get('reason', fallback)
        return fallback

    hs_table_data = [
        [
            Paragraph("PILLAR", th_style),
            Paragraph("EARNED", th_right),
            Paragraph("MAX", th_right),
            Paragraph("BENCHMARK", th_style),
            Paragraph("EVALUATED FACTORS & TRAJECTORY", th_style)
        ],
        [
            Paragraph("<b>Savings Rate</b>", table_cell),
            Paragraph(str(p1.get('score', 0)), table_cell_right_bold),
            Paragraph(str(p1.get('max', 40)), table_cell_right),
            Paragraph("≥40% Rate = 40 pts", table_cell),
            Paragraph(get_adj_reason(0, f"Current savings rate is {rate_str}"), table_cell)
        ],
        [
            Paragraph("<b>Expense Management</b>", table_cell),
            Paragraph(str(p2.get('score', 0)), table_cell_right_bold),
            Paragraph(str(p2.get('max', 25)), table_cell_right),
            Paragraph("&lt;50% Income = 25 pts", table_cell),
            Paragraph(get_adj_reason(1, f"Expenses consume {(period.total_expenses/period.total_income*100) if period.total_income > 0 else 0:.1f}% of income"), table_cell)
        ],
        [
            Paragraph("<b>Financial Stability</b>", table_cell),
            Paragraph(str(p3.get('score', 0)), table_cell_right_bold),
            Paragraph(str(p3.get('max', 20)), table_cell_right),
            Paragraph("MoM Trajectory = 20 pts", table_cell),
            Paragraph(get_adj_reason(2, "Evaluated on income continuity and savings stability"), table_cell)
        ],
        [
            Paragraph("<b>Spending Control</b>", table_cell),
            Paragraph(str(p4.get('score', 0)), table_cell_right_bold),
            Paragraph(str(p4.get('max', 15)), table_cell_right),
            Paragraph("Discretionary &lt;30% = 15 pts", table_cell),
            Paragraph(get_adj_reason(3, "Evaluated on discretionary spending discipline and spending spike absence"), table_cell)
        ],
        [
            Paragraph("<b>TOTAL SCORE</b>", table_cell_bold),
            Paragraph(f"<b>{health_data.get('raw_score', 0)}</b>", table_cell_right_bold),
            Paragraph("<b>100</b>", table_cell_right_bold),
            Paragraph(f"Confidence: {conf_str}", table_cell_bold),
            Paragraph(f"<b>Final Score: {score_str} ({cat_str} Status)</b>", table_cell_bold)
        ]
    ]

    hs_table = Table(hs_table_data, colWidths=[120, 50, 45, 115, 210])
    hs_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,1), (-1,-2), 0.5, FZ_LIGHT_GRAY),
        ('LINEABOVE', (0,-1), (-1,-1), 1.2, FZ_BLACK),
        ('BACKGROUND', (0,-1), (-1,-1), FZ_GRAY_BG),
    ]))
    elements.append(hs_table)
    elements.append(Spacer(1, 8))

    # 5. Savings and Cash Flow Dynamics (Placed on Page 1 for cohesive balance sheet view)
    elements.extend(create_section_header("3. Savings & Cash Flow Dynamics", "Net capital formation and period-over-period variance."))
    
    inc_diff_str = "—"
    exp_diff_str = "—"
    sav_diff_str = "—"
    if prev_period and not is_incomplete:
        inc_diff = period.total_income - prev_period.total_income
        exp_diff = period.total_expenses - prev_period.total_expenses
        sav_diff = period.savings - prev_period.savings
        
        ic_pct = percentage_change(period.total_income, prev_period.total_income)
        ec_pct = percentage_change(period.total_expenses, prev_period.total_expenses)
        sc_pct = percentage_change(period.savings, prev_period.savings)
        
        inc_diff_str = f"{format_inr(inc_diff)} ({ic_pct*100:+.1f}%)" if ic_pct is not None else format_inr(inc_diff)
        exp_diff_str = f"{format_inr(exp_diff)} ({ec_pct*100:+.1f}%)" if ec_pct is not None else format_inr(exp_diff)
        sav_diff_str = f"{format_inr(sav_diff)} ({sc_pct*100:+.1f}%)" if sc_pct is not None else format_inr(sav_diff)

    cf_data = [
        [
            Paragraph("METRIC", th_style),
            Paragraph("CURRENT PERIOD", th_right),
            Paragraph("PREVIOUS PERIOD", th_right),
            Paragraph("MoM NET CHANGE", th_right)
        ],
        [
            Paragraph("Gross Cash Inflow", table_cell),
            Paragraph(format_inr(period.total_income), table_cell_right_bold),
            Paragraph(format_inr(prev_period.total_income) if prev_period else "—", table_cell_right),
            Paragraph(inc_diff_str, table_cell_right)
        ],
        [
            Paragraph("Total Outflow / Expenditures", table_cell),
            Paragraph(format_inr(period.total_expenses), table_cell_right_bold),
            Paragraph(format_inr(prev_period.total_expenses) if prev_period else "—", table_cell_right),
            Paragraph(exp_diff_str, table_cell_right)
        ],
        [
            Paragraph("Net Capital Savings", table_cell),
            Paragraph(savings_display, table_cell_right_bold),
            Paragraph(format_inr(prev_period.savings) if prev_period else "—", table_cell_right),
            Paragraph(sav_diff_str, table_cell_right)
        ]
    ]
    cf_table = Table(cf_data, colWidths=[160, 120, 120, 140])
    cf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
    ]))
    elements.append(cf_table)

    # Force Page Break to Page 2
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 2: INCOME STRUCTURE & DETAILED EXPENSE ANALYSIS
    # =========================================================================
    # 3. Income Analysis
    elements.extend(create_section_header("4. Income Structure & Source Breakdown", "Itemized recurring and variable cash inflows."))

    sources_to_show = income_sources or []
    if not sources_to_show:
        if period.fixed_income > 0:
            sources_to_show.append({"source": "Fixed Recurring Income", "type": "Fixed", "amount": period.fixed_income})
        if period.variable_income > 0:
            sources_to_show.append({"source": "Variable Inflow", "type": "Variable", "amount": period.variable_income})
    
    if not sources_to_show:
        sources_to_show.append({"source": "No income recorded for this period", "type": "N/A", "amount": 0.0})

    inc_rows = [
        [
            Paragraph("INCOME STREAM / SOURCE", th_style),
            Paragraph("STREAM TYPE", th_style),
            Paragraph("AMOUNT", th_right),
            Paragraph("SHARE OF INFLOW", th_right)
        ]
    ]

    for item in sources_to_show:
        amt = item.get('amount', 0.0)
        share = (amt / period.total_income * 100) if period.total_income > 0 else 0.0
        inc_rows.append([
            Paragraph(str(item.get('source', 'Income')), table_cell),
            Paragraph(str(item.get('type', 'Fixed')), table_cell),
            Paragraph(format_inr(amt), table_cell_right_bold),
            Paragraph(f"{share:.1f}%", table_cell_right)
        ])

    inc_table = Table(inc_rows, colWidths=[240, 100, 110, 90])
    inc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
    ]))
    elements.append(inc_table)
    elements.append(Spacer(1, 10))

    # 4. Expense Analysis
    elements.extend(create_section_header("5. Expense Analysis & Category Distribution", "Granular breakdown of all expenditures by category."))

    sorted_cats = sorted(period.categories.items(), key=lambda x: x[1], reverse=True) if period.categories else []
    if sorted_cats:
        top_cat, top_amt = sorted_cats[0]
        top_exp_pct = (top_amt / period.total_expenses * 100) if period.total_expenses > 0 else 0.0
        top_inc_pct = (top_amt / period.total_income * 100) if period.total_income > 0 else 0.0
        
        top_box = Table([
            [Paragraph(f"<b>Largest Expenditure Focus:</b> {top_cat} is your primary expense at <b>{format_inr(top_amt)}</b>, accounting for <b>{top_exp_pct:.1f}%</b> of total spending and consuming <b>{top_inc_pct:.1f}%</b> of monthly income.", body_style)]
        ], colWidths=[540])
        top_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), FZ_GRAY_BG),
            ('BOX', (0,0), (-1,-1), 0.75, FZ_BORDER),
            ('LINELEFT', (0,0), (0,-1), 3, FZ_RED),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(top_box)
        elements.append(Spacer(1, 6))

    exp_rows = [
        [
            Paragraph("CATEGORY", th_style),
            Paragraph("AMOUNT", th_right),
            Paragraph("SHARE OF EXPENSES", th_right),
            Paragraph("INCOME CONSUMPTION", th_right),
            Paragraph("EXPENDITURE NATURE", th_style)
        ]
    ]

    FIXED_ESSENTIALS = {'Rent & Housing', 'Rent', 'EMI', 'Insurance', 'Utilities'}

    if sorted_cats:
        for cat, amt in sorted_cats:
            exp_pct = (amt / period.total_expenses * 100) if period.total_expenses > 0 else 0.0
            inc_pct = (amt / period.total_income * 100) if period.total_income > 0 else 0.0
            nature = "Fixed Essential" if cat in FIXED_ESSENTIALS else "Variable / Discretionary"
            exp_rows.append([
                Paragraph(cat, table_cell_bold),
                Paragraph(format_inr(amt), table_cell_right),
                Paragraph(f"{exp_pct:.1f}%", table_cell_right),
                Paragraph(f"{inc_pct:.1f}%", table_cell_right),
                Paragraph(nature, table_cell)
            ])
    else:
        exp_rows.append([
            Paragraph("No expenditures recorded for this period", table_cell),
            Paragraph(format_inr(0), table_cell_right),
            Paragraph("0.0%", table_cell_right),
            Paragraph("0.0%", table_cell_right),
            Paragraph("—", table_cell)
        ])

    exp_table = Table(exp_rows, colWidths=[150, 95, 100, 105, 90])
    exp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
    ]))
    elements.append(exp_table)

    # Force Page Break to Page 3
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 3: HISTORICAL PERFORMANCE, GOALS, INSIGHTS & METHODOLOGY
    # =========================================================================
    # 6. Historical Comparison
    elements.extend(create_section_header("6. Historical Performance & Trend Trajectory", "Multi-period chronological trajectory across verified accounting periods."))

    hist_periods_to_show = [p for p in (historical_periods or [period]) if (p.total_income > 0 or p.total_expenses > 0)]
    if not hist_periods_to_show:
        hist_periods_to_show = [period]

    hist_rows = [
        [
            Paragraph("PERIOD", th_style),
            Paragraph("INCOME", th_right),
            Paragraph("EXPENSES", th_right),
            Paragraph("NET SAVINGS", th_right),
            Paragraph("SAVINGS RATE", th_right),
            Paragraph("HEALTH SCORE", th_right)
        ]
    ]

    scores_dict = historical_scores or {}

    for p in hist_periods_to_show[-8:]:
        p_rate = (p.savings_rate * 100) if p.savings_rate is not None else 0.0
        p_score_obj = scores_dict.get(p.period_id)
        if p_score_obj and isinstance(p_score_obj, dict):
            s_val = p_score_obj.get('score')
            p_score_str = f"{s_val}/100" if s_val is not None else "—"
        else:
            p_score_str = "—"
            
        hist_rows.append([
            Paragraph(f"<b>{p.period_id}</b>", table_cell),
            Paragraph(format_inr(p.total_income), table_cell_right),
            Paragraph(format_inr(p.total_expenses), table_cell_right),
            Paragraph(format_inr(p.savings), table_cell_right_bold),
            Paragraph(f"{p_rate:.1f}%", table_cell_right),
            Paragraph(p_score_str, table_cell_right_bold)
        ])

    hist_table = Table(hist_rows, colWidths=[80, 95, 95, 95, 85, 90])
    hist_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
    ]))
    elements.append(hist_table)
    elements.append(Spacer(1, 8))

    # 7. Insights and Recommendations
    elements.extend(create_section_header("7. Financial Insights & Strategic Guidance", "Deterministic behavioral observations and actionable guidance."))

    obs_list = []
    if overview and overview.get("savings_insights"):
        obs_list.extend(overview.get("savings_insights", []))
    
    if historical_periods and len(historical_periods) >= 3:
        patterns = _detect_patterns(historical_periods)
        obs_list.extend(patterns)

    if not obs_list:
        obs_list.append("Baseline financial tracking established. Historical spending patterns will evolve as transactions accumulate.")

    elements.append(Paragraph("<b>System Observations & Category Shifts:</b>", table_cell_bold))
    obs_data = []
    for obs in obs_list[:3]:
        obs_data.append([
            Paragraph("•", ParagraphStyle('Bullet', fontName=FONT_BOLD, fontSize=8, textColor=FZ_BLACK)),
            Paragraph(obs, body_style)
        ])
    obs_table = Table(obs_data, colWidths=[15, 525])
    obs_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(obs_table)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>Actionable Recommendations:</b>", table_cell_bold))
    recom_list = recommendations or []
    if recom_list:
        recom_rows = [
            [
                Paragraph("PRIORITY", th_style),
                Paragraph("ACTION ITEM & GUIDANCE", th_style)
            ]
        ]
        for r in recom_list[:3]:
            prio = r.get("priority", "MEDIUM")
            prio_color = FZ_RED if prio == "HIGH" else (FZ_AMBER if prio == "MEDIUM" else FZ_BLUE)
            prio_p = Paragraph(f"<b><font color='{prio_color.hexval()}'>[{prio}]</font></b>", table_cell_bold)
            msg_p = Paragraph(f"<b>{r.get('title', 'Recommendation')}</b>: {r.get('message', '')}", body_style)
            recom_rows.append([prio_p, msg_p])
            
        recom_table = Table(recom_rows, colWidths=[70, 470])
        recom_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
        ]))
        elements.append(recom_table)
    else:
        no_recom = Paragraph("All financial metrics remain within standard operational thresholds. Maintain consistent capital allocation.", body_style)
        elements.append(no_recom)

    elements.append(Spacer(1, 8))

    # 8. Financial Goals Tracking
    elements.extend(create_section_header("8. Financial Goals Progress", "Active capital targets and milestone fulfillment status."))

    goals_to_show = goals or []
    if goals_to_show:
        goal_rows = [
            [
                Paragraph("GOAL NAME", th_style),
                Paragraph("TARGET", th_right),
                Paragraph("SAVED", th_right),
                Paragraph("REMAINING", th_right),
                Paragraph("DEADLINE", th_style),
                Paragraph("STATUS", th_style)
            ]
        ]
        for g in goals_to_show[:4]:
            t_amt = g.get('target_amount', 0.0)
            s_amt = g.get('current_saved', 0.0)
            r_amt = g.get('remaining_amount', max(0.0, t_amt - s_amt))
            pct = g.get('completion_pct', (s_amt / t_amt * 100) if t_amt > 0 else 0.0)
            t_date = g.get('target_date')
            t_date_str = t_date.strftime('%b %Y') if hasattr(t_date, 'strftime') else str(t_date or '—')
            status = g.get('status', 'ACTIVE')
            
            goal_rows.append([
                Paragraph(f"<b>{g.get('goal_name', 'Goal')}</b>", table_cell),
                Paragraph(format_inr(t_amt), table_cell_right),
                Paragraph(format_inr(s_amt), table_cell_right_bold),
                Paragraph(format_inr(r_amt), table_cell_right),
                Paragraph(t_date_str, table_cell),
                Paragraph(f"{status} ({pct:.0f}%)", table_cell)
            ])
            
        goal_table = Table(goal_rows, colWidths=[140, 80, 80, 80, 80, 80])
        goal_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), FZ_BLACK),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, FZ_LIGHT_GRAY),
        ]))
        elements.append(goal_table)
    else:
        no_goals_p = Paragraph("No financial goals are currently configured for this account. Goals can be created to monitor target allocations.", body_style)
        elements.append(no_goals_p)

    elements.append(Spacer(1, 8))

    # 9. Methodology and Data Limitations
    elements.extend(create_section_header("9. Methodology, Data Limitations & Legal Disclaimer"))

    meth_text = (
        "<b>Calculation Methodology:</b> Net Savings = Total Inflow – Total Outflow. Savings Rate = Net Savings / Gross Income. "
        "Health Score is evaluated on a 100-point model across 4 pillars: Savings Rate (40%), Expense Management (25%), Financial Stability (20%), and Spending Control (15%), "
        "scaled by Data Confidence factor (50%–100%) reflecting historical accounting depth and completeness.<br/>"
        "<b>Data Limitations:</b> Monthly figures reflect user-recorded entries. If transactions are pending, figures remain provisional.<br/>"
        "<b>Disclaimer:</b> This document is generated algorithmically for personal informational purposes only and does not constitute formal financial, investment, or tax advice."
    )
    disc_table = Table([
        [Paragraph(meth_text, ParagraphStyle('Disc', fontName=FONT_REGULAR, fontSize=7, textColor=FZ_MID_GRAY, leading=9.5))]
    ], colWidths=[540])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), FZ_GRAY_BG),
        ('BOX', (0,0), (-1,-1), 0.5, FZ_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(disc_table)

    doc.build(elements, canvasmaker=NumberedCanvas)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
