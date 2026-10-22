import time

import streamlit as st


def initialize_session():
    defaults = {
        "interview_started": False,
        "interview_finished": False,
        "duration": 30,
        "max_questions": 25,
        "end_time": None,
        "job_role": "",
        "seniority": "",
        "question": "",
        "question_number": 1,
        "topic": "",
        "topic_question_count": 1,
        "previous_topics": [],
        "reason": "",
        "history": [],
        "finish_reason": "",
        "quota_error": False,
        "retry_message": ""
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def time_remaining():
    if st.session_state.end_time is None:
        return 0

    return max(
        0,
        int(st.session_state.end_time - time.time())
    )


def finish_interview(reason):
    st.session_state.interview_started = False
    st.session_state.interview_finished = True
    st.session_state.finish_reason = reason


def terminate_interview(retry_message=""):
    st.session_state.clear()
    st.session_state.quota_error = True
    st.session_state.retry_message = retry_message

    st.rerun()
