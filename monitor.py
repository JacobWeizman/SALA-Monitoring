# -*- coding: utf-8 -*-
"""
SALA-Monitoring – Rechenkern.

Holt pro Umfrage die eingegangenen teilnehmerIDs aus Jotform, liest die
Schulliste (Google Sheet, als CSV veroeffentlicht) und wendet die strikte
85-%-Regel an: jede faellige Umfrage muss ueber 85 % Beteiligung liegen,
sonst geht die Lampe an.

Konfiguration ueber Umgebungsvariablen (in GitHub als Secrets hinterlegt):
  JOTFORM_API_KEY   – Jotform-API-Schluessel (EU)
  SHEET_CSV_URL     – veroeffentlichte CSV-URL der Schulliste (optional,
                      Fallback = unten eingetragene URL)
"""
import os, io, csv, json, urllib.request, datetime

# --- Konfiguration -----------------------------------------------------------
API_KEY = os.environ.get("JOTFORM_API_KEY", "").strip()
SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL", "").strip() or (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRyqyCuL5dQiu0enQq1xt05ZQCStVBrNyis9Ys7Q__W0dShyUWO_8zQ7IdV43uWdkCVPD2L5RHFeMUP"
    "/pub?gid=1850223523&single=true&output=csv"
)

# Umfragen in Reihenfolge: (Name, Jotform-Form-ID, faellig-ab-Woche)
WAVES = [
    ("Start",     "260902004947050", 0),
    ("W1",        "260893714295063", 1),
    ("W2",        "260894061921055", 2),
    ("W3",        "260892241253051", 3),
    ("Abschluss", "260893696843071", 4),
]

THRESH = 85          # strikte Schwelle in Prozent
GELB_AB = 70         # ab hier gelb statt rot


def _load_ids(form_id):
    """Alle eingegangenen teilnehmerIDs (control_hidden) einer Umfrage – paginiert."""
    got, offset = set(), 0
    while True:
        url = (f"https://eu-api.jotform.com/form/{form_id}/submissions"
               f"?apiKey={API_KEY}&limit=1000&offset={offset}")
        data = json.loads(urllib.request.urlopen(url, timeout=90).read())
        chunk = data.get("content", [])
        for sub in chunk:
            tid = next((a.get("answer", "").strip()
                        for a in sub.get("answers", {}).values()
                        if a.get("type") == "control_hidden"), "")
            if tid:
                got.add(tid)
        if len(chunk) < 1000:
            break
        offset += 1000
    return got


def _ids_of_row(row):
    """4-stellige, fuehrend-genullte IDs aus ID_von/ID_bis (+ optional ID2_*)."""
    out = set()
    pairs = [(row.get("ID_von", ""), row.get("ID_bis", "")),
             (row.get("ID2_von", ""), row.get("ID2_bis", ""))]
    for a, b in pairs:
        a, b = str(a).strip(), str(b).strip()
        if a and b:
            for i in range(int(a), int(b) + 1):
                out.add(f"{i:04d}")
    return out


def compute(today=None):
    """Liefert (zeilen, today). Jede Zeile ist ein dict pro Klasse."""
    if today is None:
        today = datetime.date.today()
    sets = {name: _load_ids(fid) for name, fid, _ in WAVES}

    raw = urllib.request.urlopen(SHEET_CSV_URL, timeout=30).read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(raw)))

    out = []
    for r in rows:
        schule = (r.get("Schule") or "").strip()
        klasse = (r.get("Klasse") or "").strip()
        if not schule:
            continue
        try:
            sus = int(r["SuS"])
            start = datetime.datetime.strptime(r["Programmstart"].strip(), "%d.%m.%Y").date()
        except (KeyError, ValueError):
            # Zeile ohne gueltiges Startdatum / SuS -> als "wartet" markieren
            out.append(dict(schule=schule, klasse=klasse, sus=0, woche=0,
                            due=[], worst=100, amp="wartet", bad=[], status="Startdatum fehlt"))
            continue

        ids = _ids_of_row(r)
        days = (today - start).days

        if days < 0:
            # Programm startet erst in der Zukunft -> noch nichts faellig
            out.append(dict(schule=schule, klasse=klasse, sus=sus, woche=0,
                            due=[], worst=100, amp="wartet",
                            bad=[], status=f"startet {start.strftime('%d.%m.%Y')}"))
            continue

        wk = days // 7
        due = [(name, round(len(ids & sets[name]) / sus * 100) if sus else 0)
               for name, _, w in WAVES if wk >= w]
        worst = min((p for _, p in due), default=100)
        amp = "gruen" if worst >= THRESH else ("gelb" if worst >= GELB_AB else "rot")
        out.append(dict(schule=schule, klasse=klasse, sus=sus, woche=min(wk, 4),
                        due=due, worst=worst, amp=amp,
                        bad=[(n, p) for n, p in due if p < THRESH], status=""))

    # schlechteste zuerst; "wartet" (worst=100) landet hinten
    out.sort(key=lambda x: (0 if x["amp"] != "wartet" else 1, x["worst"], x["schule"], x["klasse"]))
    return out, today


if __name__ == "__main__":
    data, today = compute()
    from collections import Counter
    c = Counter(d["amp"] for d in data)
    print(f"Stand {today}: gruen {c['gruen']} | gelb {c['gelb']} | rot {c['rot']} "
          f"| wartet {c['wartet']} | gesamt {len(data)}")
