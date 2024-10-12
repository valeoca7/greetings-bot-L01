import json
import unittest

from greetings_bot.bedrock_information import (
    BedrockInformationProvider,
    information_prompt,
    titan_request,
)
from greetings_bot.information import InformationProviderError, InformationRequest


class FakeBody:
    def __init__(self, value):
        self.value = value

    def read(self):
        return self.value


class FakeBedrockClient:
    def __init__(self, answer="A useful answer."):
        self.answer = answer

    def invoke_model(self, **request):
        self.request = request
        value = {"results": [{"outputText": self.answer}]}
        return {"body": FakeBody(json.dumps(value).encode("utf-8"))}


class BedrockInformationTest(unittest.TestCase):
    def test_builds_short_joke_and_fact_prompts(self):
        joke = information_prompt(InformationRequest("joke"))
        fact = information_prompt(InformationRequest("fact"))

        self.assertIn("one short, family-friendly joke", joke)
        self.assertIn("one short, useful fun fact", fact)
        self.assertIn("Return only", joke)

    def test_builds_bounded_person_and_place_prompts(self):
        person = information_prompt(
            InformationRequest("person", "Ada Lovelace")
        )
        place = information_prompt(
            InformationRequest("place", "Victoria BC")
        )

        self.assertIn("Ada Lovelace", person)
        self.assertIn("Victoria BC", place)
        self.assertIn("two concise factual sentences", person)
        self.assertIn("two concise factual sentences", place)
        self.assertIn("say that clearly", person)

    def test_rejects_unsupported_request_kind(self):
        with self.assertRaises(ValueError):
            information_prompt(InformationRequest("advice", "sleep"))

    def test_encodes_a_small_titan_text_request(self):
        body = json.loads(titan_request("Tell me something useful."))

        self.assertEqual(body["inputText"], "Tell me something useful.")
        self.assertEqual(
            body["textGenerationConfig"],
            {
                "maxTokenCount": 160,
                "temperature": 0.4,
                "topP": 0.9,
                "stopSequences": [],
            },
        )

    def test_invokes_the_selected_model(self):
        client = FakeBedrockClient("Why did the bot wave? To say hello!")
        provider = BedrockInformationProvider(client, "amazon.titan-lite")

        answer = provider.answer(InformationRequest("joke"))

        self.assertEqual(answer, "Why did the bot wave? To say hello!")
        self.assertEqual(client.request["modelId"], "amazon.titan-lite")
        self.assertEqual(client.request["accept"], "application/json")
        self.assertEqual(client.request["contentType"], "application/json")
        body = json.loads(client.request["body"])
        self.assertIn("family-friendly joke", body["inputText"])

    def test_normalizes_malformed_model_responses(self):
        class BadClient:
            def invoke_model(self, **request):
                return {"body": FakeBody(b"not json")}

        provider = BedrockInformationProvider(BadClient(), "model")

        with self.assertRaises(InformationProviderError):
            provider.answer(InformationRequest("fact"))

    def test_normalizes_client_errors(self):
        class SdkError(Exception):
            pass

        class OfflineClient:
            def invoke_model(self, **request):
                raise SdkError("request rejected")

        provider = BedrockInformationProvider(OfflineClient(), "model")

        with self.assertRaises(InformationProviderError):
            provider.answer(InformationRequest("place", "Victoria BC"))


if __name__ == "__main__":
    unittest.main()
