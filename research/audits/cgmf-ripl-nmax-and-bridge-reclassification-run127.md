# RIPL Nmax completeness cutoff 与 G2 bridge 失败重分类（Run #127）

- 分支：`qi/fix-discrete-start-index`
- 基线提交：`f3d41a067a0f598b2f8bdd30810471543c11ceeb`
- 性质：只读数据/源码/CI 审计；未修改生产数据、物理选择规则或 golden。
- 主要对象：Run #260（44688397076）、Run #261（44688405081）。

## 1. 关键结论

此前 Run #126 将 (^{132}\mathrm I)、(^{96}\mathrm Y) 等“ENSDF/RIPL 可见激发态未进入 runtime discreteLevels”暂列为可能的数据库遗漏。本轮核对 RIPL 原始头记录后，需要修正这一分类：

**这八个失败核素的 RIPL-3 头记录全部为 (N_{\max}=1)**。RIPL 的 (N_{\max}) 不是总的已观察能级数，而是能级方案被认为完整的截止序号。对这些核素，原始 RIPL 可以列出多个实验能级，但其完整性截止仍停在基态。CGMF 专用文件每核素只保留一个离散态，与该截止相符。

因此，不能把 (^{132}\mathrm I)、(^{96}\mathrm Y)、(^{105}\mathrm{Nb}) 的高阶已观察能级未进入运行时文件，直接称为意外丢失或预处理损坏。它们首先是 **RIPL completeness cutoff / Nmax=1** 的结果。与此同时，(^{89}\mathrm{Br}) 和 (^{105}\mathrm{Zr}) 的最终基态 (J^\pi) 存在独立的奇质量数自旋格点问题；该问题不能被 Nmax 解释掉。

## 2. RIPL 原始头记录与 CGMF 专用文件

本轮直接读取仓库中的 RIPL-3 原始文件：

- `data/ripl3-levels.dat`，blob SHA `c3c3a816730deef172ccbd11b0dfd58b6d197d90`。
- `data/discreteLevels.dat`，blob SHA `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`。

RIPL header 的字段顺序为 `Nol, Nog, Nmax, Nc`。其中：
- `Nol`：原始衰变方案中的能级数；
- `Nmax`：能级方案被认为完整的最高能级序号；
- `Nc`：实验自旋/宇称被认为唯一的最高能级序号。

RIPL 技术手册说明：(N_{\max}) 是能级方案完整性的截止；(N_c) 是自旋/宇称唯一性的截止。手册还说明，在已知能级少于 20 个或不确定能级超过 2 个、因而没有进行恒温拟合的情况下，默认 (N_{\max}=1)、(N_{\min}=1)、(E_{\max}=0)。参见 IAEA RIPL 手册：
https://www-nds.iaea.org/RIPL-3/handbook/ripl2.pdf （格式定义约第 14 页；默认值约第 17 页，PDF 文本行 1035–1048、1504–1506）。

CGMF 源码 `libcgmf/src/ripl2levels.cpp::riplSetNmax` 明确区分：
- `normal`：使用 `Nc`；
- `reassign` / `extended`：使用 `Nmax`；
- `all`：使用 `Nol`。

该选择逻辑与下表中 `discreteLevels.dat` 的单能级记录数量相符。历史 notebook `transformLevelDataFile.ipynb` 和 Python 类 `Nucleus.py` 在当前仓库中不可用，因此本轮不声称已重建专用文件生成的全部历史步骤；准确表述是：最终文件的单能级数量与 RIPL 的 (N_{\max}=1) 截止一致，且 CGMF 源码存在按 (N_{\max}) 截取的导入路径。

