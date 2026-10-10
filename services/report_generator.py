"""
Report Generation & Export Service for InsightIQ.
Generates comprehensive PDF reports and structured CSV exports for executive presentation.
"""

import io
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_pdf_report(
    kpis: Dict[str, Any],
    insights: List[Dict[str, Any]],
    data_quality: Optional[Dict[str, Any]] = None,
    dataset_name: str = "Active Dataset"
) -> io.BytesIO:
    """
    Generate a polished PDF executive briefing document using ReportLab.
    """
    buffer = io.BytesIO()

    if not HAS_REPORTLAB:
        # Fallback text representation if ReportLab unavailable
        content = f"InsightIQ Executive Report - {dataset_name}\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"Total Revenue: ${kpis.get('total_revenue', 0):,.2f}\n"
        content += f"Total Orders: {kpis.get('total_orders', 0):,}\n"
        content += f"Profit Margin: {kpis.get('profit_margin_pct', 0):.1f}%\n\n"
        content += "Key Insights:\n"
        for ins in insights:
            content += f"- {ins.get('title')}: {ins.get('finding')}\n"
        buffer.write(content.encode("utf-8"))
        buffer.seek(0)
        return buffer

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14,
    )

    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    bold_body = ParagraphStyle(
        "BoldBody",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("InsightIQ • Business Intelligence Report", title_style))
    story.append(Paragraph(f"Dataset: <b>{dataset_name}</b> | Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=12))

    # Executive KPI Summary Table
    story.append(Paragraph("1. Executive Performance Summary", h2_style))

    kpi_data = [
        [
            Paragraph("<b>Metric</b>", bold_body),
            Paragraph("<b>Computed Value</b>", bold_body),
            Paragraph("<b>Status / Benchmark</b>", bold_body),
        ],
        [
            Paragraph("Total Revenue", body_style),
            Paragraph(f"${kpis.get('total_revenue', 0):,.2f}" if kpis.get("total_revenue") is not None else "N/A", body_style),
            Paragraph(f"Growth: {kpis.get('revenue_growth_pct', 0):+.1f}%" if kpis.get("revenue_growth_pct") is not None else "Baseline", body_style),
        ],
        [
            Paragraph("Total Orders / Transactions", body_style),
            Paragraph(f"{kpis.get('total_orders', 0):,}" if kpis.get("total_orders") is not None else "N/A", body_style),
            Paragraph(f"AOV: ${kpis.get('average_order_value', 0):,.2f}" if kpis.get("average_order_value") is not None else "Verified", body_style),
        ],
        [
            Paragraph("Net Profit & Margin", body_style),
            Paragraph(f"${kpis.get('total_profit', 0):,.2f} ({kpis.get('profit_margin_pct', 0):.1f}%)" if kpis.get("total_profit") is not None else "N/A", body_style),
            Paragraph("Healthy" if (kpis.get("profit_margin_pct") or 0) >= 20 else "Under Observation", body_style),
        ],
        [
            Paragraph("Customer Reach & Retention", body_style),
            Paragraph(f"{kpis.get('unique_customers', 0):,} Customers" if kpis.get("unique_customers") is not None else "N/A", body_style),
            Paragraph(f"Repeat Rate: {kpis.get('repeat_customer_pct', 0):.1f}%" if kpis.get("repeat_customer_pct") is not None else "N/A", body_style),
        ],
    ]

    t = Table(kpi_data, colWidths=[180, 160, 180])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Data Quality Section
    if data_quality:
        story.append(Paragraph("2. Data Quality & Integrity Diagnostics", h2_style))
        dq_text = (
            f"Quality Score: <b>{data_quality.get('overall_score', 0)}/100 ({data_quality.get('grade', 'N/A')})</b> | "
            f"Total Records: {data_quality.get('total_rows', 0):,} | "
            f"Missing Values: {data_quality.get('missing_pct', 0):.1f}% | "
            f"Duplicate Records: {data_quality.get('duplicate_rows', 0):,}"
        )
        story.append(Paragraph(dq_text, body_style))
        story.append(Spacer(1, 10))

    # Strategic Insights & Evidence
    story.append(Paragraph("3. Evidence-Based Business Findings & Recommended Actions", h2_style))
    
    for ins in insights[:4]:
        ins_title = f"<b>• {ins.get('title')}</b> [{ins.get('supporting_metric', '')}]"
        story.append(Paragraph(ins_title, bold_body))
        story.append(Paragraph(f"<b>Observation:</b> {ins.get('finding', '')}", body_style))
        story.append(Paragraph(f"<b>Analytical Interpretation:</b> {ins.get('interpretation', '')}", body_style))
        
        actions = ins.get("recommended_actions", [])
        if actions:
            story.append(Paragraph(f"<b>Next Steps:</b> {actions[0]}", body_style))
        story.append(Spacer(1, 6))

    # Disclaimer and Limitations
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))
    disclaimer = (
        "<b>Methodological Notice & Limitations:</b> All findings, segmentation profiles, risk scores, "
        "and forecasts are generated through deterministic rules, statistical algorithms, and supervised ML models. "
        "Correlations identified in this report do not constitute definitive proof of causation. Business decisions "
        "should evaluate domain context alongside statistical outputs."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle("Disc", parent=body_style, fontSize=7.5, leading=10, textColor=colors.HexColor("#64748B"))))

    doc.build(story)
    buffer.seek(0)
    return buffer


def export_dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes for download."""
    if df is None or df.empty:
        return b""
    return df.to_csv(index=False).encode("utf-8")
