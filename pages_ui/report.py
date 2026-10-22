import streamlit as st

from utils.helpers import calculate_report


def show_report():
    if st.session_state.interview_finished:

        st.success("Interview Completed!")

        history = st.session_state.history
        overall, pros, cons = calculate_report()

        st.markdown(
            "## Interview Performance Report"
        )

        # Overall Performance
       # Overall Performance
        st.markdown(
        f"""
<div style="text-align:center; padding:20px 0;">
<h1 style="font-size:48px; margin-bottom:0;">{overall}/10</h1>
<p style="color:gray; font-size:14px;">Overall Performance</p>
</div>
""",
        unsafe_allow_html=True
    )

        st.divider()

        # Competency Scores
        st.markdown("### Competency Scores")

        valid_scores = [
            float(item["score"])
            for item in history
            if isinstance(item.get("score"), (int, float))
        ]

        avg_score = (
            sum(valid_scores) / len(valid_scores)
            if valid_scores else 0.0
        )

        # Temporary estimated competency scores.
        # A separate full-interview AI evaluation
        # will be needed for independent ratings.
        competency_scores = {
            "Technical Knowledge": avg_score,
            "Problem Solving": avg_score,
            "Concept Clarity": avg_score,
            "Communication": avg_score
        }

        for competency, score in competency_scores.items():

            score = round(
                max(0, min(10, score)),
                1
            )

            left, right = st.columns([4, 1])

            with left:
                st.write(competency)

            with right:
                st.write(f"**{score}/10**")

            st.progress(score / 10)

        st.divider()

        # Pros and Cons
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ Pros")

            for item in pros:
                st.write(item)

        with col2:
            st.markdown("### ❌ Cons")

            for item in cons:
                st.write(item)

        st.divider()

        # Improvement Recommendations
        st.markdown(
            "### Improvement Recommendations"
        )

        weak_answers = [
            item for item in history
            if isinstance(item.get("score"), (int, float))
            and item["score"] < 7
        ]

        if weak_answers:

            st.write(
                "Focus on the following questions "
                "and concepts:"
            )

            for item in weak_answers[:5]:
                st.write(
                    f"• Review: {item['question']}"
                )

        else:
            st.write(
                "Continue practicing advanced technical "
                "questions and real-world problem-solving "
                "scenarios."
            )

        st.divider()

        # Question-wise Evaluation
        st.subheader("Question-wise Evaluation")

        for item in history:

            with st.expander(
                f"Q{item['number']} — "
                f"Score: {item['score']}/10"
            ):

                st.write(
                    "**Question:**",
                    item["question"]
                )

                st.write(
                    "**Your Answer:**",
                    item["answer"]
                )

                st.write(
                    "**Feedback:**",
                    item["feedback"]
                )
