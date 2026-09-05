# Academic Literature Search

一个面向 Agent 的学术文献检索 Skill，以及可独立安装的 Python 工具包。项目用于从公开学术数据源发现、整理和筛选文献，并在确认存在合法公开全文入口后，按用户选择下载文件。

## 项目解决的问题

学术检索通常同时面临以下问题：

1. 研究主题过于宽泛，直接搜索容易偏离真正的研究问题。
2. 不同数据库的题名、作者、日期、期刊和 DOI 字段格式不一致。
3. 同一篇论文可能在多个来源重复出现，需要可靠去重。
4. DOI 页面、出版社详情页、机构仓储和开放 PDF 的可访问性不同，难以选择稳定且合法的入口。
5. 论文下载涉及版权和访问限制，不能把普通详情页或错误网页误当成 PDF。
6. 初次检索和下载混在一起时，容易在用户未确认范围前产生外部访问或文件写入。

本项目将这些环节拆成可复用的流水线：主题判断与澄清、有限关键词扩展、多源检索、元数据规范化、去重与排序、合法访问入口选择、Excel 导出，以及用户明确选择后的安全下载。

## 主要功能

- **主题澄清**：对 `核燃料`、`LLM agent` 等可能对应多个成熟子方向的输入给出澄清问题；主题不明确时不启动检索。
- **检索计划生成**：解析年份、目标数量、文献类型和中英文关键词，并进行受控的同义词/缩写扩展。
- **多源检索**：默认适配 Crossref、OpenAlex、Semantic Scholar 和 arXiv。每个来源独立失败，单个来源不可用时仍继续其他来源。
- **开放获取补充**：配置 `UNPAYWALL_EMAIL` 后，可按 DOI 查询 Unpaywall 的开放获取位置。
- **元数据处理**：规范化 DOI，保留无法确认的字段为空；通过 DOI、标准化题名和保守的模糊题名匹配去重。
- **可解释排序**：根据题名/摘要词法匹配、DOI、摘要、开放获取信息和年份范围计算 0–100 的相关性分数。
- **合法入口选择**：优先使用开放获取页面、机构仓储、合法公开文件，其次使用 DOI 或出版社详情页；不会猜测 DOI 或拼接未验证下载地址。
- **Excel 导出**：生成 `Literature` 工作表，固定使用 8 列，并设置表头加粗、筛选、冻结首行、列宽和可点击链接。
- **安全下载**：只有 `download_permission_verified=True` 的记录可以下载；支持指定序号/范围和文献类型筛选。
- **下载校验与报告**：设置超时、重试和访问间隔，检查 HTTP 状态、Content-Type、PDF 文件头和最小文件大小，并输出 `download_report.csv`。
- **工作流状态保护**：提供 `TaskStateMachine`，供 Agent 或上层集成确保只有在 Excel 导出并获得用户选择后才进入下载阶段。

## 安装方法

### 运行环境

- Python 3.11 或更高版本
- 网络连接：检索时需要访问公开学术 API；离线环境只能使用已有数据调用导出/分析功能
- 运行时依赖：`requests>=2.31,<3`、`openpyxl>=3.1,<4`

### Windows PowerShell

在项目根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

安装完成后可检查 CLI 是否可用：

```bash
literature-search --help
```

运行测试需要额外安装测试工具，因为 `pytest` 不是运行时依赖：

```bash
python -m pip install pytest
python -m pytest
```

## 使用方法

### 命令行检索

```bash
literature-search "2021-2026 AI finite element analysis surrogate models" --target 50 --output-dir results
```

参数含义：

- `topic`：研究主题或研究问题，必填。
- `--target`：最终保留的记录数，默认 30，程序限制在 1–200 之间。
- `--output-dir`：Excel 输出目录，默认当前目录；CLI 会直接在该目录下生成带时间戳的 `.xlsx` 文件。
- `--log-level`：`DEBUG`、`INFO`、`WARNING` 或 `ERROR`，默认 `INFO`。

初次检索只导出 Excel，不会自动下载文件。CLI 会输出原始候选数、去重后的最终数量、已确认存在合法公开下载入口的数量、Excel 路径和来源失败信息。

### 宽泛主题的澄清行为

```bash
literature-search "核燃料"
```

程序会输出类似下面的澄清问题，并以退出码 `2` 结束，不进行检索：

