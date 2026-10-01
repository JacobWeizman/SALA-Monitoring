# -*- coding: utf-8 -*-
"""Rendering: Alarm-E-Mail (mail-sicheres HTML) und Status-Dashboard."""
import os, json, base64

HERE = os.path.dirname(os.path.abspath(__file__))

# --- Marke -------------------------------------------------------------------
SIG, GOLD, INK, SLATE, MUT = "#E86217", "#F0B646", "#3A465C", "#455577", "#77839C"
SOFT, PAGE = "#FAF3EA", "#F6F4F0"
GREEN, YELLOW, RED, GREY = "#2E9E5B", "#C98A1A", "#CC3A2F", "#9AA3B2"
GRAD = f"linear-gradient(120deg,{SIG} 0%,{GOLD} 100%)"
DOT = {"gruen": GREEN, "gelb": YELLOW, "rot": RED, "wartet": GREY}


def _b64(path):
    with open(os.path.join(HERE, path), "rb") as f:
        return base64.b64encode(f.read()).decode()


def _logo(white=True):
    return "data:image/png;base64," + _b64(f"assets/logo-{'weiss' if white else 'dunkel'}.png")


# ============================================================================
#  E-MAIL  (mail-sicheres HTML: Tabellen, Inline-Styles, Arial)
# ============================================================================
def email_html(data, today, dash_url):
    gruen = [d for d in data if d["amp"] == "gruen"]
    gelb = [d for d in data if d["amp"] == "gelb"]
    rot = [d for d in data if d["amp"] == "rot"]
    flag = [d for d in data if d["amp"] in ("gelb", "rot")]
    datum = today.strftime("%d.%m.%Y")

    # Schul-Rollup
    schools = {}
    for d in data:
        if d["amp"] == "wartet":
            continue
        s = schools.setdefault(d["schule"], {"g": 0, "y": 0, "r": 0, "n": 0})
        s["n"] += 1
        s["g" if d["amp"] == "gruen" else ("y" if d["amp"] == "gelb" else "r")] += 1

    def worst(s):
        return "rot" if s["r"] else ("gelb" if s["y"] else "gruen")

    over = ""
    for name, s in sorted(schools.items(), key=lambda kv: (-kv[1]["r"], -kv[1]["y"], kv[0])):
        tot = s["n"]
        wp = round(s["r"] / tot * 100)
        yp = round(s["y"] / tot * 100)
        gp = 100 - wp - yp
        seg = lambda w, c: (f'<td width="{w}%" style="background:{c};font-size:0;line-height:6px;'
                            f'height:6px;">&nbsp;</td>' if w > 0 else "")
        bar = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
               f'style="border-radius:4px;overflow:hidden;"><tr>'
               f'{seg(gp, GREEN)}{seg(yp, YELLOW)}{seg(wp, RED)}</tr></table>')
        cnt = "".join(f'<span style="color:{c};font-weight:bold;margin-left:9px;">{n}</span>'
                      for c, n in [(GREEN, s["g"]), (YELLOW, s["y"]), (RED, s["r"])] if n)
        over += f'''<tr>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;font-size:13px;vertical-align:middle;"><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{DOT[worst(s)]};margin-right:7px;"></span><b style="color:{INK};">{name}</b></td>
      <td width="42%" style="padding:9px 8px;border-bottom:1px solid #eee;vertical-align:middle;">{bar}</td>
      <td style="padding:9px 8px;border-bottom:1px solid #eee;font-size:12px;text-align:right;vertical-align:middle;white-space:nowrap;">{cnt}<span style="color:{MUT};margin-left:9px;">/ {tot}</span></td></tr>'''

    def wave_cell(n, p):
        col = RED if p < 70 else (YELLOW if p < 85 else GREEN)
        strong = "font-weight:bold;" if p < 85 else ""
        return f'<span style="display:inline-block;margin-right:10px;color:{col};{strong}">{n} {p}%</span>'

    rows = ""
    for d in flag:
        waves = "".join(wave_cell(n, p) for n, p in d["due"])
        rows += f'''<tr>
      <td style="padding:7px 8px;border-bottom:1px solid #eee;font-size:13px;"><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{DOT[d['amp']]};margin-right:7px;"></span><b style="color:{INK};">{d['schule']}</b> · {d['klasse']}</td>
      <td style="padding:7px 8px;border-bottom:1px solid #eee;font-size:12px;color:{MUT};white-space:nowrap;">Woche {d['woche']}</td>
      <td style="padding:7px 8px;border-bottom:1px solid #eee;font-size:12px;">{waves}</td></tr>'''

    def box(col, num, lab):
        return (f'<td align="center" style="padding:10px;background:{SOFT};border-radius:10px;">'
                f'<div style="font-size:26px;font-weight:bold;color:{col};">{num}</div>'
                f'<div style="font-size:11px;color:{SLATE};">{lab}</div></td>')

    def label(t):
        return (f'<tr><td style="padding:16px 24px 8px;"><div style="font-size:12px;font-weight:bold;'
                f'letter-spacing:1.5px;text-transform:uppercase;color:{SIG};">{t}</div></td></tr>')

    alarm = len(flag) > 0
    subject = (f"{'🔴' if alarm else '✅'} SALA Status {datum} · "
               + (f"{len(flag)} Klassen unter 85%" if alarm else "alle Umfragen über 85%"))

    detail_block = (label(f"Detailansicht · {len(flag)} Klassen unter 85%") +
                    f'<tr><td style="padding:0 24px 18px;"><table role="presentation" width="100%" '
                    f'cellpadding="0" cellspacing="0">{rows}</table></td></tr>') if flag else (
        f'<tr><td style="padding:20px 24px;"><div style="background:{SOFT};border-radius:10px;'
        f'padding:18px;text-align:center;color:{GREEN};font-weight:bold;">Alle fälligen Umfragen '
        f'liegen über 85 %. Keine Klasse im Handlungsbedarf.</div></td></tr>')

    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:{PAGE};font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE};"><tr><td align="center" style="padding:18px 10px;">
