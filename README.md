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
- `/language [en|uk]` shows or changes the message language
- `/style [friendly|brief|cheerful]` shows or changes the scheduled greeting style
- `/preview` renders the selected greeting without scheduling a delivery
- `/timezone [area/name]` shows or changes the user's timezone
- `/days [daily|weekdays|days...]` chooses local greeting weekdays
- `/quiet [start end]` sets local quiet hours; `/quiet off` removes them
- `/digest [daily|off]` controls daily summary delivery
- `/location [latitude longitude name|off]` manages the weather location
- `/weather` shows today's forecast; `/weather units metric|imperial` changes units
- `/weather daily` adds weather to the daily digest; `/weather off` unsubscribes
- `/ask joke|fact|person|place|advice` requests a short generated response
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

English and Ukrainian messages are included. Telegram's language is used when a
profile is first created, and `/language` stores later changes. Unknown or incomplete
locales fall back to English without changing user-provided names, notes, reminder
text, weather place names, or generated information answers.

Scheduled greetings use one of three built-in styles. Templates accept only `name`,
`weekday`, and `date` values; attribute access, format expressions, unknown variables,
and oversized output are rejected. Previewing uses the same renderer as delivery and
does not write a delivery marker or call a remote provider.

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
not prepare the same daily greeting again. Cloud delivery records use conditional
writes, so overlapping scheduler invocations have a single claimant for each user and
local day.

Before claiming due work, the dispatcher reads the approximate visible, delayed, and
in-flight queue depth. It pauses at 1,000 messages by default and emits queue depth
and backpressure metrics. `DISPATCH_BATCH_SIZE` and
`DELIVERY_QUEUE_HIGH_WATERMARK` set bounded runtime limits. Prepared messages are
written to SQS in batches of at most ten.

Notes are stored beside the owner's profile under `NOTE#<id>` sort keys. Lookups and
deletes always include the Telegram user ID, and note listings query only that user
partition.

One-time reminders use the profile timezone for command input and are stored as UTC.
Pending records appear in the sparse `DueIndex`; once dispatched, they move to the
`sent` state and leave that index.

Reminder occurrences use short-lived conditional claim records before a reply is
prepared. This prevents overlapping dispatcher invocations from sending the same
one-time or recurring occurrence twice.

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

Provider calls, accepted model requests, and accepted queue messages emit separate
service-unit metrics. Daily soft budgets emit one warning per warm runtime when
crossed; they do not block work or claim to represent a currency charge. Configure
them with `WEATHER_DAILY_BUDGET`, `INFORMATION_DAILY_BUDGET`, and
`QUEUE_DAILY_BUDGET`.

## Weather provider

Weather locations store a display name and validated latitude/longitude pair on the
user profile. The provider boundary currently supports one-day forecasts through an
injectable Open-Meteo adapter with a five-second default timeout. Set
`WEATHER_TIMEOUT_SECONDS` to change that bound.

The `/weather` command calls the adapter only after a registered user saves a
location. Provider and command tests use fake HTTP openers and saved dictionaries,
so local verification performs no network requests. Failed or malformed provider
responses return a short temporary-unavailable message without exposing internals.

Daily weather is opt-in and requires a saved location. It is appended to the normal
scheduled greeting using the profile's local date and units. `/digest off` pauses
summary delivery while keeping the weather subscription; `/weather off` removes the
subscription. A provider failure leaves the greeting unchanged.

Forecasts are cached for one hour in the shared DynamoDB table. Provider failures
can use a cached forecast up to 24 hours old, and cache records expire automatically
after two days. A warm Lambda allows at most 20 uncached provider calls per minute.
These defaults can be changed with `WEATHER_CACHE_MINUTES`, `WEATHER_STALE_HOURS`,
and `WEATHER_MAX_CALLS`. Cache hits, provider calls, stale fallbacks, errors, and
rate-limit events are emitted under the `GreetingsBot` metrics namespace.

## Information requests

The provider-neutral `/ask` flow accepts `joke`, `fact`, `person <name>`,
`place <name>`, and `advice <topic>`. Queries are limited to 120 characters and
answers to 600 characters.
`INFO_REQUESTS_ENABLED` defaults to `false`. When enabled in Lambda, requests use
Amazon Titan Text Lite through Bedrock Runtime. `BEDROCK_MODEL_ID` can select another
compatible Titan model, and the SAM role limits invocation to that model ARN.

