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
- `/days [daily|weekdays|days...]` chooses local greeting weekdays
- `/quiet [start end]` sets local quiet hours; `/quiet off` removes them
- `/digest [daily|off]` controls daily summary delivery
- `/note add <text>` saves a private note and returns its short ID
- `/notes` lists the current user's notes
- `/note <id>` shows a note; `/note delete <id>` removes it
- `/remind YYYY-MM-DD HH:MM <text>` creates a one-time local reminder
- `/remind every day HH:MM <text>` creates a daily reminder
- `/remind every <weekday> HH:MM <text>` creates a weekly reminder
- `/reminders` lists reminder due times and lifecycle status
- `/reminder <id>` shows reminder details
- `/reminder edit <id> <text>` updates active reminder text
- `/reminder pause|resume|cancel <id>` changes reminder state
- `/reminder snooze <id> <duration>` delays it by `30m`, `2h`, or `1d`
- `/help` lists the available actions

Run the tests with:

```sh
make test
```

Run the complete local verification or build a tracked-source archive with:

```sh
make check
make package
```

The `Jenkinsfile` uses those same targets, limits concurrent and stalled builds, and
archives the resulting tarball. It does not deploy infrastructure or contact AWS.

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

Scheduled greetings are checked once per minute and limited to 100 messages in one
invocation. The saved EventBridge event can be used with the local SAM runtime:

```sh
sam local invoke GreetingDispatcherFunction --event events/scheduled.json
```

The dispatcher records a delivery for each user's local date so repeated events do
not prepare the same daily greeting again.

Notes are stored beside the owner's profile under `NOTE#<id>` sort keys. Lookups and
deletes always include the Telegram user ID, and note listings query only that user
partition.

One-time reminders use the profile timezone for command input and are stored as UTC.
Pending records appear in the sparse `DueIndex`; once dispatched, they move to the
`sent` state and leave that index.

Recurring reminders retain their local wall-clock time across timezone offset
changes. A daily or weekly occurrence that falls inside a daylight-saving gap is
skipped, and the next valid occurrence remains pending.

Paused and cancelled reminders leave the due index. Snoozing a pending or paused
reminder moves its next deadline by at most seven days and makes it pending again.

Greeting weekdays and quiet hours are evaluated in the profile timezone. The daily
digest preference is stored with the profile so summary sources can use one delivery
choice as they are added; it is off for existing and newly registered users.

Cloud one-time reminders can use EventBridge Scheduler `at(...)` schedules. Each
schedule targets a narrow reminder-delivery Lambda, deletes itself after completion,
and is updated or removed when the user snoozes, pauses, or cancels the reminder.
Local runs retain the minute-based in-memory path and make no Scheduler API calls.

Greeting and reminder handlers place outbound messages on an encrypted SQS queue.
The delivery worker sends them to Telegram in batches, records completed delivery
IDs in DynamoDB, and returns individual failures for retry. Messages that fail five
times move to the dead-letter queue.

The saved queue event can be checked without polling SQS:

```sh
sam local invoke DeliveryWorkerFunction --event events/delivery_batch.json
```

This command still requires local table and bot-token configuration. The project
does not create a queue or send a Telegram message unless an operator deploys and
configures it separately.

## Operations

Lambda entry points write single-line JSON events with request IDs. Delivery retry
events also include the SQS record and delivery IDs, but never the greeting or note
text. Dispatch and delivery counts use CloudWatch embedded metric format under the
`GreetingsBot` namespace.

The SAM template defines alarms for failed delivery attempts and visible messages in
the dead-letter queue. Alarm notification actions are intentionally left for the
deploying environment to configure.

## Weather provider

Weather locations store a display name and validated latitude/longitude pair on the
user profile. The provider boundary currently supports one-day forecasts through an
injectable Open-Meteo adapter with a five-second default timeout. Set
`WEATHER_TIMEOUT_SECONDS` to change that bound.

The adapter is not called by any command in this release. Its tests use fake HTTP
openers and saved dictionaries, so local verification performs no network requests.
