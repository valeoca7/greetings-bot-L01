import os
from typing import Mapping, Optional

from greetings_bot.bedrock_information import (
    BedrockClient,
    BedrockInformationProvider,
)
from greetings_bot.information import InformationService


DEFAULT_BEDROCK_MODEL_ID = "amazon.titan-text-lite-v1"
DEFAULT_INFORMATION_WEEKLY_LIMIT = 5


def information_requests_enabled(
    environ: Mapping[str, str] = os.environ,
) -> bool:
    value = environ.get("INFO_REQUESTS_ENABLED", "false").lower()
    if value not in ("true", "false"):
        raise ValueError("INFO_REQUESTS_ENABLED must be true or false")
    return value == "true"


def information_weekly_limit(
    environ: Mapping[str, str] = os.environ,
) -> int:
    try:
        limit = int(
            environ.get(
                "INFO_WEEKLY_LIMIT", str(DEFAULT_INFORMATION_WEEKLY_LIMIT)
            )
        )
    except ValueError as error:
        raise ValueError("INFO_WEEKLY_LIMIT must be a positive integer") from error
    if limit < 1:
        raise ValueError("INFO_WEEKLY_LIMIT must be a positive integer")
    return limit


def information_service_from_env(
    environ: Mapping[str, str] = os.environ,
    client: Optional[BedrockClient] = None,
) -> Optional[InformationService]:
    if not information_requests_enabled(environ):
        return None
    model_id = environ.get("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID).strip()
    if not model_id:
        raise ValueError("BEDROCK_MODEL_ID must not be blank")
    if client is None:
        import boto3

        client = boto3.client("bedrock-runtime")
    return InformationService(BedrockInformationProvider(client, model_id))
