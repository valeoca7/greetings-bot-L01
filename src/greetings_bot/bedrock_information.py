import json
from typing import Mapping, Protocol

from greetings_bot.information import InformationProviderError, InformationRequest


class BedrockClient(Protocol):
    def invoke_model(self, **request) -> Mapping[str, object]:
        ...


def information_prompt(request: InformationRequest) -> str:
    if request.kind == "joke":
        return "Tell one short, family-friendly joke. Return only the joke."
    if request.kind == "fact":
        return "Give one short, useful fun fact. Return only the fact."
    if request.kind == "person":
        return _factual_prompt("person", request.query)
    if request.kind == "place":
        return _factual_prompt("place", request.query)
    raise ValueError(f"unsupported information request: {request.kind}")


def _factual_prompt(subject: str, query: str) -> str:
    return (
        f"Give two concise factual sentences about this {subject}: {query}. "
        "If you are unsure, say that clearly. Return only the answer."
    )


def titan_request(prompt: str) -> str:
    return json.dumps(
        {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 160,
                "temperature": 0.4,
                "topP": 0.9,
                "stopSequences": [],
            },
        }
    )


class BedrockInformationProvider:
    def __init__(self, client: BedrockClient, model_id: str) -> None:
        self.client = client
        self.model_id = model_id

    def answer(self, request: InformationRequest) -> str:
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=titan_request(information_prompt(request)),
                accept="application/json",
                contentType="application/json",
            )
            value = json.loads(response["body"].read())
            answer = value["results"][0]["outputText"]
            if not isinstance(answer, str):
                raise TypeError("model answer is not text")
            return answer
        except Exception as error:
            raise InformationProviderError(
                "information provider unavailable"
            ) from error
