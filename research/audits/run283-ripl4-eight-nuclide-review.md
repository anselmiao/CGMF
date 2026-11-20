# Run #283：RIPL-4（2026）对八个失败核素的升级复核

**目标分支**：`qi/fix-discrete-start-index`  
**CGMF 数据基线**：`data/discreteLevels.dat` blob `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`（文件头声明由 RIPL-3 生成）  
**新参考库**：IAEA RIPL-4，2026-05 发布；LEVELS 数据基于 2025-10 ENSDF 并补充 NUBASE 2020。  
**范围**：Run #277 八个失败核素，外加十条失败 event-state 记录的 E1 候选筛查。

## 1. 为什么升级到 RIPL-4

IAEA RIPL-4 官方 README 明确说明：RIPL-4 于 2026 年 5 月发布；LEVELS 包含截至 2025 年 10 月 ENSDF 的已知能级方案，并结合 NUBASE 2020。当前 CGMF `discreteLevels.dat` 文件头仍声明它由 RIPL-3 数据生成。因此，RIPL-4 是本次数据来源升级审计的参考，不应静默替换生产输入。

官方来源：
- https://github.com/IAEA-NDS/RIPL-4/blob/main/README.md
- https://github.com/IAEA-NDS/RIPL-4/tree/main/levels
- https://github.com/IAEA-NDS/RIPL-4/blob/main/levels/levels-readme.html

RIPL-4 的 level header 字段仍为 `Nol, Nog, Nmax, Nc`；官方 readme 明确区分：
- `Nol`: 衰变方案中的能级数；
- `Nog`: gamma-ray 数；
- `Nmax`: 能级方案被认为完整的最高能级序号；
- `Nc`: 自旋和宇称唯一的最高能级序号。

因此，评估 CGMF 适用的“完整且唯一 Jπ”能级时，`min(Nmax,Nc)` 是一个保守边界。它是一个数据审核边界，不等于已经证明 CGMF 历史转换器内部就是按该表达式实现。

## 2. RIPL-3 → RIPL-4 版本差异

| 核素 | RIPL-3 Nol/Nmax/Nc | RIPL-4 Nol/Nmax/Nc | CGMF ndisc |
|---|---:|---:|---:|
| ¹³⁶I | 11 / 1 / 1 | 22 / 10 / 1 | 1 |
| ¹³⁷I | 15 / 1 / 1 | 15 / 1 / 13 | 1 |
| ¹⁰⁵Zr | 1 / 1 / 1 | 4 / 1 / 1 | 1 |
| ⁸⁹Br | 1 / 1 / 1 | 11 / 1 / 1 | 1 |
| ¹⁰⁵Nb | 6 / 1 / 1 | 25 / 16 / 1 | 1 |
| ⁹⁶Y | 7 / 1 / 3 | 8 / 1 / 3 | 1 |
| ¹³⁸Te | 7 / 1 / 1 | 25 / 16 / 1 | 1 |
| ¹³²I | 6 / 1 / 1 | 6 / 1 / 1 | 1 |

重要观察：
- 八个核素在 RIPL-4 中的 `min(Nmax,Nc)` 都是 1，当前 CGMF `ndisc=1` 与这个保守边界数值一致。
- ¹³⁶I 的完整性边界从 1 提高到 10，但唯一 Jπ 边界仍为 1。
- ¹⁰⁵Nb、¹³⁸Te 的完整性边界提高到 16，但唯一 Jπ 边界仍为 1。
- ¹³⁷I 的唯一 Jπ 边界提高到 13，但完整性边界仍为 1。
- 因此不能只看 `Nol` 或 `Nmax`，也不能把 `Nc` 当作能级总数。八例 ndisc=1 与 `min(Nmax,Nc)` 一致，但这只是数据结果上的一致性，转换器历史逻辑仍需单独确认。

## 3. 两个基态 Jπ 数据异常

### ¹⁰⁵Zr

- RIPL-3 原始基态：J=-1，parity=0（未知）。
- RIPL-4 基态数值字段：J=1/2，parity=+1；原始 spin 信息字段为 `1/2+#`。
- CGMF 当前基态：J=4，parity=+1。
- A=105 为奇数，物理自旋必须是半整数；当前 CGMF 的整数 J=4 是 **INVALID_ODD_A_INTEGER_J**。
- ZIP correction 建议改为 1/2+，与 RIPL-4 数值字段一致；但 `#` 表示非实验赋值来源的标记，不能把它升级为实验确认。

### ⁸⁹Br

- RIPL-3 原始基态：J=-1，parity=0（未知）。
- RIPL-4 数值字段仍为 J=-1，parity=0；原始 spin 信息保留 `(3/2-,5/2-)` 两种可能。
- CGMF 当前基态：J=2，parity=+1。
- A=89 为奇数，当前整数 J=2 是 **INVALID_ODD_A_INTEGER_J**。
- ZIP correction 的 5/2− 是两种候选之一；它不能从 RIPL-4 原始记录单独升级为唯一确定值。需要固定版本的 ENSDF adopted 原始记录及赋值依据。
- 当前 public reference CSV 的 3/2− 也只是候选之一；不能把它与 5/2− 冲突静默消解。

