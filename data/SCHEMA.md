# Digest JSON Schema（data/digests/YYYY-MM-DD.json）

每期日报对应一个 JSON 文件，文件名为发布日期。结构如下：

```json
{
  "meta": {
    "title": "AI合同审查日报",
    "date": "2026-08-18",
    "demo": false,
    "generator": "QoderWork cron 自动生成"
  },
  "insight": "今日洞见，120字以内，概括当天主线与对法务团队的含义。",
  "sections": [
    {
      "id": "tools",
      "name": "A · 工具动态",
      "items": [
        {
          "rank": 1,
          "title": "中文标题",
          "summary": "一句话摘要，50字以内",
          "legal_tip": "法务启示，1-2句（可选，无则省略该字段）",
          "score": 4,
          "tags": ["标签1", "标签2"],
          "source": "信源名称",
          "url": "https://真实链接（必须来自本次检索结果，禁止编造）",
          "published": "2026-08-17"
        }
      ]
    }
  ],
  "sources_hit": ["本期命中的信源名称列表"]
}
```

## 字段约定

| 字段 | 必填 | 说明 |
|---|---|---|
| meta.title | 是 | 站点标题，固定"AI合同审查日报" |
| meta.date | 是 | 发布日期 YYYY-MM-DD（北京时间） |
| meta.demo | 是 | 正式日报固定 false |
| meta.generator | 否 | 生成方式说明，显示在页脚 |
| insight | 是 | 今日洞见；当天无高价值信息时写"今日无高价值信息" |
| sections[].id | 是 | 固定四个：tools / methods / opensource / regulation |
| sections[].name | 是 | 对应：A · 工具动态 / B · 前沿方法 / C · 开源与Prompt / D · 监管与案例 |
| items[].rank | 是 | 全局连续序号，从 1 开始 |
| items[].score | 是 | 整数 1-5，仅收录 ≥3 的条目 |
| items[].url | 是 | 真实可访问链接，红线：禁止编造 |
| items[].published | 否 | 信息发布日期，未知可省略 |

## 空刊处理

当天无高价值信息时，仍生成文件：sections 各栏目 items 为空数组，insight 写"今日无高价值信息"。这样归档页时间线保持连续。
