# Academic Literature Search

一个可作为 Agent Skill 使用、也可独立安装的 Python 学术文献检索工具。它在现有“研究主题澄清 → 多源检索 → Excel 汇总 → 用户确认后下载”流程上，增加了专业 Provider、合法全文解析、本地文献查重、manifest、临时文件、PDF 校验、SHA256 二次去重和结构化归档。

## 能做什么

- 对宽泛主题先提问，对明确主题直接检索。
- 通过 QueryPlanner 做有限的中英文关键词、同义词和缩写扩展。
- 聚合 Crossref、OpenAlex、Semantic Scholar、arXiv，以及按主题启用的 OSTI、HAL、CORE。
- 对核工程主题提供 OSTI、NRC ADAMS、IAEA INIS、HAL-CEA 入口；NRC ADAMS 和 INIS 在没有稳定公开 API 时采用 link-only，不虚构接口。
- 使用 DOI、标题、作者、年份、来源 ID 和严格模糊标题规则去重。
- 选择最佳合法获取入口；landing page 与实际 PDF 下载 URL 分开保存。
- 只有用户明确执行第二阶段下载时才下载，并且只下载已验证的合法公开 PDF。
- 下载前扫描目标文件夹，优先 DOI 精确查重；手动放入的 PDF 也会尝试读取 DOI、标题、作者和年份。
- 下载后执行 PDF 文件头、Content-Type、大小、parser 和 SHA256 校验。
- 输出 Excel、内部记录 JSON、`literature_manifest.json`、`download_report.csv` 和 `pdf/` 归档目录。

## 安装

要求 Python 3.11+。

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

开发测试依赖：

```bash
python -m pip install pytest
python -m pytest
```

运行时依赖为 `requests`、`openpyxl` 和 `pypdf`。

## 使用

### 第一阶段：检索并导出

```bash
literature-search search "2020-2026 M5 cladding high burnup corrosion" --target 50 --output-dir literature_output
```

也兼容旧调用：

```bash
literature-search "AI finite element surrogate model" --target 30
```

宽泛主题会先停止并提示澄清：

```bash
literature-search "核燃料"
```

此时不会启动多源检索，也不会下载文件。检索阶段输出 Excel 和 `metadata/records_时间戳.json`，并在 Excel 旁保留内部记录，供第二阶段使用。

### 第二阶段：用户确认后下载

下载全部已确认合法公开的全文：

```bash
literature-search download literature_output/literature_search_YYYYMMDD_HHMMSS.xlsx
```

按序号/范围下载：

```bash
literature-search download literature_output/literature_search_YYYYMMDD_HHMMSS.xlsx --selection "1,3,8-12"
```

按类型、相关性或年份筛选：

```bash
literature-search download results.xlsx --type "博士论文,期刊论文"
literature-search download results.xlsx --threshold 80 --start-year 2020 --end-year 2026
```

强制重新下载不是默认行为，只有显式传入以下参数才会忽略本地存在检查：

```bash
literature-search download results.xlsx --force-redownload
```

## 本地文献查重

每次下载任务开始时，`LocalLibraryChecker` 会先扫描目标目录中的所有 PDF，并加载或更新 `literature_manifest.json`。扫描不依赖文件名，优先级如下：

1. 规范化 DOI 精确匹配；
2. Provider 唯一 ID（OpenAlex、OSTI、arXiv、HAL、CORE、NRC 等）匹配；
3. 标准化标题 + 第一作者 + 年份；
4. 标题相似度至少 0.95，且第一作者一致、年份差不超过 1 年；
5. 生成目标文件名后检查有效 PDF。

如果命中本地文献，记录会标记为 `skipped_existing`，写入已有路径和匹配原因，且在调用 HTTP 客户端之前直接跳过。核心验收条件由测试明确断言：`mock_http_get.assert_not_called()`。

手动放入的 PDF 没有 manifest 记录时，扫描器会读取 PDF 前两页文本和 metadata，尝试提取 DOI、标题、第一作者和年份，并将识别结果补入 manifest。没有 DOI 的文献只有在严格标题/作者/年份规则成立时才自动判重；作者不同的相似标题不会被自动视为重复。

下载完成后还会计算 SHA256。如果新临时文件与已有 PDF 内容相同，则删除临时文件并标记 `skipped_duplicate`，不会保留第二份。

## 输出结构

```text
literature_output/
├── literature_search_YYYYMMDD_HHMMSS.xlsx
├── metadata/
│   ├── records_YYYYMMDD_HHMMSS.json
│   └── records.json
├── literature_manifest.json
├── download_report.csv
├── pdf/
├── logs/
├── failed/
└── .download_tmp/
```

Excel 工作表名为 `Literature`。原有 8 列仍保留在前部：

```text
序号 | 文献类型 | 文献名 | 中文名 | 文献发表日期 | 期刊/来源 | 研究内容 | 备注
```

