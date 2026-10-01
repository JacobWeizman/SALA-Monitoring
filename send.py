# -*- coding: utf-8 -*-
"""Versand der Alarm-Mail ueber Mailjet (Send API v3.1)."""
import os, json, base64, urllib.request

MJ_KEY = os.environ.get("MAILJET_API_KEY", "").strip()
MJ_SECRET = os.environ.get("MAILJET_SECRET", "").strip()
SENDER = os.environ.get("ALERT_SENDER", "linda@smartphoneaus-lebenan.de").strip()
RECIPIENTS = [e.strip() for e in os.environ.get(
    "ALERT_RECIPIENTS", "linda@smartphoneaus-lebenan.de,jacob@smartphoneaus-lebenan.de"
).split(",") if e.strip()]


def send(subject, html, text):
    if not (MJ_KEY and MJ_SECRET):
        raise RuntimeError("MAILJET_API_KEY / MAILJET_SECRET fehlen.")
    if not RECIPIENTS:
        raise RuntimeError("Keine Empfaenger konfiguriert.")
    body = {"Messages": [{
        "From": {"Email": SENDER, "Name": "SALA Monitoring"},
        "To": [{"Email": e} for e in RECIPIENTS],
        "Subject": subject,
        "HTMLPart": html,
        "TextPart": text,
    }]}
    auth = base64.b64encode(f"{MJ_KEY}:{MJ_SECRET}".encode()).decode()
    req = urllib.request.Request(
        "https://api.mailjet.com/v3.1/send",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read())
    status = res.get("Messages", [{}])[0].get("Status")
    if status != "success":
        raise RuntimeError(f"Mailjet-Antwort: {json.dumps(res)[:500]}")
    return RECIPIENTS