Prompts request short answers and do not include profile, note, or reminder data.
Provider failures return a temporary-unavailable message. All local tests inject a
fake Bedrock client and make no model, network, or AWS calls.

Each user can make five accepted information requests per UTC week by default. Set
`INFO_WEEKLY_LIMIT` or the SAM `InformationWeeklyLimit` parameter to change the
allowance. The counter is incremented atomically before calling Bedrock and resets on
Monday; failed provider attempts remain counted because the remote invocation may
already have started. Quota records expire from DynamoDB after their useful window.

Advice prompts ask for at most three practical suggestions, treat the topic as data,
and direct high-stakes medical, legal, financial, or emergency topics toward local
professional help. Content-filtered or malformed model results are not returned.
`BEDROCK_TIMEOUT_SECONDS` defaults to eight seconds and accepts values from 1 to 30.

## Admin API

The SAM template includes a separate read-only admin Lambda with `GET /admin/health`,
`GET /admin/stats`, `GET /admin/users`, and `GET /admin/users/{id}`. All routes
require an `Authorization: Bearer <token>` header.
`AdminApiToken` is a hidden deployment parameter with a 24-character minimum; the
application compares it in constant time and never writes it to request logs.

The health route reports service status and package version. The statistics route
currently returns only the total user count and has DynamoDB scan permission, with no
write actions. Responses disable caching and content sniffing. Handler tests use local
repositories and synthetic API Gateway events, so they do not invoke AWS resources.

`GET /admin/audit` and `/admin/dashboard/audit` provide bounded, newest-first audit
history with category and ISO-8601 time filters. Records contain request correlation,
source, action, and allowlisted changed-key names only. Configuration values, tokens,
request bodies, note text, reminder text, and user identifiers are not stored.

Feature flags use strict `true` or `false` environment values. The dashboard exposes
only the registered public flag names and enabled states; unrelated environment
variables never enter the configuration snapshot.

The user list accepts a case-insensitive `q` name or exact Telegram ID, a `status` of
`all`, `active`, or `disabled`, and a `limit` from 1 to 50. Responses are ordered by
user ID and return an opaque `next_cursor` when another page is available. Detail
responses expose scheduling and delivery preferences but omit chat IDs and location
coordinates. Audit logs record only the read category, request ID, and outcome.

`GET /admin/delivery` reports approximate pending, in-flight, and dead-letter queue
counts. `POST /admin/delivery/redrive` starts an SQS message move task only when its
JSON body contains `{"confirm":"redrive_failed_deliveries","rate":25}`. The rate may
be 1 through 500 messages per second. Redrive returns `202` with the SQS task handle;
it does not wait for completion. Queue errors return `503`, and action bodies are not
written to audit logs. Tests use a fake SQS client and never move real messages.

`GET /admin/dashboard` renders a responsive, server-side overview using the same
bearer authorization. It shows package health, active and disabled user counts, and
delivery queue counts when SQS is available. The page uses no JavaScript or external
frontend assets. Responses disable caching, framing, referrers, and content sniffing,
and apply a restrictive content security policy.

The dashboard links to searchable user and preference pages, a safe configuration
snapshot, and delivery operations. Configuration output is limited to feature states,
model names, and numeric limits; tokens, queue URLs, ARNs, and weather coordinates are
not rendered. A failed-message redrive requires the same explicit confirmation and
bounded rate as the JSON API. The JSON endpoints remain available for scripts.

### User data controls

`GET /admin/users/{id}/export` downloads a deterministic, versioned JSON document
containing the user's profile, notes, and reminders. Chat delivery IDs and DynamoDB
keys are excluded, records are ownership checked, and oversized exports fail instead
of producing an unbounded response.

Deletion uses three protected POST requests: `/admin/users/{id}/deletion` creates a
30-minute confirmation challenge, `/deletion/confirm` verifies the returned token,
and `/deletion/execute` removes the confirmed account. Only the token digest is
stored. Cleanup removes active one-time schedules and bounded owner-data batches,
leaving the profile until the remaining records are gone.

Daily delivery markers expire after 90 days and opaque delivery receipts after 14
days by default. `DeliveryHistoryDays` and `DeliveryReceiptDays` set bounded retention
periods in the SAM template. Receipt records contain no message text or user ID.