| 核素 | RIPL Nol | Nmax | Nc | RIPL 首个激发态 | CGMF ndisc |
|---|---:|---:|---:|---|---:|
| (^{89}\mathrm{Br}) | 1 | 1 | 1 | RIPL 无后续能级 | 1 |
| (^{96}\mathrm Y) | 7 | 1 | 3 | 122.297 keV, (1^-\) | 1 |
| (^{105}\mathrm{Zr}) | 1 | 1 | 1 | RIPL 无后续能级 | 1 |
| (^{105}\mathrm{Nb}) | 6 | 1 | 1 | 127.9 keV, (7/2^+\) | 1 |
| (^{132}\mathrm I) | 6 | 1 | 1 | 22.0 keV, (5^+\) | 1 |
| (^{136}\mathrm I) | 11 | 1 | 1 | 86.73 keV, J 未指派 | 1 |
| (^{137}\mathrm I) | 15 | 1 | 1 | 243.3 keV, (5/2^+\) | 1 |
| (^{138}\mathrm{Te}) | 7 | 1 | 1 | 443.1 keV, (2^+\) | 1 |

特别注意 (^{96}\mathrm Y)：(N_c=3) 而 (N_{\max}=1)。CGMF 的 `reassign` 路径使用 (N_{\max})，不是 (N_c)，因此仍只保留基态。不能把 (N_c) 与 (N_{\max}) 混为一个“可用能级数”。

## 3. 对 Run #253 / #260 / #261 失败的重分类

Run #253 与 Run #260/#261 的 native regression 日志均显示 12 条桥接诊断、涉及 8 个核素；所有诊断的运行时 `ndisc=1)。失败不再按“运行数据库漏掉了已知能级”简单归类，而应分成以下不同情况：

### A. (N_{\max}=1) 导致离散方案只含基态，连续态从低能区延伸

- (^{136}\mathrm I)：事件约 20.540、79.303、81.165 keV；首个 RIPL/ENSDF 激发态 86.73 keV，且该态 J 未指派。
- (^{137}\mathrm I)：事件约 77.394、132.298 keV；首个激发态 243.3 keV。
- (^{138}\mathrm{Te})：事件约 177.691 keV；首个激发态 443.1 keV。
- (^{89}\mathrm{Br})：事件约 23.216 keV；ENSDF 2021 首个激发态 130.3 keV。

这些事件的能量低于相应已评价的首个激发态。因为最高离散态只有基态，`statSetupEnergyBin` 在 `elmax == 0` 时把连续态网格延伸到零附近，低能统计连续态因此可能进入真实能级结构尚未覆盖的区域。

### B. 已观察能级存在，但在 RIPL completeness cutoff 之外

- (^{132}\mathrm I)：事件约 277.059 keV；RIPL 原始表列出 22、49.72、120、161.52、277.86 keV 等能级，但 (N_{\max}=1)、(N_c=1)。
- (^{96}\mathrm Y)：事件约 186.721 keV；RIPL 原始表列出 122.297 keV 的 (1^-\) 首激发态，但 (N_{\max}=1)、(N_c=3)。
- (^{105}\mathrm{Nb})：事件约 282.518 keV；RIPL 原始表列出 127.9 keV 的 (7/2^+\) 首激发态，但 (N_{\max}=1)。

这些不是已证明的文件截断 bug；它们是“存在被观察能级”与“模型只接纳完整方案内的能级”之间的差异。是否应在 CGMF 中采用 (N_c)、(N_{\max})、二者较小值或更细粒度的逐能级可信度，必须另做受控模型比较，不能直接切换到 `all`。

### C. 原始 RIPL 本身只有基态记录

- (^{105}\mathrm{Zr})：RIPL 当前条目 `Nol=1, Nmax=1`，没有后续能级；ENSDF A=105 数据集存在，但本轮尚未提取其完整 adopted level 表。

该核素不能套用“RIPL 中已有首激发态但被 Nmax 排除”的说法。

## 4. 另一个独立问题：(^{89}\mathrm{Br}) 与 (^{105}\mathrm{Zr}) 的奇 A 整数自旋

(^{89}\mathrm{Br}) 与 (^{105}\mathrm{Zr}) 的 CGMF 专用文件基态分别记录为 (J^\pi=2^+) 和 (4^+)。二者质量数均为奇数，因此整数 (J) 与核子数奇偶性不相容。此前全库审计已将它们列入 114 条奇 A 整数 J 异常；RIPL 原始记录的数值 J/宇称均未指派。

