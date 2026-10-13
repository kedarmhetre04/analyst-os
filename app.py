import streamlit as st
import pandas as pd

from src.pipeline import run_analysis
from src.visualizations import (
    METRIC_LABELS,
    format_period,
    get_dimension_changes,
    get_period_summary,
    parse_scope,
)


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AnalystOS",
    page_icon="📊",
    layout="wide",
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def currency_delta(value):
    if value >= 0:
        return f"+${abs(value):,.0f}"

    return f"-${abs(value):,.0f}"


def escape_markdown_currency(text):
    return text.replace("$", r"\$")


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("AnalystOS")

st.caption(
    "Agentic Business Intelligence for autonomous analysis, "
    "validation, and decision support"
)


# --------------------------------------------------
# QUESTION INPUT
# --------------------------------------------------

question = st.text_input(
    "Ask a business question",
    placeholder=(
        "Example: Why did contribution profit decline in the West "
        "from August 2025 to September 2025?"
    ),
)


# --------------------------------------------------
# ANALYZE
# --------------------------------------------------

if st.button("Analyze", type="primary"):

    if not question.strip():

        st.warning(
            "Enter a business question first."
        )

    else:

        # --------------------------------------------------
        # RUN ANALYSTOS
        # --------------------------------------------------

        with st.spinner(
            "AnalystOS is investigating the data..."
        ):

            result = run_analysis(
                question
            )

        critique = result["critique"]
        report = result["report"]
        investigation = result["investigation"]
        scope = parse_scope(result["plan"])

        # --------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------

        if scope:

            summary_df = get_period_summary(scope)

            baseline = summary_df.iloc[0]
            comparison = summary_df.iloc[1]

            baseline_label = format_period(scope["baseline"])
            comparison_label = format_period(scope["comparison"])
            region_label = scope["region"] or "All regions"

            st.subheader(
                "Business Performance"
            )

            st.caption(
                f"{region_label}: {comparison_label} "
                f"vs {baseline_label}"
            )

            col1, col2, col3, col4 = st.columns(4)

            for column, metric in zip(
                [col1, col2, col3],
                ["contribution_profit", "revenue", "gross_profit"],
            ):
                column.metric(
                    METRIC_LABELS[metric],
                    f"${comparison[metric]:,.0f}",
                    currency_delta(
                        comparison[metric] - baseline[metric]
                    ),
                )

            col4.metric(
                "Orders",
                f"{int(comparison['orders']):,}",
                f"{int(comparison['orders'] - baseline['orders']):+,}",
            )

            # --------------------------------------------------
            # CONTRIBUTION PROFIT BRIDGE
            # --------------------------------------------------

            bridge_df = pd.DataFrame(
                {
                    "Driver": [
                        "Gross Profit",
                        "Refunds",
                        "Shipping Cost",
                    ],
                    "Impact": [
                        comparison["gross_profit"]
                        - baseline["gross_profit"],
                        -(
                            comparison["refund_amount"]
                            - baseline["refund_amount"]
                        ),
                        -(
                            comparison["shipping_cost"]
                            - baseline["shipping_cost"]
                        ),
                    ],
                }
            )

            st.subheader(
                "Contribution Profit Bridge"
            )

            st.bar_chart(
                bridge_df.set_index(
                    "Driver"
                )
            )

            # --------------------------------------------------
            # CATEGORY DRIVER CHART
            # --------------------------------------------------

            category_df = get_dimension_changes(
                scope,
                "category",
            )

            st.subheader(
                f"{METRIC_LABELS[scope['metric']]} Change by Category"
            )

            st.bar_chart(
                category_df[["category", "change"]]
                .set_index("category")
            )

        else:

            st.info(
                "Charts are shown for questions that compare two "
                "time periods. The planner did not identify a "
                "baseline and comparison period for this question."
            )

        attempts = len(result["attempts"])

        if attempts > 1:

            st.caption(
                f"The Critic rejected the first investigation, so "
                f"AnalystOS re-ran it ({attempts} attempts in total)."
            )

        # --------------------------------------------------
        # ANALYSIS REPORT
        # --------------------------------------------------

        st.divider()

        st.subheader(
            "Analysis Report"
        )

        safe_report = (
            escape_markdown_currency(
                report
            )
        )

        st.markdown(
            safe_report
        )

        # --------------------------------------------------
        # VALIDATION STATUS
        # --------------------------------------------------

        st.divider()

        verdict = critique.get(
            "verdict",
            "UNKNOWN",
        )

        st.subheader(
            "Validation Status"
        )

        if verdict == "PASS":

            st.success(
                "Critic verdict: PASS"
            )

        elif verdict == "PASS_WITH_WARNINGS":

            st.warning(
                "Critic verdict: PASS WITH WARNINGS"
            )

        else:

            st.error(
                f"Critic verdict: {verdict}"
            )

        # --------------------------------------------------
        # ADVANCED DETAILS
        # --------------------------------------------------

        with st.expander(
            "View investigation plan"
        ):

            st.json(
                result["plan"]
            )


        with st.expander(
            "View critic review"
        ):

            st.json(
                critique
            )


        with st.expander(
            "View investigation evidence"
        ):

            st.json(
                investigation
            )