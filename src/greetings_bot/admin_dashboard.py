from dataclasses import dataclass
from html import escape
from typing import Mapping, Optional
from urllib.parse import urlencode

from greetings_bot.admin_config import DashboardConfig
from greetings_bot.admin_delivery import DeliveryQueueSummary
from greetings_bot.admin_users import AdminUserPage, AdminUserQuery
from greetings_bot.configuration_audit import AuditPage, AuditQuery


@dataclass(frozen=True)
class DashboardSnapshot:
    users: int
    active_users: int
    disabled_users: int
    pending: Optional[int] = None
    in_flight: Optional[int] = None
    failed: Optional[int] = None


def render_dashboard(
    version: str, snapshot: Optional[DashboardSnapshot] = None
) -> str:
    snapshot = snapshot or DashboardSnapshot(0, 0, 0)
    delivery = _delivery_cards(snapshot)
    content = f"""<section class="panel" aria-labelledby="status-heading">
      <h2 id="status-heading">Service status</h2>
      <p>The admin service is available.</p>
    </section>
    <section class="panel" aria-labelledby="users-heading">
      <h2 id="users-heading">Users</h2>
      <div class="grid">
        <div class="card"><strong data-metric="users">{snapshot.users}</strong>Total</div>
        <div class="card"><strong data-metric="active-users">{snapshot.active_users}</strong>Active</div>
        <div class="card"><strong data-metric="disabled-users">{snapshot.disabled_users}</strong>Disabled</div>
      </div>
    </section>
    <section class="panel" aria-labelledby="delivery-heading">
      <h2 id="delivery-heading">Delivery</h2>
      {delivery}
    </section>"""
    return _render_layout(
        "Greetings Bot Admin",
        "System overview",
        "A read-only operational summary.",
        version,
        content,
    )


