# CGMF 离散能级转换链因果修正与 Run #266/#267 复核（Run #128）

- 分支：`qi/fix-discrete-start-index`
- 审计基线：`a7acc2e1a629b1657c03ab35feec05f36569b9ab`
- 范围：只读源码路径审计、CI artifact 复核、转换链来源核验。
- 未修改：生产核数据、物理规则、RNG、golden、模拟矩阵。

## 1. Run #266/#267 最新结果（COMPUTATION_VERIFIED）

两个 workflow run 均使用提交 `a7acc2e1a629b1657c03ab35feec05f36569b9ab`，均以 failure 结束：

- Run #266 push：44691039787
- Run #267 pull_request：44691047345

两者唯一 job `build-and-g2-matrix` 均失败。Run #267 的 Configure、Build、G2 合成分析单测、RNG seed matrix validator 均成功；完整 G2 sidecar matrix 在第一个 case `cf252-sf` 执行时退出，CGMF 子进程返回 255。

Run #267 artifact `cgmf-g2-mixed-history-matrix`（ID 14608247787）中的 `cf252-sf/on/sidecar-on.stdout` 显示：

- event 6，HF，ⁱ³⁶I；
- 当前态 (E=0.0793032525585) MeV、(J^π=7^+)；
- 低能连续态下一 bin 约 0.029303 MeV；
- runtime `ndisc=1`，唯一离散态桥接因角动量条件拒绝；
- 随后报错 `lower-cut transition has no mappable discrete state`。

同一 artifact 仅包含 21 条 neutron transitions、10 条 mixed-history summaries，`rng-audit.tsv` 为空；不是完整 200-event 矩阵，不能用于 P/H/O 推断。

Run #267 的 CTest artifact（ID 14607889209）记录 99 项测试中 12 项执行测试失败；失败事件诊断包括 ⁱ³⁶I、ⁱ³²I、¹⁰⁵Zr、⁸⁹Br 等。CI workflow 中 native test step 的 `continue-on-error: true` 使步骤摘要可显示 success，但最终 enforcement 检查的是 `steps.native_tests.outcome`，因此仍将 job 判为失败。不得把步骤摘要误报为 native suite 通过。

## 2. 生产运行时读取路径（SOURCE_AUDITED）

本轮重新逐段检查当前分支 `libcgmf/src/ripl2levels.cpp`：

1. 生产 `readDiscreteLevelData()` 打开 `DISCRETEDATA`（即预处理后的 CGMF 专用离散能级文件）。
2. 它从每个核素头记录读取 `nol`，将其保存为 `numberLevels[c]`，然后按该数量逐条读取能量、自旋、宇称和 gamma branches。
3. 生产 `getDiscreteLevels()` 将 `numberLevels[id]` 复制给 `ncl[k].ndisc`，并将相应能级复制到运行时对象。
4. 该生产 loader 不调用 `riplSetNmax()`，也不在运行时从 RIPL header 重新计算 `Nmax/Nc`。

`riplSetNmax()` 确实存在，其逻辑为 `normal -> Nc`、`reassign/extended -> Nmax`、`all -> Nol`；但该实现位于 `#ifdef DEVUTIL` 的 RIPL 原始数据读取辅助路径中。它能证明 CGMF 的开发辅助导入路径如何按模式选取能级，不能单独证明当前生产 `data/discreteLevels.dat` 的历史生成过程采用了该函数。

因此 Run #127 的以下事实继续成立：

