#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site.py — 将 data/digests/*.json 渲染为纯静态站点（输出到 site/）。

用法:
    python3 scripts/build_site.py [--root <repo_root>]

规则:
- 最新的日报 -> site/index.html
- 每期日报   -> site/digest-YYYY-MM-DD.html
- 历史列表   -> site/archive.html
- 仅依赖 Python 标准库（3.8+）。
"""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

PLACEHOLDER_DATA = "__DATA__"
PLACEHOLDER_TITLE = "__TITLE__"
PLACEHOLDER_DATE = "__DATE__"

ARCHIVE_HEAD = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 历史归档</title>
<style>
 body{{background:#0b0e14;color:#d7dce6;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Segoe UI",Arial,sans-serif;line-height:1.6}}
 .wrap{{max-width:760px;margin:0 auto;padding:40px 20px}}
 h1{{font-size:22px;border-bottom:1px solid #232a3b;padding-bottom:14px}}
 a.back{{color:#22d3ee;text-decoration:none;font-size:13px}}
 ul{{list-style:none;margin-top:20px}}
 li{{border:1px solid #232a3b;border-radius:10px;margin-bottom:10px;background:#11151f}}
 li a{{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;color:#d7dce6;text-decoration:none}}
 li a:hover{{color:#22d3ee}}
 .cnt{{color:#8b93a7;font-size:12px;font-family:ui-monospace,Menlo,monospace}}
 .foot{{margin-top:30px;color:#8b93a7;font-size:12px;font-family:ui-monospace,Menlo,monospace}}
</style></head><body><div class="wrap">
<a class="back" href="index.html">&larr; 返回最新一期</a>
<h1>{title} · 历史归档</h1>
<ul>
"""
ARCHIVE_ROW = '<li><a href="{href}"><span>{date} · {headline}</span><span class="cnt">{n} 条</span></a></li>\n'
ARCHIVE_TAIL = """</ul>
<div class="foot">由 build_site.py 自动生成 · {built}</div>
</div></body></html>
"""


def load_digests(data_dir: Path):
    digests = []
    for f in sorted(data_dir.glob("*.json")):
        if f.name == "SCHEMA.md":
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as e:
            print(f"[WARN] skip invalid digest {f.name}: {e}", file=sys.stderr)
            continue
        if "meta" not in d or "sections" not in d:
            print(f"[WARN] skip {f.name}: missing meta/sections", file=sys.stderr)
            continue
        digests.append(d)
    digests.sort(key=lambda d: d["meta"].get("date", ""), reverse=True)
    return digests


def render_page(template: str, digest: dict) -> str:
    html = template.replace(PLACEHOLDER_DATA, json.dumps(digest, ensure_ascii=False))
    html = html.replace(PLACEHOLDER_TITLE, digest["meta"].get("title", "AI日报"))
    html = html.replace(PLACEHOLDER_DATE, digest["meta"].get("date", ""))
    return html


def headline_of(digest: dict) -> str:
    ins = (digest.get("insight") or "").strip()
    if ins:
        return ins[:40] + ("…" if len(ins) > 40 else "")
    for sec in digest.get("sections", []):
        for it in sec.get("items", []):
            return it.get("title", "")[:40]
    return "日报"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    data_dir = root / "data" / "digests"
    site_dir = root / "site"
    template_path = root / "templates" / "page.html"

    if not template_path.exists():
        sys.exit(f"template not found: {template_path}")
    if not data_dir.exists():
        sys.exit(f"data dir not found: {data_dir}")

    template = template_path.read_text(encoding="utf-8")
    digests = load_digests(data_dir)
    if not digests:
        sys.exit("no valid digests found in data/digests/")

    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True)

    title = digests[0]["meta"].get("title", "AI日报")

    # individual pages
    for d in digests:
        date = d["meta"].get("date", "unknown")
        fname = "index.html" if d is digests[0] else f"digest-{date}.html"
        (site_dir / fname).write_text(render_page(template, d), encoding="utf-8")

    # archive page
    rows = []
    for d in digests:
        date = d["meta"].get("date", "unknown")
        n = sum(len(s.get("items", [])) for s in d.get("sections", []))
        href = "index.html" if d is digests[0] else f"digest-{date}.html"
        rows.append(ARCHIVE_ROW.format(href=href, date=date, headline=headline_of(d), n=n))
    archive = ARCHIVE_HEAD.format(title=title) + "".join(rows) + ARCHIVE_TAIL.format(
        built=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    (site_dir / "archive.html").write_text(archive, encoding="utf-8")

    print(f"[OK] built {len(digests)} digest(s) -> {site_dir}")
    print(f"[OK] latest: {digests[0]['meta'].get('date')} ({site_dir/'index.html'})")


if __name__ == "__main__":
    main()