**结论**：这两条不是普通“偏好哪个 Jπ”的问题，而是当前 CGMF 文件对奇质量数核给出整数自旋，违反角动量量子化。它们应进入硬性核素数据异常，而不是只记为低置信度。

## 4. RIPL-4 下重新筛查十条 E1 bridge 失败状态

筛查条件严格沿用当前 E1 selector：
- 最终态能量严格低于初态；
- `|Ji-Jf| <= 1`，排除 0→0；
- 初末态宇称相反；
- 只在 `min(Nmax,Nc)` 保守边界内使用唯一且完整的候选。

十条 event-state 记录的候选数全部为 0。机器可读明细见 [run283-ripl4-e1-bridge-screen.csv](run283-ripl4-e1-bridge-screen.csv)。

这说明：
1. RIPL-4 更新并不能仅凭新增能级数量解决这些 E1-only bridge 失败。
2. ¹³⁶I 新增完整能级到第 10 级，但事件初态能量低于第二级 0.08673 MeV；在三条失败事件能量范围内，仍只有基态低于初态，且没有 E1 允许的 Jπ。
3. ¹⁰⁵Nb、¹³⁸Te 虽然 Nmax 提高到 16，但 Nc 仍为 1；在保守唯一 Jπ 边界内没有新的可用态。即便放宽到 RIPL4 数值赋值，事件能量以下也没有 E1 候选。
4. ¹⁰⁵Zr 在 Nmax=1 的唯一完整边界内只有基态 1/2+，与失败初态 6− 不满足 E1 角动量条件。第 4 级 0.507 MeV、11/2+ 的记录不在 Nmax/Nc 保守边界内，且原始赋值带方括号，不得直接作为已验证桥接态。
5. ⁸⁹Br 的基态 Jπ 仍不唯一，不能选定 5/2− 来制造一个 E1 候选。

**因此，RIPL-4 既揭示了旧核数据版本问题，也没有给出足以解除当前十条失败的 E1 候选。不能通过简单换数据版本宣布修复。**

## 5. 对 CGMF 核结构准入器的新增硬规则

对核素质量数 A 和自旋 J：
- A 为偶数：必须满足 J 为整数；
- A 为奇数：必须满足 J 为半整数；
- 统一检查 `2J` 是否为整数，且 `2J mod 2 = A mod 2`。

本轮八个失败核素中，当前 CGMF 基态只有两条违反：
- ¹⁰⁵Zr：A=105，J=4 → 2J=8（偶数），应为半整数；
- ⁸⁹Br：A=89，J=2 → 2J=4（偶数），应为半整数。

新增审计工具已加入：
- `scripts/audit_nuclide_level_coverage.py`：支持 RIPL-3 单文件和 RIPL-4 多元素文件；保留 `Nol/Nog/Nmax/Nc`；输出原始 spin 字符串及 odd/even-A 自旋量子化状态。
- `tests/test_audit_nuclide_level_coverage.py`：增加奇质量数整数自旋异常和 RIPL-4 Nmax/Nc 边界测试。

## 6. 数据来源与状态

RIPL-4 element file blob SHA：
- `z035.dat`: `5a662d3ae724c997b55a049e40984f8d2060e313`
- `z039.dat`: `f0643e4bd9b79d70f1e932993ccfb879837b5d47`
- `z040.dat`: `5680ed6b2b40296e05106e65dc8d2a30812b2a03`
- `z041.dat`: `7dcc1db31ef9f03d16426816e85150f4bd4c573c`
- `z052.dat`: `49eacd5335a3374e068221bb41da87685420ee1c`
- `z053.dat`: `b6d613c24bcb37b9b345140870b3aec56e483ed3`

- RIPL-4 版本及 LEVELS 截止日期：**SOURCE_VERIFIED**。
- 八个核素 RIPL-4 记录头及能级行：**COMPUTATION_VERIFIED**。
- 当前 CGMF 文件两条 odd-A integer-J 异常：**COMPUTATION_VERIFIED**。
- RIPL-4 ¹⁰⁵Zr 的 1/2+#：**SOURCE_REPORTED / NON-EXPERIMENTAL FLAG PRESERVED**，不是 PROVED。
- RIPL-4 ⁸⁹Br 的 (3/2−,5/2−)：**SOURCE_REPORTED / AMBIGUOUS**。
- 十条事件 E1 候选筛查：**COMPUTATION_VERIFIED**（基于 RIPL-4 当前数值记录与保守边界）。
- CGMF RIPL-4 转换器的历史实现：**BLOCKED**（转换生成脚本未在当前仓库中定位）。
- 是否将 RIPL-4 数据导入生产：**NOT DONE**。
- Patch A/B/C：**NOT MERGED**。
- P/H/O：**BLOCKED**。
- 气论映射：**UNCHANGED**。