- 八个目标核素的 RIPL-3 原始 header 均为 (N_{max}=1)；
- 对应生产专用文件的运行时记录均为 `ndisc=1)；

但“生产专用文件的单能级数量就是由当前 C++ `riplSetNmax(reassign)` 直接造成”这一因果表述必须降级为 **NOT ESTABLISHED**。两者相符是相关性，不是生成链证明。

## 3. 转换器文档给出的真实生成步骤（SOURCE_VERIFIED）

CGMF User Manual 的 Discrete Levels 页面明确说明，专用文件由 RIPL-3 完整数据经 `transformLevelDataFile.ipynb` 与 Python 类 `Nucleus.py` 处理生成，处理至少包含：

1. 读取 RIPL-3 完整 level data；
2. 修复缺失或未指派的 spin/parity；
3. 修复 gamma transitions。

手册还指出，未知基态的默认 Jπ 会按核素奇偶性设置；未指派宇称可能按均匀分布随机选择；不确定候选可能取首项。此处说明预处理并非简单复制或仅按 Nmax 截断。

官方文档：https://cgmf.readthedocs.io/en/stable/discreteLevels.html

当前 fork 的递归 tree 与本轮检查的上游 `lanl/CGMF` master tree 均未包含这两个转换器文件。故历史转换的具体参数、随机种子、筛选条件、Jπ 赋值及 gamma 分支修复仍为 **BLOCKED**。不能用当前生产 loader 的行为反推历史 Python 转换器。

## 4. 对 Run #127 结论的修订

| 命题 | 当前状态 | 修订 |
|---|---|---|
| 八个核素 RIPL header 的 (N_{max}=1) | COMPUTATION_VERIFIED | 保留 |
| 专用文件/运行时每个核素仅 1 个离散态 | COMPUTATION_VERIFIED | 保留 |
| RIPL (N_{max}) 表示能级方案完整性截止，非总观测能级数 | SOURCE_VERIFIED | 保留 |
| CGMF 的 DEVUTIL 原始 RIPL 路径按模式使用 Nc/Nmax/Nol | SOURCE_AUDITED | 保留 |
| 生产专用文件单能级由当前 C++ `riplSetNmax` 直接造成 | NOT ESTABLISHED | 撤销直接因果断言 |
| 历史 Python converter 是否按 Nmax、Nc 或其他规则筛选 | BLOCKED | 等待恢复 converter 或可核验历史产物 |
| 89Br/105Zr 等预处理后 Jπ 与核子奇偶性异常 | COMPUTATION_VERIFIED / NEEDS PER-LEVEL SOURCE TRACE | 保留异常事实，生成原因未定 |

## 5. 下一步执行顺序

1. 恢复或寻找 `transformLevelDataFile.ipynb`、`Nucleus.py` 的可核验历史版本（发布包、源码归档或 notebook 原始附件）；若无法恢复，则明确保留 BLOCKED。
2. 对专用文件逐核素做“原始 RIPL 行 → 转换后 level 行 → 运行时 ndisc/Level 对象”的三段式追踪。没有转换器时，不得用 Nmax/Nc 的候选模式代替真实历史转换。
3. 设计离线 test-only 对照，分别模拟 `Nmax`、`Nc`、`Nol` 及逐能级可信度策略；输出每个失败事件候选能级集合、能量可达性、Jπ 与 E1/M1/E2 选择规则，不改生产数据库。
4. 单独审查 114 条奇 A 整数 J 记录，区分 RIPL 原始已指派值、范围/候选标签、未指派值和转换器赋值；不自动覆盖 ENSDF 值。
5. 修复候选只有在物理定义、数据来源和完整矩阵验收标准明确后才进入生产分支。完整 G2 sidecar matrix 与 native regression 均通过前，不恢复 P/H/O 竞争分析。

## 6. 证据状态

- Run #266/#267 job 状态与 Run #267 artifacts：**COMPUTATION_VERIFIED**。
- Run #267 Cf-252 event 6 的 136I lower-cut 失败：**COMPUTATION_VERIFIED**。
- 生产 loader 直接读取专用文件记录、未调用 `riplSetNmax`：**SOURCE_AUDITED**。
- DEVUTIL 的 `riplSetNmax` 模式逻辑：**SOURCE_AUDITED**。
- 官方手册声明的 Python 预处理步骤：**SOURCE_VERIFIED**。
- 当前专用文件历史生成时是否使用 Nmax/Nc/其他筛选逻辑：**BLOCKED**。
- G2 完整矩阵、P/H/O 竞争识别及气论物理机制：**BLOCKED / NOT UPGRADED**。

本轮只读审计；未修改生产核数据、物理规则、RNG、golden 或模拟矩阵。