```text
当前主题可能对应多个明显不同的研究方向。
1. 你希望重点研究燃料材料、芯块、包壳、燃料棒/组件、热工水力、辐照行为、事故容错燃料、燃耗、制造工艺还是堆芯设计？也可以选择综合检索。
```

加入研究对象、问题或年份后，主题通常可以直接进入检索，例如：

```bash
literature-search "2021-2026 zirconium alloy fuel cladding irradiation damage journal articles" --target 30 --output-dir results
```

### Python API

下面的例子对应当前公开 API：先检索并导出，再由调用方在获得用户明确选择后调用下载器。

```python
from pathlib import Path

from literature_finder.downloader import SafeDownloader, parse_selection
from literature_finder.excel_writer import write_excel
from literature_finder.pipeline import run_search
from literature_finder.query_planner import parse_request

request = parse_request(
    "2021-2026 AI finite element analysis surrogate models",
    target_count=50,
)

plan, result = run_search(request)
output_dir = Path("results")
workbook_path = write_excel(
    result.records,
    output_dir / "literature_search_20260905_163000.xlsx",
)

print("原始候选：", result.raw_candidate_count)
print("最终记录：", len(result.records))
print("Excel：", workbook_path)
print("来源失败：", [(item.source, item.error) for item in result.failures])

# 必须先由用户选择下载范围，再把选择传给下载器。
selected = parse_selection("2, 5, 8-12", len(result.records))
download_results = SafeDownloader(
    timeout=30.0,
    retries=2,
    min_interval=1.0,
).download(result.records, output_dir, selected=selected)

# 也可以按文献类型筛选，例如：
# SafeDownloader().download(result.records, output_dir, type_filter={"期刊论文"})
```

`parse_selection` 支持英文逗号、中文逗号、空格和连字符范围，例如 `1, 3, 8-10`；序号从 1 开始，超出总记录数的项会被忽略。`SafeDownloader` 本身不负责询问用户，用户确认逻辑由 CLI 外的 Agent、UI 或调用方负责。

## 输入输出实例

### 输入

命令：

```text
literature-search "2021-2026 AI finite element analysis surrogate models" --target 50 --output-dir results
```

等价的核心请求对象：

```python
from literature_finder.models import ResearchRequest

ResearchRequest(
    topic="2021-2026 AI finite element analysis surrogate models",
    target_count=50,
    start_year=2021,
    end_year=2026,
)
```

### 命令行输出示例

下面的数量会随数据源返回结果和网络状态变化，仅展示输出格式：

```text
[INFO] Searching Crossref: 2021-2026 AI finite element analysis surrogate models
[INFO] Searching OpenAlex: 2021-2026 AI finite element analysis surrogate models
检索完成：原始候选 128，去重后/最终保留 50
合法公开下载入口：18
Excel：results\literature_search_20260905_163000.xlsx
下一步：仅保留 Excel，或在用户明确选择后调用 SafeDownloader；不会自动下载。
失败来源：Semantic Scholar: request failed ...
```

如果没有来源失败，CLI 不输出“失败来源”行。实际输出中的候选数、最终数量和失败信息不能预先固定。

### Excel 输出

`Literature` 工作表固定包含以下 8 列：

```text
序号 | 文献类型 | 文献名 | 文献发表日期 | 期刊/来源 | DOI号 | 链接 | 备注
```

示例记录：

| 序号 | 文献类型 | 文献名 | 文献发表日期 | 期刊/来源 | DOI号 | 链接 | 备注 |
|---:|---|---|---|---|---|---|---|
| 1 | 期刊论文 | Example surrogate model for finite element analysis | 2024-01-02 | Example Journal | 10.1234/example | `https://doi.org/10.1234/example` | Open Access 或出版社详情页；下载资格由内部字段判断 |

Excel 中的 DOI 和日期按文本写入；“链接”列在存在 URL 时设置为可点击超链接。下载权限、下载 URL 和来源等内部字段不会额外增加为 Excel 列。

### 下载输出

当调用方把同一个结果目录传给 `SafeDownloader` 时，目录结构为：

```text
results/
├── literature_search_20260905_163000.xlsx
├── download_report.csv
└── papers/
    ├── 001_Smith_2024_Example surrogate model for finite element analysis.pdf
    └── ...
```

`download_report.csv` 的列为：

```text
序号,文献名,状态,文件名,来源链接,失败原因
```

状态值来自当前下载器：

- `downloaded`：本次成功下载并通过校验。
- `already_exists`：目标文件已存在且大小大于 0。
- `failed`：请求失败、响应不是 PDF、文件过小或写入失败。
- `skipped`：记录未被确认具有合法公开下载资格。

