# G2 本轮最小充分报告

## 本轮纠错

Run #43 的 `pu239-thermal-seed10` 并非独立种子组：实际 RNG audit 为 10–49，与默认组 1–200 重叠。旧流程只检查不同 `run_id`，因此错误地把它视作独立运行。本轮将独立性检查升级为实际 `rng-audit.tsv` 种子检查，并把下一次 CI 计划中的第三组改为 401–600、200 事件。

此前 M2 曾加入 TXE、TKE proxy、激发能不对称度等列，但它们都是 M1 原始输入的确定性变换。重复加入这些列会改变 ridge 正则化分配，不能把性能变化解释为能量预算特征增加。本轮改为只增加一个 `TXE×TKE_proxy` 非线性交互，并在训练集内先对 M1 做残差化；测试集仅使用训练集拟合的投影。

M1 也删除了由原始动量向量确定的动量模长和闭合量重复列；这些仍保留为诊断量。

## 现有数据复算

只使用实际种子互不重叠的 Run #43 两组：1–200 与 201–400，每组 200 个事件。双向留出，完整事件对 bootstrap 2,000 次。

| 训练 → 测试 | M0 | M1 | M2 | M3 |
|---|---:|---:|---:|---:|
| 1–200 → 201–400 | 0.9985 | 0.7730 | 0.7819 | 0.8103 |
| 201–400 → 1–200 | 1.0207 | 0.7762 | 0.7786 | 0.7885 |

指标为四项 HF 历史目标的平均训练标准差归一化 RMSE，越低越好。

- M1 相对 M0 两个方向都显著改善：记录到的初始共同状态包含较强预测信息。
- M2 相对 M1 没有改善：第一方向变差，第二方向近似无变化。
- M3 相对 M2 两个方向都变差：当前 LF 历史摘要未显示独立预测增益。

M2−M1 的 95% bootstrap CI：第一方向 `[0.00133, 0.01651]`，反向 `[-0.00349, 0.00789]`。M3−M2 的区间分别为 `[0.00942, 0.04732]`、`[0.00179, 0.01792]`。

事件级诊断：在 seed 201–400 测试集，TXE 均值/标准差为 `26.676 ± 7.621 MeV`，TKE 非相对论代理量为 `177.642 ± 8.827 MeV`，动量闭合范数为 `0.006895 MeV/c`（标准差约 `1.5×10⁻13 MeV/c`）。反向测试集对应 TXE `25.033 ± 7.079 MeV`、TKE 代理量 `178.831 ± 9.157 MeV`，闭合残差同样近乎常数。这个几乎恒定的闭合残差更像模拟记录的约束/数值精度特征，不能当成可用于区分事件的独立状态变量。

## 证据等级与边界

- 上述两组 Run #43 数据复算：`COMPUTATION_VERIFIED`。
- M1 初始状态预测信息：在当前线性 ridge 预测任务下得到支持，不等于跨碎片直接作用机制。
- TXE×TKE proxy 非线性交互：未得到稳定预测增益。
- LF 历史增量：当前摘要特征未得到独立预测增益。
- 独立种子方差：只有两组有效种子，仍不足以稳定估计。
- 第三组 401–600：已加入待运行矩阵配置，尚未实际模拟；不能写成已验证。
- Bai/Schuster 探测器响应前向投影：本轮未开展。

## 本批修改

新增实际 RNG audit 强制读取、训练/测试种子重叠拒绝、矩阵同条件种子区间预检、M0–M3 修订模型、双向种子留出工作流和对应单元测试。未提交、未 push；GitHub Actions 尚未验证本批新代码。


## Run #84：离散-only 起点投影审计

**审计范围：** Run #84 的 31 个 sidecar 场景、2,360 个事件、4,720 条碎片历史。逐条检查首跃迁父态为离散态的历史，共 **7 条，全部为 HF**；LF 为 0 条。结果只描述本次矩阵，不外推至所有 CGMF 输入。

### 源码规则（SOURCE_AUDITED）

- `statSetupEnergyBin()` 取最高离散能级 `elmax = lev[ndisc-1].energy`；仅当 `elmax < max_energy` 时建立 continuum bins。因此 `elmax >= U` 时进入 `ncont == 0` 的离散-only 分支。
- 离散-only 分支调用 `statStoreLevelExcite()`。该函数在 `i < ndisc-1` 的候选能级中，按 `abs(max_energy - lev[i].energy)` 选择最近能级；不施加能级能量必须不高于 U 的约束，也不检查初始 J/宇称匹配。
- `specMCMainFission()` 的该分支直接以该能级启动 `mcGammaCascade()`；传入的 `initJ/initP` 只在 continuum 分支的 `statSetupInitialPopulationSpec(initJ,initP,...)` 中使用。故离散-only 起点的输入自旋/宇称没有参与起点选择。

源码位置：
- `libcgmf/src/setup.cpp`：`statSetupEnergyBin()`
- `libcgmf/src/popinit.cpp`：`statStoreLevelExcite()`
- `libcgmf/src/specmc.cpp`：`specMCMainFission()`

### 七条实际记录（COMPUTATION_VERIFIED）

| 场景 / 事件 | 碎片核素 | 初始 U (MeV) | 选中能级 E (MeV) | E−U (MeV) | 选中能级 Jπ | U 以下最高列出能级 (MeV) |
|---|---|---:|---:|---:|---|---:|
| Pu-239 10 MeV / 175 | 132Sn | 4.908737 | 4.919000 | +0.010263 | 7+ | 4.885210 |
| Pu-239 热 / 51 | 131Sn | 4.666745 | 4.670210 | +0.003465 | 11.5− | 4.641400 |
| Pu-242 sf / 5 | 133Sb | 3.417045 | 3.822700 | +0.405655 | 1.5+ | 2.791540 |
| Pu-242 sf / 11 | 139Xe | 1.422623 | 1.418200 | −0.004423 | 6.5+ | 1.418200 |
| U-235 0.5 MeV / 12 | 131Te | 1.768275 | 1.755940 | −0.012335 | 2.5− | 1.755940 |
| U-235 热 / 12 | 131Te | 1.708658 | 1.721640 | +0.012982 | 2.5+ | 1.683010 |
| U-235 热 / 164 | 132Sn | 2.251398 | 4.041200 | +1.789802 | 2+ | 0.000000 |

七条均满足该数据文件下的 `elmax >= U` 条件，故与离散-only 分支一致。五条选中能级高于 U，两条低于 U。这个差值是“最近离散能级投影差”，不能直接称作级联内部能量不守恒；但若把 U 当作严格可用激发能，则正差值意味着该近似投影并非能量可达态。

此外，七条记录的选中能级 J 均与输入初始 J 不一致，其中两条的宇称也不一致；例如 133Sb 事件 5 输入 5.5−，选中 1.5+，而 U 以下最高列出的 2.791540 MeV 能级恰为 5.5−。这说明当前离散-only 起点选择不是守恒 Jπ 的状态映射。不得把这 7 条的起点自旋/宇称当作原始碎片自旋/宇称的忠实延续。

### 对 G2 证据链的影响

- 索引错位修复仍然成立；Run #84 的 7 条记录均按修正后的 0-based 起点索引执行。
- “首态父能高于初始 U”不应再单独标成级联能量账本异常；正确标签是 **离散-only 最近能级投影差**。
- 该分支对输入 Jπ 的忽略是独立的模型近似/信息丢失，且本矩阵 7 条全部发生在 HF。对依赖初始自旋、宇称或级联首态的条件分析，应单独标注或排除敏感性检验，不能将其当作未经变换的初始状态证据。
- 不在本轮把最近能级改成 floor/nearest-below，也不覆盖三份黄金文件。任何算法更改都需先定义剩余激发能如何表示，以及角动量/宇称如何映射，再建立单独的物理验收测试。



### 离散-only 事件对 M0–M3 竞争结果的敏感性（COMPUTATION_VERIFIED）

Pu-239 热中子 600 事件模型竞争数据中，7 条全矩阵离散-only 起点记录只有 1 条进入该 600 事件样本：event 51。按原脚本独立复算，三折 M0–M3 点估计与 Run #84 输出逐项一致；随后仅做诊断性排除 event 51（训练集剔除或测试集剔除，依所在折而定），不改变特征、ridge、划分或 bootstrap 方案。

| 折（训练 / 测试） | 排除后 n | M0 | M1 | M2 | M3 |
|---|---:|---:|---:|---:|---:|
| 1–400 / 401–600 | 398 / 200 | 1.015713 | 0.722595 | 0.720846 | 0.722698 |
| 1–200 + 401–600 / 201–400 | 398 / 200 | 0.985784 | 0.732869 | 0.734125 | 0.737766 |
| 201–600 / 1–200 | 400 / 199 | 1.004717 | 0.740641 | 0.741167 | 0.748761 |

排除 event 51 后的配对事件 bootstrap（2,000 次）：

| 折 | M1−M0 | M2−M1 | M3−M2 |
|---|---|---|---|
| 1 | −0.293118 [−0.345840, −0.240407] | −0.001748 [−0.003602, +0.000305] | +0.001852 [−0.006525, +0.011173] |
| 2 | −0.252915 [−0.304814, −0.193713] | +0.001256 [−0.002770, +0.005481] | +0.003642 [−0.006006, +0.012321] |
| 3 | −0.264076 [−0.313281, −0.212916] | +0.000527 [−0.003384, +0.004344] | +0.007593 [+0.001312, +0.014190] |

结论：去掉这条离散-only HF 级联样本后，M1 相对 M0 的预测增益仍稳定；M2 的增量仍未形成跨折稳定改善；M3 的增量仍不稳定（第三折改善，但前两折区间跨零）。因此，当前 M0–M3 结论不是由该单一离散-only 投影样本驱动。此敏感性检验只针对 Pu-239 热中子 600 事件模型竞争样本，不代表对全矩阵其他 6 条离散-only 记录的排除分析。


## 三种离散起点映射方案对照（COMPUTATION_VERIFIED）

### 数据与算法口径

裂变事件路径 `specMCMainFission()` 调用 `getDiscreteLevels()`，其离散能级来自 CGMF 预处理的离散能级数据库（`readDiscreteLevelData()` 读取 `DISCRETEDATA`；`getDiscreteLevels()` 将对应核素能级复制到 `ncl`）。这不是独立调用 `getRiplDiscreteLevels()` 的单核谱计算路径。下表按仓库 `data/discreteLevels.dat` 的实际固定宽度字段解析：能量、物理自旋、宇称和跃迁分支数；并严格复现 `statStoreLevelExcite()` 的候选池 `i < ndisc-1`，不擅自把最后一个能级加入候选。

初始 `spin_stored` 的物理语义由 `FissionFragments::computeFragmentInitialConditions()` 与 `getInitialSpin()` 确认：它是抽样得到的物理 (J)（奇质量核加半整数偏移），`parity_index` 是抽样的初始宇称 (+1/-1)。它不是离散态数组索引。

三种方案均只作离线映射诊断，本轮没有修改 CGMF 物理算法，也没有生成新的级联历史：

- **A 当前最近能级：** 在 CGMF 当前候选池中最小化 (|E_i-U|)，不约束 (E_ile U)，也不约束 (J^pi)。
- **B 能量可达候选：** 只在 (E_ile U) 的候选中选择最高能级；不保证 (J^pi)。
- **C 能量 + (J^pi)：** 只在 (E_ile U)、且表中物理 (J_i=J_0)、(pi_i=pi_0) 的候选中选择最高能级；没有候选就标记 unmappable，不放宽条件。

### 七条事件逐条结果

单位均为 MeV。表中 B/C 的“剩余能量”是 (U-E_i)，只是尚未映射到离散能级的账面差额；不能把它自动解释为已实现的连续态或可直接释放的粒子能量。

| 事件 | 核素 | 初始 (U,J^pi) | A 当前最近能级 (E,J^pi) | B 最高可达能级 (E,J^pi) | C 最高可达同 (J^pi) 能级 |
|---|---|---|---|---|---|
| Pu-239 热 / 51 HF | 131Sn | 4.666745, 3.5− | 4.670210, 11.5− | 4.641400, 8.5+ | 无（唯一同 (J^pi) 候选 4.770700 高于 U） |
| U-235 0.5 MeV / 12 HF | 131Te | 1.768275, 4.5+ | 1.755940, 2.5− | 1.755940, 2.5− | 0.776900, 4.5+ |
| Pu-242 sf / 5 HF | 133Sb | 3.417045, 5.5− | 3.822700, 1.5+ | 2.791540, 5.5− | 2.791540, 5.5− |
| Pu-242 sf / 11 HF | 139Xe | 1.422623, 7.5+ | 1.418200, 6.5+ | 1.418200, 6.5+ | 无（候选池中无同 (J^pi) 能级） |
| U-235 热 / 12 HF | 131Te | 1.708658, 4.5+ | 1.721640, 2.5+ | 1.683010, 2.5+ | 0.776900, 4.5+ |
| U-235 热 / 164 HF | 132Sn | 2.251398, 17+ | 4.041200, 2+ | 0.000000, 0+ | 无（候选池中无同 (J^pi) 能级） |
| Pu-239 10 MeV / 175 HF | 132Sn | 4.908737, 9+ | 4.919000, 7+ | 4.885210, 5+ | 无（候选池中无同 (J^pi) 能级） |

汇总：

- A：7/7 可映射；5/7 选中能级高于 U；7/7 的物理 J 与输入 J 不同；2/7 的宇称也不同。
- B：7/7 可映射且 (E_ile U)，但 6/7 仍不保留 J，2/7 不保留宇称。未映射能量差额 (U-E_i) 范围为 0.004423–2.251398 MeV。
- C：只有 3/7 有表内同 (J^pi) 且 (E_ile U) 的候选；另 4/7 必须标记 unmappable。三个可映射事件的剩余差额分别为 0.991375、0.625505、0.931758 MeV。

**解释边界：** C 的 4/7 无候选，只能说明在当前 CGMF 离散能级表和当前候选池中找不到严格同 (J^pi) 的可达离散态；不能推断真实核素不存在这种态。离散数据库可能不完备，初始碎片的 (J^pi) 是统计抽样标签，而不是已观测的具体核能级。B/C 的剩余能量也不能无定义地“丢掉”。因此目前没有依据把 A 直接替换为 B 或 C；正确的算法升级需要一个明确的未映射能量/连续态表示，并定义角动量、宇称如何在该表示中保留。

### 对 matched conditional LF/HF 残差分析的影响（COMPUTATION_VERIFIED）

对 Run #84 三个 matched-history 数据集，按原脚本算法复算，固定随机种子 20261119，并把符号翻转置换从 CI 的 250 次增加到 5,000 次。首先，未排除任何事件时，5,000 次复算的点统计量与原 JSON 文件逐项一致；250 次旧 p 值因蒙特卡洛分辨率较粗，不再作为本次敏感性比较的精度口径。

再排除在相应数据集中出现的离散-only HF 事件：Pu-239 热中子排除 event 51；U-235 热中子排除 events 12、164；Cf-252 无对应离散-only 事件，作为对照。

| 数据集 / 排除 | caliper 1.5：匹配对数；统计量；p | caliper 2.5：匹配对数；统计量；p |
|---|---|---|
| Cf-252 sf / 无 | 49；6.429686；0.01480 | 53；6.369274；0.00460 |
| Pu-239 热 / 无 | 44；6.636577；0.03399 | 48；5.638847；0.05879 |
| Pu-239 热 / 排除 51 | 43；6.695490；0.03479 | 47；5.682935；0.06359 |
| U-235 热 / 无 | 45；8.591002；0.02959 | 57；9.215706；0.00420 |
| U-235 热 / 排除 12、164 | 45；8.591002；0.02819 | 57；9.215706；0.00280 |

解释：

1. Pu-239 event 51 确实进入原匹配集合；排除后两个 caliper 的匹配对数各减少 1，统计量和 p 值略变，但没有改变“存在探索性残差关联、不能据此证明直接跨碎片作用”的判断。
2. U-235 events 12、164 本身没有进入最终匹配事件集合；排除后匹配对数与观测统计量不变。由于匹配标准化与贪心配对在全样本上重算，配对组合/有限次置换估计仍有小幅变化，但没有改变结论。
3. 将 Cf-252、Pu-239、U-235 的两个 caliper 共六个 p 值作为一个检验族作 Holm 校正，排除事件后的调整值约为：Cf-252 1.5 = 0.05919、Cf-252 2.5 = 0.02300、Pu-239 1.5/2.5 = 0.08458、U-235 1.5 = 0.08458、U-235 2.5 = 0.01680。只有 Cf-252 与 U-235 的 2.5 caliper 仍低于 0.05；这些仍是探索性匹配分析，不是预注册的直接机制检验。
4. 本项 5,000 次置换是对已有 Run #84 侧车数据的离线重分析；未重跑物理模拟，未生成新 sidecar，也未改变 P/H/O 或 C2 状态。

**本轮结论：** 离散-only 起点投影确实是需要控制的状态映射误差源，但排除已识别的 3 条相关事件后，现有 G2 matched residual association 没有整体消失，也没有升级为直接跨碎片机制证据。M1–M3 的主结论仍以此前 Run #84 及其 event 51 排除敏感性分析为准。


### 对“直接改走 continuum 分支”的源码排除（SOURCE_AUDITED）

本轮继续检查了 `specMCMainFission()` 的另一条路径，避免把“保留初始 (J^pi)”误当成只需绕开离散-only 分支：

- continuum 分支确实调用 `statSetupInitialPopulationSpec(initJ,initP,...)`，将初始物理 (J^pi) 放入顶端能量 bin。
- 但 `mcHistoryLoop()` 每一步调用 `mcRestorePopulation()`，后者重新执行 `statSetupEnergyBin()` 并清空/重建能量网格；当 `ncont=0` 时没有可用的 continuum-to-continuum bins，离散布居 `lpop` 也没有由该路径建立。
- `mcFindNext()` 在没有可采样转移时进入强制离散态回退：优先按注释中的 E1 条件（宇称反转、(|Delta J|<2)、三角条件）挑选，但候选循环没有 (E_ile U) 过滤；若没有 E1 候选，则退化为只按最近 J 选择，同样没有能量可达约束。

因此，简单地让这 7 条记录改走 continuum 分支，并不能构成合格修复：它可能保留初始 (J^pi) 作为顶端 bin 标签，却仍可能选择能量高于当前状态的离散终态，甚至触发只按 J 的回退。不能把该路径直接作为方案 C 的实现。

