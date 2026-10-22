import os

from dotenv import load_dotenv

load_dotenv(override=True)

APP_TITLE = "Adaptive Interview Simulator"
APP_ICON = "🎯"

START_URL = os.getenv("N8N_WEBHOOK_URL")
EVALUATION_URL = os.getenv("N8N_EVALUATION_URL")

QUESTION_LIMITS = {
    15: 10,
    30: 25,
    45: 35,
    60: 50
}
