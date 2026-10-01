# -*- coding: utf-8 -*-
"""
Orchestrator – wird taeglich von GitHub Actions ausgefuehrt.

Ablauf:
  1. Status berechnen (monitor.compute)
  2. Verschluesseltes Dashboard nach ./site/ schreiben (immer – das ist die Status-Seite)
  3. Alarm-Mail ueber Mailjet verschicken
  4. E-Mail-Status an GitHub melden (schlaegt der Versand fehl, faellt der Lauf am
     Ende rot aus -> GitHub schickt eine Fehler-Benachrichtigung = zweites Sicherheitsnetz)

Das Dashboard wird IMMER geschrieben, auch wenn der Mailversand scheitert.
"""
import os, sys, json, html as _html
import monitor, render, send
from crypto_pack import encrypt_payload


def _dash_url():
    """Dashboard-Adresse aus GitHub-Umgebung ableiten: user.github.io/repo/<pfad>/."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")           # "owner/repo"
    path = os.environ.get("DASHBOARD_PATH", "").strip().strip("/")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        base = f"https://{owner.lower()}.github.io/{name}"
    else:
        base = os.environ.get("PAGES_BASE", "https://example.github.io/sala-status").rstrip("/")
    return f"{base}/{path}/" if path else f"{base}/", path


def _gh_output(key, val):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"{key}={val}\n")


def _text_fallback(data, today, url):
    flag = [d for d in data if d["amp"] in ("gelb", "rot")]
    lines = [f"SALA Status {today.strftime('%d.%m.%Y')}",
             f"{len(flag)} Klassen unter 85% (Schwelle je faelliger Umfrage).",
             f"Status-Seite: {url}", ""]
    for d in flag:
        waves = ", ".join(f"{n} {p}%" for n, p in d["due"])
        lines.append(f"- {d['schule']} · {d['klasse']} (Woche {d['woche']}): {waves}")
    return "\n".join(lines)


def main():
    pw = os.environ.get("DASHBOARD_PASSWORD", "").strip()
    if not pw:
        print("::error::DASHBOARD_PASSWORD fehlt.", flush=True)
        sys.exit(1)

    # 1) Berechnen
    data, today = monitor.compute()
    from collections import Counter
    c = Counter(d["amp"] for d in data)
    print(f"Stand {today}: gruen {c['gruen']} | gelb {c['gelb']} | rot {c['rot']} "
          f"| wartet {c['wartet']} | gesamt {len(data)}", flush=True)

    url, _path = _dash_url()

    # 2) Dashboard IMMER schreiben
    payload = {"datum": today.strftime("%d.%m.%Y"),
               "data": [{"schule": d["schule"], "klasse": d["klasse"], "woche": d["woche"],
                         "due": d["due"], "amp": d["amp"]} for d in data]}
    enc = encrypt_payload(payload, pw)
    page = render.dashboard_html(enc, today.isoformat())

    os.makedirs("site", exist_ok=True)
    target = os.path.join("site", _path) if _path else "site"
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    # schlichte Tarn-Startseite an der Wurzel (gibt den echten Pfad nicht preis)
    with open(os.path.join("site", "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><meta charset="utf-8"><title>·</title>'
                '<body style="font-family:sans-serif;color:#999;text-align:center;'
                'margin-top:20vh">Nichts zu sehen.</body>')
    with open(os.path.join("site", ".nojekyll"), "w") as f:
        f.write("")
    print(f"Dashboard geschrieben -> {url}", flush=True)

    # 3) Mail verschicken
    email_ok = False
    try:
        subject, mail = render.email_html(data, today, url)
        text = _text_fallback(data, today, url)
        to = send.send(subject, mail, text)
        print(f"Mail verschickt an: {', '.join(to)}", flush=True)
        email_ok = True
    except Exception as e:  # noqa: BLE001
        print(f"::error::Mailversand fehlgeschlagen: {_html.escape(str(e))}", flush=True)

    # 4) Status melden (Workflow faellt am Ende rot aus, wenn die Mail scheiterte)
    _gh_output("email_ok", "true" if email_ok else "false")
    _gh_output("dashboard_url", url)


if __name__ == "__main__":
    main()
