#!/usr/bin/env python3
"""Minimal web app for recording shift-related dates."""

from __future__ import annotations

import html
import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "shifts.json"
HOST = "0.0.0.0"
PORT = 8000

QUESTIONS = [
    ("service", "Πότε θα κάνεις υπηρεσία;"),
    ("presence", "Πότε θα κάνεις παρουσία;"),
    ("leave", "Πότε θα πάρεις κενό;"),
]


def load_entries() -> list[dict[str, str]]:
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_entries(entries: list[dict[str, str]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)


def page_layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang=\"el\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    }}
    body {{
      margin: 0;
      background: #f5f7fb;
      color: #1f2933;
    }}
    .container {{
      max-width: 720px;
      margin: 40px auto;
      background: #fff;
      border-radius: 16px;
      padding: 32px;
      box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
    }}
    header {{
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
    }}
    p {{
      margin: 0 0 16px;
      color: #4b5563;
    }}
    form {{
      display: grid;
      gap: 16px;
    }}
    label {{
      font-weight: 600;
    }}
    input {{
      margin-top: 6px;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid #d1d5db;
      font-size: 16px;
    }}
    .actions {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin-top: 8px;
    }}
    button {{
      background: #2563eb;
      color: #fff;
      border: none;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
    }}
    a {{
      color: #2563eb;
      text-decoration: none;
      font-weight: 600;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 16px;
    }}
    th, td {{
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid #e5e7eb;
    }}
    .empty {{
      padding: 16px;
      background: #fef9c3;
      border-radius: 8px;
      color: #92400e;
    }}
  </style>
</head>
<body>
  <div class=\"container\">
    {body}
  </div>
</body>
</html>"""


def render_form(message: str | None = None) -> str:
    message_html = ""
    if message:
        message_html = f"<p>{html.escape(message)}</p>"

    fields = "".join(
        f"""
        <div>
          <label for=\"{key}\">{html.escape(label)}</label>
          <input id=\"{key}\" name=\"{key}\" type=\"text\" placeholder=\"π.χ. 2024-06-15\" />
        </div>
        """
        for key, label in QUESTIONS
    )

    body = f"""
    <header>
      <h1>Καταγραφή Υπηρεσιών</h1>
      <p>Συμπλήρωσε τις ημερομηνίες και αποθήκευσέ τες τοπικά.</p>
      {message_html}
    </header>
    <form method=\"post\" action=\"/\">
      {fields}
      <div class=\"actions\">
        <button type=\"submit\">Αποθήκευση</button>
        <a href=\"/list\">Προβολή καταχωρήσεων</a>
      </div>
    </form>
    """
    return page_layout("Καταγραφή Υπηρεσιών", body)


def render_list(entries: list[dict[str, str]]) -> str:
    if not entries:
        body = """
        <header>
          <h1>Καταχωρήσεις</h1>
          <p>Δεν υπάρχουν καταχωρήσεις ακόμα.</p>
        </header>
        <div class=\"empty\">Πρόσθεσε νέες ημερομηνίες από τη φόρμα.</div>
        <div class=\"actions\" style=\"margin-top: 20px;\">
          <a href=\"/\">Επιστροφή στη φόρμα</a>
        </div>
        """
        return page_layout("Καταχωρήσεις", body)

    rows = "".join(
        """
        <tr>
          <td>{type}</td>
          <td>{date}</td>
          <td>{recorded_at}</td>
        </tr>
        """.format(
            type=html.escape(entry.get("type", "-")),
            date=html.escape(entry.get("date", "-")),
            recorded_at=html.escape(entry.get("recorded_at", "-")),
        )
        for entry in entries
    )

    body = f"""
    <header>
      <h1>Καταχωρήσεις</h1>
      <p>Όλες οι αποθηκευμένες ημερομηνίες.</p>
    </header>
    <table>
      <thead>
        <tr>
          <th>Τύπος</th>
          <th>Ημερομηνία</th>
          <th>Καταγράφηκε</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <div class=\"actions\" style=\"margin-top: 20px;\">
      <a href=\"/\">Επιστροφή στη φόρμα</a>
    </div>
    """
    return page_layout("Καταχωρήσεις", body)


class ShiftHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self.respond(render_form())
            return
        if self.path.startswith("/list"):
            entries = load_entries()
            self.respond(render_list(entries))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length).decode("utf-8")
        data = parse_qs(payload)

        entries = load_entries()
        timestamp = datetime.now().isoformat(timespec="seconds")

        for key, _ in QUESTIONS:
            value = "".join(data.get(key, [])).strip()
            if not value:
                continue
            entries.append(
                {
                    "date": value,
                    "type": key,
                    "recorded_at": timestamp,
                }
            )

        save_entries(entries)
        self.respond(render_form("Οι καταχωρήσεις αποθηκεύτηκαν."))

    def respond(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ShiftHandler)
    print(f"Server running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