**下一项源码任务应先定义并测试“未解析初始态 ((U,J^pi)) → 可达离散态”的桥接核：**候选终态必须满足能量可达；转移必须满足所选电磁多极性的角动量/宇称规则；如果没有候选，必须保留为未映射状态并报告失败，不能静默退化到 nearest-J。桥接核的转移概率/剩余能量去向需要有物理依据，不能为通过测试临时补参数。该核完成前，最近能级规则保持现状并明确标注近似。


## Run #95：原生回归基准差异归因与严格重基准（COMPUTATION_VERIFIED）

Run #95（commit `0590629244853c57c4e9c1d0f821046b524b9369`）的 CMake Configure、C++ Build、原生模拟执行、全部 G2 分析单测及 31 场景 G2 矩阵均通过。最终失败仅来自三个 serial history 文件与旧基准的逐字节比较。

下载并检查 Run #95 原生输出后，将每个 40-event serial 文件按 20 个 event（每个 event 两条 fragment header）切分为 rank 0 / rank 1 对照：

| 用例 | 新 serial 输出 SHA-256 | 新 rank 0 SHA-256 | rank 1 与旧基准 |
|---|---|---|---|
| Pu-242 sf | `bfa266d2d13dec98ed2dc1d425fee94ff691e1f3b162e6075db68c9918c65402` | `d49d9157c3fb5bd4088e4ff02adf7b7a595eeaf05bd6a22cae96d7c40cebddc7` | 完全一致 |
| U-235 thermal | `2b504cc64d3170fb2736c5c29e0a9119b72c53a6fef21a5689211f2a8f926a5a` | `5a39d3f29c2645c854167c7f47204a77839992ed35b67c79a137fc2aab691972` | 完全一致 |
| U-235 thermal + time window | `7fc4f1d6742df234275b0094dfc92d872ba373f9c366352b99ca97209458fdbd` | `e168064ab1c2ef8d02dea8a4a082d0211ff76996b64bb8ca92dbf5a914a2feda` | 完全一致 |

旧 rank 1 Git blob SHA 分别为 `511c9ba82b8230cb65379f9e5c3ea3efa1e23436`、`3b4c9e1ad091ae96e3e241ba37579c2184ce27cc`、`1e578d6763972081060001c52022295f884e3097`，与 Run #95 serial 输出后半段切片计算出的 Git blob SHA 逐一相同。变化全部集中在前三个用例的前 20 个 event（rank 0），不是随机波动或 rank 1 漂移。

因此，这三项旧 rank 0 golden 已被 1-based → 0-based 离散起点修复后的确定性输出取代。为避免把整份输出复制进 CMake，改用 CMake 原生 `file(SHA256)` 对 serial 全文件和 MPI rank 0 文件执行严格 SHA-256 回归；MPI rank 1 继续与原始 golden 逐字节比较。旧 rank 0 reference 文件保留作历史溯源，不再作为修复后输出的验收值。其余原生测试及 golden 不变。

这不是放宽门禁：serial、MPI rank 0 仍然要求完整输出字节级相同（SHA-256）；MPI rank 1 仍逐字节比较。Run #95 原始输出 artifact：`cgmf-native-regression-outputs`，artifact ID `14550306265`。


### 严格重基准实现状态（2026-11-20）

已将 Run #95 的审定输出摘要落实为 CTest 检查：新增 `checkHistorySha256.cmake`，对 Pu-242 sf、U-235 thermal、U-235 thermal+time 三个受影响用例分别校验 serial 全文件 SHA-256 与 MPI rank 0 SHA-256；MPI rank 1 继续逐字节对照原始 reference。三份旧 rank 0 reference 未删除，保留溯源。该实现没有使用 `continue-on-error` 绕过差异，也没有改变其余用例的 golden。

**验证状态必须分开记录：** Run #95 验证的是旧 CTest 逐字节比较，故其最终失败不能算新 SHA-256 门禁通过；新门禁已进入当前工作分支源码，但仍需由该分支的新 CI 运行验证 Configure、Build、96 项原生测试与 G2 矩阵。新 CI 通过前，不标记为 CI 已修复完成。


## Run #96 后续源码审计：离散终态回退（SOURCE_AUDIT_VERIFIED）

复查当前分支 `libcgmf/src/specmc.cpp` 的 `mcHistoryLoop()` 与 `mcFindNext()`，确认存在两处独立的强制离散终态回退：

1. `mcFindNext()` 在连续/离散布居累计概率未命中时，先按 E1 形式条件（异宇称、\(|\Delta J|<2\)、三角条件）扫描全部离散能级；若无候选，再按最近 J 选择。
2. `mcHistoryLoop()` 在 `CONTINUUM_LOWER_CUT` 触发时另有一套几乎相同的 E1 扫描与 nearest-J 回退。

两处扫描都未过滤候选能级是否满足 &nbsp;\(E_f\le E_i\)。因此即使只修正 `mcFindNext()`，第二条 lower-cut 路径仍可能选到能量不可达终态；反之亦然。并且当前实现把 E1 条件写死为唯一优先规则，失败后又允许违反该规则的 nearest-J 选择。当前代码没有在这些强制回退处返回显式的不可映射状态。

**实现决策：暂不直接修改物理选择逻辑。** 先将两条路径统一到一个纯候选筛选函数，并为其建立独立单元测试；候选筛选至少必须满足能量可达性与明确指定的多极性规则。若现有 level 数据没有给出足够的跃迁多极性/分支信息，则不能假装已知转移概率；应返回结构化的 `UNMAPPABLE`，并由调用层显式处理，禁止 nearest-J 静默兜底。还需检查 `MCPoint` 的无效状态表达和 `mcHistoryLoop()` 对终止状态的处理，避免返回无候选后访问 `lev[-1]`。

**测试矩阵：** (a) 终态能量高于初态必须拒绝；(b) 能量可达且 E1 角动量/宇称允许才可列入 E1 候选；(c) 同宇称/禁戒 \(\Delta J\) 必须拒绝；(d) 空候选返回 `UNMAPPABLE`；(e) lower-cut 与常规无转移两条入口调用同一筛选逻辑；(f) 无效状态不得写入历史或访问能级数组。当前只完成源码审计与测试规格，尚未修改物理算法，也未声称桥接核完成。

CI 状态：GitHub Actions 工具当前未返回新 SHA-256 门禁提交对应的 workflow run（提交关联查询只返回 PR 触发运行，且本次没有可用的 run ID）。因此新门禁仍标记为待 CI 验证；不能把源代码存在等同于测试已通过。



## Run #97：桥接核接口可实现性审计（SOURCE_AUDIT_VERIFIED）

本轮检查了 `libcgmf/include/mchf.h`、`libcgmf/include/structur.h`、`libcgmf/include/cgm.h`，并回看当前分支 `libcgmf/src/specmc.cpp` 两条强制离散回退路径。

### 1. MCPoint 当前不能表达 UNMAPPABLE

`MCPoint` 只有 `n,p,j,k,e,l` 六个字段；`l` 仅表示是否离散态。默认构造将其初始化为普通非离散状态 `(0,0,0,0,0,false))，没有终止/失败状态，也没有合法性谓词。当前 `mcHistoryLoop()` 在 `mcFindNext()` 返回后会执行 `mcStoreHistory()`、赋值 `mcurr=mnext`，随后仅用 `ifDiscrete()` 判断是否结束；循环结束后又可能以 `mnext.getK()` 作为 `lev[]` 索引调用 `mcGammaCascade()`。因此把“无候选”编码成 `k=-1` 或默认 MCPoint 都不安全，可能把失败状态写入 history，或导致无效索引访问。

### 2. Level 数据没有桥接跃迁所需的多极性标签

`Level` 结构目前只有能量、自旋、宇称、寿命、`fstate`、`branch`、`gratio`；没有每条跃迁的 E/M 类型或多极阶数。数据库中已知的离散能级跃迁分支，记录的是已列出能级之间的终态索引与分支/内转换信息；它并不提供“未解析初态 (U,Jπ) 到某个离散能级”的多极性或跃迁概率。

`cgm.h` 虽定义 `GammaMultipol {E1,M1,E2}`，但这只是模型中可用的多极类别，不会自动给某个未解析初态—离散终态配对提供实际多极性或分支概率。不能把候选符合 E1、M1 或 E2 中任一选择定则，误当成已知该转移实际发生，更不能据此均匀抽样或临时添加概率参数。

### 3. 现有两条回退的安全性结论

- `mcFindNext()` 常规无转移回退和 `mcHistoryLoop()` 的 lower-cut 回退是两条独立入口，必须共用同一个候选/结果接口。
- 仅增加能量过滤仍不充分：空候选时必须有明确状态传播路径，不能返回默认 `MCPoint` 或 `k=-1` 后继续写 history。
- 仅增加 E1/M1/E2 选择定则也不充分：当前数据无法确定实际多极性及其相对跃迁权重。
- 因而本轮不把“允许多极性集合”转化为物理抽样分布，也不把 E1 作为唯一桥接机制。当前数据库支持的是对已知离散能级间分支的使用，不足以定义未解析初态的桥接核。

### 4. 当前可执行的最小安全设计

将桥接接口拆为两个彼此独立的层次，避免把“筛选合法候选”误当成“知道如何抽样”：

1. **纯筛选层（可单测）：** 输入明确给定的初态能量、自旋、宇称，以及每个候选的终态能量、自旋、宇称和一个明确指定的电磁多极性；检查能量可达性与该多极性的角动量/宇称选择定则。该函数只返回候选集合，不产生概率、不抽样。
2. **物理赋权层（当前 BLOCKED）：** 只有在来源提供实际多极性/分支强度，或理论推导出可审查的权重后，才允许把候选集合变成转移分布。缺少权重时返回 `UNMAPPABLE`，不做均匀抽样、不退化 nearest-J。

但要将 `UNMAPPABLE` 安全传出 `mcHistoryLoop()`，还需要新增显式结果类型/状态，并审计所有消费 `MCPoint` 的路径（history、谱累计、最终态写入、fission event 输出）；不能只给 `MCPoint` 增加一个布尔量就认为全链安全。此项涉及模拟失败/部分事件的输出契约，应先形成独立接口改动和测试，再接入物理主循环。

### 本轮裁决

**桥接核物理赋权：BLOCKED；纯筛选规则：可独立实现与单测；UNMAPPABLE 端到端传播：接口设计待完成。** 本轮没有修改模拟算法、没有改变历史输出、没有生成新物理事件，也没有把 Run #84 数据升级为桥接核证据。继续实施前，先完成调用链状态传播设计和测试夹具；在缺少实际多极性/权重证据时，最多交付纯候选筛选器，不接入随机抽样。



## Run #98：纯电磁多极性筛选器与单元测试（COMPUTATION_VERIFIED）

在不推断实际跃迁多极性、不添加转移概率的前提下，已增加独立纯函数 `libcgmf/include/gamma_transition_selection.h`，以及 CTest 用例 `utils/cgmf/tests/gamma-transition-selection.cpp`，并注册到 `utils/cgmf/tests/CMakeLists.txt`。

函数输入显式初态/终态能量、自旋、宇称，以及调用方明确指定的多极性 E1/M1/E2；仅返回该配对是否满足：
- 正的光子能量（严格要求 (E_f<E_i)）；
- 自旋三角条件 (|J_i-J_f|\le L\le J_i+J_f)；
- 电/磁多极性对应的宇称关系：E(L) 为 ((-1)^L)，M(L) 为 ((-1)^{L+1})；
- 输入为有限数值、非负能量/自旋，宇称标签为 ±1。

单测覆盖 E1/M1/E2 的允许与禁戒情形、能量不可达、角动量三角条件、(0\to0) 禁戒、无效宇称/负自旋及 NaN 输入。使用 C++14、`-Wall -Wextra -Werror -pedantic` 在本地独立编译并执行该测试程序，结果 PASS（COMPUTATION_VERIFIED）。

**适用边界：**
1. 该函数是显式给定多极性后的 selection-rule predicate，不会从 `Level` 数据推断多极性。
2. 它不返回候选概率、不抽样、不声称 E1/M1/E2 哪一种实际发生。
3. 当前 `Level` 结构仍没有逐分支多极性标签，故该函数尚未接入 `mcFindNext()` 或 lower-cut 回退。两处仍维持原逻辑，直到实际多极性/赋权依据与 `UNMAPPABLE` 端到端状态传播契约完成。
4. 这次单测的本地编译通过不等于仓库完整 CMake/CI 通过；需要新 CI 对该测试目标及原有 96 项 native tests、G2 matrix 一并验证。

相关提交：
- 纯筛选头文件：`5c3dfc3a283d2441a59f016519bb70cd8e85d450`
- 测试与 CMake 注册：`e14bcd96a2891ae601dd762790f504e2d1c37a7f`、`8745df3e3209169a481c4069493c163add568407`、`27f4c5cd2390c65aa0719be562745c8b8fee739a`
- 非有限输入保护与补充测试：`b4f9d80aed5d0e2a7792e29e78294840b2d7dce9`、`fb55229cc669c7ffea5b2108925b8c991a24d711`

本轮没有改变模拟算法或生成新事件。物理桥接核仍为 BLOCKED；当前只交付可独立验证的候选筛选基础函数。



## Run #99：MCPoint 显式状态与级联失败保护（SOURCE_AUDITED + IMPLEMENTED；CI PENDING）

### 1. MCPoint 状态类型

在 `libcgmf/include/mchf.h` 中新增：

- `Uninitialized`：默认构造、尚未赋予有效状态；
- `Valid`：由构造函数或 `set()` 明确赋值；
- `Unmappable`：调用方明确标记为无法映射。

提供 `isValid()`、`isUnmappable()`、`getStatus()`、`markUnmappable()`。重新调用 `set()` 会恢复为 Valid 并清除离散态标记。该状态随 MCPoint 拷贝进入 MCHistory，不需要使用 `k=-1` 伪装失败状态。

### 2. 主循环保护

在 `libcgmf/src/specmc.cpp` 中：
- `mcHistoryLoop()` 在接收 `mcFindNext()` 返回值后、任何扰动或 history 写入前检查状态；非 Valid 立即通过现有 `cgmTerminateCode()` 以非零退出，避免继续记录伪造事件。
- lower-cut 回退在访问最高离散能级前检查 `ndisc>0`；回退候选索引在解引用前检查范围，失败则标记 Unmappable。
- `mcFindNext()` 在离散能级表为空时返回 Unmappable；最近 J 回退的索引也在解引用前做范围检查。
- 级联返回的最终离散态索引在写入终态前检查范围。

**失败语义：** 当前 `cgmTerminateCode()` 会释放全局存储并 `exit(-1))，所以这里采用 fail-fast，而不是跳过单个碎片后继续运行。若 LF 已经写出 sidecar 而 HF 随后失败，文件可能留下不完整事件对；该运行必须按失败处理，不能把已有片段当成完整数据。现有 LF/HF 覆盖验证器是识别不完整输出的下游门禁。若未来要求逐事件跳过并继续模拟，必须另行实现事件级事务/回滚和明确的事件失败输出契约。

### 3. 测试与 CI 修复

新增 `mcpoint-status` CTest，覆盖默认 Uninitialized、Valid、离散标记、Unmappable、拷贝传播、MCHistory 保存状态及重新 set 恢复 Valid。

Run #125（workflow run ID `44576007076`）曾在 Configure 阶段失败。日志确认原因不是 C++ 编译，而是两个测试 CMakeLists 位于子目录，却引用了父目录的源文件名，导致找不到：
- `gamma-transition-selection.cpp`
- `mcpoint-status.cpp`

已将两个目标源路径分别修正为 `../gamma-transition-selection.cpp` 和 `../mcpoint-status.cpp`。该修正后的提交尚未取得新 CI 运行结果；不得把 Run #125 记为代码测试失败或通过，它只验证了错误的 CMake 源文件路径配置。

### 4. 当前边界

- 已实现 MCPoint 显式状态表示和无效索引保护。
- 仍未把“没有物理上有依据的桥接多极性/权重”转化为真实候选选择逻辑；当前 `mcFindNext()` 与 lower-cut 的历史 E1/nearest-J 选择行为仍在。新增状态检查不会自动解决其物理近似。
- 物理桥接核及赋权仍为 BLOCKED。
- 需要新 CI 先通过 Configure/Build、MCPoint 状态测试、selection-rule 测试、原生回归和 G2 矩阵；随后才进行两条回退入口的统一候选接口接线。

本轮未修改黄金文件、未改变跃迁抽样分布、未生成新物理事件。


### Run #100：状态接口 CI 编译诊断（2026-11-20）

Run #138（ID `44576738737`）已通过 CMake Configure；Build 阶段失败。日志唯一首要编译错误定位到 `mchf.h:22`：状态枚举声明意外成为 `enum enum class MCPointStatus`。已修正为 `enum class MCPointStatus`（提交 `3767e7fd5f3c0b7e7f7996343c1f9e7789f90a1a`）。因此 Run #138 不能算作构建通过；它验证了测试源文件路径修正有效，并暴露了枚举声明语法错误。修正后的构建仍待新 CI 验证。


## Run #101：统一 E1 可达离散桥接候选入口（IMPLEMENTED；CI IN PROGRESS）

### 1. 自旋索引口径审计

检查 `popinit.cpp`：
- 连续态数组的 `pop[k][j]` 中，`j` 是离散数组索引；
- 自旋分布明确使用 `J = j + halfint(lev[0].spin)`；
- `statPopinitSingle()` 通过 `j == (int)j0` 把物理初始自旋落入该索引。

因此，回退路径原先直接比较 `lev[k].spin` 与 `MCPoint.getJ()` 是不一致的：前者是物理自旋，后者在连续态路径是自旋数组索引。新增桥接候选函数先按核素首个离散态的整数/半整数偏移，将索引恢复为物理 (J_i)。

### 2. 两处回退统一

`specmc.cpp` 新增 `mcSelectE1DiscreteBridge()`，两条入口都调用它：
- `mcFindNext()` 的无转移强制离散回退；
- `mcHistoryLoop()` 的 continuum lower-cut 回退。

该函数复用已加入的纯选择定则函数，按明确的 E1 条件过滤：
- (E_f<E_i)；
- (|J_i-J_f|\le1\le J_i+J_f)；
- 初末宇称相反。

若没有候选，返回 -1，由调用点将状态标记为 `Unmappable`；已删除 nearest-J 兜底。候选集内仍沿用旧实现的等候选随机抽取方式（每个合格候选一次 RNG 抽样后取最大值），没有新增概率参数。

### 3. 物理解释边界

此修改仅把原代码已经明确写出的“E1-only fallback”变成一致的可达候选筛选，并修正连续态自旋索引与物理 (J) 的比较口径。它**不证明真实未解析态桥接必然是 E1**，也不声称现有等候选抽样具有核结构理论依据。缺少实际多极性/分支强度时，桥接核赋权仍为 BLOCKED；无 E1 候选即显式失败，而不是制造一个 nearest-J 转移。