## 数据源与 API 配置

默认检索适配器：

- Crossref REST API
- OpenAlex Works API
- Semantic Scholar Academic Graph API
- arXiv Atom API

可选环境变量：

| 环境变量 | 用途 |
|---|---|
| `CROSSREF_MAILTO` | 向 Crossref 请求中附加 `mailto`，便于礼貌访问和服务联系 |
| `OPENALEX_EMAIL` | 向 OpenAlex 请求中附加 `mailto` |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 请求头中的可选 API key |
| `UNPAYWALL_EMAIL` | 按 DOI 查询 Unpaywall 开放获取位置 |

PowerShell 临时设置示例：

```powershell
$env:UNPAYWALL_EMAIL = "you@example.org"
$env:OPENALEX_EMAIL = "you@example.org"
```

bash/zsh 示例：

```bash
export UNPAYWALL_EMAIL="you@example.org"
export OPENALEX_EMAIL="you@example.org"
```

项目不会读取或打印密钥，也不要求配置这些变量才能运行基础检索。公开 API 可能限流或变更，适配器会独立记录失败并继续运行。

相关公开接口文档：[Crossref REST API](https://api.crossref.org/)、[OpenAlex API](https://docs.openalex.org/)、[Semantic Scholar API](https://www.semanticscholar.org/product/api)、[arXiv API](https://info.arxiv.org/help/api/) 和 [Unpaywall API](https://unpaywall.org/products/api)。

## 合法性与下载安全

项目只使用公开 API、开放获取页面、机构仓储、合法作者版本和其他可公开访问的入口。它不会：

- 登录账号、使用机构 Cookie 或读取泄露凭据；
- 绕过付费墙、机构认证、验证码、robots 规则、反爬措施或访问限流；
- 使用盗版数据库、Sci-Hub 或其他未授权资源；
- 根据题名猜测 DOI，或拼接未经来源确认的下载 URL；
- 把 HTML 错误页保存成 PDF 文件。

“公开可访问”不等于用户拥有任意转载或再分发权。使用者仍需遵守来源网站条款、许可证和适用法律。

## 项目结构

```text
academic-literature-search/
├── agents/openai.yaml                 # Agent Skill 的显示信息和默认提示词
├── src/literature_finder/
│   ├── cli.py                          # literature-search 命令行入口
│   ├── pipeline.py                     # 检索流水线
│   ├── query_planner.py                # 请求解析与查询计划
│   ├── search.py                       # 多适配器检索与失败隔离
│   ├── metadata.py                     # DOI/题名规范化与合并
│   ├── dedup.py                        # 去重
│   ├── ranking.py                      # 相关性排序
│   ├── link_resolver.py                # 合法入口和 OA 资格处理
│   ├── excel_writer.py                 # 8 列 Excel 导出
│   ├── downloader.py                   # 选择性 PDF 下载与报告
│   ├── state_machine.py                # 下载前置状态保护
│   └── sources/                        # 各公开学术数据源适配器
├── tests/                              # 单元测试
├── SKILL.md                            # Agent Skill 行为约定
├── pyproject.toml                      # 打包、依赖和 CLI 配置
└── LICENSE                             # MIT License
```

## 已知限制

- 默认不抓取中国商业数据库；`GenericWebAdapter` 只生成合法的检索入口 URL，不抓取搜索引擎或出版社页面。
- 元数据、引用数和开放获取信号依赖上游服务；来源异常时可能出现空字段或失败记录。
- 当前相关性排序是可解释的词法排序，不是语义向量排序。
- arXiv 通过公开 Atom API 检索，因此在 arXiv 覆盖较好的领域效果更好。
- CLI 没有交互式下载参数；它在 Excel 导出后停止。下载需要由 Agent/UI/调用方明确传入序号集合或文献类型筛选。
- 下载器不会保证所有标记为开放获取的出版社页面都能被自动化 HTTP 客户端直接取得；遇到 403 或非 PDF 响应时会记录失败并保留页面入口。

## 开发与贡献

新增数据源或行为时，请同时添加单元测试，并保持：

- 单个来源失败不阻断整次检索；
- DOI 和开放获取信息必须来自真实来源；
- 不提交密钥、机构 Cookie 或本地绝对路径；
- 说明数据源的服务条款、访问频率和许可证边界。

运行测试：

```bash
python -m pip install pytest
python -m pytest
```

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
