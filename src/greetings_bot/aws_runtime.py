from importlib import import_module
from typing import Any


def aws_client(service_name: str, **configuration: Any) -> Any:
    boto3 = import_module("boto3")
    return boto3.client(service_name, **configuration)


def aws_resource(service_name: str) -> Any:
    boto3 = import_module("boto3")
    return boto3.resource(service_name)
