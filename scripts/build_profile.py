#!/usr/bin/env python3
"""Build local profile artwork. Pass --refresh to fetch public GitHub data."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "KnightFang36"
SNAPSHOT = ROOT / "data" / "profile.json"
ASSETS = ROOT / "assets"
PALETTES = {
    "dark": {
        "bg": "#101719", "surface": "#182224", "raised": "#1d2b2c",
        "line": "#344344", "grid": "#334142", "text": "#f0f1e9",
        "muted": "#a6b6b4", "accent": "#d5f786", "orange": "#ff906b",
        "teal": "#8adbd0", "shadow": "#080d0f",
    },
    "light": {
        "bg": "#f3f3eb", "surface": "#e9ece2", "raised": "#e0e7d9",
        "line": "#bdc8bc", "grid": "#c4cfc2", "text": "#1a302b",
        "muted": "#52665e", "accent": "#406b23", "orange": "#b74b28",
        "teal": "#1b716b", "shadow": "#b7c5b4",
    },
}
LANGUAGE_COLORS = {
    "Python": "#e7bd75", "TypeScript": "#86bdf5", "Go": "#85d8ca",
    "JavaScript": "#e3e789", "CSS": "#b5a4eb", "HTML": "#ec9c87",
    "Shell": "#b3cf96", "Other": "#a4b2b0",
}
LIGHT_LANGUAGE_COLORS = {
    "Python": "#92702d", "TypeScript": "#2c6cac", "Go": "#23796e",
    "JavaScript": "#777b1f", "CSS": "#7962af", "HTML": "#b35a43",
    "Shell": "#5b7c3a", "Other": "#657d77",
}


def text(x, y, value, size=16, *, fill, weight=400, mono=False, extra=""):
    family = "'SFMono-Regular',Consolas,'Liberation Mono',monospace" if mono else "Inter,'Segoe UI',Arial,sans-serif"
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" {extra}>{escape(value)}</text>')


def svg(width, height, title, description, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(title)}</title>\n'
            f'<desc id="desc">{escape(description)}</desc>\n{body}\n</svg>\n')


def stack_art(p, mobile=False):
    """Exploded interface/retrieval/protocol layers with traveling packets."""
    out = ['<g>']
    for index, (dy, color, label) in enumerate([
        (156, p["orange"], "03 / PROTOCOL"),
        (78, p["teal"], "02 / RETRIEVAL"),
        (0, p["accent"], "01 / INTERFACE"),
    ]):
        out.append(f'<g transform="translate(0 {dy})">')
        out.append(f'<path d="M30 125 205 35 380 125 205 215Z" fill="{p["surface"]}" stroke="{p["line"]}"/>')
        out.append(f'<path d="M30 125v13l175 90 175-90v-13l-175 90Z" fill="{p["raised"]}" stroke="{p["line"]}"/>')
        for i in range(1, 6):
            t = i / 6
            ax, ay = 30 + 175 * t, 125 - 90 * t
            bx, by = 205 + 175 * t, 215 - 90 * t
            out.append(f'<path d="M{ax:.1f} {ay:.1f} {bx:.1f} {by:.1f}" stroke="{p["grid"]}" stroke-width=".7" opacity=".55"/>')
            ax, ay = 205 + 175 * t, 35 + 90 * t
            bx, by = 30 + 175 * t, 125 + 90 * t
            out.append(f'<path d="M{ax:.1f} {ay:.1f} {bx:.1f} {by:.1f}" stroke="{p["grid"]}" stroke-width=".7" opacity=".55"/>')
        route = "M65 125 135 89 205 125 275 89 345 125 275 161 205 125 135 161 65 125"
        out.append(f'<path d="{route}" fill="none" stroke="{color}" stroke-width="1.7" opacity=".8"/>')
        out.append(f'<path class="packet packet-{index}" d="{route}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="14 650"/>')
        for x, y in [(65, 125), (135, 89), (275, 89), (345, 125), (275, 161), (135, 161)]:
            out.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{p["surface"]}" stroke="{color}" stroke-width="1.4"/>')
        out.append(f'<path d="M178 125 205 111 232 125 205 139Z" fill="{color}"/>')
        out.append(f'<path d="M178 125v7l27 14 27-14v-7l-27 14Z" fill="{color}" opacity=".45"/>')
        out.append('</g>')
    for dy, color, label in [(0, p["accent"], "01 / INTERFACE"),
                             (78, p["teal"], "02 / RETRIEVAL"),
                             (156, p["orange"], "03 / PROTOCOL")]:
        out.append(text(12, 129 + dy, label, 14 if mobile else 12, fill=color, mono=True,
                        extra='text-anchor="end" letter-spacing=".7"'))
        out.append(f'<path d="M18 {125+dy}H30" stroke="{color}"/>')
    for x, y in [(65, 125), (345, 125)]:
        out.append(f'<path d="M{x} {y}v156" stroke="{p["muted"]}" stroke-width="1" stroke-dasharray="3 6" opacity=".5"/>')
    out.append('</g>')
    return "\n".join(out)


def render_hero(theme, mobile=False):
    p = PALETTES[theme]
    width, height = (480, 600) if mobile else (1200, 460)
    out = [f'''<defs>
      <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
        <circle cx="1" cy="1" r=".8" fill="{p['grid']}"/>
      </pattern>
      <clipPath id="frame"><rect width="{width}" height="{height}" rx="16"/></clipPath>
    </defs>
    <style>
      .packet {{ animation: travel 9s linear infinite; }}
      .packet-1 {{ animation-delay: -3s; }}
      .packet-2 {{ animation-delay: -6s; }}
      @keyframes travel {{ to {{ stroke-dashoffset: -664; }} }}
      @media (prefers-reduced-motion: reduce) {{ .packet {{ animation: none; }} }}
    </style>
    <g clip-path="url(#frame)">
    <rect width="{width}" height="{height}" fill="{p['bg']}"/>
    <rect x="{0 if mobile else 690}" width="{width}" height="{height}" fill="url(#dots)" opacity=".65"/>
    <path d="M0 1H{width}" stroke="{p['accent']}" stroke-width="2"/>
    '''.rstrip()]
    margin = 34 if mobile else 46
    out.append(f'<rect x="{margin}" y="32" width="31" height="31" rx="7" fill="{p["accent"]}"/>')
    out.append(text(margin + 15.5, 53, "M", 18, fill=p["bg"], weight=800, extra='text-anchor="middle"'))
    out.append(text(margin + 44, 53, "KNIGHTFANG36", 13, fill=p["text"], mono=True, weight=600, extra='letter-spacing="2"'))
    if not mobile:
        out.append(text(1154, 53, "DEVELOPER / BUILDER / STUDENT", 11, fill=p["muted"], mono=True, extra='text-anchor="end" letter-spacing="1.3"'))
    out.append(text(margin, 123 if mobile else 132, "MANAS ROY", 60 if mobile else 75, fill=p["text"], weight=800, extra='letter-spacing="-3"'))
    out.append(text(margin + 2, 159 if mobile else 171, "Curious at every layer.", 25 if mobile else 28, fill=p["accent"], weight=500, extra='letter-spacing="-.5"'))
    if mobile:
        out.append(text(margin + 2, 205, "Full-stack development.", 19, fill=p["muted"]))
        out.append(text(margin + 2, 234, "AI that connects to real products.", 19, fill=p["muted"]))
        out.append(text(margin + 2, 263, "Systems worth understanding.", 19, fill=p["muted"]))
        out.append('<g transform="translate(106 280) scale(.65)">')
    else:
        out.append(text(margin + 2, 229, "Full-stack development. Applied AI.", 21, fill=p["muted"]))
        out.append(text(margin + 2, 261, "And the systems underneath.", 21, fill=p["muted"]))
        out.append(f'<path d="M48 306H582" stroke="{p["line"]}"/>')
        out.append(text(48, 335, "WEB", 12, fill=p["accent"], mono=True, extra='letter-spacing="2"'))
        out.append(text(127, 335, "/", 12, fill=p["muted"], mono=True))
        out.append(text(165, 335, "INTELLIGENCE", 12, fill=p["teal"], mono=True, extra='letter-spacing="2"'))
        out.append(text(323, 335, "/", 12, fill=p["muted"], mono=True))
        out.append(text(361, 335, "SYSTEMS", 12, fill=p["orange"], mono=True, extra='letter-spacing="2"'))
        out.append('<g transform="translate(739 38) scale(.94)">')
    out.append(stack_art(p, mobile))
    out.append('</g>')
    y = height - 23
    out.append(f'<path d="M{margin} {y-22}H{width-margin}" stroke="{p["line"]}"/>')
    out.append(text(margin, y, "B.TECH / IIIT KOTTAYAM", 11, fill=p["muted"], mono=True, extra='letter-spacing="1.3"'))
    out.append(text(width - margin, y, "BUILD. UNDERSTAND. REPEAT.", 10 if mobile else 11, fill=p["muted"], mono=True, extra='text-anchor="end" letter-spacing="1"'))
    out.append('</g>')
    return svg(width, height, "Manas Roy — curious at every layer",
               "Full-stack development, applied AI, and systems. B.Tech at IIIT Kottayam. "
               "An animated exploded circuit stack connects interface, retrieval, and protocol layers.", "\n".join(out))


def language_shares(repos):
    totals = Counter()
    for repo in repos:
        totals.update(repo["languages"])
    ordered = totals.most_common()
    if len(ordered) > 4:
        ordered = ordered[:4] + [("Other", sum(count for _, count in ordered[4:]))]
    return ordered


def display_date(value, fmt="%d %b %Y"):
    return date.fromisoformat(value[:10]).strftime(fmt).upper()


def render_signal(data, theme, mobile=False):
    p = PALETTES[theme]
    colors = LANGUAGE_COLORS if theme == "dark" else LIGHT_LANGUAGE_COLORS
    width, height = (480, 680) if mobile else (1200, 394)
    margin = 24 if mobile else 40
    repos = data["repositories"]
    shares = language_shares(repos)
    total_bytes = sum(n for _, n in shares)
    dated = sorted((r for r in repos if r.get("pushed_at")), key=lambda r: r["pushed_at"], reverse=True)
    out = [f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="14" fill="{p["bg"]}" stroke="{p["line"]}"/>']
    out.append(f'<circle cx="{margin+4}" cy="36" r="4" fill="{p["accent"]}"/>')
    out.append(text(margin + 19, 41, "REPOSITORY SIGNAL", 14 if mobile else 12, fill=p["accent"], mono=True, weight=600, extra='letter-spacing="2"'))
    out.append(text(width - margin, 41, display_date(data["updated_at"]), 14 if mobile else 11, fill=p["muted"], mono=True, extra='text-anchor="end"'))
    out.append(text(margin, 100, "The work, in code.", 32 if mobile else 34, fill=p["text"], weight=700, extra='letter-spacing="-1"'))
    out.append(text(margin, 132, f'{len(repos):02d} original public projects', 20 if mobile else 16, fill=p["muted"]))
    if not mobile:
        out.append(f'<path d="M620 76V322" stroke="{p["line"]}"/>')
    bar_y = 204 if mobile else 194
    out.append(text(margin, bar_y - 22, "SOURCE LANGUAGES / BY BYTES", 14 if mobile else 11, fill=p["muted"], mono=True, extra='letter-spacing="1"'))
    bar_width = width - 2 * margin if mobile else 534
    out.append(f'<defs><clipPath id="bar"><rect x="{margin}" y="{bar_y}" width="{bar_width}" height="13" rx="6"/></clipPath></defs>')
    if total_bytes:
        out.append('<g clip-path="url(#bar)">')
        offset = margin
        for language, count in shares:
            length = bar_width * count / total_bytes
            out.append(f'<rect x="{offset:.3f}" y="{bar_y}" width="{length:.3f}" height="13" fill="{colors.get(language, colors["Other"])}"/>')
            offset += length
        out.append('</g>')
        for index, (language, count) in enumerate(shares):
            x = margin + index % 2 * (bar_width / 2)
            y = bar_y + 47 + index // 2 * 31
            color = colors.get(language, colors["Other"])
            out.append(f'<circle cx="{x+4}" cy="{y-5}" r="4" fill="{color}"/>')
            out.append(text(x + 18, y, language, 18 if mobile else 14, fill=p["text"]))
            out.append(text(x + bar_width / 2 - 25, y, f'{100*count/total_bytes:.1f}%', 16 if mobile else 13, fill=p["muted"], mono=True, extra='text-anchor="end"'))
    else:
        out.append(text(margin, bar_y + 48, "No source-language data yet.", 15, fill=p["muted"]))
    rx, ry = (margin, 392) if mobile else (664, 103)
    if mobile:
        out.append(f'<path d="M{margin} 351H{width-margin}" stroke="{p["line"]}"/>')
    out.append(text(rx, ry, "LATEST REPOSITORY PUSHES", 14 if mobile else 11, fill=p["muted"], mono=True, extra='letter-spacing="1"'))
    for index, repo in enumerate(dated[:3]):
        y = ry + 44 + index * 70
        name = repo["name"] if len(repo["name"]) <= 20 else repo["name"][:19] + "…"
        out.append(text(rx, y, name, 24 if mobile else 20, fill=p["text"], weight=600))
        out.append(text(width - margin, y - 2, display_date(repo["pushed_at"], "%d %b %y"), 14 if mobile else 11, fill=p["muted"], mono=True, extra='text-anchor="end"'))
        out.append(text(rx, y + 22, repo.get("language") or "Unclassified", 16 if mobile else 12, fill=p["teal"], mono=True))
        if index < min(len(dated), 3) - 1:
            out.append(f'<path d="M{rx} {y+34}H{width-margin}" stroke="{p["line"]}" opacity=".6"/>')
    foot_y = height - (45 if mobile else 31)
    out.append(f'<path d="M{margin} {foot_y-23}H{width-margin}" stroke="{p["line"]}"/>')
    if mobile:
        out.append(text(margin, foot_y, "GITHUB REST API / ORIGINAL PUBLIC SOURCES", 12, fill=p["muted"], mono=True))
        out.append(text(margin, foot_y + 20, "Original repositories only. Dated snapshot.", 12, fill=p["muted"]))
    else:
        out.append(text(margin, foot_y, "GITHUB REST API / ORIGINAL PUBLIC SOURCES", 10, fill=p["muted"], mono=True, extra='letter-spacing=".7"'))
        out.append(text(width - margin, foot_y, "FORKS + PROFILE EXCLUDED / DATED SNAPSHOT", 10, fill=p["muted"], mono=True, extra='text-anchor="end" letter-spacing=".5"'))
    summary = ", ".join(f"{name} {100*count/total_bytes:.1f}%" for name, count in shares) if total_bytes else "No source-language data."
    return svg(width, height, "Repository signal — public project snapshot",
               f'Updated {data["updated_at"]}. {len(repos)} original public projects. '
               f'Source-language bytes: {summary}. Forks and the profile repository are excluded. '
               'Repository pushes are not deployment activity or individual commit authorship.', "\n".join(out))


def github_get(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"{USERNAME}-profile",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_snapshot():
    repositories = []
    page = 1
    while True:
        query = urlencode({"per_page": 100, "page": page, "sort": "pushed", "type": "owner"})
        batch = github_get(f"/users/{USERNAME}/repos?{query}")
        if not isinstance(batch, list):
            raise ValueError("GitHub did not return a repository list")
        for repo in batch:
            if (repo["fork"] or repo.get("private") or repo["archived"] or repo.get("disabled")
                    or repo["name"].lower() == USERNAME.lower() or not repo["size"]):
                continue
            language_data = github_get(f'/repos/{USERNAME}/{repo["name"]}/languages')
            repositories.append({
                "name": repo["name"], "url": repo["html_url"],
                "language": repo["language"], "languages": language_data,
                "pushed_at": repo["pushed_at"],
            })
        if len(batch) < 100:
            break
        page += 1
    return {"username": USERNAME, "updated_at": datetime.now(timezone.utc).date().isoformat(),
            "source": "https://api.github.com", "repositories": repositories}


def validate_snapshot(data):
    if data.get("username") != USERNAME:
        raise ValueError("Snapshot username does not match the profile")
    date.fromisoformat(data["updated_at"])
    repos = data["repositories"]
    if not isinstance(repos, list):
        raise ValueError("Snapshot repositories must be a list")
    seen = set()
    for repo in repos:
        name = repo["name"]
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name.lower() == USERNAME.lower()
                or name.lower() in seen):
            raise ValueError("Invalid or duplicate project name")
        seen.add(name.lower())
        if not isinstance(repo.get("languages"), dict):
            raise ValueError("Missing source-language data")
        if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in repo["languages"].values()):
            raise ValueError("Language byte counts must be non-negative integers")
        if repo.get("pushed_at"):
            datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))


def build(data):
    validate_snapshot(data)
    files = {}
    for theme in PALETTES:
        for mobile in (False, True):
            suffix = f'{"mobile-" if mobile else ""}{theme}.svg'
            files[ASSETS / f"hero-{suffix}"] = render_hero(theme, mobile)
            files[ASSETS / f"signal-{suffix}"] = render_signal(data, theme, mobile)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Fetch public GitHub data before building")
    parser.add_argument("--check", action="store_true", help="Check that artwork is reproducible")
    args = parser.parse_args()
    if args.check and args.refresh:
        parser.error("--check and --refresh are separate operations")
    try:
        data = fetch_snapshot() if args.refresh else json.loads(SNAPSHOT.read_text())
        files = build(data)
        if args.check:
            stale = [str(p.relative_to(ROOT)) for p, content in files.items() if not p.is_file() or p.read_text() != content]
            if stale:
                print("Artwork needs rebuilding:\n" + "\n".join(stale), file=sys.stderr)
                return 1
            print(f"All {len(files)} SVG assets match the snapshot.")
            return 0
        ASSETS.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        if args.refresh:
            SNAPSHOT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        for path, content in files.items():
            path.write_text(content)
        print(f'Built {len(files)} assets from {data["updated_at"]}: {len(data["repositories"])} public projects.')
        return 0
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Profile build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
