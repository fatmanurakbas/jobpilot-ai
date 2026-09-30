"""Local visible-browser bridge for JobPilot (binds to loopback only)."""
import base64
import json
import re
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


ALLOWED_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1):(5173|5174|3000)$")
MAX_REQUEST_BYTES = 20 * 1024 * 1024


def _fill_visible(envelope):
    app_id = int(envelope["application_id"])
    api_base = envelope["api_base"].rstrip("/")
    plan = envelope["plan"]
    uploads = envelope.get("uploads", {})
    if int(plan["application_id"]) != app_id or not plan.get("ready_to_fill"):
        raise ValueError("The backend form plan is not ready or does not match the application.")

    with tempfile.TemporaryDirectory(prefix="jobpilot-review-") as tmp:
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(Path(__file__).parent / "browser-profile"),
                headless=False,
                accept_downloads=True,
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(plan["url"], wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1000)
            controls = page.locator("input, textarea, select")
            checks = []
            for field in plan["fields"]:
                action = field["action"]
                if action == "SKIP":
                    continue
                if action == "UNRESOLVED":
                    raise ValueError(f"Unresolved field: {field.get('field_name')}")
                control = controls.nth(field["field_index"])
                if action == "UPLOAD":
                    upload = uploads.get(str(field["field_index"]))
                    if not upload:
                        raise ValueError(f"Upload file is missing: {field.get('field_name')}")
                    file_path = Path(tmp) / Path(upload["filename"]).name
                    file_path.write_bytes(base64.b64decode(upload["content_base64"], validate=True))
                    control.set_input_files(str(file_path))
                    actual = control.evaluate("el => el.files?.[0]?.name || ''")
                    expected = file_path.name
                else:
                    tag = control.evaluate("el => el.tagName.toLowerCase()")
                    if tag == "select":
                        try:
                            control.select_option(value=field["value"])
                        except Exception:
                            control.select_option(label=field["value"])
                        actual = control.input_value()
                        selected = control.locator("option:checked").text_content() or ""
                        expected = field["value"] or ""
                        verified = actual.strip().lower() == expected.strip().lower() or selected.strip().lower() == expected.strip().lower()
                        checks.append({"field_index": field["field_index"], "field_name": field.get("field_name"), "verified": verified})
                        continue
                    control.fill(field.get("value") or "")
                    actual = control.input_value()
                    expected = field.get("value") or ""
                verified = actual == expected
                checks.append({"field_index": field["field_index"], "field_name": field.get("field_name"), "verified": verified})

            failed = sum(not item["verified"] for item in checks)
            evidence = {"verified": failed == 0, "verified_count": len(checks) - failed, "failed_count": failed, "fields": checks}
            if failed:
                raise ValueError(f"Visible form verification failed: {failed} field(s).")

            screenshot = page.screenshot(full_page=True)
            body = json.dumps({
                "screenshot_base64": base64.b64encode(screenshot).decode("ascii"),
                "final_url": page.url,
                "verification": evidence,
            }).encode("utf-8")
            request = urllib.request.Request(
                f"{api_base}/applications/{app_id}/browser-review-result",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                print("JobPilot form prepared:", response.read().decode("utf-8"))
            print("Review the open application page. Submit manually on the site if you choose; JobPilot will not submit it.")
            while not page.is_closed():
                page.wait_for_timeout(1000)
            context.close()


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin", "")
        if ALLOWED_ORIGIN.fullmatch(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path not in {"/", "/health"}:
            self.send_error(404, "Not found. Use the JobPilot app to start a browser review.")
            return
        body = json.dumps({
            "service": "JobPilot Browser Agent",
            "status": "ready",
            "next_step": "Return to JobPilot and select Review in Browser.",
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/review" or not ALLOWED_ORIGIN.fullmatch(self.headers.get("Origin", "")):
            self.send_error(403, "Only the local JobPilot web app can start a review.")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_error(413, "Review plan exceeds the local size limit.")
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except Exception:
            self.send_error(400, "Invalid review request.")
            return
        threading.Thread(target=self._run, args=(payload,), daemon=True).start()
        response = json.dumps({"started": True, "message": "Visible review browser is opening."}).encode()
        self.send_response(202)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    @staticmethod
    def _run(payload):
        try:
            _fill_visible(payload)
        except Exception as error:
            print("JobPilot Browser Agent error:", error)

    def log_message(self, _format, *_args):
        pass


if __name__ == "__main__":
    print("JobPilot Browser Agent listening on http://127.0.0.1:8765")
    print("Keep this window open while reviewing an application.")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