### 4. 回归状态

代码提交 `0ccd1dab9a0e2a174fb47b3b30d52d8f2d1b7b27` 完成两处统一；随后移除一个无用候选计数变量，最新代码文件提交 `163bddaa57da15211acc84570c2871433e15280f`。CI Run #146（ID `44582671415`）已触发，目前正在执行；在结果完成前不标记编译、原生回归或 G2 matrix 通过。

本轮没有修改黄金文件，没有引入桥接概率参数。模拟路径发生了有意的筛选行为变化（加入能量可达条件并移除 nearest-J 回退），必须以 CI 和后续事件分布审计验证其影响。


## Run #102：E1 桥接诊断结果与物理阻断确认（COMPUTATION_VERIFIED + SOURCE_AUDITED）

### CI 结果

Run #151（workflow run ID `44586698377`，commit `3d8c45a7a119a43795c0c630fba35f3abddf575d`）：
- CMake Configure、C++ Build：PASS。
- 原生 CTest：98 项中 74 项通过；12 项执行测试失败，另有 12 项依赖测试因前置执行失败而未运行。两个新增独立测试 `gamma-transition-selection` 与 `mcpoint-status` 均 PASS。
- G2 分析单元测试、种子区间验证：均 PASS。
- 完整 G2 sidecar matrix：失败；模拟进程以 255 退出。
- 最终 workflow 失败。native golden enforcement 也失败，但不能把它与前述模拟路径失败混为一类；旧 golden 未被覆盖。

### 桥接失败诊断

从 Run #151 job log 提取到 12 条 `[MC bridge diagnostic]`：
- 11 条因角动量三角条件不满足而无 E1 候选；
- 1 条因宇称选择定则不满足；
- 0 条由能量条件拒绝；
- 0 条无离散能级；
- 12 条均为 `ndisc=1`。

入口分布：lower-cut 10 条，mc_find_next 2 条。涉及核素：53-136（3）、53-137（2）、41-105、39-96、40-105（2）、52-138、53-132、35-89。

代表性记录包括：
- HF ^{136}I，event 6：初态能量 0.0793033 MeV、物理自旋 7、宇称 +1，唯一离散候选因角动量条件被拒；
- HF ^{136}I，event 2：初态能量 0.0205397 MeV、自旋 3、宇称 −1，唯一候选因角动量条件被拒；
- LF ^{89}Br，event 34：初态能量 0.0232161 MeV、自旋 3、宇称 +1，唯一候选因宇称条件被拒。

这些是程序筛选诊断，不是实验观测，也不说明真实核跃迁不存在；`ndisc=1` 只表示当前 CGMF 离散能级表中仅有一个可用离散态。

### 机制解释边界

回查基线 `83ea71c` 的旧代码，两处回退本来就是“先按 E1 条件选候选，若没有则 nearest-J 强制选态”。当前严格实现删除了第二步，因此把旧代码原先隐藏的近似强制映射暴露为显式失败。Run #151 的诊断说明失败主因是候选态稀少且 E1 角动量条件不满足，不是能量过滤，也不是数组越界。

但不能据此直接增加 M1/E2 或更高多极性：当前 `Level` 数据没有为未解析初态到离散态的桥接提供实际多极性和分支强度。允许某一多极性也不等于知道真实转移发生，更不能均匀抽样补出概率。旧 nearest-J 回退同样不是有物理依据的替代方案。

### 后续决策

1. 暂不恢复 nearest-J，暂不把 M1/E2/高阶多极性加入随机选择。
2. 把“未解析初态到离散能级”的物理赋权继续标为 BLOCKED；E1 纯筛选器仅是数学选择定则测试，不是桥接核。
3. 下一项工程工作应设计事件级失败契约：将无法映射的 fragment/event 明确标记为不完整，不得输出成完整 LF/HF 配对；下游 validator 必须拒绝不完整事件。当前 `cgmTerminateCode()` 会终止整个进程，尚未实现事件级跳过、回滚或失败记录。
4. 在事件级失败契约和覆盖率报告实现前，不使用本轮失败运行生成的部分 sidecar 做 M0–M3、匹配残差或 P/H/O 竞争分析。

**结论：** Run #151 已验证诊断代码可编译并在原生测试中运行。当前阻断是离散能级数据/桥接物理赋权不足以支持所有强制映射，不是可通过放宽筛选条件来安全修复的普通软件缺陷。G2 新数据矩阵仍未获得有效完整数据。


## Run #103：LF/HF 事件写入生命周期审计

### 已核实的源码事实

- `cgmfEvents.cpp` 对每个 G2 事件先设置 `(event_id, LF)` 并调用 `specMCMainFission(&eventLF)`，随后设置同一 `event_id` 的 `HF` 并调用 `specMCMainFission(&eventHF)`。两侧顺序固定为 LF→HF。
- 两次调用最终都进入 `recordEmittedParticlesFission(fe)`。中子 sidecar 在该函数内逐碎片构造 JSONL，并立即以 append 模式写入、`flush()`；LF 成功写入后，HF 尚未开始。
- 混合历史 sidecar 同样在每次 `recordEmittedParticlesFission` 内逐碎片 append/flush；每个碎片一条摘要，即使该侧没有中子也会写一条混合历史记录。
- 因此，Run #151 在 LF 已成功、HF 桥接失败时，确实可能留下 LF 单侧记录。此结论由调用顺序和写入位置直接支持，不只是根据失败日志推断。
- `testG2MixedHistory.py` 已要求每个预期事件都恰有 LF、HF 两条混合历史摘要；它能拒绝不完整事件，但这是事后拒绝，不会阻止不完整记录先落盘。`testG2Sidecar.py` 单独验证中子记录的键、连续索引和运动学一致性；不应单独把“出现某事件的 neutron row”当作完整事件证据。

### 最小安全修正设计（尚未实现）

1. 在进程内为当前唯一活动事件暂存 LF 中子 JSONL 与 LF 混合历史 JSONL，不打开输出文件。
2. HF 完成并通过两类记录的内部一致性检查后，将对应 LF+HF payload 分别一次性 append 到各自文件；HF 无中子时，中子 payload 可为空，但混合历史仍必须包含 HF 摘要。
3. 事件 ID 不匹配、缺少 LF 暂存、重复 LF/HF 或写入失败均应 fail closed；不得自动覆盖旧暂存或补造记录。
4. 目前 `cgmTerminateCode()` 直接终止进程，故本修正只建立“成对落盘”边界，不宣称实现事件级恢复/跳过。物理桥接失败仍终止本次模拟；尚未提交的 LF 暂存随进程退出而丢弃。
5. 两个输出文件之间无法通过普通文件 append 获得跨文件事务原子性。每个文件内的 LF+HF payload 可合并为单次写入；若任一文件写入失败，整次 run 仍标记失败，不能进入分析。后续仍由 mixed-history validator 检查每个 event_id 的 LF/HF 覆盖。

### 状态

- 源码生命周期审计：**COMPUTATION/ SOURCE-VERIFIED（静态源码路径核验）**，不是运行验证。
- LF 单侧落盘风险：**SOURCE-VERIFIED**。
- 成对暂存/提交机制：**PROPOSED，未实现、未测试**。
- Run #151 输出及其所有不完整事件：仍不可用于 M0–M3 或 P/H/O。


## Run #104：LF/HF sidecar 成对暂存实现与测试加固（SOURCE_AUDITED + IMPLEMENTED；完整 CI 未通过）

### 实现核对

当前分支已加入 `G2SidecarEventBuffer`（`libcgmf/include/g2_sidecar_transaction.h`），并在 `specmc.cpp` 的 `recordEmittedParticlesFission()` 中统一暂存中子 sidecar 与 mixed-history sidecar：

1. LF 记录只进入内存缓冲区，不立即打开输出文件。
2. 同一 event_id 的 HF 到达后，缓冲器返回 Complete。
3. 每个输出文件分别将 LF+HF payload 合并为一次 append/write/flush；中子 payload 为空时不写空行，mixed-history 仍保留两侧摘要。
4. HF 先到、event_id 错配、重复 LF/HF、未知 side 等序列 fail closed；不会覆盖活动缓冲。
5. `cgmTerminateCode()` 仍然是进程级退出。该机制只建立 sidecar 的成对提交边界，不实现事件跳过或恢复。

### 新发现并修复的测试缺陷

原 `g2-sidecar-transaction.cpp` 使用标准 `assert()`。顶层 CMake 默认构建类型为 Release，通常定义 `NDEBUG`，因此这些断言可能被编译掉；CTest 显示 PASS 并不能证明配对逻辑断言实际执行。

已在提交 `968c7c48f17982bf66822e14acfc16600070a69e` 将其改为显式 `require()` 检查，失败时输出错误并返回非零。补齐/明确覆盖：
- LF 暂存、HF 完成及 LF→HF 顺序；
- HF 前不得出现 HF payload；
- 零中子 payload 仍能完成事件，mixed 摘要不丢失；
- HF 先到、事件 ID 错配、重复 LF、重复 HF；
- 完成后未 reset 不得覆盖下一事件；
- event_id=0、非法 fragment_side。

这次只是测试代码修正，必须由新 CI 实际运行后才能把这些断言标记为 COMPUTATION_VERIFIED。

### Run #156：实际 CI 状态

Run #156（workflow ID `44589725299`，commit `b0c417d580a52e412113a786af5d8e33bf30fff3`）：
- CMake Configure、C++ Build：PASS。
- Native CTest：98 项中 76% 通过；12 项事件执行测试失败，另有 12 项依赖测试未运行。失败日志仍指向无 E1 可映射离散态；不是成对缓冲器的断言失败。
- G2 分析单元测试、种子矩阵验证：PASS。
- G2 sidecar matrix：仍因模拟进程 exit 255 失败；后续模型分析步骤被跳过。
- native golden enforcement 失败；旧 golden 不应覆盖。

注意：Run #156 的 transaction 测试是在旧 `assert()` 版本下执行，且 Release 构建可能使断言失效。因此不能用该次 CTest PASS 证明事务逻辑正确。新显式检查提交之后，尚无对应 CI 结果。

### 原子性边界与剩余风险

- LF+HF 在**单个文件内部**通过单次合并写入，避免了原先逐侧写入窗口。
- neutron JSONL 与 mixed-history JSONL 是两个独立文件，普通文件 append 无法提供跨文件事务原子性。若第一文件写入成功而第二文件失败，run 必须整体作废；不得将其视为完整数据。
- 该缓冲器没有事件级失败记录、跳过或回滚能力；桥接失败仍终止进程，尚未提交的 LF 暂存随进程退出丢弃。
- 仍需验证实际运行中 LF/HF 配对输出、零中子边界、validator 的拒绝行为；单元测试通过也不能替代完整 G2 matrix。

### 状态修订

Run #103 中“成对暂存/提交机制 PROPOSED、未实现”的状态由本节更新为：**IMPLEMENTED，显式测试已加固，CI 待验证**。Run #151/156 因桥接失败生成的部分数据仍不可用于 M0–M3、匹配残差或 P/H/O；物理桥接赋权继续 BLOCKED。


## Run #105：成对暂存测试真实 CI 验证（COMPUTATION_VERIFIED；G2 运行仍 BLOCKED）

### Run #170 结果

Workflow run ID `44593509889`，提交 `968c7c48f17982bf66822e14acfc16600070a69e`：
- Configure：PASS。
- C++ Build：PASS。
- Native CTest：99 项中 75 项通过；12 个事件执行测试失败，另有 12 个依赖测试未运行。其余 75 项包含新增 `g2-sidecar-transaction`，该测试在 Release CI 中以显式 `require()` 断言实际执行并 PASS。
- G2 三层分析、条件完整历史、匹配条件历史、事件状态模型竞争、碎片状态消融、RNG seed matrix 单元测试：均 PASS。
- 完整 G2 sidecar matrix：模拟程序 exit 255，失败。
- 真实模拟后续分析步骤：SKIPPED。
- native golden enforcement：FAIL；未覆盖旧 golden。

### 事务测试能证明什么

Run #170 的 transaction test 实际执行了 LF 暂存、HF 配对、LF→HF payload 顺序、零中子、HF 先到、事件 ID 错配、重复 LF/HF、未 reset 时覆盖下一事件、event_id=0 和非法 side 等检查。由此将缓冲器的状态机单元测试从“可能被 NDEBUG 消除的 assert”升级为 **COMPUTATION_VERIFIED**。

### 仍未证明的内容

1. 12 个事件执行测试失败的根因仍是离散桥接无可映射状态；日志中的代表案例仍为 HF ^136I、LF ^105Nb 等只有一个离散候选且不满足 E1 角动量条件。transaction test 通过不能改变这一点。
2. 完整 sidecar matrix 没有完成，因此没有新一轮真实运行可验证 LF/HF 成对输出。
3. 缓冲器单元测试没有模拟真实文件系统的写入失败；两个 sidecar 文件之间仍无跨文件原子事务保证。
4. 由于 `cgmTerminateCode()` 仍直接终止进程，失败事件不会继续运行或生成失败事件记录；但 LF 尚在内存缓冲时进程退出，不应留下该事件的 LF sidecar 行。

### 当前状态

- 缓冲器状态机：**COMPUTATION_VERIFIED**（Run #170）。
- `recordEmittedParticlesFission()` 到缓冲器的静态接线：**SOURCE_AUDITED**。
- 实际模拟下的成对 sidecar 输出：**BLOCKED / NOT VERIFIED**（因桥接失败，完整 G2 matrix 未运行完成）。
- 跨文件写入原子性、事件级恢复/失败账本：**NOT IMPLEMENTED**。
- Run #170 的失败运行产物不得用于 M0–M3、匹配残差或 P/H/O。

### 下一项研究工作

当前不应继续围绕已经通过的缓冲器状态机重复加测试。应转向桥接输入证据审计：对 Run #151/170 诊断中出现的核素，核查 CGMF 实际加载的离散能级表、连续态终止能量、实验评价能级数据库及对应核素的能级自旋宇称资料，判断是当前模型能级表截断/不完整，还是确实缺乏可识别桥接态。外部评价能级只用于识别数据覆盖和候选状态，不得直接当作 CGMF 采样概率或桥接多极性。只有找到可追溯的分支多极性/强度依据，才重新评估物理桥接核；否则保持 BLOCKED，不补参数、不恢复 nearest-J。


## Run #106：外部评价能级对 ¹³⁶I 桥接失败的独立核查（PAPER_VERIFIED；不构成桥接概率）

核查 NNDC ENSDF《¹³⁶I Adopted Levels, Gammas》，评价日期 April 2018，评估者 E. A. McCutchan，NDS 152, 331 (2018)：https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=136I

评价表列出 0 keV 基态 (1−)、86.73(7) keV (2−,1−,0−)、201(26) keV (6−)、243.6 keV (7−) 及 1355.4 keV (9−)。Run #151/170 的两个 HF ¹³⁶I 初态为：
- event 6：Ei=0.0793033 MeV、Ji=7、π=+1；
- event 2：Ei=0.0205397 MeV、Ji=3、π=−1。

event 6 的 86.73 keV 及以上能级均高于 79.303 keV；能量可达的评价末态只有基态 0 keV、1−。Ji=7 到 Jf=1 有 |ΔJ|=6，不满足 E1/M1/E2 的角动量条件。event 2 能量更低，同样只有基态能量可达；Ji=3 到 Jf=1 有 |ΔJ|=2，也不满足 E1/M1/E2 角动量条件；初末宇称同为负，E1 宇称条件亦不满足。

### 结论与边界

这条外部评价数据说明，对这两个事件，不能简单把 ndisc=1 归结为 CGMF 漏掉了某个已知低能级。即使使用 ENSDF 已评价的低能级，按初态能量筛选后仍没有 E1/M1/E2 可达候选。

- 不恢复 nearest-J；它会强制映射到不满足已知选择条件的末态。
- 不因“没有 E1 候选”就改写成“实际发生 M1/E2”；本例低能可达态也不满足 M1/E2 角动量条件。
- ENSDF 资料未提供未解析态到基态的高多极跃迁强度或概率，故桥接赋权继续 BLOCKED。
- 这只是两个 ¹³⁶I 事件的 PAPER_VERIFIED 对照，不能外推到其他核素；后续应按诊断频次逐核素核查评价能级、自旋宇称、能量可达性和分支资料。

状态：¹³⁶I 评价能级 **PAPER_VERIFIED**；两个事件的 E1/M1/E2 可达候选筛选 **COMPUTATION_VERIFIED from published level table + logged initial states**；物理桥接核/跃迁赋权 **BLOCKED**。不修改模拟规则、不新增参数、不修改 golden。


## Run #107：Run #151 逐事件诊断与 ENSDF 交叉核验（部分完成；不改模拟）

### 1. 重新提取的原始事件诊断

重新从 GitHub Actions Run #151（ID `44586698377`）的 job log 提取全部 12 条 `[MC bridge diagnostic]`，并保留事件、碎片侧、初态能量、自旋、宇称及拒绝原因：

| 核素 | event | side | Ei (MeV) | Ji | πi | 程序拒绝原因 |
|---|---:|---|---:|---:|---:|---|
| ¹³⁶I | 6 | HF | 0.0793033 | 7 | + | angular momentum |
| ¹³⁶I | 2 | HF | 0.0205397 | 3 | − | angular momentum |
| ¹⁰⁵Nb | 9 | LF | 0.2825179 | 5.5 | + | angular momentum |
| ⁹⁶Y | 24 | LF | 0.1867211 | 8 | − | angular momentum |
| ¹³⁷I | 7 | HF | 0.1322979 | 11.5 | − | angular momentum |
| ¹⁰⁵Zr | 12 | LF | 1.1799976 | 6 | − | angular momentum |
| ¹³⁸Te | 20 | HF | 0.1776905 | 11 | − | angular momentum |
| ¹³⁶I | 15 | HF | 0.0811650 | 4 | − | angular momentum |
| ¹³⁷I | 16 | HF | 0.0773941 | 7.5 | + | angular momentum |
| ¹³²I | 20 | HF | 0.2770588 | 8 | + | angular momentum |
| ¹⁰⁵Zr | 12 | LF | 1.1799976 | 6 | − | angular momentum |
| ⁸⁹Br | 34 | LF | 0.0232161 | 3 | + | parity |

Run #151 的 12 条记录中，11 条为角动量拒绝、1 条为宇称拒绝；均为 ndisc=1。¹⁰⁵Zr event 12 的同一初态在两条回退入口各触发一次诊断，故表中保留两条程序记录，不将其误算为两个独立物理事件。

