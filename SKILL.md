---
name: academic-literature-search
description: 面向学术文献检索的 Agent Skill：先判断研究主题是否需要澄清，再进行多源检索、元数据核验、公开免费全文解析、Excel 导出和用户确认后的受控下载；适用于论文、学位论文、会议论文、技术报告和预印本。
metadata:
  short-description: 多源检索、公开免费全文解析与本地去重下载
---

# Academic Literature Search

当用户要求“帮我找某方向的论文”“系统搜集国内外文献”“查找近年文献并整理 Excel”“寻找合法获取入口”或在确认后下载公开全文时使用本 Skill。

## 交互边界

先解析研究对象、研究问题、关键词、方法、材料、时间范围、语言、文献类型、排除条件和目标数量。不要强制用户一次填写全部字段。

- 主题过于宽泛或存在多个明显不同的子方向时，先提出具体澄清问题，停止正式检索；例如“核燃料”应询问材料、芯块、包壳、燃料棒/组件、热工水力、辐照行为等侧重点。
- 主题已足够明确时直接规划检索，不重复追问。
- 生成有限的中英文关键词、同义词、缩写/全称和查询组合，始终保持主题相关，不无限扩展。

## 检索与证据

程序入口位于 `src/literature_finder/`。通用来源包括 Crossref、OpenAlex、Semantic Scholar、arXiv、Europe PMC、DOAJ、Zenodo 和 HAL。核工程主题路由增加 OSTI、NRC ADAMS、IAEA INIS、OECD-NEA 和 INL Advanced Fuels Campaign；学位论文主题路由增加 OATD、theses.fr 和 CORE。NRC ADAMS/INIS 继续只生成官方检索入口；OECD-NEA 和 INL 是 robots.txt 感知的官方页面适配器，解析失败时降级为 landing page。OATD 接口不可用时不伪造论文记录。

单个 Provider 失败、超时、限流或缺少 API Key 时必须记录并继续其他 Provider。DOI、标题、日期、来源、摘要和全文地址只能来自真实返回结果或官方页面；不得猜测 DOI、拼接未经验证的下载 URL，最终记录至少保留一个可验证来源。

`LiteratureRecord` 统一维护来源 ID、规范化 DOI/标题、开放获取状态、最佳合法入口、PDF URL、相关性评分、下载状态、本地路径和 SHA256。元数据去重依次使用规范化 DOI、规范化标题、标题+作者+年份和严格模糊匹配；模糊匹配必须同时满足高相似度、作者一致和年份差不超过 1 年。

相关性排序使用可解释的词项覆盖、摘要、年份、引用和开放获取信号；默认过滤低于 45 分的候选，不能为了达到数量目标而保留明显无关文献。

## 公开免费全文与获取链接策略

默认采用“公开免费优先、尽可能完整获取”的策略。不要因为域名不在固定白名单、上游 OA 标记缺失或链接不是以 `.pdf` 结尾，就提前禁用一个来源提供的公开下载入口。优先顺序为：

1. 来源明确提供的公开 PDF 或其他可验证全文文件；
2. 出版商公开页面上的正常全文下载入口；
3. OpenAlex OA location、Unpaywall `best_oa_location`；
4. OSTI、HAL、CORE、NRC、INIS、机构知识库、作者公开稿和 arXiv 等合法公开版本；
5. 只有 DOI、出版商或数据库详情页时，保留稳定 landing page，但不把它误标为可下载全文。

“只要能下载”指普通公开 HTTP 访问能够取得真实、可读的全文文件；不是指绕过访问控制后强行下载。下载器会在保存前检查 HTTP 状态、Content-Type、PDF 文件头和解析结果。公开页面返回登录页、付费墙、验证码、Cloudflare/反爬拦截或其他 HTML 错误页时，必须停止该条下载并保留最佳合法入口。不得自动登录、导入 Cookie、绕过 CAPTCHA、构造隐藏下载地址或使用盗版/影子数据库。

`download_permission_verified` 表示检索阶段已经发现了来源提供的公开下载候选；最终是否可保存仍由下载阶段的响应和 PDF 校验决定。这样既不会过度限制免费网站，也不会把“HTTP 可连接”误认为“已合法获取”。

公开下载候选按以下顺序优先：机构仓储/预印本（HAL、arXiv、PMC、Zenodo 等）→ 开放学位论文库（OATD、theses.fr）→ OA 期刊来源（DOAJ、Europe PMC）→ 官方报告来源（OSTI、OECD-NEA、INL）→ 出版商公开 PDF。候选来源全部保存在 `record.raw["download_candidates"]`，首选失败时必须尝试下一候选。

## 两阶段下载流程

检索始终先完成 Excel 和内部 JSON 记录，再等待用户明确选择。即使用户一开始说“把能下载的都下载下来”，也不得跳过确认。

1. `search` 阶段：澄清 → QueryPlanner → 多源检索 → 元数据统一/去重/排序 → 公开全文解析 → Excel 导出。
2. `download` 阶段：处理检索阶段发现的公开免费全文候选（`download_permission_verified == True`）；若记录只有 DOI，先通过 Unpaywall 和 OpenAlex 做 OA 二次探测，再按候选链回退；可按全部、序号/范围、文献类型、相关性阈值和年份筛选。

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
literature-search download literature_output/literature_search_YYYYMMDD_HHMMSS.xlsx --resume
```

旧调用方式 `literature-search "主题"` 自动按 `search` 处理。程序化调用可使用 `parse_request`、`build_plan`、`run_search`、`write_excel`、`DownloadManager`、`LocalLibraryChecker` 和 `LiteratureManifest`。

## 合法性要求

本 Skill 会尽可能发现和下载普通公开网页、开放获取版本、机构仓储、作者公开稿、官方报告、公开学位论文和预印本中的全文，但不会把“免费网站”理解为可以突破访问控制。禁止 Sci-Hub、LibGen、盗版数据库、影子文献库、付费墙/登录/机构认证/CAPTCHA/反爬绕过、泄露 Cookie/token、代理轮换或伪造认证。环境变量和 `.env` 中的密钥不得提交或写入日志。公开可访问也不自动意味着可以任意再分发；用户应遵守来源网站条款和适用版权许可。
