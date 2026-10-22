import streamlit as st


def show_error_page():
    if not st.session_state.get("quota_error", False):
        return False

    st.markdown(
        """
<div style="text-align:center; padding:40px 20px; border:2px solid #ef4444; border-radius:16px; margin-top:25px;">

<h1 style="color:#ef4444; font-size:36px;">
⚠ INTERVIEW TERMINATED
</h1>

<h2 style="font-size:23px;">
AI Evaluation Is Temporarily Unavailable
</h2>

<p style="font-size:18px; line-height:1.7;">
The AI evaluation service is currently unavailable or has reached its usage limit.
</p>

<h2 style="color:#ef4444; font-size:23px;">
Please Try Again After the Service Becomes Available
</h2>

<p style="font-size:17px; line-height:1.8;">
Your interview has ended immediately.<br>
All questions, answers, scores and interview progress have been discarded.<br>
You must begin a completely new interview from Question 1.
</p>

</div>
        """,
        unsafe_allow_html=True
    )

    retry_message = st.session_state.get("retry_message", "")

    if retry_message:
        st.error(retry_message)
    else:
        st.warning(
            "The exact retry time is not available. "
            "Please try again after the AI service quota resets."
        )

    return True
