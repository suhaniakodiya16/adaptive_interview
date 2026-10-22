import streamlit as st

from config import APP_ICON, APP_TITLE
from pages_ui.error_page import show_error_page
from pages_ui.interview import show_interview
from pages_ui.report import show_report
from services.session import initialize_session

HR_FORM_URL = (
    "https://sajidpatel11.app.n8n.cloud/form/"
    "1c8aed6a-0068-491f-a8c6-4125c4ffd72b"
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="centered"
)

initialize_session()

if show_error_page():
    st.stop()

if st.session_state.interview_started or st.session_state.interview_finished:
    st.title("🎯 Adaptive Interview Simulator")
    st.write("AI-powered technical interview system")

    show_interview()
    show_report()
    st.stop()

job_id = st.query_params.get("job_id")
if job_id:
    try:
        job_id = int(job_id)
    except (TypeError, ValueError):
        st.title("🎯 Adaptive Interview Simulator")
        st.error("Invalid Job ID in the interview URL.")
        st.stop()

    if job_id < 1:
        st.title("🎯 Adaptive Interview Simulator")
        st.error("Invalid Job ID in the interview URL.")
        st.stop()

    st.title("🎯 Adaptive Interview Simulator")
    st.write("AI-powered technical interview system")
    show_interview(job_id=job_id)
    st.stop()

st.title("🎯 Adaptive Interview Simulator")
st.write("Welcome. Complete the hiring team's job setup form to continue.")
st.link_button(
    "Fill HR Job Setup Form",
    HR_FORM_URL,
    type="primary",
    use_container_width=True,
)
