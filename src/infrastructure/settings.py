import os


def get_external_api_url() -> str:
    external_api_url = os.getenv("EXTERNAL_API_URL")
    if external_api_url is None or external_api_url.strip() == "":
        raise RuntimeError("EXTERNAL_API_URL environment variable is required")
    return external_api_url.rstrip("/")