### 2. 已完成的 ENSDF 对照

**⁹⁶Y：** ENSDF 2008 年评价列出 0 keV (0−)、122.297 keV (1−)、652.29 keV (2−)、718.70 keV (1+,2+) 和 931.70 keV (1+) 等能级。对 event 24，Ei=186.721 keV，因此 652.29 keV 及以上不可达；可达的 0、122.297 keV 两个态，其 J=0、1 与 Ji=8 均不满足 E1 的 L=1 角动量三角条件。该事件的 E1 桥接失败不能仅由 ndisc=1 解释为漏掉一个已知低能态。ENSDF 还给出 122.297→0 keV 的 M1 与实测 B(M1)，但这不是本事件 Ji=8 初态到该态的桥接强度。来源：https://www.nndc.bnl.gov/ensnds/96/Y/adopted.pdf 。

**¹³⁷I：** ENSDF 评价能级表列出基态 0 keV (7/2+)，下一已列能级为 243.3 keV (5/2+)。event 7 的 Ei=132.298 keV、Ji=11.5、π=−，event 16 的 Ei=77.394 keV、Ji=7.5、π=+；两事件都只有基态能量可达。对应自旋差分别为 8 和 4，均不满足 E1 的角动量条件。来源：https://www.nndc.bnl.gov/ensnds/137/I/adopted.pdf 。

**¹³²I：** ENSDF 评价列出 0 keV (4+)、约 22 keV (5+，自旋宇称标注带不确定性)、49.72 keV (3+)、120 keV (8−)、161.52 keV (2+) 和 277.86 keV (1+)。event 20 的 Ei=277.058 keV，故 277.86 keV 态不可达；但 120 keV (8−) 态在能量上可达，且从初态 Ji=8、π=+ 到该态 Jf=8、π=− 满足 E1 的角动量与宇称选择条件。它是一个**外部评价能级给出的 E1-允许候选**，说明不能把该事件概括为“ENSDF 也没有 E1-允许的低能态”。然而，ENSDF 中该 120 keV 态是长寿命同核异能态；其已评价衰变表并未因此证明 CGMF 连续态初态到该态存在实际 E1 分支，更未给出本事件桥接概率。当前 CGMF ndisc=1 与 ENSDF 已评价能级覆盖之间存在值得追查的数据覆盖差异。来源：https://www.nndc.bnl.gov/ensnds/132/I/adopted.pdf 。

**⁸⁹Br：** ENSDF 2021 年评价给出基态 0 keV (5/2−)，下一能级 130.3 keV (3/2−)。event 34 的 Ei=23.216 keV、Ji=3、π=+，故只有基态能量可达。按 ENSDF 基态 Jπ，Ji=3→Jf=5/2 满足 E1 角动量条件，且宇称相反，因而 E1 选择规则本身允许；但 Run #151 程序日志却报告唯一候选被 parity 拒绝。这构成**CGMF 当前离散态宇称/核素表与 ENSDF adopted ground-state Jπ 的待核查不一致**，不能直接归因为物理上不存在 E1 候选。必须检查 CGMF 实际载入的 ⁸⁹Br 离散能级记录、parity_index 到物理宇称的映射，以及运行时核素索引，确认是否数据文件、映射约定或事件状态造成差异。ENSDF 对该基态 Jπ 的说明注明其依据包括壳模型预测及邻核类比，且 1/2+ 也有理论提议；不应把该 Jπ 当作无不确定性的直接测量。来源：https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=89Br 。

### 3. 尚未完成的核素

¹⁰⁵Nb、¹⁰⁵Zr、¹³⁸Te 的逐事件评价能级对照尚未完成。本轮未取得足够可靠的对应 adopted-level 表内容，故不对其候选数、可达性或缺级情况作结论。

### 4. 当前修订后的判断

1. ¹³⁶I 与 ⁹⁶Y 的已查事件：现有 ENSDF 低能可达态仍不满足 E1 角动量条件。
2. ¹³⁷I 的两个已查事件：已评价可达态也不满足 E1 角动量条件。
3. ¹³²I event 20：ENSDF 存在一个能量可达且满足 E1 选择规则的 120 keV (8−) 态；但没有证据证明该连续态初态到该态的实际分支或强度。
4. ⁸⁹Br event 34：ENSDF 基态选择规则允许 E1，而程序报告宇称拒绝；优先审计 CGMF 实际能级数据与宇称编码，不应先解释成物理禁戒。
5. ¹⁰⁵Nb、¹⁰⁵Zr、¹³⁸Te 仍为未核验。

**状态：** Run #151 诊断日志提取为 COMPUTATION_VERIFIED；上述 ENSDF 能级及选择规则对照为 PAPER_VERIFIED + 基于日志的 COMPUTATION_VERIFIED；¹³²I 的候选桥接分支、⁸⁹Br 的程序/数据库宇称不一致根因、其余三核素核验均为 BLOCKED。没有更改模拟算法、没有增加多极性/概率参数、没有恢复 nearest-J、没有修改 golden。Run #151/170 的失败 sidecar 仍不得进入 M0–M3 或 P/H/O。


## Run #108：CGMF 离散能级数据库逐核素实读（SOURCE_AUDITED；外部对照部分完成）

### 1. 数据来源与解析路径

本轮直接读取当前分支 `data/discreteLevels.dat` 的 Git blob（SHA `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`），而非根据 CI 诊断推测能级内容。文件头明确说明：该文件由 RIPL-3 评价离散能级预处理生成；缺失的自旋/宇称按 CGMF 手册规则设置。源码 `libcgmf/src/ripl2levels.cpp` 的 `readDiscreteLevelData()` 按 ZAID 与能级数读取该文件，并将每条能级的能量、自旋、宇称读入 `Level`；`getDiscreteLevels()` 再按核素 ZAID 将这些记录复制到运行时 `ncl[k].lev`。因此这里核对的是当前分支模拟实际加载的数据源，不是另一条 CGM 单核谱计算路径。

### 2. 八种诊断核素的实际数据库记录

对 Run #151 诊断涉及的八个核素逐一定位 ZAID（1000Z+A），并读取其能级计数和第一条（基态）记录：

| 核素 | ZAID | ndisc | CGMF 文件基态能量 (MeV) | CGMF 基态 Jπ |
|---|---:|---:|---:|---:|
| ⁸⁹Br | 35089 | 1 | 0.000000 | 2+ |
| ⁹⁶Y | 39096 | 1 | 0.000000 | 0− |
| ¹⁰⁵Zr | 40105 | 1 | 0.000000 | 4+ |
| ¹⁰⁵Nb | 41105 | 1 | 0.000000 | 5/2+ |
| ¹³⁸Te | 52138 | 1 | 0.000000 | 0+ |
| ¹³²I | 53132 | 1 | 0.000000 | 4+ |
| ¹³⁶I | 53136 | 1 | 0.000000 | 1− |
| ¹³⁷I | 53137 | 1 | 0.000000 | 7/2+ |

**确定事实：** 八种核素在当前 CGMF 预处理离散能级文件中全部只有一个离散能级，即基态；Run #151 的诊断 `ndisc=1` 与实际文件完全一致。这不是仅由运行时索引或事件诊断打印错误造成的。

### 3. ⁸⁹Br 的确定数据冲突

当前 CGMF 文件把 ⁸⁹Br 基态记为 2+。NNDC ENSDF 2021 年 11 月评价的 ⁸⁹Br Adopted Levels 则给出基态 (0) keV、(5/2^-)，并列出 130.3 keV 的 (3/2^-) 能级。Run #151 event 34 的初态为 (E_i=23.2161) keV、(J_i=3)、(pi_i=+)，故 130.3 keV 态能量不可达，基态是唯一能量可达的已评价末态：
- 若使用 CGMF 文件 2+，初末宇称相同，E1 宇称条件拒绝，正好对应程序日志；
- 若使用 ENSDF 基态 (5/2^-)，则 (|3-5/2|=1/2le1le 11/2)，且宇称相反，E1 选择规则允许。

因此 Run #151 的 parity rejection **可由 CGMF 当前离散基态宇称记录解释**；此前“程序与 ENSDF 冲突”的判断现在有了明确的数据源定位。该差异并不自动授权把运行时基态改成 ENSDF 值：还要确认 RIPL-3 原始条目、CGMF 数据预处理版本/规则以及该基态 Jπ 的评价依据。当前文件头说明有缺失值按手册补赋，但仅凭当前记录不能判定 2+ 究竟是 RIPL 原始值、预处理补值还是旧评价输入。

### 4. 可交叉核对的其他核素

- **¹⁰⁵Nb：** CGMF 记录 (5/2^+)。独立文献表列出的 ¹⁰⁵Nb 基态也是 (5/2^+)，半衰期约 2.91 s；因此目前没有基态 Jπ 不一致证据。该事件初态 (J_i=5.5,pi_i=+)，对 (5/2^+) 基态的 E1 仍因角动量和宇称条件不满足而不能作为 E1 桥接。该文献表还指出 ¹⁰⁵Nb β 衰变到 ¹⁰⁵Mo 的评价能级资料存在未量化 feeding 问题；这与本次未解析态到自身基态的桥接强度不是同一量。
- **¹³²I：** CGMF 基态 4+ 与 ENSDF adopted 基态 4+ 一致。ENSDF 的 120 keV ((8^-)) 同核异能态确实存在，但它没有进入当前 CGMF 离散表（当前 ndisc=1）。对 event 20，它是能量可达且 E1 选择规则允许的外部候选；但它的已评价衰变为 120→22 keV 的 E3，不能据此推定 event 20 的连续态初态到该态有 E1 分支或相应强度。
- **⁹⁶Y、¹³⁶I、¹³⁷I：** 当前 CGMF 基态 Jπ 分别为 (0^-)、(1^-)、(7/2^+)，与前轮使用的 ENSDF adopted 基态值一致；本轮未发现基态 Jπ 编码冲突。
- **¹⁰⁵Zr、¹³⁸Te：** 当前 CGMF 记录分别为 4+、(0^+)。本轮未取得足够可直接引用的 ENSDF adopted ground-state 细节，故不宣称已完成评价一致性核验。

### 5. 机制与数据治理结论

1. 目前可以确定：这些失败不是因为程序误把一个多能级核素读成 ndisc=1；当前输入文件本身就只给这八种核素各保留一个基态。
2. ⁸⁹Br 至少存在一项实质性 Jπ 数据源差异，且该差异直接改变 event 34 的 E1 宇称筛选结果。应先做 RIPL 原始条目和生成流程审计，而不是放宽 E1 规则或添加高多极性。
3. ¹³²I 的 120 keV 同核异能态说明当前 CGMF 离散表对该核素的覆盖远少于 ENSDF adopted 表；但其存在不等于它是本事件的实际桥接终态。
4. 其他核素目前主要表现为离散能级覆盖不足（当前文件只保留基态）；是否还存在基态 Jπ 冲突，必须逐核素用 adopted 数据核实。
5. 不应把 ENSDF 的全部能级直接拼接进 CGMF 文件：需要先审计 RIPL→CGMF 预处理规则、能级上限、spin/parity 缺失赋值、gamma branch 字段及数据库版本；且外部评价能级也不提供未解析连续初态的跃迁概率。

### 状态

- 当前分支 `discreteLevels.dat` 八核素记录与 ndisc：**SOURCE_AUDITED / COMPUTATION_VERIFIED（直接读取文件并按 ZAID 解析）**。
- `readDiscreteLevelData()` / `getDiscreteLevels()` 的载入路径：**SOURCE_AUDITED**。
- ⁸⁹Br CGMF–ENSDF 基态 Jπ 差异：**PAPER_VERIFIED + SOURCE_AUDITED**；差异成因（RIPL 原始值或预处理补值）**BLOCKED**。
- ¹⁰⁵Nb 基态 (5/2^+) 外部交叉核验：**PAPER_VERIFIED**。
- ¹³²I 120 keV 同核异能态：**PAPER_VERIFIED**；本事件真实桥接分支/强度 **BLOCKED**。
- ¹⁰⁵Zr、¹³⁸Te 的 adopted ground-state 一致性：**BLOCKED / NOT YET VERIFIED**。
- 本轮未修改模拟算法、未修改离散数据库、未修改 golden、未生成新事件。



## Run #108：⁸⁹Br 宇称冲突的来源分层审计（SOURCE_AUDITED + PAPER_VERIFIED；根因仍 BLOCKED）

### 1. 选择器源码核对

当前分支 `libcgmf/src/specmc.cpp` 的 `mcSelectE1DiscreteBridge()`：
- 将连续态自旋索引转换为物理自旋：`initialSpin = spinIndex + halfint(target.lev[0].spin)`；
- 对候选态直接读取 `candidate.parity`；
- 要求初末宇称均为 ±1，且 `initialParity * candidate.parity == -1`；
- 选择器中没有额外 parity_index→物理宇称转换，也没有对候选宇称进行二次翻转。

因此，Run #151 的 ⁸⁹Br parity rejection 直接意味着：运行时传入的 `initialParity` 与唯一候选 `candidate.parity` 未满足相反宇称条件（或者候选/初态宇称值非法而被计入 invalid；原诊断报告的是 parity rejection，需保留原日志核对字段）。目前不能仅凭选择器源码断言转换 bug。

### 2. ⁸⁹Br 外部评价资料

NNDC ENSDF ⁸⁹Br Adopted Levels, Gammas（评价版本 Nov 2021；ENSDF index 显示 2022-01 数据集）列出：
- 0 keV：((5/2^-)) 基态；
- 130.3 keV：((3/2^-))；
- 后续已列能级 506.7、531.5、953.4 keV 等。

Run #151 event 34：Ei=23.2161 keV、Ji=3、πi=+。按 ENSDF adopted ground state，能量可达的只有 0 keV 基态，E1 的 (|ΔJ|=0.5leq1) 且初末宇称相反，故选择规则允许。来源：https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=89Br 。

### 3. 重要发现：CGMF 的数据准备流程会“修补”缺失/不确定 Jπ

CGMF 官方用户手册明确说明，运行用 `cgmfDiscreteLevels.dat` 从 RIPL-3 完整数据经 `transformLevelDataFile.ipynb` / `Nucleus.py` 生成；对缺失自旋/宇称的能级会按 KCK 连续能级密度系统补值，缺失宇称可能随机选择；RIPL 给出多个 Jπ 选项时取第一项；基态完全未知时按质量奇偶采用默认 Jπ。手册特别警告这些任意处理会影响特定核素的 γ 级联研究。来源：https://cgmf.readthedocs.io/en/stable/discreteLevels.html 。

因此，⁸⁹Br 的差异可能发生在 **RIPL/ENSDF → CGMF 离散能级文件预处理**，而不一定在 E1 选择器。ENSDF 的括号标记也代表评价自旋宇称带有建议/不确定性质，不能把所有评价赋值视为无误差直接测量。

### 4. 还不能下的结论

本分支当前可读取到的源码确认了选择器逻辑，但本轮没有成功定位并读取运行实际使用的 `cgmfDiscreteLevels.dat`、⁸⁹Br 对应原始 RIPL 行及预处理后的记录，也未从 Run #151 原始产物取得该事件的 candidate.parity 原值。因此：
- 不能宣称 ⁸⁹Br parity bug 已修复或已定位到具体文件；
- 不能把 ENSDF 的 5/2− 直接覆盖 CGMF 输入；
- 不能将 ENSDF 允许 E1 等同于存在已测 E1 分支或可赋予桥接概率；
- 不能据此修改模拟抽样、补充概率或重跑 G2 矩阵。

### 5. 下一步可执行的最小审计包

需要从 Run #151 的构建/运行环境或仓库实际数据目录取出并归档：
1. 运行时 `DATADIR` 的真实值和文件 SHA-256；
2. `cgmfDiscreteLevels.dat` 中 Z=35,A=89 的全部记录（能量、spin、parity、level index）；
3. 对应 RIPL-3 原始记录；
4. `transformLevelDataFile.ipynb` / `Nucleus.py` 对该核素执行补全前后的逐条差异；
5. event 34 的运行时初态宇称、唯一候选的原始 parity、level index、文件来源行。

得到这些材料后，才可判定是数据版本差异、RIPL 不确定 Jπ 的预处理选择、初态宇称口径不一致，还是实际代码错误。

**状态：** E1 选择器宇称判定源码 **SOURCE_AUDITED**；⁸⁹Br ENSDF adopted Jπ **PAPER_VERIFIED**；CGMF 实际输入记录与预处理根因 **BLOCKED**；物理桥接强度 **BLOCKED**。无代码改动、无模拟规则改动、无 golden 改动。


## Run #109：Run #151 的离散能级数据路径与 CI 产物审计（SOURCE_AUDITED；运行时最终路径仍待锁定）

### 1. CMake 配置给出的两个候选数据目录

审计 Run #151 对应提交 `3d8c45a7a119a43795c0c630fba35f3abddf575d` 的源码：

- 根目录 `CMakeLists.txt` 使用 `GNUInstallDirs`，默认构建配置下启用安装；数据安装规则将 `data/*.dat*` 安装到 `${CMAKE_INSTALL_DATADIR}/data/cgmf-${CGMF_VER}`。
- `libcgmf/CMakeLists.txt` 定义：
  - `BUILD_DATADIR = ${CMAKE_CURRENT_SOURCE_DIR}/../data`，即源码 checkout 的 `data/`；
  - `INSTALL_DATADIR = ${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/data/cgmf-${CGMF_VER}`；
  - 由 `cgmf_config.h.in` 生成编译期配置。
- Run #151 的 CI 日志显示配置命令为 `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -Dcgmf.tests=ON`，没有传入自定义 install prefix；日志显示执行了 build，没有显示 `cmake --install`。

### 2. 运行时目录解析优先级

源码 `libcgmf/src/cgmfEvents.cpp`：

1. `readUserInput()` 先读取 `-d` 参数；若没有 `-d`，再读取环境变量 `CGMFDATA`。
2. `setdatapath(path)` 在 path 仍为空时，先检查 `INSTALL_DATADIR` 是否为目录；若不是，再检查 `BUILD_DATADIR`。
3. `readDiscreteLevelData()` 在当前工作目录先尝试打开 `discreteLevels.dat`；失败后再打开 `datadir + DISCRETEDATA`。
4. `DISCRETEDATA` 在 `libcgmf/include/ripl2levels.h` 定义为 `discreteLevels.dat`。

因此，CI 的实际选择顺序是：**工作目录中的同名文件 → `CGMFDATA` 指向目录中的文件 → 编译时安装目录（若存在）→ 源码 checkout 的 `data/discreteLevels.dat`**。这里的前两项由调用环境决定，不能仅凭 CMake 配置跳过核实。

