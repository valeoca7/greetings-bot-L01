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

The application currently checks its configuration and handles saved Telegram update
payloads. It does not contact Telegram yet.

Run the tests with:

```sh
make test
```
