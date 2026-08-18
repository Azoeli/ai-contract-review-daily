# AI合同审查日报 · 网站

参考 [ai-frontier](https://pupujanet-eng.github.io/ai-frontier/) 模式搭建的每日 AI 资讯简报站点：定时采集 → LLM 加工 → 静态站 → GitHub Pages 自动发布。

## 架构

```
信源(sources.md) → 采集 → LLM加工(JSON) → build_site.py → GitHub Pages
                              ↑
                  两种模式二选一（见下）
```

## 目录结构

```
.github/workflows/pages.yml              推送即部署（必需）
.github/workflows/daily-github-actions.yml  GitHub 侧全自动生成（可选）
data/digests/YYYY-MM-DD.json             每期日报数据（唯一数据源）
data/SCHEMA.md                           JSON 结构约定
scripts/build_site.py                    JSON -> 静态站（仅标准库）
scripts/daily_pipeline.py                可选：GitHub Actions 模式的采集+LLM管线
templates/page.html                      页面模板（分区/搜索/键盘导航）
site/                                    构建产物（CI 生成，无需手工维护）
```

## 两种运行模式（二选一）

### 模式 A：QoderWork cron 生成（当前默认）

本机的 QoderWork 定时任务「AI合同审查日报」每天 08:30 生成日报，除了写入钉钉文档/邮件外，同时把结构化 JSON 写入 `data/digests/` 并 push。推送后由 `pages.yml` 自动构建部署。优点：复用已有采集与评分流程，不额外消耗 API 额度。

### 模式 B：GitHub Actions 全自动（复刻 ai-frontier）

启用 `.github/workflows/daily-github-actions.yml`：仓库 Secrets 配置 `ANTHROPIC_API_KEY`，取消 schedule 注释，按需修改 `scripts/daily_pipeline.py` 的信源。优点：不依赖本机开机。

## 首次发布步骤

1. 在 GitHub 创建仓库（如 `ai-contract-review-daily`）
2. `git remote add origin <仓库地址>` 并推送 main 分支
3. 仓库 Settings → Pages → Source 选择 **GitHub Actions**
4. 推送后等待 Actions 完成，站点地址为 `https://<用户名>.github.io/<仓库名>/`

## 本地预览

```bash
python3 scripts/build_site.py
open site/index.html
```