### 3. Run #151 的实际调用与工作目录

- Run #151 workflow job log 显示矩阵入口调用 `python3 tools/tests/runG2SidecarMatrix.py`，二进制为 `build/utils/cgmf/cgmf.x`。
- 在 `runG2SidecarMatrix.py` 中，三个模式分别以每个 case 的 `on/`、`off/`、`baseline/` 子目录作为 subprocess 的 `cwd`。
- CGMF 命令行参数包含 `-n`、`-e`、`-i`、可选 `-s` 和 `-f`，没有传 `-d`。
- Python 脚本从 `os.environ.copy()` 继承环境，并没有自行设置 `CGMFDATA`。但当前取得的 job log 未打印完整环境变量，workflow YAML 的 job-level/env-level 设置尚未独立读取。因此不能把“没有在 Python 脚本中设置”扩大成“CI 环境一定没有 CGMFDATA”。

### 4. 与 Run #151 同提交的数据身份

直接对 Run #151 的 checkout commit 读取 GitHub Contents API 元数据，`data/discreteLevels.dat` 的 Git blob SHA 为：

`dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`

它与此前 Run #108 在当前分支读取并解析的 `data/discreteLevels.dat` blob SHA 一致。故可确认：**Run #151 对应源码提交中的仓库数据文件身份，与 Run #108 审计的仓库数据文件身份相同**。这项结论是 Git blob 身份核对，不是文件 SHA-256，也不单独证明运行进程最终打开的就是该路径。

`ripl2levels.cpp` 对该数据的读取方式也已核实：先打开工作目录中的 `discreteLevels.dat`；若失败才使用 `datadir + DISCRETEDATA`。文件记录字段按固定宽度解析为 ZAID、能级数，以及逐能级的 energy、spin、parity、half-life、gamma branch 数及分支记录。

### 5. Run #151 artifact 审计

通过 GitHub Actions artifact API 获取 Run #151 的 `cgmf-g2-mixed-history-matrix`，artifact ID `14562330132`，并实际下载、解压检查。内容仅包括：

- `cf252-sf/on/mixed-history.jsonl`
- `cf252-sf/on/neutron-transition.jsonl`
- `cf252-sf/on/histories.cgmf.0`
- `cf252-sf/on/sidecar-on.stdout`
- 空的 `rng-audit.tsv`

没有包含 `discreteLevels.dat`、生成的 `cgmf_config.h`、运行时 DATADIR 记录或核素级离散候选快照。该 artifact 的 `sidecar-on.stdout` 确认首次失败仍为 event 6、¹³⁶I、HF、ndisc=1、角动量拒绝；不能从该产物反推出运行时文件的绝对路径或文件 SHA-256。

### 6. 当前结论与下一项最小取证

- **SOURCE_AUDITED：** CMake 数据目录变量、`setdatapath()` 优先级、`-d/CGMFDATA` 入口、当前目录优先打开逻辑、矩阵脚本的 case 工作目录与参数。
- **COMPUTATION_VERIFIED：** Run #151 checkout commit 的 `data/discreteLevels.dat` Git blob SHA 与 Run #108 审计的 blob SHA 相同；Run #151 artifact 已下载并检查，未包含运行时数据文件。
- **BLOCKED：** 尚未从 workflow YAML/运行环境确认 `CGMFDATA` 是否被设置；未取得 CI 进程最终解析出的绝对 DATADIR；未从 Run #151 运行时归档得到文件 SHA-256 和 Z=35/A=89、Z=53/A=132 的实际载入记录。
- 因此，Run #108 对仓库 `data/discreteLevels.dat` 的核素记录解析仍然成立，但“Run #151 运行时一定打开了这份仓库文件”目前只能视为高度可追踪的候选路径，尚未达到运行时直接证据等级。

下一轮最小补证应只增加只读诊断：在 `readDiscreteLevelData()` 成功打开文件后打印 `fp` 实际打开的路径（或由调用端传入并记录最终路径）、文件 SHA-256，以及 ZAID 35089/53132 的 ndisc 和所有能级 energy/spin/parity；同时打印 `CGMFDATA` 是否存在、`-d` 是否传入、`INSTALL_DATADIR` 与 `BUILD_DATADIR` 的目录存在性。诊断不得改动选择器、抽样、离散数据库或 golden。取得该证据前，不重跑完整 G2 matrix，也不将 Run #151/170 失败数据纳入 M0–M3/P/H/O。

本轮无模拟代码改动、无数据库改动、无 golden 改动；仅完成源码、CI 日志与既有 artifact 的只读审计。


## Run #110：运行时离散能级审计开关（IMPLEMENTED；CI待执行）

### 1. 只读诊断实现

在 `libcgmf/src/ripl2levels.cpp::readDiscreteLevelData()` 增加环境变量门控的诊断：

- 仅当 `CGMF_DATA_AUDIT` 存在时输出诊断，不改变正常执行路径。
- 在成功打开文件后，记录实际传给 `ifstream::open` 的 `opened_file` 字符串、全局 `datadir`、`CGMFDATA` 环境变量，以及编译期 `INSTALL_DATADIR` / `BUILD_DATADIR` 对应离散数据文件是否存在。
- 数据库读完后，仅对 ZAID 35089（⁸⁹Br）和 53132（¹³²I）输出数据库记录中的 `ndisc` 与逐级 `level_index / energy_MeV / spin / parity`；若核素不在数据库中，明确输出 `not_in_database`。
- 诊断使用现有读入后的 `allLevels` / `zaidIndex` / `numberLevels`，不重解析、不修订、不补写任何物理数据。

### 2. 矩阵日志的文件哈希取证

在 `tools/tests/runG2SidecarMatrix.py` 增加只读审计前缀：

- 仅为 sidecar-on 子进程设置 `CGMF_DATA_AUDIT=1`，sidecar-off 与 baseline 环境保持不变。
- 在启动 on 子进程前，按源码优先级解析工作目录同名文件、`CGMFDATA`、编译生成配置中的安装目录/构建目录；把选中路径、选择来源和 Python `hashlib.sha256` 文件哈希写入同一个 `sidecar-on.stdout` 日志。
- C++ 侧同时输出真实成功打开的路径和两种核素的内存数据库快照。两侧路径一致时，哈希可归属到运行时实际读入文件；若不一致，审计将暴露解析差异，而不会把 Python 预测当作运行时事实。
- Python 路径解析特意遵循 `setdatapath()` 的目录存在性优先级：安装目录存在但文件缺失时不会错误回退到构建目录。

### 3. 影响边界

- 诊断由环境变量显式开启；未设置时仅增加一次环境变量读取，不输出数据，不改计算。
- 不改 E1 选择器、初态生成、跃迁抽样、随机数、sidecar schema、golden 或数据库文件。
- on 模式额外输出诊断文本，因此原先 on/off stdout 字节相等的比较在诊断开关打开时会因预期诊断行而失效。当前脚本仍保留既有 stdout 比较；因此本轮 CI 若在该比较处通过不了，需要将“诊断输出”从物理 stdout 非干扰比较中剥离或对比去除诊断行后的 stdout，不能将预期诊断差异误判为模拟行为变化。**注意：当前首个 CF-252 case 在 Run #151 已于模拟启动后很早失败；若再次在该点失败，stdout 比较不会执行，诊断日志仍会由 always artifact 上传。**

### 4. 状态

- `SOURCE_AUDITED`：诊断点位于实际成功打开的文件之后，能报告 C++ 读入的实际核素表。
- `IMPLEMENTED`：代码与矩阵日志脚本已提交到研究分支。
- `BLOCKED / CI_PENDING`：尚未有本轮编译与运行结果；不能称诊断已编译验证或已取得运行时 SHA/能级数据。
- 下一项：读取该提交触发的 CI build 结果；若编译通过，检查 artifact 中 `cf252-sf/on/sidecar-on.stdout` 的 Python SHA、C++ opened_file、ZAID 35089/53132 能级快照。然后再决定是否以同样开关执行针对性的单事件复现；不运行完整矩阵，不触碰旧 golden。

本轮为诊断代码/测试日志辅助代码改动，无模拟物理规则改动。


### Run #110 追加修正：诊断行与非干扰比较隔离

在首次提交诊断实现后，发现原矩阵脚本直接比较 on/off/baseline 的完整 stdout；由于诊断仅在 on 模式开启，诊断行会造成预期的日志差异。已在 `tools/tests/runG2SidecarMatrix.py` 增加 `stdout_without_data_audit()`：仅从 stdout 非干扰比较输入中剔除以 `[CGMF DATA AUDIT` 开头的来源诊断行，其他输出逐字节比较规则不变。原始 stdout 文件仍完整保留 Python SHA 预检和 C++ 实际打开路径/能级快照，原始日志 SHA-256 也仍对完整文件计算。

这项修正避免把只读 provenance 文本误判为模拟行为差异；并不放宽或跳过其他 stdout 内容比较。修正提交后会触发新的 CI；前一轮 CI 运行的是隔离修正前的提交，不能代表最终版本。


### Run #110 CI 编译反馈与修正

- 对提交 `6bfaf852c453336c1ad18b1fa5c89c5b8c783018` 的 CI Run #196（push）实际检查构建日志：`ripl2levels.cpp` 因未包含生成配置头文件而无法识别 `INSTALL_DATADIR`、`BUILD_DATADIR`，Build step FAIL；后续测试均跳过。
- 已在 `libcgmf/src/ripl2levels.cpp` 增加 `#include "cgmf_config.h"`。该头文件由 `libcgmf/CMakeLists.txt` 的 `configure_file` 生成，且其 build 目录已加入目标编译 include 路径。
- 修正提交：`67ba723759086cfeb7b5ebd75559f6d7df363d2e`。
- 状态仍为 `IMPLEMENTED / CI_PENDING`；Run #196 的失败不能被覆盖为成功，后续只以包含该修正的 CI run 判断编译结果。


### Run #110 追加简化：避免诊断依赖生成头文件

对 CMake 生成头文件的 include 路径做了保守处理：撤销在 `ripl2levels.cpp` 中包含 `cgmf_config.h` 的改动，并移除该文件对 `INSTALL_DATADIR` / `BUILD_DATADIR` 宏的直接引用。原因是这两个宏属于生成配置，诊断不应为此引入额外编译期 include 依赖。现在：

- C++ 只记录真实打开的文件名、运行时 `datadir`、`CGMFDATA` 和实际加载的目标核素能级表。
- Python 日志前缀负责按配置头文件解析安装/构建目录优先级，并记录选中路径与 SHA-256。
- 只有 Python 预检路径与 C++ 实际打开路径吻合时，才将该哈希认定为实际输入文件哈希。

简化提交：`d9bf5e64481feda1b0f8da980a58605b997f2a47`。此前“C++ 侧打印 INSTALL/BUILD 目录存在性”的描述已由本条修正：目录候选解析和文件哈希归 Python 预检日志，C++ 负责提供运行时实际打开路径与内存快照。CI 尚待该提交验证。


## Run #111：CI 运行时离散能级快照核验（COMPUTATION_VERIFIED；⁸⁹Br 数据根因已显著收敛）

### 1. CI 运行结果与产物

- CI Run #206，run ID：`44604419671`；代码提交：`d9bf5e64481feda1b0f8da980a58605b997f2a47`。
- CMake Configure、C++ Build、Native CGMF test suite 均 PASS。
- G2 三层分析、conditional full-history、matched conditional history、event-state model competition、fragment-state ablation、RNG seed matrix 等合成夹具单元测试均 PASS。
- G2 sidecar 完整矩阵仍 FAIL；后续条件分析/模型竞争/消融步骤因矩阵失败而 SKIPPED。原生 golden enforcement 仍 FAIL。不得把本次 CI 记为全套通过。
- 成功保存并下载 artifact `cgmf-g2-mixed-history-matrix`，artifact ID `14568633111`。实际检查 `cf252-sf/on/sidecar-on.stdout`，诊断内容完整。

### 2. 运行时文件身份：路径和 SHA 对上

C++ 实际输出：
`opened_file=/home/runner/work/CGMF/CGMF/libcgmf/../data/discreteLevels.dat`

Python 预检输出：
`selected_by=BUILD_DATADIR`
`selected_file=/home/runner/work/CGMF/CGMF/data/discreteLevels.dat`
`CGMFDATA=<unset>`

两条路径规范化后指向同一个文件；因此 Python 预检 SHA 可归属到 C++ 实际打开的数据文件：

`c79679e4247ddf69e3766ccce0b3177fcb7b253e26fd50ff621d2721d023c80e`

本轮第一次把 CI 实际打开路径、预检路径、SHA-256 三者闭合为同一数据身份。此结论仅针对 Run #206 的该次 CI 执行。

### 3. C++ 内存中实际加载的 ⁸⁹Br / ¹³²I 记录

C++ 在数据库读取完成后从 `allLevels` / `numberLevels` / `zaidIndex` 输出：

| ZAID | 核素 | ndisc | level_index | energy (MeV) | spin (ℏ) | parity |
|---:|---|---:|---:|---:|---:|---:|
| 35089 | ⁸⁹Br | 1 | 0 | 0 | 2 | +1 |
| 53132 | ¹³²I | 1 | 0 | 0 | 4 | +1 |

源码核对：`ripl2levels.cpp` 将文件字段 `s` 直接赋给 `Level.spin`，将字段 `p` 直接赋给 `Level.parity`；没有在这段载入逻辑中把 ⁸⁹Br 的 spin/parity 转换成另一套物理 Jπ。因此该快照是程序内存中的实际字段值，不只是文本文件 grep 结果。

### 4. 对先前物理核验的影响

**⁸⁹Br：**
- ENSDF Adopted Levels 记录基态 0 keV `((5/2^-)))，130.3 keV `((3/2^-))`。
- 本次 CI 的 CGMF 运行时库却只载入 0 keV `J=2, π=+` 一个态。
- 这不是微小的能级截断差异，而是基态 Jπ 与 ENSDF adopted 值存在实质差异；当前文件既没有 130.3 keV 态，也没有把基态记录为 ENSDF 的 5/2−。
- 对此前 Run #151 event 34 的报告初态 `Ji=3, πi=+`，若使用当前已确认的同一 Git 数据 blob / 运行时记录，则唯一候选态 `Jf=2, πf=+` 会因宇称相同而被 E1 选择器拒绝；而 ENSDF 的 `5/2−` 基态在角动量和宇称条件上允许 E1。故当前证据强烈指向**输入离散库的 ⁸⁹Br 基态 Jπ 记录差异是该 parity rejection 的直接数据层解释**，而不是先前已证明的选择器宇称转换错误。
- 但尚未读取原始 RIPL-3 对应条目及 `transformLevelDataFile.ipynb` / `Nucleus.py` 的逐步处理，不能判定差异究竟来自 RIPL 原始评价、预处理选项/补值，还是数据文件生成版本；也不能把 ENSDF 值直接覆盖进模拟输入。

**¹³²I：**
- 运行时库只载入基态 `0 MeV, J=4, π=+`，与 ENSDF 基态 `4+` 一致。
- ENSDF 中约 120 keV 的 `8−` 长寿命异能态没有进入当前 CGMF 离散库；因此它不可能是本次 CGMF E1 bridge selector 从该库选出的候选终态。
- 其外部存在性是 PAPER_VERIFIED，但并不建立连续初态到该异能态的实际分支或跃迁强度。

### 5. 当前失败边界

本次 artifact 的首个模拟失败仍是 event 6、¹³⁶I、HF、`ndisc=1`、角动量拒绝；Run #206 的矩阵在到达 ⁸⁹Br event 34 前已终止。因此：
- 运行时文件身份及 ⁸⁹Br/¹³²I 内存快照：**COMPUTATION_VERIFIED**；
- ⁸⁹Br CGMF 输入 Jπ 与 ENSDF adopted Jπ 差异：**PAPER_VERIFIED + COMPUTATION_VERIFIED**；
- 该差异解释 Run #151 event 34 parity rejection：**STRONGLY_SUPPORTED / SAME-DATA-CROSS-RUN INFERENCE**，不是 Run #206 同一事件的直接复现；
- ⁸⁹Br 差异的上游来源（RIPL 原始数据或生成处理）：**BLOCKED**；
- ¹³²I 120 keV 异能态是否存在本事件真实跃迁分支：**BLOCKED**；
- G2 sidecar matrix、完整事件级证据链：仍 **FAIL / INCOMPLETE**。

### 6. 下一步（最小化、只审数据生成源）

不重跑完整矩阵，不改选择器，不改 E1 规则，不把 ENSDF 直接拼入数据库。下一轮只追踪 ⁸⁹Br 的来源链：
1. 定位仓库内 RIPL 原始输入、转换 notebook / Python 处理代码、数据生成版本及其来源元数据；
2. 核对 Z=35,A=89 的原始 Jπ 选项、缺失值标志、是否有多解，以及转换时如何选择或补值；
3. 若仓库不含原始 RIPL 输入，明确记录外部源文件/版本/校验值缺口，不猜测原因；
4. 只有确定来源后，才讨论是否需要单独的数据修正提案；任何数据修正都必须单独分支、保留原 golden，并以新的验证协议评估，不能混入本轮审计。

本轮没有修改模拟规则、离散数据库或 golden；仅通过环境门控诊断完成 CI 运行时数据来源和内存记录取证。


## Run #112：⁸⁹Br 上游数据生成链的仓库盘点（SOURCE_AUDITED；原始 RIPL 行待读取）

### 1. 仓库内已确认的源材料

对当前分支 Git tree 做完整递归盘点，发现：
- `data/ripl3-levels.dat`：27,316,178 bytes；Git blob SHA `c3c3a816730deef172ccbd11b0dfd58b6d197d90`。
- `data/ripl3-levels-2015.dat`：70,158,325 bytes；Git blob SHA `3be0a27558c793837f6c3cc5deb45ea1deee7259`。
- `data/discreteLevels.dat`：4,250,841 bytes；Git blob SHA `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`。

仓库树中没有发现 `transformLevelDataFile.ipynb` 或 `Nucleus.py`。因此，CGMF 当前仓库包含两份 RIPL3 大型源数据文件和最终运行文件，但没有文档所述的转换 notebook / Python 处理类。

### 2. 官方仓库文档确认的转换规则

读取 `doc/rtd/discreteLevels.rst`，其明确说明：
- `cgmfDiscreteLevels.dat` 从 RIPL-3 完整数据文件生成；
- 先读完整 RIPL 数据，再修复缺失/未指派的自旋和宇称，最后修复 gamma transitions；
- 对缺失或未指派 Jπ 的能级，按 KCK 连续能级密度系统处理；缺失宇称按均匀分布假设随机选择；
- RIPL-3 对不确定能级给出多个 Jπ 选项时，选第一项；
- 基态 Jπ 完全未知时，按核素奇偶性采用默认值（奇 A 核默认 1/2+）；
- 文档明确警告这些任意处理可能显著影响特定核素的 γ 级联研究。

这使“预处理时的多解选择/缺失值补全”成为 ⁸⁹Br 数据差异的可检验候选路径，但还不能证明它就是本例原因。

### 3. 本轮尚未完成的内容

- 两份 RIPL3 文件均为大型数据文件；本轮只从 Git tree 取得文件大小和 blob SHA，未取得 ⁸⁹Br 的原始记录行。
- 未能从仓库定位转换 notebook、`Nucleus.py` 或可复现生成命令。
- 因此不能判断 ⁸⁹Br 的原始 RIPL 记录是否为 5/2−、是否提供多个候选 Jπ、是否缺失/不确定，或 2+ 是如何产生的。
- 不可把文档中“奇 A 默认 1/2+”直接套用到本例：运行时记录是 2+，这更需要原始条目和转换步骤来解释。

### 4. 状态与下一步

- 仓库 RIPL3 源文件存在性、大小、Git blob SHA：**SOURCE_AUDITED / COMPUTATION_VERIFIED**。
- 官方文档对生成流程和缺失 Jπ 处理规则的说明：**SOURCE_AUDITED**。
- ⁸⁹Br 原始 RIPL3 Jπ、对应版本差异、最终 2+ 的生成原因：**BLOCKED**。
- 下一步仅做两份 RIPL3 大文件的定点解析：按其真实文件格式识别 Z=35,A=89 的记录边界，抽取能级及候选 Jπ 原文，并与最终 `discreteLevels.dat` 对照；随后判断转换工具是否可从仓库历史/上游项目恢复。若源数据本身没有 ⁸⁹Br 记录或候选项，明确记录缺失，不推测补值来源。
- 继续不改模拟选择器、E1 规则、离散数据或 golden；不重跑完整矩阵。

本轮为仓库和官方说明的来源盘点，没有改动物理代码或模拟数据。


## Run #113：⁸⁹Br RIPL-3 原始 Jπ 记录与最终离散行逐字段对照（COMPUTATION_VERIFIED；转换根因仍 BLOCKED）

### 1. RIPL-3 原始记录（data/ripl3-levels.dat）

通过 Git blob API 读取完整 `data/ripl3-levels.dat`（27,316,178 bytes；blob SHA `c3c3a816730deef172ccbd11b0dfd58b6d197d90`），定位到第 78,451 行：

```text
89Br   89   35    1    0    1    1    5.909000   11.981001
 1   0.000000  -1.0  0   4.40E+00  0               (3/2-,5/2-)  2 =    100.0000 %B-     =     13.8000 %B-N
