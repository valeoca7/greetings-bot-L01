from typing import Any, Dict, Mapping, Union

from greetings_bot.api_gateway import ApiGatewayResponse


LambdaResponse = Dict[str, Union[int, str]]


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> LambdaResponse:
    return ApiGatewayResponse(200).to_dict()
