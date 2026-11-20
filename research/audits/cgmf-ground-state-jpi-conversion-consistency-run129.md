# CGMF 基态 Jπ 转换一致性审计与 Run #270 复核（Run #129）

- 分支：`qi/fix-discrete-start-index`
- 基线：`992c51c1f50b26032e9253bfc2d6d99db852ef0e`
- 范围：RIPL-3 原始基态记录、CGMF 专用离散能级文件、官方手册规则及 Run #270 artifacts 的只读对照。
- 未修改：生产核数据、物理规则、RNG、golden、模拟矩阵。

## 1. Run #270 最新 CI（COMPUTATION_VERIFIED）

Run #270（push，ID `44692563592`）使用提交 `992c51c1f50b26032e9253bfc2d6d99db852ef0e`，最终失败。

- Configure、Build、合成 G2 分析测试、RNG seed matrix validator 均通过。
- 完整 G2 sidecar matrix 在 Cf-252 SF 第一个 case 中止。
- Run #270 G2 artifact ID：`14609382036`。
- Build/CTest artifact ID：`14608899120`。
- Native regression artifact ID：`14608899128`。

G2 artifact 的 `cf252-sf/on/sidecar-on.stdout` 再次显示 event 6、HF、ⁱ³⁶I：当前态 (E=0.079303252558488524) MeV、(J^π=7^+)，runtime `ndisc=1`，唯一离散桥接候选因角动量条件拒绝；随后报 `lower-cut transition has no mappable discrete state`。

本次 G2 artifact 仍只有 21 条 neutron transitions、10 条 mixed-history summaries，`rng-audit.tsv` 为空。完整矩阵未完成。

Run #270 native regression 的 `LastTestsFailed.log` 列出 12 个失败测试；`LastTest.log` 中有 12 条 bridge diagnostics，覆盖 8 个核素，仍全部 `ndisc=1`。其中 ⁸⁹Br 的 event 34、(E=23.216111) keV、(J=3)、正宇称，因唯一离散基态宇称条件被拒绝。不得把此 native regression 结果与 G2 sidecar 部分样本合并为一个数据集。

## 2. 两个关键核素的原始 RIPL 与专用文件对照（COMPUTATION_VERIFIED）

直接读取当前分支完整 `data/ripl3-levels.dat` 与 `data/discreteLevels.dat`：

| 核素 | RIPL-3 原始基态 | CGMF 专用文件 | 直接差异 |
|---|---|---|---|
| ⁸⁹Br | (E=0)，(J=-1)，π=0；备注候选 ((3/2^-,5/2^-)) | (E=0)，(J^π=2^+) | 与原始候选值不一致 |
| ¹⁰⁵Zr | (E=0)，(J=-1)，π=0；无候选标签 | (E=0)，(J^π=4^+) | 未指派输入被赋成整数自旋 |

两个核素的 RIPL header 都为 `Nol=1, Nmax=1, Nc=1`，所以专用文件只有基态与 `Nmax=1` 的数量结果一致。但这不能解释具体 Jπ 赋值为何分别为 (2^+) 和 (4^+)。

专用文件顶部的注释称它由 RIPL-3 evaluated levels 生成，缺失 spin/parity 按 CGMF manual 规则补齐。因此这里可以建立明确的输入/输出对照，而不需要推测转换器内部实现。

## 3. 与 CGMF 官方手册规则的对照（SOURCE_VERIFIED）

CGMF 官方手册的 Discrete Levels 章节说明：

1. 对 RIPL-3 不确定的 Jπ 候选，选择第一项；
2. 对完全未知的基态，默认赋值为：even-even (0^+)、odd-odd (1^+)、even-odd (1/2^+)；
3. 手册明确警告，任意 Jπ 决策会对具体 gamma decay chains 产生非忽略影响。

来源：
- https://cgmf.readthedocs.io/en/stable/discreteLevels.html
- 上游源码文档：https://github.com/lanl/CGMF/blob/master/doc/rtd/discreteLevels.rst

据此：

- ⁸⁹Br 的 RIPL 文本候选第一项是 (3/2^-)，专用文件却为 (2^+)。这与手册描述的“候选取第一项”不一致。
- ¹⁰⁵Zr 为奇质量数、RIPL 基态无 Jπ 赋值且无候选标签；按手册 odd-A 默认值应为 (1/2^+)，专用文件却为 (4^+)。这与手册描述的完全未知基态默认值不一致。