```

字段层面可以直接确认：
- 核素：Z=35、A=89；
- 仅有一个 RIPL level；
- 能量为 0；
- 数值 spin 字段为 -1.0，parity 字段为 0，表示数值 Jπ 未指派；
- 记录文本另列 `(3/2-,5/2-)` 两个候选标记；
- 半衰期字段为 4.40E+00，gamma branch count 为 0；本轮重点只在 Jπ，不对衰变分支做推断。

这条源记录并非数值上给出 2+。它提供的是未指派的数值 Jπ 与括号中的两个负宇称候选标记。

### 2. 最终 CGMF 运行文件的逐字段对照

通过 Git blob API 读取当前分支 `data/discreteLevels.dat`（4,250,841 bytes；blob SHA `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`），第 50,378 行：

```text
89Br  35089   1
 0.000000   2.0  1  4.40000e+00  0
```

对照结果：
- 核素与能级数保持：一个 0-MeV level；
- 半衰期从 RIPL 的 4.40E+00 转为最终文件的 4.40000e+00，数值一致；
- RIPL 数值 J=-1、π=0 被最终文件替换为 J=2、π=+1；
- RIPL 文本候选 `(3/2-,5/2-)` 没有作为最终数值 Jπ 保留。

因此，数据差异明确发生在 **RIPL 源记录到 CGMF 离散运行文件的预处理/生成层**，不是本轮 E1 选择器在读取最终文件时自行把 5/2− 改成 2+。运行时 C++ 快照又独立确认最终文件中的 `2.0,+1` 被原样载入内存。

### 3. 对生成规则的解释边界

CGMF 文档说明：数值 spin 或 parity 缺失/未指派时会按 KCK 系统处理，缺失宇称按均匀分布假设随机选择；若 RIPL 对不确定能级提供多个 Jπ 选项，则文档称选择第一项。

本例原始数值字段 `spin=-1.0, parity=0` 与“Jπ 未指派”处理条件相符；文本标签 `(3/2-,5/2-)` 又与“多候选”规则相关。但没有 `transformLevelDataFile.ipynb` / `Nucleus.py` 的实际代码、输入版本元数据、随机种子和生成日志，无法确定这条记录究竟走了哪一条分支，以及最终 2+ 的具体来源。不能把文档中的“多选取第一项”直接解释成最终 2+，因为源标签的第一项是 (3/2^-)，并不等于 2+。

### 4. 数据版本与仍缺证部分

- 当前仓库 `data/ripl3-levels.dat` 的 ⁸⁹Br 原始行已直接读取。
- `data/ripl3-levels-2015.dat` 文件存在，大小 70,158,325 bytes，blob SHA `3be0a27558c793837f6c3cc5deb45ea1deee7259`；本轮未能安全读取其完整内容并定位对应行，不能声称两个 RIPL 文件版本记录相同。
- 仓库树未包含转换 notebook / `Nucleus.py`；当前仓库没有可直接重跑的原始转换链。
- 尚未确认 `discreteLevels.dat` 是由仓库中的哪份 RIPL 文件、哪个工具版本、何种随机状态生成。

### 5. 当前结论与下一步

- RIPL3 当前源文件的 ⁸⁹Br 未指派数值 Jπ 和括号候选文本：**COMPUTATION_VERIFIED**。
- 最终运行文件中的 2+ 记录与 RIPL 源数值字段不同：**COMPUTATION_VERIFIED**。
- CI 实际载入该最终 2+ 记录：**COMPUTATION_VERIFIED**（Run #206）。
- 转换过程将该记录赋为 2+ 的具体算法/随机性：**BLOCKED**。
- `ripl3-levels-2015.dat` 对应原始行：**BLOCKED / NOT READ**。
- 对 event 34 parity rejection 的解释：当前输入数据层差异是强证据，但尚无同一提交、同一事件的直接重跑复现；状态仍为 **STRONGLY_SUPPORTED**，不是单事件直接验证。

下一步应先从上游 `lanl/CGMF` 历史、发布包或文档源仓库寻找转换 notebook / Python 类及其版本，再用确定的转换器对该 RIPL 行做可复现重建。若转换工具与随机种子无法恢复，应把 2+ 标记为历史生成产物、不可完全复现，而不是猜测补值算法或直接改成 ENSDF 的 5/2−。

本轮未修改物理规则、输入数据、golden 或运行事件。


## Run #114：⁸⁹Br 最终 spin=2 的运行时语义与补值调用链核验（SOURCE_AUDITED；转换来源仍 BLOCKED）

### 1. 先纠正一个重要歧义：spin=2 不是自旋索引

在官方 CGMF 源码 `libcgmf/include/cgm.h` 中，半整数判断宏定义为：

```c
#define halfint(x) ( (((int)(x*2.0+0.001) % 2)==1) ? 0.5 : 0.0 )
```

该宏直接检查数值自旋的两倍是否为奇数。因此，离散文件中的 `spin=2.0` 是整数自旋值，不是从零开始的索引，也不等价于 (5/2)。这与此前已核实的文件字段解析一致：`ripl2levels.cpp` 将 spin 字段直接赋给 `Level.spin`。

### 2. 运行时缺失值修复不会把当前 2,+ 改成别的值

官方 `libcgmf/src/setup.cpp` 的 `statFixDiscreteLevels()`：
- 仅在某个能级满足 `spin < 0.0` 或 `parity == 0` 时触发修复；
- 缺失 spin 时按 KCK spin-cutoff 分布抽样；
- 缺失 parity 时按均匀分布假设随机取 (+1/-1)。

官方 `libcgmf/src/specmc.cpp` 的片段显示，核素初始化后会调用 `statFixDiscreteLevels(&ncl[i])`。但本次运行时快照中的 ⁸⁹Br 基态已是 `spin=2.0, parity=+1`，不满足上述缺失条件，所以这段运行时修复逻辑不会对该基态重新抽样。

这只能排除**运行时缺失值修复**是当前已赋值记录的直接来源；不能据此推断历史生成脚本如何写入 `discreteLevels.dat`。

### 3. 转换脚本的历史定位结果

- 对官方 `lanl/CGMF` 仓库 commit `46ca6451dc5e449d7a9d0ced98eba0b593fcdf14` 做完整递归 Git tree 检查，未发现 `transformLevelDataFile.ipynb` 或 `Nucleus.py`。
- 对 GitHub path history 分别查询这两个路径，API 返回空提交列表；在当前可查询的官方仓库历史中，没有找到它们作为受版本控制文件的提交记录。
- 官方 `doc/rtd/discreteLevels.rst` 仍明确描述了该 notebook/class 和 Jπ 缺失处理规则，但文档本身不能替代实际转换实现。

### 4. 当前可支持的结论

- ⁸⁹Br RIPL 源行的数值字段为 `spin=-1.0, parity=0`，括号文字为 `(3/2-,5/2-)`；最终 CGMF 文件为 `spin=2.0, parity=+1`：**COMPUTATION_VERIFIED**（Run #113）。
- `spin=2.0` 在 CGMF 语义中为整数自旋，不是半整数索引：**SOURCE_AUDITED**。
- 当前运行时缺失值修复不会修改这条已经完整赋值的记录：**SOURCE_AUDITED**。
- 最终 `2.0,+1` 是由哪份 RIPL 版本、哪一版 notebook/class、哪一随机状态或人工处理写入：**BLOCKED**。
- 官方文档描述的“缺失 Jπ 按 KCK/随机宇称补值”是可能的处理类别，但不能仅凭该规则反推出本条最终数值，更不能把括号候选的“第一项”误说成 `2,+`。

### 5. 下一步的最小验证

不再围绕运行时 `statFixDiscreteLevels()` 做重复排查。下一步应定点解析 `ripl3-levels-2015.dat` 中 Z=35、A=89 的原始条目，并与已读取的 `ripl3-levels.dat` 行比较；同时检查该文件的版本头、日期和记录格式。若两份 RIPL 源文件均为未指派 Jπ，则生成器缺失仍是主要阻断项，应将最终 2+ 暂列为不可追溯的历史预处理产物，不猜算法、不改输入数据库、不改 E1 选择器。

本轮没有修改物理代码、输入数据库、golden 或事件矩阵。


## Run #115：官方文档规则、数据文件历史与转换器可追溯性边界

### 1. 官方文档的确切规则（SOURCE_AUDITED）

官方 `doc/rtd/discreteLevels.rst`（CGMF 1.0.0 文档，提交 `b1a10b7` 引入）明确说明：
- 专用离散能级文件由 RIPL-3 完整数据文件生成；
- 文档点名 `transformLevelDataFile.ipynb` 与 `Nucleus.py`；
- 缺失/未指定 spin、parity 的处理规则：J 按 KCK level-density systematics 选择，缺失宇称按均匀分布随机选择；
- RIPL 给出不确定能级的多个 Jπ 选择时，选第一项；
- 基态完全未知时按核素奇偶类别赋默认值；
- 文档警告任意修正可能显著影响特定 γ 衰变链研究。

这份文档没有给出逐条记录处理的优先顺序、随机数种子、解析括号候选项的精确代码，也没有证明 ⁸⁹Br 这条记录经过哪一条分支。

### 2. 数据文件历史（COMPUTATION_VERIFIED）

通过官方 GitHub commits API 按路径查询：
- `data/discreteLevels.dat` 只有两条提交记录：CGMF 1.0.0（2020-11-18，`b1a10b7`）与 CGMF 1.1.0（2021-04-30，`e333c9c`）。
- `transformLevelDataFile.ipynb`、`Nucleus.py`、`data/cgmfDiscreteLevels.dat`、`data/cgmfDiscreteLevels-2015.dat` 在官方仓库 path-history 查询中均无提交记录。
- 头文件 `libcgmf/include/ripl2levels.h` 说明运行时专用文件名为 `discreteLevels.dat`，并注释“used to be called 'cgmfDiscreteLevels-2015.dat'”。这与 RIPL 源文件 `ripl3-levels-2015.dat` 是两个不同名称，不能混淆。

### 3. 对 ⁸⁹Br 的结论边界

RIPL 原始行的数值字段 `spin=-1.0, parity=0`，文本注释为 `(3/2-,5/2-)`；当前 CI 运行时专用库记录为 `spin=2.0, parity=+1`。官方文档描述的 KCK/random/first-choice 规则只能说明转换阶段可能进行过数据修正，不能从现有证据推出这一条最终 2+ 的具体来源。尤其“第一候选”若直接对应文本括号内容，也不能解释为何最终是 2+。

因此：
- 专用文件的历史提交节点：**COMPUTATION_VERIFIED**；
- 官方文档描述的转换规则：**SOURCE_AUDITED**；
- ⁸⁹Br 最终 2+ 的具体生成分支、输入版本与随机状态：**BLOCKED**；
- 当前没有证据支持将最终值归因于运行时 `statFixDiscreteLevels()`，也没有证据支持归因于“选第一候选”。

### 4. 访问限制与后续路线

GitHub 文件读取接口对 `ripl3-levels-2015.dat` 的整文件响应超过当前接口大小限制；本轮没有拿到该文件的可核验 ⁸⁹Br 定点记录。不能把读取失败当成“记录不存在”或“与另一版本一致”。

最小后续路线：
1. 获取文件的分块/可定点读取方式，或在有该仓库完整 checkout 的环境中本地检索 ⁸⁹Br 条目；
2. 对照官方 1.0.0 与 1.1.0 的 `discreteLevels.dat` 记录，确认何时从原始 Jπ 变成 2+；
3. 若生成 notebook/class 未能恢复，则将具体生成机制标为不可追溯历史预处理，不自行补造算法。

本轮没有改动物理选择规则、数据库、golden 或模拟代码。


## Run #115：官方 CGMF 1.0.0 / 1.1.0 的 ⁸⁹Br 离散能级版本对照（COMPUTATION_VERIFIED）

### 1. 两个版本的 Git 对象已直接读取

通过官方仓库 Git tree 取得 `data/discreteLevels.dat` 的 blob：
- CGMF 1.0.0（commit `b1a10b7bb542cbb7ada12adef28935da25364c7f`）：blob `96a40d82bbcc937ab40421145e1d6cc7654eff28`，大小 2,306,451 bytes。
- CGMF 1.1.0（commit `e333c9ca3bd869032a170393a50942b31d992aeb`）：blob `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`，大小 4,250,841 bytes。

两个 blob 均已通过 GitHub blob 接口读取并按文本逐行定位 ZA=35089 的记录。

### 2. ⁸⁹Br 记录在两个版本中完全相同

CGMF 1.0.0：
```
89Br  35089   1
 0.000000   2.0  1  4.40000e+00  0
```
CGMF 1.1.0：
```
89Br  35089   1
 0.000000   2.0  1  4.40000e+00  0
