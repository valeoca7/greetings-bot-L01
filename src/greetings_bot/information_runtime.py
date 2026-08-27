import os
from typing import Callable, Mapping, Optional

from greetings_bot.bedrock_information import (
    BedrockClient,
    BedrockInformationProvider,
)
from greetings_bot.aws_runtime import aws_client
from greetings_bot.clock import Clock
from greetings_bot.config_values import integer_value, nonblank_value
from greetings_bot.information import InformationService
from greetings_bot.feature_flags import feature_flags_from_env
from greetings_bot.usage import UsageMeter


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
    return integer_value(
        environ, "INFO_WEEKLY_LIMIT", DEFAULT_INFORMATION_WEEKLY_LIMIT, 1
    )


def bedrock_timeout_seconds(
    environ: Mapping[str, str] = os.environ,
) -> int:
    return integer_value(
        environ,
        "BEDROCK_TIMEOUT_SECONDS",
        DEFAULT_BEDROCK_TIMEOUT_SECONDS,
        1,
        30,
    )


def bedrock_model_id(environ: Mapping[str, str] = os.environ) -> str:
    return nonblank_value(environ, "BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID)


def information_service_from_env(
    environ: Mapping[str, str] = os.environ,
    client: Optional[BedrockClient] = None,
    client_builder: Optional[Callable[[int], BedrockClient]] = None,
    usage_meter: Optional[UsageMeter] = None,
    clock: Optional[Clock] = None,
) -> Optional[InformationService]:
    if not information_requests_enabled(environ):
        return None
    model_id = bedrock_model_id(environ)
    if client is None:
        builder = client_builder or _default_bedrock_client
        client = builder(bedrock_timeout_seconds(environ))
    return InformationService(
        BedrockInformationProvider(client, model_id),
        usage_meter=usage_meter,
        clock=clock,
    )


def _default_bedrock_client(timeout: int) -> BedrockClient:
    from botocore.config import Config

    config = Config(
        connect_timeout=timeout,
        read_timeout=timeout,
        retries={"max_attempts": 1, "mode": "standard"},
    )
    return aws_client("bedrock-runtime", config=config)
