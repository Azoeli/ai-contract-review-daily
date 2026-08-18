#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_pipeline.py — 可选：GitHub Actions 全自动模式（复刻 ai-frontier）

流程: 抓 RSS 信源 -> Claude API 翻译/分类/评分 -> data/digests/YYYY-MM-DD.json
依赖: pip install feedparser anthropic
环境变量: ANTHROPIC_API_KEY

本脚本只是最小可用骨架：信源、栏目划分与评分标准请按需修改。
如果日报由 QoderWork cron 在本机生成，则无需本脚本。
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import anthropic
    import feedparser
except ImportError:
    sys.exit("missing deps: pip install feedparser anthropic")

# ---------------- 配置区 ----------------
SITE_TITLE = "AI合同审查日报"
HOURS_BACK = 48  # 采集窗口（小时）

# 信源列表：按需增删。与 ~/Desktop/AI合同审查日报/sources.md 保持同源最佳。
RSS_SOURCES = {
    "Artificial Lawyer": "https://www.artificiallawyer.com/feed/",
    "LawNext": "https://www.lawnext.com/feed",
    "Anthropic News": "https://www.anthropic.com/rss.xml",
    "OpenAI News": "https://openai.com/news/rss.xml",
    "arXiv cs.CL": "https://rss.arxiv.org/rss/cs.CL",
}

SECTIONS = ["A · 工具动态", "B · 前沿方法", "C · 开源与Prompt", "D · 监管与案例"]

SYSTEM_PROMPT = """你是法律科技情报分析师。用户给你一批过去48小时抓取的原始条目（标题+摘要+来源+链接），请生成一份中文日报JSON。
规则：
1. 仅保留与 AI 合同审查/法律科技直接相关或方法论可迁移的条目，总量 5-12 条。
2. 分入四个栏目：%s。
3. 每条输出字段：rank(全局序号)、title(中文标题)、summary(一句话摘要50字内)、legal_tip(对合同审查工作的法务启示1-2句)、score(1-5整数：5=改变行业格局、4=头部产品重大发布或顶会论文、3=常规更新与实用资产，低于3的丢弃)、tags(1-3个)、source(信源名)、url(必须原样使用输入中的链接，禁止编造)、published(YYYY-MM-DD，未知则省略)。
4. 另写一段 insight（今日洞见，120字内，概括当天主线与对法务团队的含义）。
5. 严格输出如下 JSON，不要任何额外文字：
{"insight":"...","sections":[{"id":"tools|methods|opensource|regulation","name":"栏目名","items":[...]}],"sources_hit":["命中信源名"]}""" % "、".join(SECTIONS)


def collect():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
    raw = []
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[WARN] fetch fail {name}: {e}", file=sys.stderr)
            continue
        for e in feed.entries[:15]:
            published = None
            ts = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if ts:
                published = datetime.fromtimestamp(time.mktime(ts), timezone.utc)
                if published < cutoff:
                    continue
            raw.append({
                "source": name,
                "title": e.get("title", "").strip(),
                "summary": (e.get("summary") or "").strip()[:500],
                "url": e.get("link", ""),
                "published": published.strftime("%Y-%m-%d") if published else None,
            })
    return raw


def generate(raw_items):
    client = anthropic.Anthropic()
    user_msg = "原始条目（JSON）：\n" + json.dumps(raw_items, ensure_ascii=False)
    resp = client.messages.create(
        model=os.environ.get("DIGEST_MODEL", "claude-sonnet-4-5"),
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    # 容错：剥离可能的 ```json 包裹
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def main():
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    out = Path("data/digests") / f"{today}.json"
    if out.exists():
        print(f"[OK] {out} already exists, skip")
        return

    raw = collect()
    print(f"[INFO] collected {len(raw)} raw items from {len(RSS_SOURCES)} sources")
    if len(raw) < 3:
        sys.exit("[WARN] too few items collected, abort to avoid low-quality digest")

    digest = generate(raw)
    digest["meta"] = {
        "title": SITE_TITLE,
        "date": today,
        "demo": False,
        "generator": "GitHub Actions + Claude API 自动生成",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out}")


if __name__ == "__main__":
    main()
