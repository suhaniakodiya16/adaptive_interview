import requests


def post_start_request(url, job_id):
    return requests.post(
        url,
        json={"job_id": int(job_id)},
        timeout=60
    )


def post_evaluation_request(url, payload):
    return requests.post(
        url,
        json=payload,
        timeout=90
    )


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
