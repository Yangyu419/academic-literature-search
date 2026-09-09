---
name: academic-literature-search
description: 面向学术文献检索的 Agent Skill：先判断研究主题是否需要澄清，再进行多源检索、元数据核验、合法全文解析、Excel 导出和用户确认后的受控下载；适用于论文、学位论文、会议论文、技术报告和预印本。
metadata:
  short-description: 多源检索、合法全文解析与本地去重下载
---

# Academic Literature Search

当用户要求“帮我找某方向的论文”“系统搜集国内外文献”“查找近年文献并整理 Excel”“寻找合法获取入口”或在确认后下载公开全文时使用本 Skill。

## 交互边界

先解析研究对象、研究问题、关键词、方法、材料、时间范围、语言、文献类型、排除条件和目标数量。不要强制用户一次填写全部字段。

- 主题过于宽泛或存在多个明显不同的子方向时，先提出具体澄清问题，停止正式检索；例如“核燃料”应询问材料、芯块、包壳、燃料棒/组件、热工水力、辐照行为等侧重点。
- 主题已足够明确时直接规划检索，不重复追问。
- 生成有限的中英文关键词、同义词、缩写/全称和查询组合，始终保持主题相关，不无限扩展。

## 检索与证据

程序入口位于 `src/literature_finder/`。基础来源包括 Crossref、OpenAlex、Semantic Scholar 和 arXiv；按主题路由可启用 OSTI、HAL 和 CORE。核工程主题还提供 OSTI、NRC ADAMS、IAEA INIS、HAL-CEA 的专业入口，其中 NRC ADAMS/INIS 在没有稳定可用 API 时只生成合法检索入口，不伪造 API 或抓取受限页面。

单个 Provider 失败、超时、限流或缺少 API Key 时必须记录并继续其他 Provider。DOI、标题、日期、来源、摘要和全文地址只能来自真实返回结果或官方页面；不得猜测 DOI、拼接未经验证的下载 URL，最终记录至少保留一个可验证来源。

`LiteratureRecord` 统一维护来源 ID、规范化 DOI/标题、开放获取状态、最佳合法入口、PDF URL、相关性评分、下载状态、本地路径和 SHA256。元数据去重依次使用规范化 DOI、规范化标题、标题+作者+年份和严格模糊匹配；模糊匹配必须同时满足高相似度、作者一致和年份差不超过 1 年。

相关性排序使用可解释的词项覆盖、摘要、年份、引用和开放获取信号；默认过滤低于 45 分的候选，不能为了达到数量目标而保留明显无关文献。

合法全文解析优先顺序：原始来源明确 OA PDF、出版商 OA、OpenAlex OA location、Unpaywall `best_oa_location`、OSTI/HAL/CORE 等机构仓储、arXiv 或作者/机构 repository；只有合法 landing page 时保留入口，不把它当成可下载 PDF。

## 两阶段下载流程

检索始终先完成 Excel 和内部 JSON 记录，再等待用户明确选择。即使用户一开始说“把能下载的都下载下来”，也不得跳过确认。

1. `search` 阶段：澄清 → QueryPlanner → 多源检索 → 元数据统一/去重/排序 → 合法全文解析 → Excel 导出。
2. `download` 阶段：只处理 `download_permission_verified == True` 的记录；可按全部、序号/范围、文献类型、相关性阈值和年份筛选。

下载器使用 `DownloadManager`；旧的 `SafeDownloader` 名称仍可用。真正发送 HTTP 请求前，必须先运行 `LocalLibraryChecker.refresh()` 扫描目标目录并加载 `literature_manifest.json`，再按以下顺序查重：

1. 规范化 DOI 精确匹配；
2. OpenAlex、OSTI、arXiv、HAL、CORE、NRC 等 Provider 唯一 ID 匹配；
3. 规范化标题，并结合第一作者和年份；
4. `>= 0.95` 的标题相似度、第一作者一致、年份差不超过 1 年；
5. 生成目标文件名后检查现有有效 PDF。

命中本地文献时必须设置 `download_status = skipped_existing`、`existing_local_copy = True` 和已有路径，并且不得调用 HTTP 下载函数。只有显式传入 `--force-redownload` 时才允许忽略本地存在检查；默认不覆盖、不删除、不生成 `(1)` 副本。

下载写入 `.download_tmp/*.part`，然后执行 HTTP 状态、Content-Type、`%PDF-` 文件头、文件大小和 PDF parser 校验。通过后计算 SHA256；若与本地 PDF 相同，删除临时文件并设置 `skipped_duplicate`，不保留第二份。唯一文件才原子移动到 `pdf/` 并更新 manifest、JSON、Excel 和 `download_report.csv`。HTML、登录页、403、验证码页、Cloudflare 或其他错误响应不得保存为 PDF。

## 运行入口

```bash
literature-search search "M5 cladding high burnup corrosion" --target 50 --output-dir literature_output
literature-search download literature_output/literature_search_YYYYMMDD_HHMMSS.xlsx --selection "1,3,8-12"
literature-search download literature_output/literature_search_YYYYMMDD_HHMMSS.xlsx --type "博士论文,期刊论文"
literature-search download literature_output/literature_search_YYYYMMDD_HHMMSS.xlsx --threshold 80 --force-redownload
```

旧调用方式 `literature-search "主题"` 自动按 `search` 处理。程序化调用可使用 `parse_request`、`build_plan`、`run_search`、`write_excel`、`DownloadManager`、`LocalLibraryChecker` 和 `LiteratureManifest`。

## 合法性要求

只使用公开 API、公开学术页面、开放获取版本、机构仓储、官方报告和明确允许公开下载的资源。禁止 Sci-Hub、盗版数据库、付费墙/登录/机构认证/CAPTCHA/反爬绕过、泄露 Cookie/token、代理轮换或伪造认证。环境变量和 `.env` 中的密钥不得提交或写入日志。