<table role="presentation" width="720" cellpadding="0" cellspacing="0" style="max-width:720px;background:#fff;border-radius:14px;overflow:hidden;">
<tr><td style="background:{SIG};background:{GRAD};padding:20px 24px;">
  <img src="{_logo()}" width="150" style="display:block;border:0;margin-bottom:8px;">
  <div style="color:#fff;font-size:18px;font-weight:bold;">Täglicher Status · Umfrage-Beteiligung</div>
  <div style="color:#fff;opacity:.9;font-size:12px;margin-top:3px;">Stand {datum} · Schwelle 85 % je fälliger Umfrage</div></td></tr>
<tr><td style="padding:18px 24px 2px;">
  <table role="presentation" width="100%"><tr>{box(GREEN, len(gruen), 'grün (≥85%)')}<td width="10"></td>{box(YELLOW, len(gelb), 'gelb (70–84%)')}<td width="10"></td>{box(RED, len(rot), 'rot (&lt;70%)')}</tr></table></td></tr>
{label('Auf einen Blick · nach Schule')}
<tr><td style="padding:0 24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{over}</table></td></tr>
<tr><td align="center" style="padding:20px 24px 6px;">
  <a href="{dash_url}" style="display:inline-block;background:{SIG};background:{GRAD};color:#fff;text-decoration:none;font-weight:bold;font-size:14px;padding:13px 30px;border-radius:9px;">Status-Seite öffnen →</a>
  <div style="font-size:11px;color:{MUT};margin-top:7px;">passwortgeschützt · täglich automatisch aktualisiert</div></td></tr>
{detail_block}
<tr><td style="background:{SIG};background:{GRAD};padding:13px 24px;color:#fff;font-size:11px;">Smartphone aus – Leben an · automatischer Tagesreport · Zuordnung pflegst du in der Schulliste (Google Sheet)</td></tr>
</table></td></tr></table></body></html>'''
    return subject, html


# ============================================================================
#  DASHBOARD  (verschluesselter Inhalt, clientseitige Entschluesselung)
# ============================================================================
def dashboard_html(enc, datum_iso):
    """enc = dict(salt, iv, ct, iter) aus crypto.encrypt_payload()."""
    font = lambda n, w: (f"@font-face{{font-family:'Manrope';font-weight:{w};font-style:normal;"
                         f"font-display:swap;src:url(data:font/ttf;base64,{_b64('assets/' + n)}) format('truetype');}}")
    fonts = font("Manrope-Regular.ttf", 400) + font("Manrope-SemiBold.ttf", 600) + font("Manrope-Bold.ttf", 700)
    logo = _logo()                 # weiss – fuer den Verlaufs-Header
    logo_dark = _logo(white=False)  # dunkel – fuer das weisse Gate
    enc_js = json.dumps(enc)

    return f'''<!DOCTYPE html><html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>SALA Status</title>
