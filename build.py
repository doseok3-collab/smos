"""Build the SMOS lab site.

Produces:
  index.html            -> GitHub Pages version (relative asset paths)
  preview.html          -> artifact preview (no doctype; images inlined)
Edit content in content.py / pubs.json, then run:  python3 build.py
"""
import base64, html, json, re, pathlib

ROOT = pathlib.Path(__file__).parent
pubs = json.load(open(ROOT / "pubs.json"))
from content import RESEARCH, MEMBERS, ALUMNI, NEWS

E = html.escape


def bold_pi(authors):
    out = []
    for a in authors:
        s = E(a)
        if re.fullmatch(r"(Doseok Kim|Kim Doseok|D\. Kim)", a):
            s = f"<b>{s}</b>"
        out.append(s)
    if len(out) > 12:
        out = out[:10] + ["…"] + out[-1:]
    return ", ".join(out)


def pub_html():
    years = sorted({p["year"] for p in pubs}, reverse=True)
    rows = []
    for y in years:
        items = [p for p in pubs if p["year"] == y]
        lis = []
        for p in items:
            ref = E(p["journal"])
            if p["volume"]:
                ref += f" <span class=vol>{E(str(p['volume']))}</span>"
            if p["page"]:
                ref += f", {E(str(p['page']))}"
            doi = p["doi"].replace("https://doi.org/", "")
            search = E((p["title"] + " " + " ".join(p["authors"]) + " " + p["journal"]).lower())
            lis.append(
                f'<li data-s="{search}"><span class=ptitle>{E(p["title"])}</span>'
                f'<span class=pauth>{bold_pi(p["authors"])}</span>'
                f'<span class=pref><i>{ref}</i> ({y}) · <a href="{E(p["doi"])}" target="_blank" rel="noopener">doi:{E(doi)}</a></span></li>'
            )
        rows.append(
            f'<section class=pyear data-year="{y}"><h3>{y}</h3><ol>{"".join(lis)}</ol></section>'
        )
    return "\n".join(rows), len(pubs), years[-1]


def research_html():
    out = []
    for r in RESEARCH:
        tags = "".join(f"<li>{E(t)}</li>" for t in r["tags"])
        out.append(
            f'<article class=topic><p class=band>{E(r["band"])}</p><h3>{E(r["title"])}</h3>'
            f'<p>{E(r["text"])}</p><ul class=tags>{tags}</ul></article>'
        )
    return "\n".join(out)


def members_html():
    groups = []
    for g, people in MEMBERS:
        cards = "".join(
            f'<li><span class=mname>{E(n)}</span><span class=mrole>{E(d)}</span></li>' for n, d in people
        )
        groups.append(f"<div class=mgroup><h3>{E(g)}</h3><ul class=mlist>{cards}</ul></div>")
    al = "".join(
        f"<tr><td class=aname>{E(n)}</td><td>{E(deg)}</td><td>{E(topic)}</td><td>{E(now)}</td></tr>"
        for n, deg, topic, now in ALUMNI
    )
    return "\n".join(groups), al


def news_html():
    return "".join(f"<li><time>{E(d)}</time><p>{E(t)}</p></li>" for d, t in NEWS)


def spectrum_svg():
    """Illustrative |chi(2)|^2 SFG spectrum, CH + OH region, drawn to scale."""
    import cmath, math
    modes = [(2855, 1.0, 9), (2875, 1.3, 7), (2920, -0.6, 10), (2935, 0.9, 8), (2960, -1.1, 9),
             (3200, 45, 120), (3420, 26, 130)]
    W, H, x0, x1, padL, padR, padT, padB = 640, 220, 2800, 3700, 20, 20, 30, 40
    def X(w): return padL + (w - x0) / (x1 - x0) * (W - padL - padR)
    pts = []
    vals = []
    for i in range(361):
        w = x0 + (x1 - x0) * i / 360
        chi = 0.15 + sum(a / (w - w0 + 1j * g) for w0, a, g in modes)
        vals.append((w, abs(chi) ** 2))
    m = max(v for _, v in vals)
    for w, v in vals:
        y = H - padB - v / m * (H - padT - padB)
        pts.append(f"{X(w):.1f},{y:.1f}")
    path = "M" + " L".join(pts)
    area = path + f" L{X(x1):.1f},{H-padB} L{X(x0):.1f},{H-padB} Z"
    ticks = "".join(
        f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{H-padB}" y2="{H-padB+5}" class=ax />'
        f'<text x="{X(t):.1f}" y="{H-padB+20}" class=tk text-anchor=middle>{t}</text>'
        for t in range(2800, 3701, 200))
    labels = [(2900, "CH stretch"), (3200, "OH 3200"), (3420, "OH 3400")]
    lab = "".join(
        f'<line x1="{X(w):.1f}" x2="{X(w):.1f}" y1="{padT-6}" y2="{H-padB}" class=guide />'
        f'<text x="{X(w)+4:.1f}" y="{padT-10}" class=lb>{E(t)}</text>' for w, t in labels)
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Illustrative sum-frequency spectrum, 2800 to 3700 inverse centimeters">'
            f'{lab}<path d="{area}" class=area /><path d="{path}" class=curve />'
            f'<line x1="{padL}" x2="{W-padR}" y1="{H-padB}" y2="{H-padB}" class=ax />{ticks}'
            f'<text x="{W-padR}" y="{H-4}" class=tk text-anchor=end>IR wavenumber (cm⁻¹)</text></svg>')


def build(preview=False):
    tpl = (ROOT / "template.html").read_text()
    plist, npubs, firsty = pub_html()
    mem, alumni = members_html()
    rep = {
        "{{PUBS}}": plist, "{{NPUBS}}": str(npubs), "{{FIRSTY}}": str(firsty),
        "{{RESEARCH}}": research_html(), "{{MEMBERS}}": mem, "{{ALUMNI}}": alumni,
        "{{NEWS}}": news_html(), "{{SPECTRUM}}": spectrum_svg(),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    if preview:
        for f in sorted(ROOT.glob("*.png")) + sorted(ROOT.glob("*.jpg")):
            mime = "image/png" if f.suffix == ".png" else "image/jpeg"
            uri = f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
            tpl = tpl.replace(f'"{f.name}"', f'"{uri}"')
        tpl = tpl.replace('href="archive/index.html"', 'href="https://web.archive.org/web/2019/http://smos.sogang.ac.kr/wiki/index.php/Main_Page"')
        tpl = re.sub(r"<!doctype html>\s*<html[^>]*>\s*<head>|</head>\s*<body>|</body>\s*</html>", "", tpl, flags=re.I)
        tpl = re.sub(r'<meta charset[^>]*>\s*|<meta name="viewport"[^>]*>\s*', "", tpl)
    return tpl


(ROOT / "index.html").write_text(build())
(ROOT / "preview.html").write_text(build(preview=True))
print("built", len(pubs), "publications")
