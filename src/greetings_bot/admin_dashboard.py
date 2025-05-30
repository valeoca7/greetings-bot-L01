from dataclasses import dataclass
from html import escape
from typing import Optional


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
    safe_version = escape(version)
    snapshot = snapshot or DashboardSnapshot(0, 0, 0)
    delivery = _delivery_cards(snapshot)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Greetings Bot Admin</title>
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
      <a href="/admin/users">Users API</a>
      <a href="/admin/delivery">Delivery API</a>
    </nav>
  </header>
  <main>
    <section class="intro">
      <div><h1>System overview</h1><p class="muted">A read-only operational summary.</p></div>
      <p class="muted">Version {safe_version}</p>
    </section>
    <section class="panel" aria-labelledby="status-heading">
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
    </section>
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
