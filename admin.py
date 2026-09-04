import hashlib
import hmac
import html
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from config import BLOCKCHAINS
from user_bans import ban_user, list_banned_users, unban_user
from wallets import list_wallets, save_wallets


ADMIN_PORT = int(os.getenv("PORT", "5000"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
SESSION_VALUE = hmac.new(
    SESSION_SECRET.encode(),
    b"wallet-admin-session",
    hashlib.sha256,
).hexdigest()


def is_authenticated(handler):
    cookie_header = handler.headers.get("Cookie", "")
    cookies = {}
    for part in cookie_header.split(";"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            cookies[key] = value
    return hmac.compare_digest(cookies.get("wallet_admin", ""), SESSION_VALUE)


def page_shell(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1020;
      --panel: #131b31;
      --panel-2: #1a2541;
      --text: #f5f7ff;
      --muted: #9aa8c7;
      --accent: #7c9cff;
      --success: #55d6a3;
      --border: #2b3a61;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at top right, #18264c, var(--bg) 46%);
      color: var(--text);
      font: 15px/1.5 system-ui, -apple-system, sans-serif;
    }}
    .wrap {{ width: min(1100px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0 64px; }}
    header {{ display: flex; justify-content: space-between; gap: 20px; align-items: start; margin-bottom: 28px; }}
    h1, h2, p {{ margin-top: 0; }}
    h1 {{ font-size: clamp(28px, 5vw, 44px); letter-spacing: -0.03em; margin-bottom: 8px; }}
    h2 {{ font-size: 19px; margin-bottom: 8px; }}
    .muted {{ color: var(--muted); }}
    .panel {{
      background: rgba(19, 27, 49, .92);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 18px 50px rgba(0,0,0,.2);
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 16px; }}
    label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
    textarea, input[type=password], input[type=number], input[type=text] {{
      width: 100%; border: 1px solid var(--border); border-radius: 10px;
      background: var(--panel-2); color: var(--text); padding: 12px;
      font: inherit; outline: none;
    }}
    textarea {{ min-height: 118px; resize: vertical; }}
    textarea:focus, input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(124,156,255,.15); }}
    button {{
      border: 0; border-radius: 10px; padding: 11px 16px; color: #091023;
      background: var(--accent); font: inherit; font-weight: 800; cursor: pointer;
    }}
    button:hover {{ filter: brightness(1.08); }}
    .top-button {{ background: transparent; color: var(--muted); border: 1px solid var(--border); }}
    .actions {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 24px; }}
    .count {{ color: var(--success); font-size: 13px; }}
    .notice {{ margin: 0 0 20px; padding: 12px 14px; border-radius: 10px; background: rgba(85,214,163,.12); color: #a8f0d0; }}
    .login {{ max-width: 430px; margin: 12vh auto 0; }}
    .login form {{ display: grid; gap: 14px; }}
    .user-form {{ display: grid; grid-template-columns: minmax(180px, 1fr) minmax(220px, 2fr) auto; gap: 12px; align-items: end; }}
    .user-form .field {{ min-width: 0; }}
    .user-list {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    .user-list th, .user-list td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    .user-list th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }}
    .user-list form {{ margin: 0; }}
    .empty {{ color: var(--muted); margin: 12px 0 0; }}
    code {{ color: #c8d4ff; word-break: break-all; }}
    @media (max-width: 760px) {{ .user-form {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 620px) {{ header {{ display: block; }} .top-button {{ margin-top: 12px; }} .user-list {{ display: block; overflow-x: auto; }} }}
  </style>
</head>
<body><main class="wrap">{body}</main></body>
</html>"""


def login_page(error=""):
    notice = f'<p class="notice">{html.escape(error)}</p>' if error else ""
    return page_shell(
        "Wallet Admin Login",
        f"""
        <section class="panel login">
          <h1>Wallet Admin</h1>
          <p class="muted">Manage the rotating public payment wallets for every blockchain.</p>
          {notice}
          <form method="post" action="/login">
            <input type="text" name="username" autocomplete="username"
                   value="admin" hidden aria-hidden="true">
            <label for="password">Admin password</label>
            <input id="password" name="password" type="password" autocomplete="current-password" required>
            <button type="submit">Sign in</button>
          </form>
        </section>
        """,
    )


def dashboard_page(message=""):
    wallets = list_wallets()
    banned_users = list_banned_users()
    cards = []
    for blockchain in BLOCKCHAINS:
        entries = wallets.get(blockchain, [])
        values = "\n".join(item["address"] for item in entries if item["active"])
        cards.append(
            f"""
            <section class="panel">
              <label for="wallet-{html.escape(blockchain)}">{html.escape(blockchain)}</label>
              <p class="muted">Paste one public receiving wallet per line.</p>
              <textarea id="wallet-{html.escape(blockchain)}"
                        name="wallet_{html.escape(blockchain)}"
                        placeholder="Wallet address 1&#10;Wallet address 2">{html.escape(values)}</textarea>
              <div class="count">{len([item for item in entries if item["active"]])} active wallet(s)</div>
            </section>
            """
        )
    notice = f'<p class="notice">{html.escape(message)}</p>' if message else ""
    banned_rows = "".join(
        f"""
        <tr>
          <td><code>{html.escape(str(item["telegram_user_id"]))}</code></td>
          <td>{html.escape(item["reason"] or "No reason provided")}</td>
          <td>{html.escape(str(item["banned_at"]))}</td>
          <td>
            <form method="post" action="/users/unban">
              <input type="hidden" name="user_id" value="{html.escape(str(item["telegram_user_id"]))}">
              <button class="top-button" type="submit">Unban</button>
            </form>
          </td>
        </tr>
        """
        for item in banned_users
    )
    banned_list = (
        f"""
        <table class="user-list">
          <thead><tr><th>Telegram user ID</th><th>Reason</th><th>Banned at</th><th></th></tr></thead>
          <tbody>{banned_rows}</tbody>
        </table>
        """
        if banned_rows
        else '<p class="empty">No users are currently banned.</p>'
    )
    return page_shell(
        "Wallet Admin",
        f"""
        <header>
          <div>
            <h1>Wallet rotation</h1>
            <p class="muted">Save multiple receiving wallets per chain. The bot assigns the least recently used wallet.</p>
          </div>
          <form method="post" action="/logout"><button class="top-button" type="submit">Sign out</button></form>
        </header>
        {notice}
        <form method="post" action="/wallets/save">
          <div class="grid">{''.join(cards)}</div>
          <div class="actions">
            <span class="muted">Only public receiving addresses belong here.</span>
            <button type="submit">Save wallet pools</button>
          </div>
        </form>
        <section class="panel" style="margin-top: 16px;">
          <h2>User access</h2>
          <p class="muted">Ban a Telegram user from using the bot. This does not delete payment or order history.</p>
          <form method="post" action="/users/ban" class="user-form">
            <div class="field">
              <label for="user-id">Telegram user ID</label>
              <input id="user-id" name="user_id" type="number" min="1" step="1" required>
            </div>
            <div class="field">
              <label for="ban-reason">Reason (optional)</label>
              <input id="ban-reason" name="reason" type="text" maxlength="500" placeholder="Reason for the ban">
            </div>
            <button type="submit">Ban user</button>
          </form>
          {banned_list}
        </section>
        """,
    )


class AdminHandler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        return

    def send_html(self, content, status=200, headers=None):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        return parse_qs(
            self.rfile.read(length).decode("utf-8"),
            keep_blank_values=True,
        )

    def do_GET(self):
        if self.path != "/":
            self.send_html("Not found", status=404)
            return
        if not is_authenticated(self):
            self.send_html(login_page())
            return
        try:
            self.send_html(dashboard_page())
        except Exception:
            self.send_html(
                login_page("The wallet database is not ready yet. Please try again."),
                status=503,
            )

    def do_POST(self):
        if self.path == "/login":
            form = self.read_form()
            submitted = form.get("password", [""])[0]
            if (
                ADMIN_PASSWORD
                and SESSION_SECRET
                and hmac.compare_digest(submitted, ADMIN_PASSWORD)
            ):
                self.send_html(
                    dashboard_page(),
                    headers={
                        "Set-Cookie": "wallet_admin="
                        f"{SESSION_VALUE}; HttpOnly; SameSite=Strict; Path=/"
                    },
                )
            else:
                self.send_html(login_page("Incorrect password."), status=401)
            return

        if self.path == "/logout":
            self.send_html(
                login_page(),
                headers={
                    "Set-Cookie": "wallet_admin=; Max-Age=0; HttpOnly; "
                    "SameSite=Strict; Path=/"
                },
            )
            return

        if self.path == "/wallets/save" and is_authenticated(self):
            form = self.read_form()
            saved = 0
            for blockchain in BLOCKCHAINS:
                addresses = form.get(f"wallet_{blockchain}", [""])[0].splitlines()
                saved += save_wallets(blockchain, addresses)
            self.send_html(dashboard_page(f"Saved {saved} active wallet address(es)."))
            return

        if self.path == "/users/ban" and is_authenticated(self):
            form = self.read_form()
            try:
                user_id = int(form.get("user_id", [""])[0])
                if user_id <= 0:
                    raise ValueError
                ban_user(user_id, form.get("reason", [""])[0])
                self.send_html(
                    dashboard_page(f"User {user_id} has been banned.")
                )
            except ValueError:
                self.send_html(
                    dashboard_page("Enter a valid positive Telegram user ID."),
                    status=400,
                )
            except Exception:
                self.send_html(
                    dashboard_page("Could not update the user ban list."),
                    status=503,
                )
            return

        if self.path == "/users/unban" and is_authenticated(self):
            form = self.read_form()
            try:
                user_id = int(form.get("user_id", [""])[0])
                if user_id <= 0:
                    raise ValueError
                removed = unban_user(user_id)
                message = (
                    f"User {user_id} has been unbanned."
                    if removed
                    else f"User {user_id} was not on the ban list."
                )
                self.send_html(dashboard_page(message))
            except ValueError:
                self.send_html(
                    dashboard_page("Enter a valid positive Telegram user ID."),
                    status=400,
                )
            except Exception:
                self.send_html(
                    dashboard_page("Could not update the user ban list."),
                    status=503,
                )
            return

        self.send_html("Not found", status=404)


def start_admin_server():
    server = ThreadingHTTPServer(("0.0.0.0", ADMIN_PORT), AdminHandler)
    server.daemon_threads = True
    server.serve_forever()