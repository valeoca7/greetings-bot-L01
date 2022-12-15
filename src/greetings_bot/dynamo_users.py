from typing import Dict, Mapping, Optional, Protocol, Sequence

from greetings_bot.users import User, user_from_dict, user_to_dict


class DynamoTable(Protocol):
    def put_item(self, *, Item: Mapping[str, object]) -> Mapping[str, object]:
        ...


class DynamoResource(Protocol):
    def Table(self, name: str) -> DynamoTable:
        ...

    def get_item(self, *, Key: Mapping[str, object]) -> Mapping[str, object]:
        ...

    def scan(self, **kwargs: object) -> Mapping[str, object]:
        ...


def user_key(telegram_id: int) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(telegram_id),
        "sk": "PROFILE",
    }


def user_item(user: User) -> Dict[str, object]:
    item = user_to_dict(user)
    item.update(user_key(user.telegram_id))
    item["entity"] = "user"
    return item


def user_from_item(item: Dict[str, object]) -> User:
    return user_from_dict(item)


class DynamoUserRepository:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def save(self, user: User) -> None:
        self.table.put_item(Item=user_item(user))

    def get(self, telegram_id: int) -> Optional[User]:
        result = self.table.get_item(Key=user_key(telegram_id))
        item = result.get("Item")
        if not isinstance(item, dict):
            return None
        return user_from_item(item)

    def all(self) -> Sequence[User]:
        items = []
        scan_args = {}
        while True:
            result = self.table.scan(**scan_args)
            items.extend(result.get("Items", []))
            last_key = result.get("LastEvaluatedKey")
            if not isinstance(last_key, dict):
                break
            scan_args["ExclusiveStartKey"] = last_key
        users = [
            user_from_item(item)
            for item in items
            if isinstance(item, dict) and item.get("entity") == "user"
        ]
        return sorted(users, key=lambda user: user.telegram_id)

    def count(self) -> int:
        return len(self.all())


def repository_for_table(
    table_name: str, resource: Optional[DynamoResource] = None
) -> DynamoUserRepository:
    if resource is None:
        import boto3

        resource = boto3.resource("dynamodb")
    return DynamoUserRepository(resource.Table(table_name))
