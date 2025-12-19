import os
from typing import Callable, Mapping, Optional

from greetings_bot.bedrock_information import (
    BedrockClient,
    BedrockInformationProvider,
)
from greetings_bot.information import InformationService
from greetings_bot.feature_flags import feature_flags_from_env


DEFAULT_BEDROCK_MODEL_ID = "amazon.titan-text-lite-v1"
DEFAULT_INFORMATION_WEEKLY_LIMIT = 5
DEFAULT_BEDROCK_TIMEOUT_SECONDS = 8


def information_requests_enabled(
    environ: Mapping[str, str] = os.environ,
) -> bool:
    return feature_flags_from_env(environ).enabled("information_requests")


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


def bedrock_timeout_seconds(
    environ: Mapping[str, str] = os.environ,
) -> int:
    try:
        timeout = int(
            environ.get(
                "BEDROCK_TIMEOUT_SECONDS",
                str(DEFAULT_BEDROCK_TIMEOUT_SECONDS),
            )
        )
    except ValueError as error:
        raise ValueError("Bedrock timeout must be an integer") from error
    if not 1 <= timeout <= 30:
        raise ValueError("Bedrock timeout must be between 1 and 30 seconds")
    return timeout


def information_service_from_env(
    environ: Mapping[str, str] = os.environ,
    client: Optional[BedrockClient] = None,
    client_builder: Optional[Callable[[int], BedrockClient]] = None,
) -> Optional[InformationService]:
    if not information_requests_enabled(environ):
        return None
    model_id = environ.get("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID).strip()
    if not model_id:
        raise ValueError("BEDROCK_MODEL_ID must not be blank")
    if client is None:
        builder = client_builder or _default_bedrock_client
        client = builder(bedrock_timeout_seconds(environ))
    return InformationService(BedrockInformationProvider(client, model_id))


def _default_bedrock_client(timeout: int) -> BedrockClient:
    import boto3
    from botocore.config import Config

    config = Config(
        connect_timeout=timeout,
        read_timeout=timeout,
        retries={"max_attempts": 1, "mode": "standard"},
    )
    return boto3.client("bedrock-runtime", config=config)
