"""Bhashini (Government of India ULCA/Dhruva) translation integration.

Two-step call per Bhashini's published pipeline API:
1. getModelsPipeline - trade account credentials for a short-lived
   inference key plus the actual compute endpoint to call.
2. POST the text to that compute endpoint.

Falls back to returning the original text untouched if no credentials
are configured, or if the API call fails for any reason - a translation
outage should never turn into a request failure.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BHASHINI_USER_ID = os.environ.get("BHASHINI_USER_ID", "")
BHASHINI_API_KEY = os.environ.get("BHASHINI_API_KEY", "")

_PIPELINE_CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
# Government-hosted default translation pipeline (documented default ID).
_DEFAULT_PIPELINE_ID = "64392f96daac500b55c543cd"

# Per-target-language pipeline config, fetched once and reused - it
# doesn't change between requests.
_pipeline_cache: dict[str, dict] = {}


def _get_pipeline(target_lang: str) -> dict | None:
    if target_lang in _pipeline_cache:
        return _pipeline_cache[target_lang]

    try:
        resp = httpx.post(
            _PIPELINE_CONFIG_URL,
            headers={
                "userID": BHASHINI_USER_ID,
                "ulcaApiKey": BHASHINI_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {"sourceLanguage": "en", "targetLanguage": target_lang}
                        },
                    }
                ],
                "pipelineRequestConfig": {"pipelineId": _DEFAULT_PIPELINE_ID},
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

        endpoint = data["pipelineInferenceAPIEndPoint"]
        service_id = data["pipelineResponseConfig"][0]["config"][0]["serviceId"]
        key_name = endpoint["inferenceApiKey"]["name"]
        key_value = endpoint["inferenceApiKey"]["value"]

        pipeline = {
            "compute_url": endpoint["callbackUrl"],
            "auth_header": {key_name: key_value},
            "service_id": service_id,
        }
        _pipeline_cache[target_lang] = pipeline
        return pipeline
    except Exception:
        return None


def translate_text(text: str, target_lang: str) -> str:
    if not text or target_lang == "en" or not (BHASHINI_USER_ID and BHASHINI_API_KEY):
        return text

    pipeline = _get_pipeline(target_lang)
    if pipeline is None:
        return text

    try:
        resp = httpx.post(
            pipeline["compute_url"],
            headers={**pipeline["auth_header"], "Content-Type": "application/json"},
            json={
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {"sourceLanguage": "en", "targetLanguage": target_lang},
                            "serviceId": pipeline["service_id"],
                        },
                    }
                ],
                "inputData": {"input": [{"source": text}]},
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()["pipelineResponse"][0]["output"][0]["target"]
    except Exception:
        return text
