
import os
import time
import requests
import streamlit as st

from dotenv import load_dotenv

load_dotenv(override=True)

START_URL = os.getenv("N8N_WEBHOOK_URL")
EVALUATION_URL = os.getenv("N8N_EVALUATION_URL")

QUESTION_LIMITS = {
    15: 10,
    30: 25,
    45: 35,
    60: 50
}

st.set_page_config(
    page_title="Adaptive Interview Simulator",
    page_icon="🎯",
    layout="centered"
)


# --------------------------------
# SESSION STATE
# --------------------------------

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


# --------------------------------
# HELPER FUNCTIONS
# --------------------------------

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
    # Delete the complete current interview session.
    st.session_state.clear()

    # Keep only the error-screen information.
    st.session_state.quota_error = True
    st.session_state.retry_message = retry_message

    st.rerun()


def get_retry_message(response):
    """
    Use a retry duration only when the API supplies one.
    Do not invent an estimated reset time.
    """
    if response is None:
        return ""

    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            seconds = int(float(retry_after))

            hours, remainder = divmod(seconds, 3600)
            minutes = (remainder + 59) // 60

            if minutes >= 60:
                hours += 1
                minutes -= 60

            if hours > 0:
                return (
                    f"Please try again after approximately "
                    f"{hours} hour(s) and {minutes} minute(s)."
                )

            return (
                f"Please try again after approximately "
                f"{max(1, minutes)} minute(s)."
            )

        except (ValueError, TypeError):
            return f"Retry after: {retry_after}"

    return ""


def answer_is_skip(answer):
    cleaned = answer.strip().lower().strip(" .!?")

    skip_phrases = {
        "i don't know",
        "i dont know",
        "don't know",
        "dont know",
        "idk",
        "no idea",
        "not sure",
        "skip",
        "pass",
        "next question",
        "i have no idea",
        "i do not know",
        "i can't answer",
        "i cannot answer",
        "no"
    }

    return cleaned in skip_phrases


def initial_topic(question):
    q = question.lower()

    topics = {
        "Lists and Tuples": ["list", "tuple"],
        "Dictionaries": ["dictionary", "dict"],
        "Sets": ["set"],
        "OOP": [
            "class",
            "object",
            "inheritance",
            "polymorphism"
        ],
        "Functions": ["function", "lambda"],
        "Exception Handling": [
            "exception",
            "error handling"
        ],
        "SQL": ["sql", "database", "query"],
        "APIs": ["api", "http", "rest"]
    }

    for topic, keywords in topics.items():
        if any(word in q for word in keywords):
            return topic

    return "General Technical Concepts"


def calculate_report():
    history = st.session_state.history

    scores = [
        float(item["score"])
        for item in history
        if isinstance(item.get("score"), (int, float))
    ]

    overall = (
        round(sum(scores) / len(scores), 1)
        if scores else 0.0
    )

    strengths = [
        item for item in history
        if isinstance(item.get("score"), (int, float))
        and item["score"] >= 7
    ]

    weaknesses = [
        item for item in history
        if isinstance(item.get("score"), (int, float))
        and item["score"] < 7
    ]

    pros = [
        f"Q{item['number']}: {item['feedback']}"
        for item in strengths[:4]
    ]

    cons = [
        f"Q{item['number']}: {item['feedback']}"
        for item in weaknesses[:4]
    ]

    if not pros:
        pros = [
            "No consistently strong areas identified yet."
        ]

    if not cons:
        cons = [
            "Review detailed feedback for opportunities "
            "to improve."
        ]

    return overall, pros, cons


# --------------------------------
# LIVE TIMER
# --------------------------------

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


# --------------------------------
# AI SERVICE ERROR SCREEN
# --------------------------------

# --------------------------------
# AI SERVICE ERROR SCREEN
# --------------------------------

if st.session_state.get("quota_error", False):

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

    st.stop()


# --------------------------------
# MAIN UI
# --------------------------------

st.title("🎯 Adaptive Interview Simulator")
st.write("AI-powered technical interview system")


# --------------------------------
# START SCREEN
# --------------------------------

if (
    not st.session_state.interview_started
    and not st.session_state.interview_finished
):

    job_id = st.number_input(
        "Enter Job ID",
        min_value=1,
        value=7,
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

                response = requests.post(
                    START_URL,
                    json={"job_id": int(job_id)},
                    timeout=60
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


# --------------------------------
# INTERVIEW SCREEN
# --------------------------------

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

                    response = requests.post(
                        EVALUATION_URL,
                        json=payload,
                        timeout=90
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


# --------------------------------
# FINAL REPORT
# --------------------------------

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