后续增加：相关性评分、作者、年份、出版商、DOI、摘要、关键词、OA 状态、最佳合法获取链接、PDF 链接、全文来源、检索数据库、下载状态、本地存在状态、本地路径、重复判断方式、是否重复和 SHA256。表头加粗、冻结首行、自动筛选；DOI 为文本；合法链接和 PDF 链接可点击。

状态包括：`pending`、`downloading`、`downloaded`、`skipped_existing`、`skipped_duplicate`、`unavailable`、`failed`、`invalid_pdf`、`corrupt`。

## API Key 与配置

复制 `.env.example` 为 `.env`，或通过环境变量配置：

```text
CORE_API_KEY=
UNPAYWALL_EMAIL=you@example.org
OPENALEX_EMAIL=
CROSSREF_MAILTO=you@example.org
SEMANTIC_SCHOLAR_API_KEY=
```

CORE 未配置 `CORE_API_KEY` 时自动跳过，不影响其他来源。Unpaywall 需要 email 参数；没有 DOI 或未配置 email 时不调用。项目不会打印、提交或写入日志的密钥、Cookie、密码和 token。

官方接口参考：

- [Crossref REST API](https://api.crossref.org/)
- [OpenAlex API](https://help.openalex.org/)
- [Unpaywall API 与数据格式](https://unpaywall.org/data-format)
- [CORE API](https://core.ac.uk/services/api)
- [OSTI.GOV API](https://www.osti.gov/api/v1/docs)
- [HAL API](https://api.hal.science/docs/search)
- [NRC ADAMS Public Search API](https://adams-api-developer.nrc.gov/)
- [IAEA INIS Repository Search](https://inis.iaea.org/search/)
- [arXiv API Access](https://info.arxiv.org/help/api/index.html)

## 合法性和版权边界

本项目只从公开 API、出版社 OA 页面、机构仓储、作者合法公开版本、官方报告、公开学位论文和 arXiv 等合法来源检索和获取资源。

本项目不会：

- 绕过付费墙、账号登录、机构认证、访问控制或 CAPTCHA；
- 使用 Sci-Hub、盗版数据库、影子文献库或泄露 Cookie/token；
- 绕过 robots、Cloudflare、限流或其他反爬措施；
- 构造未经来源确认的 DOI/PDF URL；
- 将 HTML 错误页、登录页或 Access denied 页面保存为 PDF。

公开可访问不等于可以任意转载或再分发。使用者仍须遵守来源服务条款、许可证和适用法律。

## 项目结构

```text
src/literature_finder/
├── models.py                 # 统一 LiteratureRecord
├── query_planner.py          # 请求解析和关键词扩展
├── domain_router.py          # 按主题选择专业来源
├── search.py                 # 多 Provider 检索与失败隔离
├── metadata.py               # DOI/标题/年份规范化
├── dedup.py                  # 元数据去重
├── link_resolver.py          # 合法入口和 OA 解析
├── excel_writer.py           # 扩展字段 Excel
├── persistence.py            # 内部 records JSON
├── library/
│   ├── scanner.py            # 本地 PDF 扫描和元数据提取
│   ├── detector.py           # ExistingDocumentResult 查重
│   └── manifest.py           # literature_manifest.json
├── download/
│   ├── manager.py             # 下载前查重、临时文件、二次 hash 去重
│   └── validator.py           # PDF 校验和 SHA256
├── downloader.py             # SafeDownloader 兼容入口
└── sources/                  # Crossref/OpenAlex/CORE/OSTI/HAL 等适配器
```

## 测试与已知限制

运行：

```bash
python -m pytest -q
```

测试覆盖澄清、查询扩展、来源失败隔离、DOI 元数据去重、本地 DOI/来源 ID/标题/文件名查重、手动 PDF 识别、manifest、下载前不发 HTTP、强制下载覆盖开关、PDF 校验和 SHA256 二次去重。

已知限制：NRC ADAMS 和 INIS 的自动化结构化检索需要依赖官方 API 订阅或接口变化，目前以 link-only 入口为主；中国商业数据库未作为核心爬虫接入；相关性排序仍是可解释的词法评分，并默认过滤低于 45 分的候选；上游 API 的限流、字段变化和 OA 标注可能导致空字段或失败记录；下载器不会把出版社登录页视为可下载全文。

## Roadmap

- 增加更多官方 API 和机构 repository adapter；
- 将 DOI/标题语义排序升级为可选向量排序；
- 在不破坏两阶段确认和合法性边界的前提下增加批量任务恢复；
- 提供 SQLite 索引作为大规模本地库的可选后端。

## Contributing

新增 Provider 时请：

1. 只使用官方 API 或明确允许的结构化端点；
2. 继承或遵循 `SourceAdapter`，单个 Provider 失败不能中断整次检索；
3. 提供字段映射和来源 ID；
4. 添加 mock 单元测试，不依赖实时网络；
5. 不提交 `.env`、密钥、本地绝对路径、下载缓存或用户文献。

## License

MIT License，详见 [LICENSE](LICENSE)。
