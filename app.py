import streamlit as st

from src.pipeline import run_analysis


st.set_page_config(
    page_title="AnalystOS",
    page_icon="📊",
    layout="wide",
)


st.title("AnalystOS")
st.caption(
    "Agentic Business Intelligence for autonomous analysis, "
    "validation, and decision support"
)


question = st.text_input(
    "Ask a business question",
    placeholder=(
        "Example: Why did contribution profit decline in the West "
        "from August 2025 to September 2025?"
    ),
)


if st.button("Analyze", type="primary"):

    if not question.strip():
        st.warning("Enter a business question first.")

    else:

        with st.spinner(
            "AnalystOS is investigating the data..."
        ):

            result = run_analysis(question)

        critique = result["critique"]
        report = result["report"]

        st.divider()

        st.subheader("Analysis Report")

        safe_report = report.replace("$", r"\$")

        st.markdown(safe_report)

        st.divider()

        verdict = critique.get(
            "verdict",
            "UNKNOWN",
        )

        st.subheader("Validation Status")

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
                result["investigation"]
            )