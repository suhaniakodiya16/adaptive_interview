import streamlit as st


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