def _render_layout(
    title: str, heading: str, subtitle: str, version: str, content: str
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #17202a; --muted: #607080;
      --panel: #ffffff; --line: #dce3e8; --accent: #176b61; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); background: #f3f6f7;
      font: 16px/1.5 system-ui, sans-serif; }}
    header {{ color: white; background: #123d3a; padding: 1rem 1.5rem; }}
    header strong {{ font-size: 1.15rem; }}
    nav {{ display: flex; gap: 1rem; margin-top: .65rem; flex-wrap: wrap; }}
    nav a {{ color: #d7f5ef; text-underline-offset: .2rem; }}
    main {{ width: min(72rem, 100%); margin: 0 auto; padding: 2rem 1.5rem; }}
    .intro {{ display: flex; justify-content: space-between; gap: 1rem;
      align-items: end; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0 0 .25rem; font-size: clamp(1.6rem, 4vw, 2.25rem); }}
    .muted {{ color: var(--muted); }}
    .panel {{ margin-top: 1.5rem; padding: 1.25rem; background: var(--panel);
      border: 1px solid var(--line); border-radius: .65rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
      gap: 1rem; margin-top: 1rem; }}
    .card {{ padding: 1rem; border: 1px solid var(--line); border-radius: .5rem; }}
    .card strong {{ display: block; color: var(--accent); font-size: 1.8rem; }}
    .details {{ display: grid; grid-template-columns: minmax(9rem, 1fr) 2fr;
      gap: .65rem 1rem; }}
    .details dt {{ color: var(--muted); font-weight: 600; }}
    .details dd {{ margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: .7rem; text-align: left; border-bottom: 1px solid var(--line); }}
    input, select, button {{ min-height: 2.6rem; padding: .45rem .6rem;
      font: inherit; border: 1px solid #9aa9b2; border-radius: .35rem; }}
    button {{ color: white; background: var(--accent); cursor: pointer; }}
    footer {{ width: min(72rem, 100%); margin: 0 auto; padding: 0 1.5rem 2rem;
      color: var(--muted); font-size: .9rem; }}
    @media (max-width: 38rem) {{ .intro {{ display: block; }} }}
  </style>
</head>
<body>
  <header>
    <strong>Greetings Bot</strong>
    <nav aria-label="Admin navigation">
      <a href="/admin/dashboard">Overview</a>
      <a href="/admin/dashboard/users">Users</a>
      <a href="/admin/dashboard/delivery">Delivery</a>
      <a href="/admin/dashboard/config">Configuration</a>
      <a href="/admin/dashboard/audit">Audit</a>
    </nav>
  </header>
  <main>
    <section class="intro">
      <div><h1>{escape(heading)}</h1><p class="muted">{escape(subtitle)}</p></div>
      <p class="muted">Version {escape(version)}</p>
    </section>
    {content}
  </main>
  <footer>Protected administration surface</footer>
</body>
</html>"""


def _delivery_cards(snapshot: DashboardSnapshot) -> str:
    if None in (snapshot.pending, snapshot.in_flight, snapshot.failed):
        return '<p class="muted">Delivery summary unavailable.</p>'
    return f"""<div class="grid">
        <div class="card"><strong data-metric="pending">{snapshot.pending}</strong>Pending</div>
        <div class="card"><strong data-metric="in-flight">{snapshot.in_flight}</strong>In flight</div>
        <div class="card"><strong data-metric="failed">{snapshot.failed}</strong>Failed</div>
      </div>"""


def render_user_list(
    version: str, page: AdminUserPage, query: AdminUserQuery
) -> str:
    rows = "".join(_user_row(item) for item in page.items)
    if not rows:
        rows = '<tr><td colspan="5" class="muted">No matching users.</td></tr>'
    next_link = ""
    if page.next_cursor:
        params = {
            "q": query.term,
            "status": query.status,
            "limit": str(query.limit),
            "cursor": page.next_cursor,
        }
        href = "/admin/dashboard/users?" + urlencode(params)
        next_link = f'<p><a href="{escape(href)}">Next page</a></p>'
    options = "".join(
        '<option value="{}"{}>{}</option>'.format(
            status,
            " selected" if query.status == status else "",
            status.title(),
        )
        for status in ("all", "active", "disabled")
    )
    content = f"""<section class="panel">
      <form method="get" action="/admin/dashboard/users">
        <label>Search <input name="q" value="{escape(query.term)}" maxlength="50"></label>
        <label>Status <select name="status">{options}</select></label>
        <label>Rows <input name="limit" type="number" min="1" max="50" value="{query.limit}"></label>
        <button type="submit">Apply</button>
      </form>
    </section>
    <section class="panel">
      <div role="region" aria-label="User results" tabindex="0">
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Timezone</th><th>Greeting</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      {next_link}
    </section>"""
    return _render_layout(
        "Users · Greetings Bot Admin",
        "User administration",
        "Search profiles and inspect delivery preferences.",
        version,
        content,
    )


def _user_row(item) -> str:
    user_id = int(item["id"])
    return """<tr>
      <td><a href="/admin/dashboard/users/{id}">{id}</a></td>
      <td>{name}</td><td>{status}</td><td>{timezone}</td><td>{greeting}</td>
    </tr>""".format(
        id=user_id,
        name=escape(str(item["name"])),
        status=escape(str(item["status"])),
        timezone=escape(str(item["timezone"])),
        greeting=escape(str(item["greeting_time"])),
    )


def render_user_detail(version: str, detail: Mapping[str, object]) -> str:
    preferences = detail["preferences"]
    days = ", ".join(preferences["greeting_days"])
    quiet = preferences["quiet_hours"]
    quiet_label = (
        "{}–{}".format(quiet["start"], quiet["end"])
        if isinstance(quiet, dict)
        else "Not set"
    )
    weather_location = preferences["weather_location"] or "Not set"
    content = """<p><a href="/admin/dashboard/users">← Back to users</a></p>
    <section class="panel">
      <dl class="details">
        <dt>Telegram ID</dt><dd>{id}</dd>
        <dt>Status</dt><dd>{status}</dd>
        <dt>Locale</dt><dd>{locale}</dd>
        <dt>Timezone</dt><dd>{timezone}</dd>
        <dt>Greeting time</dt><dd>{greeting_time}</dd>
        <dt>Greeting style</dt><dd>{greeting_style}</dd>
        <dt>Greeting days</dt><dd>{days}</dd>
        <dt>Quiet hours</dt><dd>{quiet}</dd>
        <dt>Digest</dt><dd>{digest}</dd>
        <dt>Weather units</dt><dd>{units}</dd>
        <dt>Weather summary</dt><dd>{weather_summary}</dd>
        <dt>Weather location</dt><dd>{weather_location}</dd>
      </dl>
    </section>""".format(
        id=int(detail["id"]),
        status=escape(str(detail["status"]).title()),
        locale=escape(str(preferences["locale"])),
        timezone=escape(str(preferences["timezone"])),
        greeting_time=escape(str(preferences["greeting_time"])),
        greeting_style=escape(
            str(preferences["greeting_template_category"]).title()
        ),
        days=escape(days),
        quiet=escape(quiet_label),
        digest=escape(str(preferences["digest_mode"]).title()),
        units=escape(str(preferences["weather_units"]).title()),
        weather_summary=(
            "Enabled" if preferences["weather_summary"] else "Disabled"
        ),
        weather_location=escape(str(weather_location)),
    )
    return _render_layout(
        "User · Greetings Bot Admin",
        str(detail["name"]),
        "Profile and delivery preferences.",
        version,
        content,
    )


def render_config(version: str, config: DashboardConfig) -> str:
    flags = ", ".join(
        "{}={}".format(name, "on" if enabled else "off")
        for name, enabled in config.feature_flags
    )
    usage_budgets = ", ".join(
        "{}={}".format(name, value) for name, value in config.usage_budgets
    )
    content = """<section class="panel">
      <p><strong>Deployment managed.</strong> Change these values through the stack
      parameters or Lambda environment, then redeploy.</p>
      <dl class="details">
        <dt>Information requests</dt><dd>{information}</dd>
        <dt>Weekly allowance</dt><dd>{weekly_limit} requests per week</dd>
        <dt>Bedrock model</dt><dd>{model}</dd>
        <dt>Weather provider limit</dt><dd>{weather_calls} per minute</dd>
        <dt>Weather cache</dt><dd>{cache_minutes} minutes</dd>
        <dt>Weather stale fallback</dt><dd>{stale_hours} hours</dd>
        <dt>Delivery administration</dt><dd>{delivery}</dd>
        <dt>Dispatch batch limit</dt><dd>{dispatch_batch_size} messages</dd>
        <dt>Queue high watermark</dt><dd>{queue_high_watermark} messages</dd>
        <dt>Daily usage warnings</dt><dd>{usage_budgets}</dd>
        <dt>Delivery history retention</dt><dd>{history_days} days</dd>
        <dt>Receipt retention</dt><dd>{receipt_days} days</dd>
        <dt>Message languages</dt><dd>{locales}</dd>
        <dt>Message fallback</dt><dd>{fallback_locale}</dd>
        <dt>Greeting styles</dt><dd>{template_categories}</dd>
        <dt>Safe template variables</dt><dd>{template_variables}</dd>
        <dt>Feature flags</dt><dd>{feature_flags}</dd>
      </dl>
    </section>""".format(
        information="Enabled" if config.information_enabled else "Disabled",
        weekly_limit=config.information_weekly_limit,
        model=escape(config.bedrock_model),
        weather_calls=config.weather_max_calls,
        cache_minutes=config.weather_cache_minutes,
        stale_hours=config.weather_stale_hours,
        delivery="Available" if config.delivery_admin_configured else "Unavailable",
        dispatch_batch_size=config.dispatch_batch_size,
        queue_high_watermark=config.queue_high_watermark,
        usage_budgets=escape(usage_budgets),
        history_days=config.delivery_history_days,
        receipt_days=config.delivery_receipt_days,
        locales=escape(", ".join(config.supported_locales)),
        fallback_locale=escape(config.fallback_locale),
        template_categories=escape(", ".join(config.template_categories)),
        template_variables=escape(", ".join(config.template_variables)),
        feature_flags=escape(flags),
    )
    return _render_layout(
        "Configuration · Greetings Bot Admin",
        "Configuration",
        "Safe runtime settings and operational limits.",
        version,
        content,
    )


def render_audit(version: str, page: AuditPage, query: AuditQuery) -> str:
    rows = "".join(
        """<tr><td>{time}</td><td>{category}</td><td>{action}</td>
        <td>{source}</td><td>{request_id}</td><td>{keys}</td></tr>""".format(
            time=escape(record.occurred_at.isoformat()),
            category=escape(record.category),
            action=escape(record.action),
            source=escape(record.source),
            request_id=escape(record.request_id),
            keys=escape(", ".join(record.changed_keys) or "None"),
        )
        for record in page.records
    )
    if not rows:
        rows = '<tr><td colspan="6">No matching audit records.</td></tr>'
    next_link = ""
    if page.next_cursor:
        values = {"limit": str(query.limit), "cursor": page.next_cursor}
        if query.category:
            values["category"] = query.category
        if query.since:
            values["since"] = query.since.isoformat()
        if query.until:
            values["until"] = query.until.isoformat()
        next_link = '<p><a href="?{}">Next page</a></p>'.format(
            escape(urlencode(values))
        )
    content = """<section class="panel">
      <p>Privacy-safe configuration and administration history.</p>
      <table><thead><tr><th>Time</th><th>Category</th><th>Action</th>
      <th>Source</th><th>Request</th><th>Changed keys</th></tr></thead>
      <tbody>{rows}</tbody></table>{next_link}
    </section>""".format(rows=rows, next_link=next_link)
    return _render_layout(
        "Audit · Greetings Bot Admin",
        "Audit history",
        "Bounded operational attribution without configuration values.",
        version,
        content,
    )


def render_delivery(
    version: str,
    summary: DeliveryQueueSummary,
    feedback: Optional[str] = None,
) -> str:
    notice = (
        '<p role="status">{}</p>'.format(escape(feedback))
        if feedback
        else ""
    )
    content = f"""<section class="panel" aria-labelledby="queue-heading">
      <h2 id="queue-heading">Queue status</h2>
      <div class="grid">
        <div class="card"><strong data-metric="pending">{summary.pending}</strong>Pending</div>
        <div class="card"><strong data-metric="in-flight">{summary.in_flight}</strong>In flight</div>
        <div class="card"><strong data-metric="failed">{summary.failed}</strong>Failed</div>
      </div>
    </section>
    <section class="panel" aria-labelledby="redrive-heading">
      <h2 id="redrive-heading">Redrive failed deliveries</h2>
      {notice}
      <form method="post" action="/admin/dashboard/delivery/redrive">
        <label>Rate <input name="rate" type="number" min="1" max="500" value="25" required></label>
        <label><input name="confirm" type="checkbox"
          value="redrive_failed_deliveries" required> Confirm redrive</label>
        <button type="submit">Start redrive</button>
      </form>
    </section>"""
    return _render_layout(
        "Delivery · Greetings Bot Admin",
        "Delivery operations",
        "Inspect queues and recover failed messages.",
        version,
        content,
    )
