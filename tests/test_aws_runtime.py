import unittest
from unittest.mock import patch

from greetings_bot.aws_runtime import aws_client, aws_resource


class FakeBoto3:
    def __init__(self):
        self.calls = []

    def client(self, service_name, **configuration):
        self.calls.append(("client", service_name, configuration))
        return "client"

    def resource(self, service_name):
        self.calls.append(("resource", service_name, {}))
        return "resource"


class AwsRuntimeTest(unittest.TestCase):
    def test_builds_clients_through_one_lazy_import(self):
        boto3 = FakeBoto3()

        with patch("greetings_bot.aws_runtime.import_module", return_value=boto3) as load:
            result = aws_client("sqs", region_name="us-west-2")

        self.assertEqual(result, "client")
        load.assert_called_once_with("boto3")
        self.assertEqual(
            boto3.calls, [("client", "sqs", {"region_name": "us-west-2"})]
        )

    def test_builds_resources_through_the_same_boundary(self):
        boto3 = FakeBoto3()

        with patch("greetings_bot.aws_runtime.import_module", return_value=boto3):
            result = aws_resource("dynamodb")

        self.assertEqual(result, "resource")
        self.assertEqual(boto3.calls, [("resource", "dynamodb", {})])


if __name__ == "__main__":
    unittest.main()
