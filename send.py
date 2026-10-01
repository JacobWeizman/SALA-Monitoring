# -*- coding: utf-8 -*-
"""Versand der Alarm-Mail ueber das eigene Postfach (SMTP).

Vorkonfiguriert fuer Google Workspace (smtp.gmail.com, STARTTLS auf Port 587).
Als Passwort wird ein Google-App-Passwort verwendet (nicht das normale
Konto-Passwort) – siehe README.
"""
import os, ssl, smtplib
from email.message import EmailMessage

HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
PORT = int(os.environ.get("SMTP_PORT", "587"))
SENDER = os.environ.get("ALERT_SENDER", "linda@smartphoneaus-lebenan.de").strip()
USER = os.environ.get("SMTP_USER", "").strip() or SENDER
PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip()
RECIPIENTS = [e.strip() for e in os.environ.get(
    "ALERT_RECIPIENTS", "linda@smartphoneaus-lebenan.de,jacob@smartphoneaus-lebenan.de"
).split(",") if e.strip()]


def send(subject, html, text):
    if not PASSWORD:
        raise RuntimeError("SMTP_PASSWORD fehlt (Google-App-Passwort).")
    if not RECIPIENTS:
        raise RuntimeError("Keine Empfaenger konfiguriert.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECIPIENTS)
    msg.set_content(text)                       # Text-Fallback
    msg.add_alternative(html, subtype="html")   # HTML-Variante

    ctx = ssl.create_default_context()
    if PORT == 465:
        with smtplib.SMTP_SSL(HOST, PORT, context=ctx, timeout=60) as s:
            s.login(USER, PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP(HOST, PORT, timeout=60) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(USER, PASSWORD)
            s.send_message(msg)
    return RECIPIENTS
