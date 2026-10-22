import time

import requests
import streamlit as st

from config import EVALUATION_URL, QUESTION_LIMITS, START_URL
from services.api import get_retry_message, post_evaluation_request, post_start_request
from services.session import finish_interview, terminate_interview, time_remaining
from utils.helpers import answer_is_skip, initial_topic


@st.fragment(run_every="1s")
def show_timer():
    remaining = time_remaining()

    if remaining <= 0:
        finish_interview("Time limit reached")
        st.rerun()

    minutes, seconds = divmod(remaining, 60)

    st.metric(
        "Time Remaining",
        f"{minutes:02d}:{seconds:02d}"
    )

    if remaining <= 60:
        st.warning("Less than one minute remaining!")


def show_interview(job_id=None):
    if (
        not st.session_state.interview_started
        and not st.session_state.interview_finished
    ):

        job_id = st.number_input(
            "Enter Job ID",
            min_value=1,
            value=job_id if job_id is not None else 7,
            step=1
        )

        duration = st.selectbox(
            "Select Interview Duration",
            options=[15, 30, 45, 60],
            index=1,
            format_func=lambda x: f"{x} Minutes"
        )

        max_questions = QUESTION_LIMITS[duration]

        st.info(
            f"Duration: {duration} minutes | "
            f"Maximum Questions: {max_questions}"
        )

        if st.button(
            "Start Interview",
            type="primary"
        ):

            if not START_URL:
                st.error(
                    "N8N_WEBHOOK_URL is missing from .env"
                )
                st.stop()

            try:
                with st.spinner("Starting interview..."):

                    response = post_start_request(
                        START_URL,
                        job_id
                    )

                    response.raise_for_status()
                    data = response.json()

                if data.get("found") is False:
                    st.error("Job not found.")

                elif not data.get("first_question"):
                    st.error(
                        "No interview question returned."
                    )

                else:
                    first_question = data["first_question"]

                    st.session_state.job_role = data.get(
                        "job_role", ""
                    )

                    st.session_state.seniority = data.get(
                        "seniority", ""
                    )

                    st.session_state.question = first_question

                    st.session_state.duration = duration
                    st.session_state.max_questions = max_questions

                    st.session_state.question_number = 1

                    st.session_state.topic = initial_topic(
                        first_question
                    )

                    st.session_state.topic_question_count = 1
                    st.session_state.previous_topics = []
                    st.session_state.reason = ""
                    st.session_state.history = []

                    st.session_state.end_time = (
                        time.time() + duration * 60
                    )

                    st.session_state.interview_started = True
                    st.session_state.interview_finished = False

                    st.rerun()

            except (requests.RequestException, ValueError) as e:
                st.error(
                    f"Could not start interview: {e}"
                )

    if st.session_state.interview_started:

        if time_remaining() <= 0:
            finish_interview("Time limit reached")
            st.rerun()

        st.write(
            "**Job Role:**",
            st.session_state.job_role
        )

        st.write(
            "**Seniority:**",
            st.session_state.seniority
        )

        show_timer()

        st.progress(
            min(
                (st.session_state.question_number - 1)
                / st.session_state.max_questions,
                1.0
            )
        )

        st.caption(
            f"Question {st.session_state.question_number} "
            f"of {st.session_state.max_questions}"
        )

        st.subheader(
            f"Question {st.session_state.question_number}"
        )

        st.info(st.session_state.question)

        if st.session_state.reason:

            with st.expander("Why this follow-up?"):
                st.write(st.session_state.reason)

        with st.form(
            key=(
                f"answer_form_"
                f"{st.session_state.question_number}"
            )
        ):

            answer = st.text_area(
                "Your Answer",
                placeholder="Type your answer here..."
            )

            submitted = st.form_submit_button(
                "Submit Answer",
                type="primary"
            )

        if submitted:

            if time_remaining() <= 0:
                finish_interview("Time limit reached")
                st.rerun()

            elif not answer.strip():
                st.warning(
                    "Please enter an answer or type 'Skip'."
                )

            elif not EVALUATION_URL:
                st.error(
                    "N8N_EVALUATION_URL missing from .env"
                )

            else:

                skip_requested = answer_is_skip(answer)

                force_new_topic = (
                    skip_requested
                    or st.session_state.topic_question_count >= 4
                )

                payload = {
                    "job_role": st.session_state.job_role,
                    "seniority": st.session_state.seniority,
                    "question": st.session_state.question,
                    "answer": answer,
                    "current_topic": st.session_state.topic,
                    "topic_question_count": (
                        st.session_state.topic_question_count
                    ),
                    "force_new_topic": force_new_topic,
                    "previous_topics": (
                        st.session_state.previous_topics
                    ),
                    "recent_history": (
                        st.session_state.history[-6:]
                    )
                }

                # -------------------------------
                # GEMINI EVALUATION REQUEST
                # -------------------------------

                try:

                    with st.spinner(
                        "Evaluating your answer..."
                    ):

                        response = post_evaluation_request(
                            EVALUATION_URL,
                            payload
                        )

                        response.raise_for_status()
                        result = response.json()

                    # Handle quota errors returned as JSON
                    # by an n8n error-handling branch.
                    if result.get("error") in {
                        "quota_exceeded",
                        "ai_unavailable"
                    }:
                        terminate_interview(
                            str(result.get("retry_message", ""))
                        )

                    score = result.get("score")

                    if not isinstance(
                        score,
                        (int, float)
                    ):
                        terminate_interview()

                    score = max(
                        0,
                        min(10, score)
                    )

                    next_question = result.get(
                        "next_question", ""
                    )

                    # A missing next question is acceptable
                    # for the final allowed question.
                    is_last_question = (
                        st.session_state.question_number
                        >= st.session_state.max_questions
                    )

                    if (
                        not is_last_question
                        and time_remaining() > 0
                        and not next_question
                    ):
                        terminate_interview()

                    st.session_state.history.append({
                        "number": (
                            st.session_state.question_number
                        ),
                        "question": (
                            st.session_state.question
                        ),
                        "answer": answer,
                        "score": score,
                        "feedback": result.get(
                            "feedback", ""
                        ),
                        "topic": st.session_state.topic
                    })

                    # -------------------------------
                    # INTERVIEW COMPLETION
                    # -------------------------------

                    if time_remaining() <= 0:
                        finish_interview(
                            "Time limit reached"
                        )
                        st.rerun()

                    if is_last_question:
                        finish_interview(
                            "Maximum questions completed"
                        )
                        st.rerun()

                    # -------------------------------
                    # NEXT ADAPTIVE QUESTION
                    # -------------------------------

                    next_topic = result.get(
                        "next_topic", ""
                    )

                    if not next_topic:
                        next_topic = initial_topic(
                            next_question
                        )

                    if force_new_topic:
                        st.session_state.previous_topics.append(
                            st.session_state.topic
                        )

                    if (
                        next_topic.strip().lower()
                        == st.session_state.topic.strip().lower()
                    ):
                        st.session_state.topic_question_count += 1

                    else:
                        st.session_state.topic = next_topic
                        st.session_state.topic_question_count = 1

                    st.session_state.question = next_question

                    st.session_state.reason = result.get(
                        "reason", ""
                    )

                    st.session_state.question_number += 1

                    st.rerun()

                # -------------------------------
                # API / QUOTA ERROR HANDLING
                # -------------------------------

                except requests.HTTPError as e:

                    status = (
                        e.response.status_code
                        if e.response is not None
                        else None
                    )

                    # n8n commonly returns HTTP 500 when
                    # its Gemini node fails with quota 429.
                    if status in {429, 500, 502, 503, 504}:

                        retry_message = get_retry_message(
                            e.response
                        )

                        terminate_interview(retry_message)

                    else:
                        # Other HTTP errors also terminate
                        # the session; no progress is retained.
                        terminate_interview()

                except (
                    requests.Timeout,
                    requests.ConnectionError,
                    requests.RequestException,
                    ValueError,
                    TypeError,
                    KeyError
                ):
                    terminate_interview()

        st.divider()

        if st.button("Finish Interview"):
            finish_interview("Ended by candidate")
            st.rerun()