```

因此，在这两个公开版本之间：
- ⁸⁹Br 基态能级条数均为 1；
- 能量均为 0；
- 自旋均为整数 (J=2)；
- 宇称均为正；
- 半衰期均为 4.40 s；
- 记录没有变化。

### 3. 版本定位结论

CGMF 1.1.0 的发布提交说明 `discreteLevels.dat` 扩展为包含全部同位素；文件总大小由约 2.31 MB 增至 4.25 MB。但 ⁸⁹Br 这一条记录在 1.0.0 和 1.1.0 中完全一致。

所以，⁸⁹Br 的 2+ 记录不是在 1.0.0 到 1.1.0 的数据扩展过程中才引入的。它**至少已经存在于 CGMF 1.0.0 发布版本**。当前比较不能确定它究竟来自更早的预处理、历史手工修订还是更早的源数据版本。

### 4. 证据状态与边界

- 两个官方发布版本的 Git blob、文件大小、目标 ZA 记录及字段：**COMPUTATION_VERIFIED**。
- 1.0.0 到 1.1.0 期间 ⁸⁹Br 记录未变：**COMPUTATION_VERIFIED**。
- 2+ 记录的首次引入时间及生成方法：**BLOCKED**。
- 不能由版本相同推断该记录物理正确；也不能据此决定将其替换为 ENSDF 的 (5/2^-)。

### 5. 下一步

沿官方 Git 历史向 CGMF 1.0.0 之前追踪 `data/discreteLevels.dat` 的首次引入提交及其 parent tree；同时检查 1.0.0 对应的源数据文件与文件头注释。如果更早历史也没有转换器，则应把 ⁸⁹Br 2+ 记录列为“历史来源不可追溯的数据项”，并将其与基于 ENSDF 的替代方案隔离保存，不能静默覆盖生产数据。


## Run #116：CGMF 1.0.0 中离散能级文件的首次入库节点与生成来源标记（COMPUTATION_VERIFIED；逐条转换算法仍 BLOCKED）

### 1. 官方路径历史与父提交核验

通过 GitHub commits API 按路径查询 `lanl/CGMF/data/discreteLevels.dat`，返回两条记录：
- CGMF 1.0.0：`b1a10b7bb542cbb7ada12adef28935da25364c7f`，提交时间 2020-11-19（committer date）；父提交为 `75960cf7625103afa0286418f3c83f53f094b189`（Initial commit）。
- CGMF 1.1.0：`e333c9ca3bd869032a170393a50942b31d992aeb`，提交时间 2021-10-20；父提交为 `09472b83a6b2c1024f0c5a70e93dcd75c931aeff`（CGMF 1.0.1 合并提交）。

直接读取 1.0.0 父提交的递归 Git tree，未发现 `data/discreteLevels.dat`；同样没有发现 RIPL level 数据文件。读取 1.0.0 发布提交的 tree，则发现：
- `data/discreteLevels.dat`：blob `96a40d82bbcc937ab40421145e1d6cc7654eff28`；
- `data/ripl3-levels.dat`：blob `c3c3a816730deef172ccbd11b0dfd58b6d197d90`；
- `data/ripl3-levels-2015.dat`：blob `3be0a27558c793837f6c3cc5deb45ea1deee7259`。

因此，`b1a10b7` 是 `discreteLevels.dat` 在当前官方 Git 历史中的首次入库提交；1.0.0 父提交没有该文件。这个结论描述的是**仓库可追溯历史**，不是数据在作者本地或外部生成环境中的绝对诞生时间。

### 2. 1.0.0 首发文件头的来源说明

直接读取 1.0.0 的 `data/discreteLevels.dat` blob，文件头原文说明：
- 该文件为 CGMF-1.0；
- 数据文件由 RIPL-3 data file 中的 evaluated discrete levels 生成；
- 缺失/未指派 spin/parity 按 CGMF manual（CPC）描述的规则设置。

这将 ⁸⁹Br 的数值变化明确定位到专用文件的生成/预处理层，而非 1.0.0→1.1.0 的后续扩展，也不是当前已核实的运行时 `statFixDiscreteLevels()` 对已赋值记录的再次补值。

### 3. ⁸⁹Br 原始行与最终行的同版本对照

同一个 1.0.0 Git tree 中：
- RIPL-3 输入 `data/ripl3-levels.dat` 的 ⁸⁹Br 行：数值字段 `spin=-1.0, parity=0`，文本候选 `(3/2-,5/2-)`；
- 最终 `data/discreteLevels.dat`：`89Br 35089 1`，能级行为 `0.000000 2.0 1 4.40000e+00 0`。

因此，同一发布快照中源数值 Jπ 未指派，而最终文件已经写入整数自旋 J=2、正宇称。不能将括号中的第一个候选直接解释成最终 2+，也不能仅凭手册概述断言该记录具体经过 KCK 抽样或某个候选解析分支。

### 4. 状态更新

- `discreteLevels.dat` 在官方 Git 历史中的首次入库提交及父 tree 不含该文件：**COMPUTATION_VERIFIED**。
- 1.0.0 同一提交树包含专用文件及两份 RIPL-3 源文件：**COMPUTATION_VERIFIED**。
- 1.0.0 专用文件头声明 RIPL-3 生成来源及缺失 Jπ 按手册处理：**SOURCE_AUDITED**。
- 1.0.0 同版本 RIPL 输入行与最终 2+ 行的差异：**COMPUTATION_VERIFIED**。
- 转换 notebook/class 的精确版本、执行顺序、随机种子、记录级分支及最终 2+ 的具体成因：**BLOCKED**。
- 数据是否在仓库初始提交之前由外部脚本或人工预生成：**BLOCKED**。

### 5. 下一步

优先从 1.0.0 发布包、文档构建源和作者可公开的辅助仓库寻找 `transformLevelDataFile.ipynb` / `Nucleus.py` 的可核验副本；并尝试对同一提交中的 `ripl3-levels-2015.dat` 做定点读取，核对其 ⁸⁹Br 记录。若工具版本或输入记录仍无法恢复，则把 2+ 标记为“可定位到 1.0.0 首发生成文件、具体生成算法不可追溯”的历史数据产物，不改生产数据库，不以 ENSDF 候选值静默覆盖。

本轮只做 Git 历史与源数据审计，不修改物理代码、离散能级数据、golden 或事件矩阵。


## Run #117：RIPL 原始记录—手册规则冲突点与 CI #221 结果（SOURCE_AUDITED / COMPUTATION_VERIFIED；生成器仍 BLOCKED）

### 1. CGMF 1.0.0 的 RIPL 原始 ⁸⁹Br 记录再次定点读取

直接读取官方 lanl/CGMF 1.0.0 的 data/ripl3-levels.dat blob（SHA c3c3a816730deef172ccbd11b0dfd58b6d197d90，27,316,178 bytes），按文本定位到 ⁸⁹Br 条目：

```text
89Br   89   35    1    0    1    1    5.909000   11.981001
  1   0.000000  -1.0  0   4.40E+00  0               (3/2-,5/2-)  2 =    100.0000 %B-     =     13.8000 %B-N
```

记录中的数值 spin/parity 字段仍是 -1.0, 0；括号中的 (3/2-,5/2-) 是文字候选标签，不是前面两个数值字段的值。该行的半衰期字段与专用文件的 4.40 s 一致。

### 2. 手册规则与最终数据之间存在尚未解释的冲突（SOURCE_AUDITED）

同一 1.0.0 发布快照的 doc/rtd/discreteLevels.rst 说明：
- spin 或 parity 缺失/未指派时，Jπ 按 KCK 系统处理，缺失宇称按均匀分布随机选择；
- 如果 RIPL 为不确定能级给出多个 Jπ 选项，则选择第一项。

但该记录的括号首选项是 3/2-，而最终 data/discreteLevels.dat 写入的是 J=2, π=+1。这两者不一致。因此目前不能简单把最终值解释成“选了第一候选”；也不能确认此记录是否被解析器识别为多候选记录，还是因数值字段未指派而走 KCK/随机补值分支。官方文档是规则说明，不是生成器源代码或逐记录执行日志。

### 3. RIPL-2015 文件的读取限制（BLOCKED / NOT READ）

data/ripl3-levels-2015.dat 在 1.0.0 tree 中确实存在，大小 70,158,325 bytes，blob SHA 3be0a27558c793837f6c3cc5deb45ea1deee7259。当前 GitHub blob 读取接口对响应长度限制为 67,108,864 bytes，完整读取请求被拒绝。本轮没有取得该文件中的 ⁸⁹Br 记录，故不能声称 2015 文件与 ripl3-levels.dat 的记录一致或不同。

### 4. GitHub Actions Run #221 实际结果（COMPUTATION_VERIFIED）

检查本分支提交 4d2f3f8d6729262693ec192fc530e8c1635b4e4b 对应的 Actions Run 44614961934：
- Configure：通过；
- Build：通过；
- Native CGMF test suite：失败，CTest 99 项中 76% 通过、24 项失败（其中执行测试失败会导致对应 diff 测试 Not Run）；
- G2 三层分析、条件历史分析、matched-history permutation、event-state model competition、fragment-state ablation、RNG seed matrix validator 等 Python 合成夹具单元测试：均通过；
- 完整 G2 neutron/mixed-history sidecar matrix：未能成功完成，因为其前置 native test suite 已失败；
- 后续基于代表性 CI 模拟的分析步骤被跳过；
- native regression baseline enforcement 因前面的回归结果失败而失败，workflow 总结为 failure。

失败的事件执行日志仍显示离散桥接处没有可映射状态。例如：
- ⁸⁹Br event 34：初态 J=3、π=+1，唯一离散态候选因 parity 被拒绝；
- ¹³⁶I、¹⁰⁵Nb、⁹⁶Y、¹³⁷I、¹³²I 等其他事件出现 angular-momentum rejection。
这些是当前分支 CI 的真实运行结果，不代表核数据已被独立评价，也不应通过放宽选择规则或更新 golden 来消除失败。

Run 页面：https://github.com/anselmiao/CGMF/actions/runs/44614961934

### 5. 状态与下一步

- 1.0.0 RIPL 源文件 ⁸⁹Br 数值字段与候选文字：COMPUTATION_VERIFIED。
- 官方手册关于 KCK/随机宇称与多候选首项规则：SOURCE_AUDITED。
- 手册所述“多候选取首项”不能直接解释最终 J=2、π=+1：COMPUTATION_VERIFIED（字段不一致）。
- 2015 RIPL 文件中的 ⁸⁹Br 记录：BLOCKED / NOT READ（接口响应大小限制）。
- 生成器对本条记录实际走过的分支、随机数状态和具体来源：BLOCKED。
- Run #221 的构建、单元测试、CTest 和 G2 matrix 先后状态：COMPUTATION_VERIFIED。

下一步应避免继续只查手册文字。优先找 RIPL-2015 文件的可分块/本地镜像读取方式，或获取其压缩发行包后只提取 Z=35、A=89；同时检查 CGMF 1.0.0 文档构建源/作者公开仓库是否保留 notebook。CI 方面应从 ⁸⁹Br event 34 与其他角动量失败事件的最小复现入手，先区分数据映射问题与物理选择规则问题；不得先改选择规则、数据库或 golden。

本轮只做数据、文档和 CI 结果审计，没有修改物理代码、输入数据库、golden 或事件矩阵。


## Run #118：PR 侧 CI 的 G2 sidecar matrix 首个 case 失败定位（COMPUTATION_VERIFIED）

对 PR #3 对应的 Actions Run 222（Run ID 44614976464）进一步读取 job log：
- Build 与前置 Python 单元测试、31 组 RNG seed range validator 均通过；
- G2 sidecar matrix 在第一个 case 即停止：Cf-252 spontaneous fission，ZAID=98252，En=0.0 MeV，event_ids=1..200，seeds=1..200；
- runG2SidecarMatrix.py 调用 cgmf.x 生成 sidecar-on histories 时，进程退出码为 255，Python 抛出 CalledProcessError；
- 该轮因此没有进入后续 30 个矩阵 case；矩阵产物只包含失败前/失败时可保存的诊断文件，不能视为完整数据集；
- native regression baseline enforcement 因前置 matrix 失败而失败。

该日志片段尚未给出 cgmf.x 的完整 stderr 根因；需要读取本次 artifact cgmf-g2-mixed-history-matrix（artifact ID 14572684411）中的 sidecar-on.stdout/stderr、data audit 和配置文件，才能判断是否与前述 native CTest 的离散桥接失败同源。当前不能把 exit 255 直接归因于 ⁸⁹Br，也不能认定是 sidecar 写入逻辑本身故障。

Run 页面：https://github.com/anselmiao/CGMF/actions/runs/44614976464

本轮只追加 CI 日志诊断，没有修改模拟代码、物理规则、数据文件或 golden。


## Run #119：⁸⁹Br 原始记录、最终派生记录与运行时修补代码的三方对照（COMPUTATION_VERIFIED / SOURCE_AUDITED）

### 1. 官方 1.1.0 完整 blob 定点提取（COMPUTATION_VERIFIED）

本轮直接读取官方 `lanl/CGMF` 的 `data/discreteLevels.dat` Git blob（SHA `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`，4,250,841 bytes），不依赖网页预览截断。按 ZA=35089 定位到第 50,378 行：

```text
89Br  35089   1
 0.000000   2.0  1  4.40000e+00  0
```

同一官方版本的 `data/ripl3-levels.dat` blob（SHA `c3c3a816730deef172ccbd11b0dfd58b6d197d90`，27,316,178 bytes）第 78,451 行：

```text
89Br   89   35    1    0    1    1    5.909000   11.981001
  1   0.000000  -1.0  0   4.40E+00  0               (3/2-,5/2-)  2 =    100.0000 %B-     =     13.8000 %B-N
