# server.py - Upgraded with:
# 1. Password Protection
# 2. Telegram Notifications
# 3. JSON + ENV variable parsing
# 4. Better Web UI

import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


# ─── Config from Environment Variables ────────────────────────────────────────
BOT_TOKEN   = os.environ.get('TELEGRAM_BOT_TOKEN', '')   # Set in Railway
CHAT_ID     = os.environ.get('TELEGRAM_CHAT_ID', '')     # Set in Railway
LOG_PASSWORD = os.environ.get('LOG_PASSWORD', 'admin123') # Set in Railway
# ──────────────────────────────────────────────────────────────────────────────


def send_telegram(message: str):
    """Send a message to Telegram group/chat."""
    if not BOT_TOKEN or not CHAT_ID:
        print("[Telegram] BOT_TOKEN or CHAT_ID not set, skipping notification.")
        return
    try:
        payload = json.dumps({
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }).encode('utf-8')
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        req = urllib.request.Request(url, data=payload,
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
        print("[Telegram] Notification sent!")
    except Exception as e:
        print(f"[Telegram] Failed to send: {e}")


def parse_body(text: str, content_type: str) -> str:
    """Parse body as JSON or ENV-style key=value."""
    result_lines = []

    # Try JSON first
    if 'application/json' in content_type or text.strip().startswith('{') or text.strip().startswith('['):
        try:
            data = json.loads(text)
            result_lines.append("📦 <b>JSON Data:</b>")
            result_lines.append(json.dumps(data, indent=2, ensure_ascii=False))
            return '\n'.join(result_lines), 'json', data
        except json.JSONDecodeError:
            pass

    # Try ENV key=value style
    result_lines.append("🔑 <b>Key=Value Data:</b>")
    parsed = {}
    for line in text.strip().split('\n'):
        if '=' in line:
            key, _, value = line.partition('=')
            parsed[key.strip()] = value.strip()
            result_lines.append(f"  {key.strip():30s} = {value.strip()}")
        elif line.strip():
            result_lines.append(f"  {line.strip()}")

    return '\n'.join(result_lines), 'env', parsed


def check_auth(handler) -> bool:
    """Check if request has correct password via query param or header."""
    # Check Authorization header: Bearer <password>
    auth_header = handler.headers.get('Authorization', '')
    if auth_header == f'Bearer {LOG_PASSWORD}':
        return True
    # Check ?password=xxx in URL
    if f'password={LOG_PASSWORD}' in handler.path:
        return True
    return False


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Debug Server</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0d1117;
    color: #c9d1d9;
    padding: 24px;
    min-height: 100vh;
  }}
  h1 {{ color: #58a6ff; font-size: 1.6rem; margin-bottom: 6px; }}
  .subtitle {{ color: #8b949e; margin-bottom: 24px; font-size: 0.9rem; }}
  .status {{ display: inline-block; background: #1f6feb22; border: 1px solid #1f6feb;
             color: #58a6ff; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-bottom: 24px; }}
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }}
  .card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 22px;
    flex: 1;
    min-width: 180px;
  }}
  .card .label {{ color: #8b949e; font-size: 0.78rem; margin-bottom: 6px; }}
  .card .value {{ color: #e6edf3; font-size: 1.4rem; font-weight: bold; }}
  .nav {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }}
  .btn {{
    display: inline-block;
    padding: 9px 20px;
    border-radius: 8px;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
  }}
  .btn-blue  {{ background: #1f6feb; color: #fff; }}
  .btn-blue:hover {{ background: #388bfd; }}
  .btn-red   {{ background: #da3633; color: #fff; }}
  .btn-red:hover {{ background: #f85149; }}
  .btn-gray  {{ background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }}
  .btn-gray:hover {{ background: #30363d; }}
  .log-box {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 0.82rem;
    line-height: 1.6;
    max-height: 60vh;
    overflow-y: auto;
    color: #c9d1d9;
  }}
  .log-box::-webkit-scrollbar {{ width: 6px; }}
  .log-box::-webkit-scrollbar-track {{ background: #0d1117; }}
  .log-box::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 3px; }}
  .section-title {{ color: #8b949e; font-size: 0.8rem; text-transform: uppercase;
                    letter-spacing: 1px; margin-bottom: 10px; }}
  .password-form {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 28px;
    max-width: 400px;
    margin: 60px auto;
    text-align: center;
  }}
  .password-form h2 {{ color: #58a6ff; margin-bottom: 16px; }}
  .password-form input {{
    width: 100%;
    padding: 10px 14px;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    font-size: 1rem;
    margin-bottom: 14px;
  }}
  .password-form input:focus {{ outline: none; border-color: #58a6ff; }}
  .error {{ color: #f85149; font-size: 0.85rem; margin-top: 8px; }}
</style>
</head>
<body>
  <h1>🛰️ Debug Server</h1>
  <p class="subtitle">POST request catcher &amp; logger</p>
  <span class="status">● Running</span>

  <div class="cards">
    <div class="card">
      <div class="label">Total Requests</div>
      <div class="value">{total_requests}</div>
    </div>
    <div class="card">
      <div class="label">Last Request</div>
      <div class="value" style="font-size:0.95rem;">{last_request}</div>
    </div>
    <div class="card">
      <div class="label">Telegram</div>
      <div class="value" style="font-size:0.95rem; color:{tg_color};">{tg_status}</div>
    </div>
  </div>

  <div class="nav">
    <a href="/logs?password={password}" class="btn btn-blue">📋 View Logs</a>
    <a href="/clear?password={password}" class="btn btn-red" onclick="return confirm('Clear all logs?')">🗑️ Clear Logs</a>
    <a href="/" class="btn btn-gray">🔄 Refresh</a>
  </div>

  <div class="section-title">Recent Activity</div>
  <div class="log-box">{recent_logs}</div>
</body>
</html>"""


def count_requests():
    try:
        with open('requests.log', 'r') as f:
            content = f.read()
        return content.count('From:')
    except FileNotFoundError:
        return 0


def get_recent_logs(n=5):
    try:
        with open('requests.log', 'r') as f:
            content = f.read()
        if not content.strip():
            return 'No requests yet...'
        parts = content.strip().split('=' * 60)
        recent = [p.strip() for p in parts if p.strip()][-n:]
        return ('\n' + '─' * 50 + '\n').join(recent)
    except FileNotFoundError:
        return 'No requests yet...'


def get_last_request_time():
    try:
        with open('requests.log', 'r') as f:
            lines = f.readlines()
        for line in reversed(lines):
            if line.startswith('['):
                return line[1:20]
        return 'Never'
    except FileNotFoundError:
        return 'Never'


class PostHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Silence default access log spam

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            text = body.decode('utf-8')
        except UnicodeDecodeError:
            text = body.decode('latin-1')

        content_type = self.headers.get('Content-Type', '')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]

        parsed_text, fmt, parsed_data = parse_body(text, content_type)

        print(f"\n{'='*60}")
        print(f"[{timestamp}] POST from {client_ip}  |  format={fmt}")
        print(parsed_text)
        print(f"Raw: {text}")
        print(f"{'='*60}\n")

        # Save to log file
        with open('requests.log', 'a') as f:
            f.write(f"\n[{timestamp}] From: {client_ip}  |  format={fmt}\n")
            f.write(f"{text}\n")
            f.write('=' * 60 + '\n')

        # Send Telegram notification
        tg_msg = (
            f"🔔 <b>New POST Request</b>\n"
            f"🕐 <b>Time:</b> {timestamp}\n"
            f"🌐 <b>IP:</b> {client_ip}\n"
            f"📄 <b>Format:</b> {fmt.upper()}\n\n"
            f"<pre>{text[:3000]}</pre>"
        )
        send_telegram(tg_msg)

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Data received, logged, and notified\n')

    def do_GET(self):
        path = self.path.split('?')[0]

        if path == '/logs':
            if not check_auth(self):
                self._send_auth_error()
                return
            try:
                with open('requests.log', 'r') as f:
                    content = f.read()
            except FileNotFoundError:
                content = 'No logs yet.'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        elif path == '/clear':
            if not check_auth(self):
                self._send_auth_error()
                return
            open('requests.log', 'w').close()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Logs cleared.\n')

        else:
            # Home page — no auth needed (stats only)
            tg_ok = bool(BOT_TOKEN and CHAT_ID)
            html = HTML_TEMPLATE.format(
                total_requests=count_requests(),
                last_request=get_last_request_time(),
                tg_color='#3fb950' if tg_ok else '#f85149',
                tg_status='Connected ✅' if tg_ok else 'Not Set ❌',
                password=LOG_PASSWORD,
                recent_logs=get_recent_logs(5),
            )
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

    def _send_auth_error(self):
        html = """<!DOCTYPE html>
<html><head><title>Access Denied</title>
<style>
  body { font-family: monospace; background:#0d1117; color:#c9d1d9; display:flex; align-items:center; justify-content:center; min-height:100vh; }
  .box { background:#161b22; border:1px solid #da3633; border-radius:10px; padding:32px; text-align:center; max-width:400px; }
  h2 { color:#f85149; margin-bottom:12px; }
  input { width:100%; padding:10px; background:#0d1117; border:1px solid #30363d; border-radius:8px; color:#e6edf3; font-size:1rem; margin-bottom:12px; }
  button { background:#1f6feb; color:#fff; border:none; padding:10px 24px; border-radius:8px; font-size:1rem; cursor:pointer; }
</style></head>
<body>
  <div class="box">
    <h2>🔒 Password Required</h2>
    <p style="color:#8b949e;margin-bottom:16px;">Enter password to view logs</p>
    <input type="password" id="pw" placeholder="Password" onkeydown="if(event.key==='Enter')go()"/>
    <br>
    <button onclick="go()">Unlock</button>
    <script>
      function go() {
        var pw = document.getElementById('pw').value;
        window.location.href = '/logs?password=' + encodeURIComponent(pw);
      }
    </script>
  </div>
</body></html>"""
        self.send_response(401)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))


def run():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), PostHandler)
    tg_ok = bool(BOT_TOKEN and CHAT_ID)
    print(f"{'='*60}")
    print(f"  Debug Server Running on port {port}")
    print(f"  POST endpoint : http://0.0.0.0:{port}/")
    print(f"  View logs     : http://0.0.0.0:{port}/logs?password={LOG_PASSWORD}")
    print(f"  Clear logs    : http://0.0.0.0:{port}/clear?password={LOG_PASSWORD}")
    print(f"  Telegram      : {'✅ Connected' if tg_ok else '❌ Not configured'}")
    print(f"{'='*60}")
    server.serve_forever()


if __name__ == '__main__':
    run()