**重要限制：** 手册可能没有完整描述历史转换器所有分支，且当前尚未恢复 `transformLevelDataFile.ipynb` / `Nucleus.py`。所以结论是“生产输出与公开文档规则不一致”，不是“已经定位到某一行 Python 代码的 bug”。转换器分支、版本、随机种子和候选解析细节仍为 **BLOCKED**。

## 4. 对其他未知基态的批量筛查（COMPUTATION_VERIFIED / INTERPRETATION LIMITED）

对当前 RIPL-3 文件与 CGMF 专用文件按核素名联表，得到：

- RIPL 原始核素记录：2,943；
- 专用文件核素记录：3,351；
- RIPL 第一能级为 (E=0)，且 (J<0) 或 π=0 的匹配核素：528；
- 其中没有括号候选文本的记录：462。

对这 462 条“无候选文本”的记录，若机械套用手册的默认 Jπ 规则，有 329 条输出与默认值不同。但这个批量比较只能作为**待核验差异筛查**：手册中“completely unknown ground state”的适用范围可能比“RIPL 第一能级 J/π 未指派”更窄；部分输出也可能来自历史版本的其他分支。因此不把 329 条直接称为错误。

这批结果提示应把核数据审计分为：
- 原始 RIPL 明确给出候选 Jπ；
- 原始 RIPL 无候选且 J/π 未指派；
- 原始 RIPL 已指派 Jπ；
- 专用文件输出与公开手册规则一致/不一致；
- 历史生成规则尚未恢复。

## 5. 对 G2 阻断原因的影响

- ⁸⁹Br：现有 lower/next bridge failure 与唯一专用基态 (2^+) 的 parity mismatch 有直接联系；但在没有确认正确基态 Jπ 前，不能仅据此修改 bridge 选择器。
- ¹⁰⁵Zr：其专用文件 (4^+) 也与 RIPL 未指派输入及手册默认规则存在不一致；native regression 中对应高自旋状态桥接失败，应作为单独核数据审计对象。
- ⁱ³⁶I：Run #270 的主要 sidecar 阻断仍是低能 (7^+) continuum 状态无法桥接唯一 (1^-) 基态。该问题与 ⁸⁹Br/¹⁰⁵Zr 的基态赋值差异是不同层次的问题，不能混为一谈。

## 6. 后续

1. 优先追溯 1.1.0 专用文件的真实转换器版本、运行日志、输入 RIPL 文件版本与随机种子。
2. 对 ⁸⁹Br、¹⁰⁵Zr 做最小复核：原始记录、公开手册规则、专用文件、运行时 Level 对象四者逐字段对照。
3. 扩展到所有 RIPL 未指派基态记录，但把“公开手册规则不一致”与“物理上确定错误”分开标记。
4. 在转换链可追溯之前，不批量覆盖 Jπ，不修改 continuum cutoff、bridge multipolarity、lower-cut 或 golden。
5. 完整 G2 sidecar matrix 与 native regression 通过前，不恢复 P/H/O 竞争识别。

## 7. 证据状态

- Run #270 的 CI job 与 artifacts：**COMPUTATION_VERIFIED**。
- Run #270 Cf-252 event 6、ⁱ³⁶I bridge failure：**COMPUTATION_VERIFIED**。
- Run #270 native regression 的 12 项失败与 12 条 bridge diagnostics：**COMPUTATION_VERIFIED**。
- ⁸⁹Br、¹⁰⁵Zr 的 RIPL 输入与专用文件 Jπ 差异：**COMPUTATION_VERIFIED**。
- CGMF 手册公开的候选/默认 Jπ 规则：**SOURCE_VERIFIED**。
- 两个核素输出与公开手册规则不一致：**SOURCE_COMPARISON_VERIFIED**。
- 历史转换器的具体实现与差异成因：**BLOCKED**。
- 完整 G2、P/H/O 与气论物理机制：**BLOCKED / NOT UPGRADED**。

本轮只读审计；没有修改生产核数据、物理规则、RNG、golden 或模拟矩阵。