```

因此同一公开发布快照的 RIPL 输入数值字段是 spin=-1.0、parity=0，注释给出 (3/2-,5/2-)；专用文件写入 J=2.0、π=+1。半衰期均为 4.40 s。该结果复核了前轮字段差异，并补上了专用文件 blob 的直接提取证据。

### 2. 官方专用文件头的来源声明（SOURCE_AUDITED）

官方 `data/discreteLevels.dat` 文件头声明：
- 文件由 RIPL-3 数据文件中的 evaluated discrete levels 生成；
- 缺失 spin/parity assignments 按 CGMF manual（CPC）中描述的规则设置。

这证明 2.0,+1 是预处理后文件中的已赋值记录；它不是 RIPL 原始数值字段，也不是 ENSDF 的直接原样抄录。

### 3. 运行时 C++ 源码排除一个常见误归因（SOURCE_AUDITED）

读取官方 `libcgmf/src/ripl2levels.cpp`：
- `readDiscreteLevelData()` 从专用 `discreteLevels.dat` 读取固定宽度字段，并将 spin、parity 直接读入 Level 对象；
- `fixLevels()` 只在基态 spin<0 或 parity==0 时进入缺失赋值处理；本条记录进入运行时文件时已经是 spin=2.0、parity=+1，不满足该条件；
- 其 `riplGSonly()` 的偶奇默认规则，对 Z=35、A=89（N=54，奇 Z、偶 N）会给出 J=1/2、π=+1，而不是 J=2、π=+1；
- 源码中另有 `riplSelectCandidate()` 辅助函数，其候选字符串解析逻辑对文本首项 `(3/2-,5/2-)` 将得到 J=3/2、π=-1；但本轮没有找到证据证明此函数是历史 Python 预处理 notebook 的实际实现或被该生成过程调用。

因此，不能把最终 (2.0,+1) 归因于当前运行时 `fixLevels()/riplGSonly()`；也不能把它归因于“选择第一候选”。当前最稳妥定位仍是：该赋值在专用离散能级文件生成阶段已经形成，而该阶段的 Python notebook/class 尚未恢复。

### 4. 转换器搜索结果与边界

- 官方仓库 master、doc、rev2 三个分支的递归 Git tree 均未包含 `transformLevelDataFile.ipynb` 或 `Nucleus.py`。
- 官方仓库按这两个路径查询提交历史均无记录。
- GitHub 全局代码搜索目前只命中官方手册中对这两个文件的文字引用，没有找到可核验的公开副本。
- 本轮没有成功读取 70 MB 的 `ripl3-levels-2015.dat`；该版本的 ⁸⁹Br 记录仍为 NOT READ，不能推断它与 2009/当前 RIPL 输入相同。
- 1.0.0 与 1.1.0 两个官方专用文件版本中的 ⁸⁹Br 记录已在前轮核实完全相同；本轮进一步确认当前 1.1.0 官方 blob 的完整内容。

### 5. 证据状态

- 官方 1.1.0 RIPL 原始行与最终专用文件行：**COMPUTATION_VERIFIED**。
- 专用文件头的 RIPL-3 生成来源声明：**SOURCE_AUDITED**。
- 当前运行时 loader 直接读取已赋值字段、不会对本条记录执行缺失基态补值：**SOURCE_AUDITED**。
- 运行时奇偶默认函数对 ⁸⁹Br 会给出 1/2+，与最终 2+ 不同：**COMPUTATION_VERIFIED（源码分支逻辑推演，非本条生成日志）**。
- 最终 2+ 的历史 Python 预处理分支、随机种子、KCK 输入及记录级日志：**BLOCKED**。
- RIPL-2015 文件中的 ⁸⁹Br 行：**BLOCKED / NOT READ**。

### 6. 下一步

不再重复检索官方仓库中已确认不存在的 notebook 路径。下一步转为核对同一原始 RIPL 记录的字段语义与 RIPL-2015/更新版数据记录；并寻找 1.0.0 发布包、OSTI 技术报告附件或其他可公开的历史发行归档。若生成器仍不可获得，则将 (2.0,+1) 保留为“官方发布的历史预处理值，生成细节不可追溯”，并将 ENSDF/RIPL 后续评估值作为独立对照，不覆盖生产库。

本轮只做 Git blob、官方文档与 C++ 源码审计，没有修改物理选择规则、数据库、golden、模拟代码或事件矩阵。


## Run #120：全库自旋量子数奇偶一致性审计（COMPUTATION_VERIFIED；生成机制待定位）

### 1. 审计范围与解析方式

直接读取官方 CGMF 1.1.0 `data/discreteLevels.dat` blob（SHA `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`，4,250,841 bytes），按文件结构解析：
- 核素头记录提供 ZAID 与离散能级数；
- 每个能级记录按固定列读取能量、自旋（hbar）、宇称和后续 γ 跃迁条数；
- 根据每条能级记录的跃迁条数跳过 γ 分支行，再读取下一条能级；
- 对全部核素与能级计数，检查 A 奇偶与 2J 奇偶是否一致。

解析得到 3,330 个核素、45,676 条离散能级；没有发现格式解析失败。该审计仅检验角动量量子数的整数/半整数格点，不检验能级能量、宇称是否符合实验，也不等同于 ENSDF 逐条评价。

### 2. 全库结果

发现 **114 条**自旋量子数与核子数奇偶性不一致的记录，分布于 **54 个核素**：
- 114 条全部是奇质量数 A 的核素，却记录整数 J；
- 没有发现偶质量数 A 却记录半整数 J 的反向异常；
- ⁸⁹Br 基态 (A=89, J=2.0) 是其中一条。

对原子核，奇数 A 的总核子数为奇数，角动量 J 应为半整数；偶数 A 应为整数。因此按专用文件头及 C++ 读取代码中明确的 spin (hbar) 字段语义，这 114 条记录属于角动量量子数格点不一致，需要逐条复核，不能直接用于物理解释。

异常记录按核素分布的前列包括：³⁵S（10 条）、⁴³K（9 条）、³⁷Cl（8 条）、⁹⁵Nb（7 条）、²³Mg（6 条）、⁷³Ga（6 条）；其余分布在其他奇 A 核素。异常并非仅集中于 ⁸⁹Br。

### 3. 原始 RIPL 对照：异常至少在预处理后发生过变化

本轮进一步从同一官方发布快照的 RIPL-3 原始 blob 中抽查了异常核素：
- ¹⁵C 的 6.417 MeV 能级，RIPL 原始记录为 J=3.5、π=-1，附有 `(3/2 TO 7/2)` 范围标签；CGMF 专用文件对应记录为 J=2.0、π=-1。
- ²³Mg 的若干能级在 RIPL 原始文件中为半整数 J，例如 4.685 MeV 为 J=2.5、5.691 MeV 为 J=1.5、5.711 MeV 为 J=4.5、6.236 MeV 为 J=0.5、6.507 MeV 为 J=4.5、7.017 MeV 为 J=3.5；CGMF 专用文件对应的 6 条记录均为整数 J。

这些抽查表明至少部分整数 J 异常不是 RIPL 原始行照抄，而是在生成专用文件时出现了改变。当前不能据少数样本断言 114 条全部由同一个转换错误造成，也不能判定是解析、KCK 赋值、范围标签处理还是人工修订。

### 4. 对 ⁸⁹Br 事件分析的影响

⁸⁹Br 不应再被当作一个孤立的“基态 Jπ 与 ENSDF 不一致”案例。它属于一个更广泛的离散能级库自旋格点一致性问题。因而：
- event 34 的 parity rejection 仍然是对当前运行时输入库的程序行为描述；
- 当前库中 ⁸⁹Br 的 J=2、π=+1 不应未经核验就作为可信物理基态；
- 不得据此直接修改 E1 选择器、回填 ENSDF 值或重写 golden；
- 在全库问题厘清前，所有依赖这些记录的 G2 物理解释应将核数据可靠性列为单独限制。

### 5. 状态与下一步

- 官方 1.1.0 专用文件 3,330 个核素 / 45,676 条能级的结构化解析：**COMPUTATION_VERIFIED**。
- 114 条奇 A 整数 J 记录、涉及 54 个核素：**COMPUTATION_VERIFIED**。
- ¹⁵C 与 ²³Mg 原始 RIPL / 最终专用文件抽查差异：**COMPUTATION_VERIFIED**。
- 114 条异常是否由同一个转换器缺陷造成：**BLOCKED**。
- 每条异常记录的 ENSDF 评价与可信 Jπ：**NOT YET AUDITED**。

下一步应将 114 条异常导出为只读审计清单（ZAID、能级能量、J、π、RIPL 原始 Jπ/不确定性标签），再按原始输入字段分组：明确 Jπ、范围/候选 Jπ、缺失 J、缺失宇称、完全未指派。优先检查 ⁸⁹Br、²³Mg、¹⁵C 和高频异常核素；在完成分类前不改动生产数据。

本轮只做全库数据完整性审计与报告更新，没有修改物理代码、数据文件、golden 或模拟矩阵。


## Run #121：114 条异常记录的 RIPL 原始行联表清单（COMPUTATION_VERIFIED）

### 1. 只读审计文件已生成并提交

新增文件：
`research/audits/cgmf-1.1.0-spin-quantization-audit.csv`

该文件逐条列出 114 条奇 A 整数 J 异常，包括：
- 核素名、ZAID、质量数 A、能级能量；
- CGMF 专用文件中的 J、宇称及行号；
- RIPL 原始文件中按核素和能量匹配到的能级序号、J、宇称和原始记录；
- 未匹配记录明确写为 `NOT_MATCHED`，不将其解释成源数据缺失。

### 2. 原始 RIPL 联表结果

114 条异常中：
- **85 条**成功匹配到同一核素、相同能量的 RIPL 原始能级记录；
- 其中 **77 条** RIPL 原始记录本来具有半整数 J，但 CGMF 专用文件变成整数 J；
- 另外 **8 条** RIPL 原始 spin 未指派；
- **29 条**本轮自动联表未匹配成功，可能涉及能量精度、记录差异或解析覆盖不足；不能将其认定为 RIPL 不存在对应能级。

示例：
- ¹⁵C，6.417 MeV：RIPL J=3.5、π=-1；CGMF J=2.0、π=-1。
- ²³Mg，4.685 MeV：RIPL J=2.5、π=+1；CGMF J=1.0、π=+1。
- ²³Mg，5.691 MeV：RIPL J=1.5、π=+1；CGMF J=2.0、π=+1。
- ⁸⁹Br，0 MeV：RIPL J 未指派、π 未指派，并有 (3/2-,5/2-) 标签；CGMF J=2.0、π=+1。

这进一步表明问题不能只归因于“缺失 J 的随机补值”：至少 77 条匹配记录在 RIPL 原始文件中已有半整数 J，专用文件却写成整数 J。可能涉及不确定范围/标签的处理、转换器字段映射或其他历史预处理逻辑；当前没有生成器源码，仍不能断言具体原因。

### 3. 证据与限制

- CSV 的 114 行来自完整 CGMF 1.1.0 专用文件解析：**COMPUTATION_VERIFIED**。
- 85 条 RIPL 原始记录联表：**COMPUTATION_VERIFIED**。
- 77 条原始半整数 J 被写成整数 J：**COMPUTATION_VERIFIED**。
- 29 条未匹配记录：**BLOCKED / NOT MATCHED**，需要人工或更精确匹配。
- 转换器的具体缺陷、错误发生位置与修复方式：**BLOCKED**。

### 4. 后续

下一轮先对 CSV 中 85 条已匹配记录做规则分组，按 RIPL 原始标记（明确 Jπ、范围、多个候选、未指派）统计转换后的变化；对 29 条未匹配项另做能量容差与核素头解析复核。之后才决定哪些记录需要 ENSDF 逐条复核。当前不修复、不覆盖专用数据，也不改 E1 选择器。

本轮只新增只读审计 CSV 与报告，没有修改物理代码、数据库、golden 或模拟矩阵。


## Run #122：RIPL 自旋异常分类与 ¹³⁶I 运行时审计扩展

本轮只读分类结果及证据边界见 [独立审计记录](research/audits/cgmf-spin-quantization-classification-run122.md)。

同时将运行时数据审计目标从 ZAID 35089、53132 扩展为增加 53136（¹³⁶I），用于在下一次 CI 运行时直接打印该核素的离散能级数及每条能级的能量、J、宇称。该改动仅增加诊断输出，不修改核数据、物理选择规则、级联逻辑或 golden。

当前基线 Run #236 已确认：Build、原生 CTest 和前置合成测试通过；G2 sidecar matrix 在 Cf-252 自发裂变 case 的 event 6 因 ¹³⁶I lower-cut 离散态无法映射而中止。原始失败 artifact 只含 event 1–5，不能作为完整矩阵数据。



## Run #123：Run #237/#238 的 ¹³⁶I E1 桥接根因与 ENSDF 对照（COMPUTATION_VERIFIED / SOURCE_VERIFIED）

独立审计记录：[Run #237/#238 ¹³⁶I discrete-bridge audit](research/audits/cgmf-run237-238-136I-discrete-bridge-audit.md)。

关键新结果：
- Run #237（push）与 #238（PR）均完成但失败；Configure、Build、合成分析测试、RNG validator 均通过；真实 G2 sidecar matrix 在第一个 Cf-252 case 失败，后续分析被跳过。
- 运行时读到 ¹³⁶I 唯一离散态为 0 MeV、Jπ=1⁻。NNDC ENSDF 2018 年 A=136 评价确认基态为 (1⁻)，第一激发态为 86.73 keV；本次失败事件初始能量约 79.30 keV，故该第一激发态高于事件能量，不能作为候选。
- `specmc.cpp::mcSelectE1DiscreteBridge` 对离散桥接硬编码 E1 选择条件。事件初态为 Jπ=7⁺，唯一可达候选为 1⁻ 基态，ΔJ=6，因此被 E1 角动量条件拒绝。诊断计数为 energyRejected=0、spinRejected=1、parityRejected=0。
- 这将失败定位到 E1-only bridge 与当前低能高自旋 continuum 状态之间的不兼容；尚不能据此断言应扩展到 E2/M6，也不能直接放宽选择规则。下一步先审计生产级联中多极性与强度的实际采样，以及低能 continuum 的 Jπ population。
- Run #238 native regression 日志还出现 ¹⁰⁵Nb、⁹⁶Y、¹³⁷I、¹⁰⁵Zr、¹³⁸Te 等多个核素的相似不可映射失败；不是单一 ¹³⁶I 数据问题。不得改写 golden、跳过失败事件或用部分 histories 做 P/H/O 推断。

本轮没有修改生产物理规则、数据库、golden 或事件矩阵；只增加诊断审计报告。



## Run #124：低能连续态自旋宇称来源审计（SOURCE_VERIFIED / EVENT TRACE BLOCKED）

独立审计：[low-energy continuum population audit](research/audits/cgmf-low-energy-continuum-population-audit-run124.md)。

本轮追踪到一个比离散桥接更上游的机制：
- `setup.cpp::statSetupEnergyBin` 在最高离散能级 `elmax == 0`（当前只有基态）时，将 `ncont` 设为 `ntotal-1`，即把连续态能量网格延伸至零激发能。
- `setup.cpp::statSetupLevelDensity` 在这些网格上逐格填充模型能级密度、自旋分布和 50/50 宇称分布。
- 仅有一个离散态时，`ldLevelSpinCutoff` 返回 0，之后采用核素质量系统学的 spin-cutoff。于是低能连续态并不被基态 (J^\pi) 限制。
- `specmc.cpp::mcFindNext` 从累积的连续态 population bins 抽样，因此低能高自旋连续态可以进入 Monte Carlo history。此机制与 ¹³⁶I 79.303 keV、(7^+) 失败事件高度吻合，但其具体 event ancestry 尚未加诊断追踪，不能标成已逐事件验证。
- `gampop.cpp::specTransitionGamma` 的生产 gamma population 同时包括 E1、M1、E2；而 `mcSelectE1DiscreteBridge` 仅允许 E1，二者范围不一致。不过对 (7^+\to1^-)，(Delta J=6)，即使把桥接扩为 E1/M1/E2 也无法解决。

因此下一步不是直接放宽 E1，而是先测量低能 continuum population 是否在实验核能级结构不支持的区域产生伪连续态。必须加 per-event ancestry / per-bin multipole contribution diagnostics，再对所有失败核素与 ENSDF/RIPL 的第一激发态作比较。未获得物理依据前，不改变 lower-cut、level density、gamma strengths、离散数据库或 golden。




## Run #125：¹³⁶I event 6 低能连续态 ancestry 已由运行时诊断确认（COMPUTATION_VERIFIED）

独立审计更新：[low-energy continuum population audit](research/audits/cgmf-low-energy-continuum-population-audit-run124.md)。

在 Run #253（PR，SHA `05876bf91975a86ebcec28081bbd28fc10c99b6e`）artifact 的 `sidecar-on.stdout` 中，新增诊断记录了 ¹³⁶I、HF、event 6 的完整关键片段：
1. (E=0.208422) MeV、(J^\pi=7^-) 的连续态，抽样到中心能量 (0.058422) MeV、(7^+) 的连续态；
2. 经过代码中的 bin 内能量扰动，下一轮日志中的当前态为 (E=0.079303) MeV、(7^+)；
3. 下一低能 bin 中心为 (0.029303) MeV，触发 lower-cut 后，桥接仍尝试从当前 (0.079303) MeV、(7^+) 态连接到唯一离散基态 (1^-)，因 E1 的 (Delta J=6) 被拒绝。

(7^-\to7^+) 满足 (Delta J=0) 且宇称改变；在当前 E1/M1/E2 生产通道中，E1 是允许通道。因此这条低能 (7^+) 连续态不是单纯由桥接阶段臆造，而是由当前连续态 population + E1 γ 跃迁 + bin 内能量扰动的组合生成。该状态位于 ENSDF 第一激发态 86.73 keV 以下，说明当前连续态模型确实把统计连续谱延伸到了该核素已评价能级结构不支持的能量区间。

诊断代码只输出 event 1–10 的低能 population bins 与抽样前后状态，不改变 RNG、population、转移选择或历史记录。Run #253 仍在真实 sidecar matrix 阶段失败，完整矩阵和后续 P/H/O 分析仍未执行。下一步应量化不同核素的低能连续态人口及首个激发态阈值关系；在物理依据和跨核素检验完成前，不改变 continuum cutoff、level density、gamma strength 或 lower-cut。


## Run #126：native regression 12 条桥接失败与 ENSDF 首激发态交叉分类

详细矩阵已追加到 [low-energy continuum population audit](research/audits/cgmf-low-energy-continuum-population-audit-run124.md)。

Run #253 的 `LastTest.log` 中 12 条 bridge diagnostics 覆盖 8 个核素，**每条均为 `ndisc=1`**。交叉 ENSDF 后，必须把统一条件拆成两类：
- **低于第一激发态的伪连续区间**：¹³⁶I（86.73 keV）、¹³⁷I（243.3 keV）、¹³⁸Te（461.10 keV）、⁸⁹Br（130.3 keV）的失败能量均低于首个 ENSDF 激发态。
- **已知离散态在事件能量范围内却未进入运行数据库**：¹³²I（22 keV 首个暂定/异能态，失败能量277 keV）和⁹⁶Y（122.297 keV 首激发态，失败能量186.7 keV）。这两种情况不能只靠调整 continuum lower threshold 处理，必须先核实并修复离散数据库覆盖。
- ¹⁰⁵Zr、¹⁰⁵Nb 的 ENSDF adopted-level 数据集已确认存在，但首个激发态能量尚待提取，暂不分类。

因此目前确认的是同一个软件条件 `ndisc=1`，但它导致至少两种不同的数据/模型问题。不能据此全局修改 continuum cutoff，也不能把 E1 桥接失败全部归因于一个核物理原因。下一步先完成 ¹⁰⁵Zr/¹⁰⁵Nb 的 ENSDF 首能级提取，再回到实际 `discreteLevels.dat` 逐核素对照来源、筛选和能级完整性。



## Run #127：RIPL Nmax 完整性截止与 G2 bridge 失败重分类

独立审计：[RIPL Nmax / bridge reclassification](research/audits/cgmf-ripl-nmax-and-bridge-reclassification-run127.md)。

关键修正：Run #126 对 (^{132}\mathrm I)、(^{96}\mathrm Y) 等核素的“已知激发态未进入运行数据库”暂时归类为可能的数据遗漏；本轮读取 RIPL-3 原始 header 后发现，8 个失败核素全部是 (N_{\max}=1)。RIPL 的 (N_{\max}) 是能级方案完整性截止，不是原始观测能级总数。IAEA 手册指出，已知能级少于 20 个或不确定能级超过 2 个、未进行恒温拟合时，默认 (N_{\max}=1)。CGMF 的 `riplSetNmax` 在 `reassign` 模式使用 (N_{\max})，而 `normal` 模式使用 Nc。因此 (^{132}\mathrm I)、(^{96}\mathrm Y)、(^{105}\mathrm{Nb}) 的较高已观察能级未进入专用文件，不能直接认定为意外丢失；必须区分 completeness cutoff 与实际数据损坏。

另一个独立问题是 (^{89}\mathrm{Br})、(^{105}\mathrm{Zr}) 的专用文件基态分别记录为 2+、4+，但二者 A 均为奇数，整数自旋不符合核子数奇偶性。(^{89}\mathrm{Br}) 的 ENSDF 2021 基态为 ((5/2^-)\)，首激发态为 130.3 keV、((3/2^-)\)。因此它的 bridge parity rejection 不能被当作单纯的 E1/M1 选择器问题。

Run #260/#261 均失败于 Cf-252 首个 sidecar case；两次 CTest artifact 均为 99 项中 87 项通过、12 项失败，12 条 bridge diagnostics 覆盖 8 个核素。原生 CTest step 的 `continue-on-error: true` 会使步骤摘要显示 success，但最终 native regression enforcement 读取真实 outcome 并失败。每个 sidecar artifact 只有 21 条 neutron transitions、10 条 mixed-history summaries，RNG audit 为空；不能用于 P/H/O 统计推断。

本轮只做 RIPL 字段、CGMF 源码、ENSDF 与 CI artifact 的审计和重分类；没有修改生产数据、物理选择规则、golden 或 RNG。下一步先核验 (^{105}\mathrm{Zr}) ENSDF，并开展 test-only 的 `N_{\max}) / Nc / 逐能级可信度选择对照，不直接切换生产 cutoff。



## Run #128：离散能级转换链因果修正与 Run #266/#267 复核

独立审计：[discrete-level conversion path correction](research/audits/cgmf-discrete-level-conversion-path-correction-run128.md)。

本轮发现 Run #127 对 RIPL (N_{max}=1) 与生产专用离散能级文件 `ndisc=1) 的因果联系说得过强，现予修正：

- 生产 `readDiscreteLevelData()` 直接读取预处理后的 `DISCRETEDATA`，逐条加载文件中的能级；生产 `getDiscreteLevels()` 只按文件头给出的记录数复制到运行时。
- `riplSetNmax()` 的 `normal/Nc)、`reassign/Nmax)、`all/Nol` 选择逻辑存在于 `#ifdef DEVUTIL` 的原始 RIPL 辅助读取路径。它不能单独证明当前生产专用文件的历史生成逻辑。
- CGMF 官方手册明确说明，专用离散能级文件由 `transformLevelDataFile.ipynb` 和 `Nucleus.py` 处理生成，且包括缺失 Jπ 与 gamma transitions 修复。当前 fork 与上游 master tree 均未找到这两个转换器文件。因此，RIPL header 的 (N_{max}=1) 与专用文件 `ndisc=1) 是已核实的相符事实，但直接因果链仍为 **BLOCKED**。

最新 Run #266（push）与 #267（PR）均使用提交 `a7acc2e1a629b1657c03ab35feec05f36569b9ab`，均失败。Run #267 build 与合成测试通过，但 G2 sidecar matrix 在 Cf-252 SF event 6、ⁱ³⁶I 的 79.303 keV、(7^+) lower-cut bridge 处失败；native CTest 有 12 项执行失败。artifact 只有 21 条 neutron transitions、10 条 mixed-history summaries，RNG audit 为空，不是完整矩阵样本。

本轮没有修改生产核数据、物理规则、RNG、golden 或模拟矩阵。下一步先恢复/追溯历史 Python converter，再做 RIPL 原始行—专用文件—运行时对象的逐核素三段式审计；在转换链未复原前，不把 (N_{max})、(N_c) 或 `Nol` 任一模式直接替换进生产流程，也不恢复 P/H/O 竞争分析。



## Run #129：基态 Jπ 转换一致性审计与 Run #270 复核

独立审计：[ground-state Jπ conversion consistency](research/audits/cgmf-ground-state-jpi-conversion-consistency-run129.md)。

Run #270（ID `44692563592`，SHA `992c51c1f50b26032e9253bfc2d6d99db852ef0e`）Build 与合成测试通过，但完整 G2 sidecar matrix 在 Cf-252 SF event 6、ⁱ³⁶I、79.303 keV、(7^+) lower-cut bridge 处失败。G2 artifact 只有 21 条 neutron transitions、10 条 mixed-history summaries，RNG audit 为空；native regression 有 12 项失败，12 条 bridge diagnostics 覆盖 8 个核素。

本轮直接比较当前分支 RIPL-3 原始数据、专用 `data/discreteLevels.dat` 与 CGMF 官方手册，发现两个明确的公开规则/生产输出差异：

- ⁸⁹Br：RIPL 基态 (J=-1,pi=0)，候选文本为 ((3/2^-,5/2^-))；CGMF 专用文件却记录 (2^+)。这与手册“候选取第一项”的说明不一致。该核素正是 native regression 中发生 parity bridge rejection 的对象。
- ¹⁰⁵Zr：RIPL 基态 (J=-1,pi=0)，无候选文本；CGMF 专用文件却记录 (4^+)。按手册对完全未知奇质量数基态的默认规则，应为 (1/2^+)。这与公开文档规则不一致。

本轮批量筛查到 528 个 RIPL 第一能级 J/π 未指派的匹配核素，其中 462 条无候选文本；机械套用公开默认规则时 329 条输出不同。但手册“completely unknown ground state”的适用范围尚需历史转换器确认，因此这 329 条只是待核验差异，不直接定性为错误。

结论是：生产专用文件中至少有两个可复核的 Jπ 输出与公开手册规则不一致，历史 Python 转换器具体实现及差异成因仍 **BLOCKED**。不据此自动覆盖数据，不改物理规则、RNG 或 golden。完整 G2、P/H/O 与气论证据状态仍未升级。
