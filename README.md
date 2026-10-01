# SALA Monitoring

Automatische tägliche Überwachung der Umfrage-Beteiligung aller Schulen.
Läuft von allein auf GitHub-Servern – nichts muss von Hand ausgelöst werden.

**Was es tut (1× pro Tag):**
1. Holt die aktuellen Einreichungen aus Jotform (Start, W1, W2, W3, Abschluss).
2. Gleicht sie mit der Schulliste ab (Google Sheet, siehe unten).
3. Wendet die strikte Regel an: **jede fällige Umfrage muss über 85 % liegen** –
   sonst geht die Lampe an.
4. Schreibt die passwortgeschützte **Status-Seite** (Inhalt verschlüsselt).
5. Schickt die **Alarm-Mail** an Linda und Jacob.

Schlägt der Mailversand fehl, fällt der Lauf rot aus – dann schickt GitHub
zusätzlich eine Fehler-Benachrichtigung (zweites Sicherheitsnetz).

---

## Einrichtung (einmalig)

### 1. Repo anlegen
Neues **öffentliches** Repo auf dem eigenen GitHub-Account anlegen und den Inhalt
dieses Ordners hochladen (`git push` oder per Weboberfläche hochziehen).

> Öffentlich ist nötig, damit GitHub Pages kostenlos funktioniert. Die Status-Seite
> ist trotzdem geschützt: Der Inhalt ist mit dem Passwort **verschlüsselt** (AES-256)
> und liegt unter einer **nicht-erratbaren Adresse**. Ohne Passwort sieht man nichts.

### 2. Secrets hinterlegen
**Settings → Secrets and variables → Actions → New repository secret** – diese fünf anlegen:

| Name | Inhalt |
|------|--------|
| `JOTFORM_API_KEY` | der Jotform-API-Schlüssel (kommt separat) |
| `MAILJET_API_KEY` | API-Key aus dem Mailjet-Konto |
| `MAILJET_SECRET` | Secret-Key aus dem Mailjet-Konto |
| `DASHBOARD_PASSWORD` | frei wählbares Passwort für die Status-Seite (lang!) |
| `DASHBOARD_PATH` | der geheime Adress-Teil (kommt separat) |

Optional: `SHEET_CSV_URL`, falls die Schulliste mal umzieht.

### 3. GitHub Pages aktivieren
**Settings → Pages → Build and deployment → Source: „GitHub Actions"**.

### 4. Mailjet-Absender verifizieren
Im Mailjet-Konto den Absender `linda@smartphoneaus-lebenan.de` bestätigen
(Sender-/Domain-Verifizierung), sonst lehnt Mailjet den Versand ab.

### 5. Ersten Lauf starten
**Actions → „SALA Monitoring" → Run workflow**. Danach läuft es täglich um
05:00 UTC (06:00 Winter / 07:00 Sommer, Berlin) von allein.

Die endgültige Adresse der Status-Seite steht nach dem ersten Lauf im Button der
Alarm-Mail und im Deploy-Schritt der Action. Sie hat die Form:
`https://<benutzername>.github.io/<repo>/<DASHBOARD_PATH>/`

---

## Schulliste pflegen (laufend)

Die Zuordnung Schule → Klasse → Schüler-IDs liegt im Google Sheet, das als CSV
veröffentlicht ist. **Neue Schule/Klasse = eine neue Zeile eintragen**, fertig –
ab dem nächsten Lauf ist sie im Monitoring.

Spalten:

| Spalte | Bedeutung |
|--------|-----------|
| `Schule` | Schulname |
| `Klasse` | Klassenbezeichnung |
| `ID_von` / `ID_bis` | Schüler-ID-Bereich (4-stellig, z. B. 0291–0315) |
| `ID2_von` / `ID2_bis` | optionaler zweiter Bereich (falls IDs nicht am Stück) |
| `SuS` | Anzahl Schülerinnen und Schüler (Nenner für die %-Rechnung) |
| `Programmstart` | Startdatum `TT.MM.JJJJ` – steuert, welche Umfrage wann fällig ist |

Fehlt der `Programmstart` oder liegt er in der Zukunft, wird die Klasse als
„wartet" geführt und nicht als Alarm gezählt.

---

## Dateien

| Datei | Zweck |
|-------|-------|
| `monitor.py` | Rechenkern: Jotform + Sheet → 85-%-Regel |
| `render.py` | baut Alarm-Mail und Status-Seite |
| `crypto_pack.py` | verschlüsselt die Dashboard-Daten (passend zum Browser-Code) |
| `send.py` | Mailversand über Mailjet |
| `build.py` | Ablaufsteuerung (wird täglich ausgeführt) |
| `.github/workflows/monitor.yml` | der tägliche Zeitplan |
| `assets/` | Logo + Schrift (Manrope) |