对 (^{89}\mathrm{Br})，NNDC ENSDF 2021 评价给出的基态为 ((5/2^-)\)，首个激发态为 130.3 keV、((3/2^-)\)。来源：
https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=89Br

因此 Run #253/#260/#261 中 (^{89}\mathrm{Br}) event 34 的 parity rejection，不能简单解释为“E1-only bridge 的普通限制”：运行时基态 (2^+\) 本身不是可信的物理基态，而且该奇 A 核素的连续态被抽样为整数 (J=3)，同样违反半整数自旋格点。修正前，不能用这条事件来判定 E1/M1 桥接的物理优劣。

(^{105}\mathrm{Zr}) 也有同类格点异常：运行时基态 (4^+\)，失败事件连续态 (J=6)，而 A=105 为奇数。其真实基态 Jπ 仍需 ENSDF 逐条核实。

## 5. Run #260/#261 CI 结果复核

两个 run 均使用同一提交 `f3d41a067a0f598b2f8bdd30810471543c11ceeb)，均失败于 G2 sidecar matrix 的第一个 Cf-252 SF case：

- Build 与合成分析单元测试通过；
- sidecar 在 event 6、(^{136}\mathrm I) 处中止；
- 每个 run 的矩阵产物只有 21 条 neutron transitions、10 条 mixed-history summaries，RNG audit 文件为空；不是完整 200-event 样本；
- CTest artifact 为 99 项中 87 项通过、12 项失败；12 条 bridge diagnostics 覆盖上述 8 个核素；
- workflow 的 native test step 设置了 `continue-on-error: true`，所以 job step summary 显示 success，但 `steps.native_tests.outcome` 为 failure，最后的 `Enforce native regression baseline after G2 diagnostics` 明确失败。

Artifacts：
- Run #260: matrix 14607771309；CTest logs 14607283384；native outputs 14607397994。
- Run #261: matrix 14607920937；CTest logs 14607422679；native outputs 14607353147。

## 6. 当前证据状态与后续

- 两个 CI run 的真实状态、artifact 内容与 CTest 12/99 失败：**COMPUTATION_VERIFIED**。
- 八个核素的 RIPL header (N_{\max}=1) 与原始 `Nol/Nc`：**COMPUTATION_VERIFIED**。
- (N_{\max}) 与 (N_c) 的字段定义、RIPL 低数据量时默认 (N_{\max}=1)：**SOURCE_VERIFIED**（IAEA RIPL 手册）。
- CGMF `reassign` 路径使用 (N_{\max})：**SOURCE_VERIFIED**。
- 历史 notebook 对每个核素如何选择/修复 Jπ 的逐条执行记录：**BLOCKED**。
- (^{89}\mathrm{Br}) ENSDF 基态与首激发态：**SOURCE_VERIFIED**。
- (^{105}\mathrm{Zr}) 当前 ENSDF adopted ground-state Jπ：**BLOCKED / NOT EXTRACTED**。
- 应否将 RIPL (N_{\max}=1) 核素切换为 (N_c) 或 `all`：**BLOCKED / MODEL COMPARISON REQUIRED**。

下一步优先顺序：

1. 先完成 (^{105}\mathrm{Zr}) 的 ENSDF adopted level 核验，并将 114 条异常记录按“原始 Jπ 明确 / 候选范围 / 未指派”分组，不做自动覆盖。
2. 建立一个 test-only 的 level-selection 对照：当前 `reassign/Nmax`、`normal/Nc`、逐能级可信度选择；只输出差异与候选 bridge，不修改生产数据或 RNG。
3. 对每个失败事件逐个计算候选态是否满足 E1/M1/E2 的角动量与宇称选择条件；区分“无可用离散态”“离散态在 Nmax 外”“基态 Jπ 错误”“多极性不匹配”。
4. 只有当完整 sidecar matrix 和 native regression 都通过后，才恢复 P/H/O 竞争识别；当前不得将部分产物作为统计证据。

本轮未修改生产核数据、continuum cutoff、gamma strength、bridge 选择规则、golden 或 RNG。
