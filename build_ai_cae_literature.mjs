import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectDir = path.dirname(fileURLToPath(import.meta.url));
const outputDir = process.env.AI_CAE_OUTPUT_DIR
  ?? path.join(projectDir, "outputs", "ai_cae_2021_2026");
const outputPath = `${outputDir}/ai_cae_literature_2021_2026.xlsx`;

const rows = [
  ["期刊论文", "Neural network-based surrogate model for a bifurcating structural fracture response", "2021-01", "Engineering Fracture Mechanics", "10.1016/j.engfracmech.2020.107424", "https://doi.org/10.1016/j.engfracmech.2020.107424", "有限元快照 + LSTM；结构断裂响应代理；机构元数据页/DOI页，未确认开放全文"],
  ["期刊论文", "Reduced Order Machine Learning Finite Element Methods: Concept, Implementation, and Future Applications", "2021-11-24", "Computer Modeling in Engineering and Sciences", "10.32604/cmes.2021.017719", "https://par.nsf.gov/servlets/purl/10300074", "HiDeNN-PGD；降阶机器学习有限元；NSF 公开 PDF；已保存"],
  ["期刊论文", "On-the-fly construction of surrogate constitutive models for concurrent multiscale mechanical analysis through probabilistic machine learning", "2021-01", "Journal of Computational Physics: X", "10.1016/j.jcpx.2020.100083", "https://pure.tudelft.nl/ws/files/86670210/1_s2.0_S2590055220300354_main.pdf", "FE² + Gaussian process + active learning；TU Delft 公开 PDF；已保存"],
  ["期刊论文", "Teaching solid mechanics to artificial intelligence—a fast solver for heterogeneous materials", "2021", "npj Computational Materials", "10.1038/s41524-021-00571-z", "https://www.nature.com/articles/s41524-021-00571-z.pdf", "DNN 替代异质材料局部应力计算；开放获取 PDF；已保存"],
  ["期刊论文", "A Machine Learning-based surrogate modeling framework for predicting the history-dependent deformation of dual phase microstructures", "2021-12", "Materials Today Communications", "10.1016/j.mtcomm.2021.102914", "https://doi.org/10.1016/j.mtcomm.2021.102914", "基于 J2 塑性 FE 数据的 LSTM；微结构时空响应代理；未确认开放全文"],
  ["期刊论文", "Surrogate modeling of elasto-plastic problems via long short-term memory neural networks and proper orthogonal decomposition", "2021-11-01", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2021.114030", "https://doi.org/10.1016/j.cma.2021.114030", "POD + LSTM；路径相关弹塑性 FE 代理；未确认开放全文"],
  ["期刊论文", "Algorithmically-consistent deep learning frameworks for structural topology optimization", "2021", "Engineering Applications of Artificial Intelligence", "10.1016/j.engappai.2021.104483", "https://doi.org/10.1016/j.engappai.2021.104483", "深度学习加速结构拓扑优化；每轮优化含 FEA；未确认开放全文"],
  ["预印本", "Data-driven synchronization-avoiding algorithms in the explicit distributed structural analysis of soft tissue", "2022-07-05", "arXiv / Computational Mechanics", "", "https://arxiv.org/pdf/2207.02194", "显式分布式 FE + 编码器-解码器 LSTM；减少共享节点同步通信；arXiv PDF；已保存"],
  ["期刊论文", "Smart parts: Data-driven model order reduction for nonlinear mechanical assemblies", "2022-03-01", "Finite Elements in Analysis and Design", "10.1016/j.finel.2021.103682", "https://doi.org/10.1016/j.finel.2021.103682", "非线性/历史相关机械部件代理；替代高保真 FE；未确认开放全文"],
  ["期刊论文", "Smart stiffness computation of one-dimensional Finite Elements", "2022-01", "Mechanics Research Communications", "10.1016/j.mechrescom.2021.103817", "https://doi.org/10.1016/j.mechrescom.2021.103817", "ANN 替代单元切线刚度；报告最高约 41% 仿真加速；未确认开放全文"],
  ["期刊论文", "Surrogate modeling of parametrized finite element simulations with varying mesh topology using recurrent neural networks", "2022-07", "Array", "10.1016/j.array.2022.100137", "https://www.sciencedirect.com/science/article/pii/S259000562200008X", "可变网格拓扑 + RNN/LSTM；DOAJ/ScienceDirect 标示开放获取；出版社 PDF 端点自动下载返回 403，保留详情页人工下载"],
  ["期刊论文", "Multi-fidelity surrogate modeling through hybrid machine learning for biomechanical and finite element analysis of soft tissues", "2022-09", "Computers in Biology and Medicine", "10.1016/j.compbiomed.2022.105699", "https://shayansss.github.io/files/2022_09.pdf", "低/高保真混合机器学习；作者公开 PDF；已保存"],
  ["期刊论文", "A mixed formulation for physics-informed neural networks as a potential solver for engineering problems in heterogeneous domains: Comparison with finite element method", "2022", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2022.115616", "https://doi.org/10.1016/j.cma.2022.115616", "混合形式 PINN；线弹性与扩散问题；与 FEM 对比；出版社页，可能需订阅"],
  ["期刊论文", "Interfacing finite elements with deep neural operators for fast multiscale modeling of mechanics problems", "2022-12-01", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2022.115027", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10300559/", "DeepONet 作为微观高保真求解器代理并与 FEM 耦合；PMC 开放全文"],
  ["期刊论文", "Learning finite element convergence with the Multi-fidelity Graph Neural Network", "2022-07-01", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2022.115120", "https://par.nsf.gov/servlets/purl/10436360", "多保真 GNN 学习 FEA 收敛；二维弹性；NSF 公开作者版本；已保存"],
  ["期刊论文", "Machine learning based inverse design of complex microstructures generated via hierarchical wrinkling", "2022-07", "Precision Engineering", "10.1016/j.precisioneng.2022.04.006", "https://doi.org/10.1016/j.precisioneng.2022.04.006", "FEA 训练 surrogate 后进行微结构逆设计；报告百万设计搜索加速；未确认开放全文"],
  ["期刊论文", "Machine learning accelerated transient analysis of stochastic nonlinear structures", "2022-04-15", "Engineering Structures", "10.1016/j.engstruct.2022.114020", "https://doi.org/10.1016/j.engstruct.2022.114020", "卷积自编码器 + 两级神经网络；随机非线性瞬态 FE 代理；未确认开放全文"],
  ["期刊论文", "Bayesian model updating with finite element vs surrogate models: Application to a miter gate structural system", "2022-12-01", "Engineering Structures", "10.1016/j.engstruct.2022.114901", "https://doi.org/10.1016/j.engstruct.2022.114901", "用 PCE/GPR 代理 FE 模型以加速贝叶斯更新；未确认开放全文"],
  ["预印本", "Physics-Informed Neural Networks for Shell Structures", "2022", "arXiv", "", "https://arxiv.org/pdf/2207.14291", "PINN 预测任意曲面薄壳小应变响应；可作为 FE 替代路线；arXiv PDF；已保存"],
  ["预印本", "Finite Element Method-enhanced Neural Network for Forward and Inverse Problems", "2022", "arXiv", "", "https://arxiv.org/pdf/2205.08321", "FEM 约束神经网络；前向/逆问题 surrogate；arXiv PDF；已保存"],
  ["期刊论文", "A data-driven reduced-order surrogate model for entire elastoplastic simulations applied to representative volume elements", "2023-08-07", "Scientific Reports", "10.1038/s41598-023-38104-x", "https://www.nature.com/articles/s41598-023-38104-x.pdf", "RNN + POD；完整 RVE 弹塑性场代理；开放获取 PDF；已保存"],
  ["期刊论文", "Topology optimization with advanced CNN using mapped physics-based data", "2023-01-06", "Structural and Multidisciplinary Optimization", "10.1007/s00158-022-03461-0", "https://link.springer.com/content/pdf/10.1007/s00158-022-03461-0.pdf", "Abaqus/FEA 数据生成 + U-Net/U-Net++；开放获取 PDF；已保存"],
  ["期刊论文", "Accelerating Analysis for Structure Design via Deep Learning Surrogate Models", "2023", "Advanced Intelligent Systems", "10.1002/aisy.202200099", "https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/aisy.202200099", "冲击靶板应力场/时间序列；FCNN + LSTM 代理 FEA；详情页"],
  ["期刊论文", "Accelerated multiscale mechanics modeling in a deep learning framework", "2023-09", "Mechanics of Materials", "10.1016/j.mechmat.2023.104709", "https://doi.org/10.1016/j.mechmat.2023.104709", "U-Net 预测复合微结构应力场；替代微观 FE 计算；未确认开放全文"],
  ["期刊论文", "A strategy to train machine learning material models for finite element simulations on data acquirable from physical experiments", "2023-03-01", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2023.115894", "https://doi.org/10.1016/j.cma.2023.115894", "从可测实验数据训练 ML 材料模型并嵌入 FE；未确认开放全文"],
  ["期刊论文", "A neural network finite element method for contact mechanics", "2023", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2023.116671", "https://doi.org/10.1016/j.cma.2023.116671", "NNFE + 超弹性接触；面向快速多查询/数字孪生；出版社页含开放手稿入口"],
  ["会议论文", "Graph Neural Network enhanced Finite Element modelling", "2023-03-24", "Proceedings in Applied Mathematics and Mechanics", "10.1002/pamm.202200306", "https://publications.rwth-aachen.de/record/954759/files/954759.pdf", "FE 网格转图 + 消息传递求解边值问题；RWTH 记录标示 OpenAccess PDF；自动下载响应非 PDF，保留直链人工下载"],
  ["期刊论文", "Low-dimensional data-based surrogate model of a continuum-mechanical musculoskeletal system based on non-intrusive model order reduction", "2023-06", "Archive of Applied Mechanics", "10.1007/s00419-023-02458-5", "https://arxiv.org/pdf/2302.06528", "PCA/kernel PCA/AE/VAE + 回归；上臂连续体 FE 代理；arXiv PDF；已保存"],
  ["会议论文", "Physics Informed Surrogate Model for Linear Elasticity", "2023-10-19", "New Materials, Machinery and Vehicle Engineering Proceedings", "10.3233/ATDE230121", "https://journals.sagepub.com/doi/10.3233/ATDE230121", "PISM/ResNet；线弹性求解速度报告为 FEM 的 8–9 倍；CC BY-NC 4.0；出版社 PDF 端点自动下载返回 403"],
  ["期刊论文", "A Hybrid Deep Neural Operator/Finite Element Method for Ice-Sheet Modeling", "2023-09-07", "Journal of Computational Physics", "10.1016/j.jcp.2023.112428", "https://www.pnnl.gov/publications/hybrid-deep-neural-operatorfinite-element-method-ice-sheet-modeling", "DeepONet 替代冰盖动量方程 FE 部分；报告数量级加速；公开机构详情页"],
  ["期刊论文", "Mesh-Informed Neural Networks for Operator Learning in Finite Element Spaces", "2023-09-23", "Journal of Scientific Computing", "10.1007/s10915-023-02331-1", "https://link.springer.com/content/pdf/10.1007/s10915-023-02331-1.pdf", "有限元空间中的网格感知算子学习；与 DeepONet/FNO 对比；开放获取 PDF；已保存"],
  ["期刊论文", "Data-driven algorithm based on the scaled boundary finite element method and deep learning for the identification of multiple cracks in massive structures", "2024-01-15", "Computers & Structures", "10.1016/j.compstruc.2023.107211", "https://doi.org/10.1016/j.compstruc.2023.107211", "SBFEM 生成波传播样本 + 膨胀因果 CNN；大结构多裂纹识别；未确认开放全文"],
  ["期刊论文", "Finite element-integrated neural network framework for elastic and elastoplastic solids", "2024", "Computer Methods in Applied Mechanics and Engineering", "", "https://www.sciencedirect.com/science/article/pii/S0045782524007291", "FEINN；有限元弱式与 PINN 融合；弹性/弹塑性边值问题；DOI 未在当前来源页确认"],
  ["期刊论文", "Introducing Finite Element Method Integrated Networks (FEMIN)", "2024", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2024.117073", "https://doi.org/10.1016/j.cma.2024.117073", "用 NN 替换碰撞仿真中的大块 FE 网格区域；面向 crash simulation 加速；未确认开放全文"],
  ["综述", "Comparison of neural FEM and neural operator methods for applications in solid mechanics", "2024-07-23", "Neural Computing and Applications", "10.1007/s00521-024-10132-2", "https://link.springer.com/content/pdf/10.1007/s00521-024-10132-2.pdf", "神经 FEM 与神经算子在固体力学中的系统比较；开放获取 PDF；已保存"],
  ["期刊论文", "A microstructure-based graph neural network for accelerating multiscale simulations", "2024-07-01", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2024.117001", "https://doi.org/10.1016/j.cma.2024.117001", "GNN 预测微观应变场并保留本构模型；加速 FE²；未确认开放全文"],
  ["期刊论文", "A machine learning assisted multifidelity modelling methodology to predict 3D stresses in the vicinity of design features in composite structures", "2024-09-01", "International Journal of Solids and Structures", "10.1016/j.ijsolstr.2024.112946", "https://doi.org/10.1016/j.ijsolstr.2024.112946", "多保真全局-局部 FE + 双向 LSTM；复合材料局部应力；未确认开放全文"],
  ["期刊论文", "Elementary-level intrusive coupling of machine learning for efficient mechanical analysis of variable stiffness composite laminates: a spatially-adaptive fidelity-sensitive computational framework", "2024", "Engineering with Computers", "10.1007/s00366-024-02082-z", "https://doi.org/10.1007/s00366-024-02082-z", "高斯过程在单元层级耦合 FE；变刚度复合材料多工况分析；未确认开放全文"],
  ["期刊论文", "An efficient surrogate model for damage forecasting of composite laminates based on deep learning", "2024-03-01", "Composite Structures", "10.1016/j.compstruct.2023.117863", "https://doi.org/10.1016/j.compstruct.2023.117863", "VQ-VAE 生成式 surrogate；低速冲击复合层合板全场损伤；未确认开放全文"],
  ["期刊论文", "Deep learning-based surrogate models for spatial field solution reconstruction and uncertainty quantification in Structural Health Monitoring applications", "2024-09-01", "Computers & Structures", "10.1016/j.compstruc.2024.107462", "https://doi.org/10.1016/j.compstruc.2024.107462", "VAE/CVAE 重构 FE 空间场并量化不确定性；船体案例；未确认开放全文"],
  ["期刊论文", "Ensemble of physics-informed neural networks for solving plane elasticity problems with examples", "2024-08-29", "Acta Mechanica", "10.1007/s00707-024-04053-3", "https://doi.org/10.1007/s00707-024-04053-3", "PINN 平面弹性；与商业有限元结果比较；未确认开放全文"],
  ["期刊论文", "Neural network-augmented differentiable finite element method for boundary value problems", "2025-01-01", "International Journal of Mechanical Sciences", "10.1016/j.ijmecsci.2024.109783", "https://doi.org/10.1016/j.ijmecsci.2024.109783", "NN + 可微 FEM；面向大规模边值问题；出版社详情页"],
  ["期刊论文", "A Finite Operator Learning Technique for Mapping the Elastic Properties of Microstructures to Their Mechanical Deformations", "2025", "International Journal for Numerical Methods in Engineering", "10.1002/nme.7637", "https://onlinelibrary.wiley.com/doi/full/10.1002/nme.7637", "有限元域分解 + PINN + 神经算子；微结构力学变形；出版社全文页"],
  ["期刊论文", "Transfer learning-enhanced finite element-integrated neural networks", "2025-03-15", "International Journal of Mechanical Sciences", "10.1016/j.ijmecsci.2025.110075", "https://ira.lib.polyu.edu.hk/bitstream/10397/112007/1/1-s2.0-S0020740325001614-main.pdf", "FEINN + 尺度/材料/载荷迁移学习；PolyU 公开 PDF；已保存"],
  ["期刊论文", "Fem-constrained neural network-based surrogate model (FCNN-SM) for rapid structural response prediction: algorithm framework and reliability analysis applications", "2025", "International Journal of Solids and Structures", "10.1016/j.ijsolstr.2025.113556", "https://doi.org/10.1016/j.ijsolstr.2025.113556", "FEM 全局方程约束的无标签 surrogate；结构可靠性计算；出版社页"],
  ["期刊论文", "Coupled data/physics-driven framework for accurate and efficient structural response simulation", "2025-03-15", "Engineering Structures", "10.1016/j.engstruct.2025.119636", "https://doi.org/10.1016/j.engstruct.2025.119636", "数据/物理耦合 + 注意力增强回归网络；三层框架 FE 响应；开放获取"],
  ["期刊论文", "An optimized physically recurrent neural network for multiscale modeling of composite materials", "2025-12-15", "International Journal of Mechanical Sciences", "10.1016/j.ijmecsci.2025.111030", "https://doi.org/10.1016/j.ijmecsci.2025.111030", "物理递归 NN + FE² + PyTorch 商业 FE 嵌入；复合材料多尺度；未确认开放全文"],
  ["期刊论文", "Fast structural analysis of concrete thin-shells using deep learning", "2026-01", "Computers & Structures", "10.1016/j.compstruc.2025.108042", "https://doi.org/10.1016/j.compstruc.2025.108042", "20,000 个薄壳 FE 样本；MLP/CNN/GNN 预测屈曲与应力；出版社页"],
  ["期刊论文", "An accessible and efficient finite element implementation for multiscale surrogate modeling using differential neural network setup", "2026-05", "Finite Elements in Analysis and Design", "10.1016/j.finel.2026.104542", "https://doi.org/10.1016/j.finel.2026.104542", "微观均匀化 surrogate + dNN；Abaqus/Standard 集成；出版社页"],
  ["期刊论文", "A surrogate model for topology optimisation of elastic structures via parametric autoencoders", "2026-01-01", "Computer Methods in Applied Mechanics and Engineering", "10.1016/j.cma.2025.118503", "https://upcommons.upc.edu/server/api/core/bitstreams/6f5228a7-8729-4bc8-9121-c4d6b4a26ee7/content", "参数自编码器预测准最优拓扑；平均优化迭代减少 53%；UPC 公开 PDF；已保存"],
];

const headers = ["序号", "文献类型", "文献名", "文献发表日期", "期刊/来源", "DOI号", "链接", "备注"];
const downloadedSequences = new Set([2, 3, 4, 8, 12, 15, 19, 20, 21, 22, 28, 31, 35, 44, 50]);
const failedDownloads = new Map([
  [11, "出版社 PDF 端点返回 403，详情页可人工下载"],
  [27, "机构 PDF 端点返回非 PDF 响应，保留直链人工下载"],
  [29, "出版社 PDF 端点返回 403，开放获取页面可人工下载"],
]);
const notesWithDownloadStatus = rows.map((r, i) => {
  const sequence = i + 1;
  if (downloadedSequences.has(sequence)) return `${r[6]}；下载状态：已下载`;
  if (failedDownloads.has(sequence)) return `${r[6]}；下载状态：未下载（${failedDownloads.get(sequence)}）`;
  return `${r[6]}；下载状态：未下载（未确认合法直接下载入口）`;
});
const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Literature");
sheet.showGridLines = false;
sheet.getRange("A1:H1").values = [headers];
sheet.getRange(`A2:H${rows.length + 1}`).values = rows.map((r, i) => [i + 1, r[0], r[1], r[2], r[3], r[4], r[5], notesWithDownloadStatus[i]]);
// Keep the URL visible as plain text and attach a hyperlink when supported by the export surface.
for (let i = 0; i < rows.length; i++) {
  const cell = sheet.getCell(i + 1, 6);
  cell.hyperlink = rows[i][5];
}

sheet.getRange(`A1:H${rows.length + 1}`).format.font = { name: "Arial", size: 10, color: "#1F2937" };
sheet.getRange("A1:H1").format = {
  fill: "#1F4E78",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
sheet.getRange(`A2:H${rows.length + 1}`).format.verticalAlignment = "top";
sheet.getRange(`B2:H${rows.length + 1}`).format.wrapText = true;
sheet.getRange(`G2:G${rows.length + 1}`).format.font = { name: "Arial", size: 10, color: "#0563C1", underline: "single" };
sheet.getRange(`A2:A${rows.length + 1}`).format.horizontalAlignment = "center";
sheet.getRange(`A1:H${rows.length + 1}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
sheet.getRange(`D2:D${rows.length + 1}`).format.numberFormat = "@";
sheet.getRange(`F2:F${rows.length + 1}`).format.numberFormat = "@";
sheet.getRange("A1:A51").format.columnWidth = 7;
sheet.getRange("B1:B51").format.columnWidth = 13;
sheet.getRange("C1:C51").format.columnWidth = 52;
sheet.getRange("D1:D51").format.columnWidth = 15;
sheet.getRange("E1:E51").format.columnWidth = 28;
sheet.getRange("F1:F51").format.columnWidth = 30;
sheet.getRange("G1:G51").format.columnWidth = 54;
sheet.getRange("H1:H51").format.columnWidth = 55;
sheet.getRange("A1:H1").format.rowHeight = 28;
sheet.getRange("A2:H51").format.rowHeight = 60;
sheet.freezePanes.freezeRows(1);
const table = sheet.tables.add(`A1:H${rows.length + 1}`, true, "LiteratureTable");
table.style = "TableStyleMedium2";
table.showFilterButton = true;

const inspect = await workbook.inspect({ kind: "table", range: `Literature!A1:H8`, include: "values,formulas", tableMaxRows: 8, tableMaxCols: 8, maxChars: 6000 });
console.log(inspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);
const preview = await workbook.render({ sheetName: "Literature", range: "A1:H12", scale: 1, format: "png" });
await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(`${outputDir}/preview.png`, new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(`Saved ${outputPath}`);
