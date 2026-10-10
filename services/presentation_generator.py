"""
Executive PowerPoint Presentation Generator for InsightIQ.
Generates widescreen (16:9) executive pitch decks using python-pptx with
branded layouts, KPI summary grids, customer analytics, churn risk, forecasts,
and methodological disclaimers.
"""

import io
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False


class PresentationGenerator:
    """
    Builds structured, widescreen PowerPoint presentations from analytical session state.
    """

    # Corporate Color Palette
    COLOR_NAVY = RGBColor(15, 23, 42)      # #0F172A
    COLOR_BLUE = RGBColor(30, 64, 175)     # #1E40AF
    COLOR_ACCENT = RGBColor(37, 99, 235)   # #2563EB
    COLOR_MUTED = RGBColor(100, 116, 139)  # #64748B
    COLOR_CARD_BG = RGBColor(248, 250, 252) # #F8FAFC
    COLOR_WHITE = RGBColor(255, 255, 255)
    COLOR_GREEN = RGBColor(5, 150, 105)    # #059669
    COLOR_BORDER = RGBColor(226, 232, 240) # #E2E8F0

    @classmethod
    def generate_deck(
        cls,
        kpis: Dict[str, Any],
        insights: List[Dict[str, Any]],
        dataset_name: str = "Active Dataset",
        churn_summary: Optional[Dict[str, Any]] = None,
        forecast_summary: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate complete PowerPoint deck and return raw bytes.
        """
        if not HAS_PPTX:
            raise RuntimeError("python-pptx package is not installed.")

        prs = Presentation()
        # Set 16:9 Widescreen Dimensions
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        blank_layout = prs.slide_layouts[6]

        # Slide 1: Title Slide
        cls._create_title_slide(prs, blank_layout, dataset_name)

        # Slide 2: Executive Summary & Performance Context
        cls._create_exec_summary_slide(prs, blank_layout, kpis, insights)

        # Slide 3: Executive KPI Dashboard Grid
        cls._create_kpi_dashboard_slide(prs, blank_layout, kpis)

        # Slide 4: Strategic Business Findings & Priorities
        cls._create_strategic_insights_slide(prs, blank_layout, insights)

        # Slide 5: Predictive Analytics & Risk Modeling (Churn & Forecast)
        cls._create_predictive_slide(prs, blank_layout, churn_summary, forecast_summary)

        # Slide 6: Methodology, Data Governance & Limitations
        cls._create_methodology_slide(prs, blank_layout)

        buffer = io.BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def _add_header(cls, slide, title: str, category: str):
        """Standardized widescreen slide header."""
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.9))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_sub = tf.paragraphs[0]
        p_sub.text = category.upper()
        p_sub.font.size = Pt(9.5)
        p_sub.font.bold = True
        p_sub.font.color.rgb = cls.COLOR_ACCENT

        p_main = tf.add_paragraph()
        p_main.text = title
        p_main.font.size = Pt(22)
        p_main.font.bold = True
        p_main.font.color.rgb = cls.COLOR_NAVY

    @classmethod
    def _create_title_slide(cls, prs, layout, dataset_name: str):
        slide = prs.slides.add_slide(layout)

        # Background banner
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = cls.COLOR_NAVY
        bg.line.fill.background()

        # Accent pill
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.6), Inches(2.2), Inches(0.4))
        pill.fill.solid()
        pill.fill.fore_color.rgb = cls.COLOR_BLUE
        pill.line.fill.background()
        p_pill = pill.text_frame.paragraphs[0]
        p_pill.text = "EXECUTIVE BRIEFING"
        p_pill.font.size = Pt(10)
        p_pill.font.bold = True
        p_pill.alignment = PP_ALIGN.CENTER
        p_pill.font.color.rgb = cls.COLOR_WHITE

        # Title Text
        tb = slide.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(10.5), Inches(3.0))
        tf = tb.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = "InsightIQ Executive Intelligence"
        p1.font.size = Pt(38)
        p1.font.bold = True
        p1.font.color.rgb = cls.COLOR_WHITE

        p2 = tf.add_paragraph()
        p2.text = f"Comprehensive Business Health, Predictive Modeling & Strategic Roadmap\nTarget Dataset: {dataset_name} • Date: {datetime.now().strftime('%B %d, %Y')}"
        p2.font.size = Pt(15)
        p2.font.color.rgb = RGBColor(148, 163, 184)

    @classmethod
    def _create_exec_summary_slide(cls, prs, layout, kpis: Dict[str, Any], insights: List[Dict[str, Any]]):
        slide = prs.slides.add_slide(layout)
        cls._add_header(slide, "Executive Summary & Core Metrics", "Business Overview")

        # Left Column: Strategic Overview Box
        box_left = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
        box_left.fill.solid()
        box_left.fill.fore_color.rgb = cls.COLOR_CARD_BG
        box_left.line.color.rgb = cls.COLOR_BORDER

        tf_l = box_left.text_frame
        tf_l.word_wrap = True
        p_lt = tf_l.paragraphs[0]
        p_lt.text = "Executive Briefing Synthesis"
        p_lt.font.size = Pt(15)
        p_lt.font.bold = True
        p_lt.font.color.rgb = cls.COLOR_NAVY

        p_lb = tf_l.add_paragraph()
        rev_str = f"${kpis.get('total_revenue', 0):,.2f}"
        profit_str = f"${kpis.get('total_profit', 0):,.2f}"
        margin_str = f"{kpis.get('profit_margin_pct', 0):.1f}%"
        orders_str = f"{kpis.get('total_orders', 0):,}"

        p_lb.text = (
            f"\n• Total Platform Volume: Generated {rev_str} in revenue across {orders_str} evaluated transactions.\n\n"
            f"• Operating Unit Margin: Net profit reached {profit_str} ({margin_str} operating margin).\n\n"
            f"• Repeat Customer Engagement: Repeat purchase rate recorded at {kpis.get('repeat_customer_pct', 0):.1f}%.\n\n"
            f"• Analytical Governance: All metrics derived from verified tabular data using dual DuckDB/PostgreSQL analytical processing."
        )
        p_lb.font.size = Pt(12)
        p_lb.font.color.rgb = cls.COLOR_NAVY

        # Right Column: Key Priorities Box
        box_right = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
        box_right.fill.solid()
        box_right.fill.fore_color.rgb = cls.COLOR_CARD_BG
        box_right.line.color.rgb = cls.COLOR_BORDER

        tf_r = box_right.text_frame
        tf_r.word_wrap = True
        p_rt = tf_r.paragraphs[0]
        p_rt.text = "Key Strategic Priorities"
        p_rt.font.size = Pt(15)
        p_rt.font.bold = True
        p_rt.font.color.rgb = cls.COLOR_NAVY

        top_ins = insights[:3]
        for i, ins in enumerate(top_ins, 1):
            p = tf_r.add_paragraph()
            p.text = f"\n{i}. {ins.get('title')}: {ins.get('finding')}\n   Action: {ins.get('recommended_actions', ['N/A'])[0]}"
            p.font.size = Pt(11)
            p.font.color.rgb = cls.COLOR_NAVY

    @classmethod
    def _create_kpi_dashboard_slide(cls, prs, layout, kpis: Dict[str, Any]):
        slide = prs.slides.add_slide(layout)
        cls._add_header(slide, "Executive Key Performance Indicators", "Financial & Commercial Health")

        cards_data = [
            ("TOTAL NET REVENUE", f"${kpis.get('total_revenue', 0):,.2f}", f"Growth: {kpis.get('revenue_growth_pct', 0):+.1f}%", cls.COLOR_BLUE),
            ("TOTAL ORDERS", f"{kpis.get('total_orders', 0):,}", f"AOV: ${kpis.get('average_order_value', 0):,.2f}", cls.COLOR_ACCENT),
            ("OPERATING PROFIT", f"${kpis.get('total_profit', 0):,.2f}", f"Margin: {kpis.get('profit_margin_pct', 0):.1f}%", cls.COLOR_GREEN),
            ("CUSTOMER BASE", f"{kpis.get('unique_customers', 0):,}", f"Repeat: {kpis.get('repeat_customer_pct', 0):.1f}%", cls.COLOR_NAVY),
        ]

        w = Inches(2.7)
        h = Inches(3.2)
        top = Inches(2.2)

        for i, (label, val, sub, color) in enumerate(cards_data):
            left = Inches(0.8 + i * 2.95)
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
            card.fill.solid()
            card.fill.fore_color.rgb = cls.COLOR_CARD_BG
            card.line.color.rgb = cls.COLOR_BORDER

            tf = card.text_frame
            tf.word_wrap = True
            
            p1 = tf.paragraphs[0]
            p1.text = label
            p1.font.size = Pt(10)
            p1.font.bold = True
            p1.font.color.rgb = cls.COLOR_MUTED

            p2 = tf.add_paragraph()
            p2.text = f"\n{val}"
            p2.font.size = Pt(24)
            p2.font.bold = True
            p2.font.color.rgb = color

            p3 = tf.add_paragraph()
            p3.text = f"\n{sub}"
            p3.font.size = Pt(11)
            p3.font.color.rgb = cls.COLOR_NAVY

    @classmethod
    def _create_strategic_insights_slide(cls, prs, layout, insights: List[Dict[str, Any]]):
        slide = prs.slides.add_slide(layout)
        cls._add_header(slide, "Evidence-Based Business Insights", "Decision Support")

        for idx, ins in enumerate(insights[:3]):
            top = Inches(1.6 + idx * 1.75)
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.7), Inches(1.55))
            card.fill.solid()
            card.fill.fore_color.rgb = cls.COLOR_CARD_BG
            card.line.color.rgb = cls.COLOR_BORDER

            tf = card.text_frame
            tf.word_wrap = True

            p1 = tf.paragraphs[0]
            p1.text = f"{ins.get('category', 'Category')} • {ins.get('title', 'Insight')}"
            p1.font.size = Pt(13)
            p1.font.bold = True
            p1.font.color.rgb = cls.COLOR_BLUE

            p2 = tf.add_paragraph()
            p2.text = f"Observation: {ins.get('finding')} ({ins.get('supporting_metric')})\nRecommendation: {ins.get('recommended_actions', ['N/A'])[0]}"
            p2.font.size = Pt(10.5)
            p2.font.color.rgb = cls.COLOR_NAVY

    @classmethod
    def _create_predictive_slide(cls, prs, layout, churn_summary, forecast_summary):
        slide = prs.slides.add_slide(layout)
        cls._add_header(slide, "Predictive Risk & Demand Forecasting", "Machine Learning")

        # Churn box
        box_c = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
        box_c.fill.solid()
        box_c.fill.fore_color.rgb = cls.COLOR_CARD_BG
        box_c.line.color.rgb = cls.COLOR_BORDER
        tf_c = box_c.text_frame
        tf_c.word_wrap = True
        tf_c.paragraphs[0].text = "Customer Churn Risk Architecture"
        tf_c.paragraphs[0].font.size = Pt(15)
        tf_c.paragraphs[0].font.bold = True
        tf_c.paragraphs[0].font.color.rgb = cls.COLOR_NAVY

        p_cb = tf_c.add_paragraph()
        p_cb.text = (
            "\n• Supervised Classifiers: Evaluated via Logistic Regression, Random Forest, and Gradient Boosting.\n\n"
            "• Leakage Guards: Customer identifiers and post-churn signals removed prior to feature processing.\n\n"
            "• Risk Tiering: Accounts tiered into High Risk (>=65%), Medium Risk (35-65%), and Low Risk (<35%).\n\n"
            "• Explainability: SHAP feature attributions identify key risk correlations without claiming causal proof."
        )
        p_cb.font.size = Pt(11.5)
        p_cb.font.color.rgb = cls.COLOR_NAVY

        # Forecast box
        box_f = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
        box_f.fill.solid()
        box_f.fill.fore_color.rgb = cls.COLOR_CARD_BG
        box_f.line.color.rgb = cls.COLOR_BORDER
        tf_f = box_f.text_frame
        tf_f.word_wrap = True
        tf_f.paragraphs[0].text = "Time-Series Revenue Projections"
        tf_f.paragraphs[0].font.size = Pt(15)
        tf_f.paragraphs[0].font.bold = True
        tf_f.paragraphs[0].font.color.rgb = cls.COLOR_NAVY

        p_fb = tf_f.add_paragraph()
        p_fb.text = (
            "\n• Temporal Backtesting: Evaluated sequentially on historical holdouts to avoid future leakage.\n\n"
            "• Statistical Models: Evaluates Holt Linear Trend, Seasonal Naive, Holt-Winters, and STL Decomposition.\n\n"
            "• Uncertainty Intervals: 80% and 95% expanding prediction bands calibrated on historical residuals.\n\n"
            "• Anomaly Scanner: Robust Median Absolute Deviation (MAD) flags statistical surges and contractions."
        )
        p_fb.font.size = Pt(11.5)
        p_fb.font.color.rgb = cls.COLOR_NAVY

    @classmethod
    def _create_methodology_slide(cls, prs, layout):
        slide = prs.slides.add_slide(layout)
        cls._add_header(slide, "Governance, Methodology & Limitations", "Methodological Integrity")

        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
        box.fill.solid()
        box.fill.fore_color.rgb = cls.COLOR_CARD_BG
        box.line.color.rgb = cls.COLOR_BORDER

        tf = box.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].text = "Core Analytical Methodologies & Boundary Notices"
        tf.paragraphs[0].font.size = Pt(15)
        tf.paragraphs[0].font.bold = True
        tf.paragraphs[0].font.color.rgb = cls.COLOR_NAVY

        p = tf.add_paragraph()
        p.text = (
            "\n1. Correlation vs. Causation Notice: Identified statistical patterns reflect historical mathematical correlations. "
            "They do not establish direct empirical causality or guarantee that altering marketing or operational levers will yield proportional outcomes.\n\n"
            "2. Data Governance & Cleanliness: All source metrics are audited through the InsightIQ Data Quality framework, evaluating completeness, "
            "uniqueness, type consistency, and IQR outliers.\n\n"
            "3. SQL Security Architecture: Conversational AI and analytical queries run against restricted DuckDB instances with AST parser allowlists "
            "blocking DML/DDL mutations.\n\n"
            "4. Model Validation Standards: Predictive churn pipelines use stratified holdouts; time-series forecasting uses strictly chronological train/test splits."
        )
        p.font.size = Pt(12)
        p.font.color.rgb = cls.COLOR_NAVY
