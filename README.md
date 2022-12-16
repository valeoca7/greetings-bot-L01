# greetings-bot

A small Telegram bot for personal greetings.

## Setup

The project requires Python 3.9 or newer. Create a virtual environment and install the
package in editable mode:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Set a bot token before starting the command line application:

```sh
export TELEGRAM_BOT_TOKEN=replace-me
make run
```

Profiles are stored in `data/users.json` by default. Set `USER_STORE_PATH` to use a
different local file:

```sh
export USER_STORE_PATH=var/greetings/users.json
```

The application currently checks its configuration and handles saved Telegram update
payloads. It does not contact Telegram yet.

To process the sample update locally:

```sh
greetings-bot --update tests/fixtures/start_update.json
```

The command prints the Telegram `sendMessage` payload that would be sent.

To preview greetings due at a particular local time:

```sh
greetings-bot --dispatch-at 2022-09-06T18:30:00
```

The result is a JSON list of messages. This local command only prepares payloads; it
does not send them to Telegram.

## Commands

- `/start` registers the user and returns a greeting
- `/register` creates a user profile
- `/me` shows the current profile
- `/timezone [area/name]` shows or changes the user's timezone
- `/quiet [start end]` sets local quiet hours; `/quiet off` removes them
- `/help` lists the available actions

Run the tests with:

```sh
make test
```

## Lambda webhook

`template.yaml` contains the first SAM definition for the webhook function. A saved
API Gateway event is available for local invocation:

```sh
sam local invoke WebhookFunction --event events/webhook.json
```

The template and handler can be tested offline. Nothing in this repository creates
AWS resources or registers the webhook with Telegram.

The Lambda configuration points `USER_TABLE_NAME` at an encrypted, on-demand DynamoDB
table. User profiles use `USER#<telegram-id>` as the partition key and `PROFILE` as
the sort key. The function role is limited to the read, write, and scan operations
currently used by the repository adapter.