<style>
{fonts}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Manrope',system-ui,sans-serif;background:{PAGE};color:{INK};-webkit-font-smoothing:antialiased;padding:18px 12px}}
.wrap{{max-width:860px;margin:0 auto}}
.card{{background:#fff;border-radius:16px;overflow:hidden;border:1px solid #ECE6DC}}
.head{{background:{GRAD};padding:24px 28px;color:#fff}}
.head img{{width:150px;display:block;margin-bottom:10px}}
.head h1{{font-size:20px;font-weight:700}}
.head .sub{{font-size:12px;opacity:.92;margin-top:4px}}
.pad{{padding:22px 28px}}
.counts{{display:flex;gap:12px;margin-bottom:6px}}
.count{{flex:1;background:{SOFT};border-radius:12px;padding:14px;text-align:center}}
.count .n{{font-size:30px;font-weight:700;line-height:1}}
.count .l{{font-size:11px;color:{SLATE};margin-top:5px}}
.ey{{font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{SIG};margin:22px 0 10px}}
.srow{{display:flex;align-items:center;gap:12px;padding:10px 4px;border-bottom:1px solid #eee;font-size:14px}}
.srow .nm{{flex:1;font-weight:600}}
.bar{{flex:0 0 38%;height:7px;border-radius:4px;overflow:hidden;display:flex;background:#eee}}
.cnt{{flex:0 0 auto;font-size:13px;white-space:nowrap;text-align:right;min-width:92px}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;vertical-align:middle}}
table.detail{{width:100%;border-collapse:collapse;font-size:13px}}
table.detail td{{padding:8px 6px;border-bottom:1px solid #eee;vertical-align:middle}}
table.detail .wk{{color:{MUT};font-size:12px;white-space:nowrap}}
.w{{display:inline-block;margin-right:11px}}
.foot{{background:{GRAD};color:#fff;font-size:11px;padding:14px 28px}}
#gate{{max-width:420px;margin:12vh auto;text-align:center}}
#gate .card{{padding:34px 30px}}
#gate img{{width:140px;margin:0 auto 18px;display:block}}
#gate h2{{font-size:17px;margin-bottom:6px}}
#gate p{{font-size:13px;color:{SLATE};margin-bottom:18px}}
#pw{{width:100%;padding:13px 14px;border:1.5px solid #E0D8CC;border-radius:10px;font-size:15px;font-family:inherit}}
#pw:focus{{outline:none;border-color:{SIG}}}
#go{{width:100%;margin-top:12px;padding:13px;border:0;border-radius:10px;background:{GRAD};color:#fff;font-weight:700;font-size:15px;cursor:pointer;font-family:inherit}}
#err{{color:{RED};font-size:13px;margin-top:12px;min-height:18px;font-weight:600}}
.hidden{{display:none}}
</style></head>
<body>
<div id="gate">
  <div class="card">
    <img src="{logo_dark}" alt="">
    <h2>SALA Status</h2>
    <p>Bitte Passwort eingeben.</p>
    <input id="pw" type="password" autocomplete="current-password" placeholder="Passwort" autofocus>
    <button id="go">Öffnen</button>
    <div id="err"></div>
  </div>
</div>

<div id="app" class="hidden"><div class="wrap"><div class="card">
  <div class="head"><img src="{logo}" alt="">
    <h1>Täglicher Status · Umfrage-Beteiligung</h1>
    <div class="sub">Stand <span id="stand"></span> · Schwelle 85 % je fälliger Umfrage</div></div>
  <div class="pad" id="body"></div>
  <div class="foot">Smartphone aus – Leben an · automatischer Tagesreport · Zuordnung in der Schulliste (Google Sheet)</div>
</div></div></div>

<script>
const ENC = {enc_js};
const C = {{gruen:"{GREEN}",gelb:"{YELLOW}",rot:"{RED}",wartet:"{GREY}"}};
const b2u = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

async function decrypt(pw){{
  const km = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    {{name:"PBKDF2", salt:b2u(ENC.salt), iterations:ENC.iter, hash:"SHA-256"}},
    km, {{name:"AES-GCM", length:256}}, false, ["decrypt"]);
  const pt = await crypto.subtle.decrypt({{name:"AES-GCM", iv:b2u(ENC.iv)}}, key, b2u(ENC.ct));
  return JSON.parse(new TextDecoder().decode(pt));
}}

const esc = s => String(s).replace(/[&<>]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));

function render(p){{
  document.getElementById("stand").textContent = p.datum;
  const data = p.data;
  const g = data.filter(d=>d.amp==="gruen"), y = data.filter(d=>d.amp==="gelb"),
        r = data.filter(d=>d.amp==="rot"), flag = data.filter(d=>d.amp==="gelb"||d.amp==="rot");

  // Schul-Rollup
  const sc = {{}};
  data.forEach(d=>{{ if(d.amp==="wartet") return;
    const s = sc[d.schule] || (sc[d.schule]={{g:0,y:0,r:0,n:0}});
    s.n++; s[d.amp==="gruen"?"g":(d.amp==="gelb"?"y":"r")]++; }});
  const worst = s => s.r?"rot":(s.y?"gelb":"gruen");
  const schools = Object.entries(sc).sort((a,b)=> b[1].r-a[1].r || b[1].y-a[1].y || a[0].localeCompare(b[0]));

  let over = "";
  for(const [nm,s] of schools){{
    const tot=s.n, wp=Math.round(s.r/tot*100), yp=Math.round(s.y/tot*100), gp=100-wp-yp;
    const seg=(w,c)=> w>0?`<span style="width:${{w}}%;background:${{c}}"></span>`:"";
    const cnt=[["g",C.gruen],["y",C.gelb],["r",C.rot]].map(([k,c])=>s[k]?`<b style="color:${{c}};margin-left:9px">${{s[k]}}</b>`:"").join("");
    over+=`<div class="srow"><span class="nm"><span class="dot" style="background:${{C[worst(s)]}}"></span>${{esc(nm)}}</span>
      <span class="bar">${{seg(gp,C.gruen)}}${{seg(yp,C.gelb)}}${{seg(wp,C.rot)}}</span>
      <span class="cnt">${{cnt}}<span style="color:{MUT};margin-left:9px">/ ${{tot}}</span></span></div>`;
  }}

  const wave=(n,pct)=>{{const col=pct<70?C.rot:(pct<85?C.gelb:C.gruen);return `<span class="w" style="color:${{col}};${{pct<85?'font-weight:700':''}}">${{n}} ${{pct}}%</span>`;}};
  let rows="";
  for(const d of flag){{
    rows+=`<tr><td><span class="dot" style="background:${{C[d.amp]}}"></span><b>${{esc(d.schule)}}</b> · ${{esc(d.klasse)}}</td>
      <td class="wk">Woche ${{d.woche}}</td><td>${{d.due.map(w=>wave(w[0],w[1])).join("")}}</td></tr>`;
  }}

  const detail = flag.length
    ? `<div class="ey">Detailansicht · ${{flag.length}} Klassen unter 85%</div><table class="detail">${{rows}}</table>`
    : `<div style="background:{SOFT};border-radius:10px;padding:18px;text-align:center;color:{GREEN};font-weight:700">Alle fälligen Umfragen liegen über 85 %.</div>`;

  document.getElementById("body").innerHTML = `
    <div class="counts">
      <div class="count"><div class="n" style="color:{GREEN}">${{g.length}}</div><div class="l">grün (≥85%)</div></div>
      <div class="count"><div class="n" style="color:{YELLOW}">${{y.length}}</div><div class="l">gelb (70–84%)</div></div>
      <div class="count"><div class="n" style="color:{RED}">${{r.length}}</div><div class="l">rot (&lt;70%)</div></div>
    </div>
    <div class="ey">Auf einen Blick · nach Schule</div>${{over}}
    ${{detail}}`;
  document.getElementById("gate").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
}}

async function tryOpen(){{
  const pw = document.getElementById("pw").value;
  const err = document.getElementById("err");
  if(!pw) return;
  err.textContent = "…";
  try{{ const p = await decrypt(pw); sessionStorage.setItem("sala_pw", pw); render(p); }}
  catch(e){{ err.textContent = "Falsches Passwort."; }}
}}
document.getElementById("go").addEventListener("click", tryOpen);
document.getElementById("pw").addEventListener("keydown", e => {{ if(e.key==="Enter") tryOpen(); }});
// bequemes Wiederoeffnen innerhalb der Browser-Sitzung
(async()=>{{ const s=sessionStorage.getItem("sala_pw"); if(s){{ try{{ render(await decrypt(s)); }}catch(e){{}} }} }})();
</script>
</body></html>'''
