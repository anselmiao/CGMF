# G2 Fix Discrete Handoff ZIP 审核（Run #281）

**审核对象**：`g2-fix-discrete-handoff.zip`（11 files）  
**目标分支**：`qi/fix-discrete-start-index`  
**包声明基线**：`1562f0145a04d0da543b9d7187703fe34cd00952`  
**审核时分支 HEAD**：`ca7763f2a72584b134d07bbe1df457f7c2571ad4`  
**性质**：移植前代码/数据/准入逻辑审计；本次不修改生产 C++、核数据、随机种子或 golden。

## 1. 总结

该 ZIP 的分层思路值得吸收：核素准入（N1–N4）、事件准入（E1–E4）、失败事件隔离、连续态 floor 对照、基态 Jπ opt-in override。但不能原样合并。

本次确认：
- 包内 patch 头部记录的四个现有 C++ 文件基线 blob，与审核时目标分支当前 blob 一致：
  - `specmc.cpp`: `3c283dff4bfecb821c168301025f7be1f66b614a`
  - `cgmf.cpp`: `af315c7aedaabe570f536f548813dfcf227d632e`
  - `setup.cpp`: `f4861e1c033b45550ca13c3170e9c525547faa5d`
  - `ripl2levels.cpp`: `ca52f32948c6a59a8e73f8874d45337249606a25`
- 因此代码文件自包声明的旧基线以来没有变化；这使三个 patch 具备进一步做真实 `git apply --check` 的条件，但本轮尚未声称已运行该命令或已编译。
- 包内 89Br 的两个 CSV 对同一核素给出冲突值：correction 表为 5/2−，public reference 表为 3/2−。NNDC 当前 ENSDF adopted 页面列为 `(5/2−)`，并说明该赋值来自 shell-model 预测及 Br 同位素能级结构类比；因此 public CSV 的 3/2− 不能作为已核实值。括号也必须保留，不能把模型/类比赋值写成无条件实验证实。
- 另外 14 个 Jπ 值、527 个截断核素、各核素 RIPL `nol/nmax/nc` 与运行时数据对应关系，本轮未逐核独立复现，继续标记 REPORTED_UNVERIFIED。

## 2. Patch 兼容性和风险

### Patch A：事件隔离

可借鉴“事件级事务隔离”思想，但当前 patch 不应原样合并：
- skip log 的 `event_id` 使用局部 `i+1`，没有记录实际 RNG seed（代码实际 seed 表达式为 `i + ip*nevents + startingEvent`），多批次/多次运行下无法唯一定位事件。
- 没有记录 run identifier、fragment side、实际 seed、失败发生在构造/记录哪个阶段。
- RNG audit 行在 `cgmfEvent` 构造成功后才写；被跳过事件不会有对应 RNG audit 记录。该行为可以接受为 failure-isolated diagnostic，但必须明确记录缺失 seed，且不得进入 audited-seed model competition。
- `g2ResetSidecarStaging()` 目前只清理 `g2PendingEvent`；移植前必须审查 sidecar transaction 中是否还有其他跨事件暂存状态，证明 LF/HF 半事件不会残留。
- `printSummaryEvents(event)` 的 null guard 是必要的，但应增加连续失败、首事件失败、末事件失败和多个 `ip` 批次测试。
- 跳过后重新设置每个事件的 RNG seed 可隔离随机流，但输出事件序号和 seed 必须分别保存，不得混用。

建议：保留默认 fail-closed；skip 作为独立诊断开关。结构化 skip 记录至少包含 run_id、global_event_index、rng_seed、Z/A、fragment_side、site、E/J/pi、exception category。增加 LF-only/HF-only/两侧均失败/连续失败的事务测试。

### Patch B：continuum floor

只可作为 opt-in 对照实验，不是离散桥接修复：
- 仅在 `elmax==0` 时生效，默认行为不变的意图清楚。
- per-nuclide 表解析缺少严格输入校验：重复 ZAID、非有限/负能量、空文件、文件打不开、floor 超过网格范围等没有显式诊断。
- “RIPL 首个 E>0 能级”不自动等于 CGMF 连续态物理下界；需核对 RIPL level assignment、Nmax/Nc/Nol 语义、CGMF continuum population 和实验 γ/ν 结果。
- 对照结果应单独标记 floor configuration、表文件 hash、缺失核素回退情况；不得与默认模型混合统计。

### Patch C：ground-state Jπ override

采用外部 opt-in 文件而不覆盖生产文件的方向正确，但需增加：
- 对 ZAID 唯一性、J≥0、两倍自旋整数性、parity∈{-1,+1}、是否确为基态记录的检查；
- 每条 override 的来源版本、引用、赋值状态（adopted/tentative/systematics）、原值/新值审计日志；
- 冲突时 fail closed，不允许“最后一行覆盖前一行”；
- 不应把 tentative/compilation 数据默认加载为生产修正。

## 3. 准入脚本缺陷

### `admission_classifier.py`

1. N1 对 even-even 只检查 `J=0`，没有检查 ground-state parity=+1；计划文字写的是 `0+`，代码未实现完整条件。
2. odd-A 半整数检查用浮点 `s != int(s)`，应改为带容差的 `2Jinmathbb{Z}` 检查，并同时验证 J 非负。
3. N4（odd-A integer spin）与 N1 的 odd-A 分支重复；应保留为独立 anomaly code，但不能将重复计数误解为两条独立证据。
4. N2 将 public CSV 中的值视为单一确定参考，未保留来源状态、评价日期、括号/不确定性和冲突候选。89Br 的 3/2− vs (5/2−) 已证明该设计会产生错误 mismatch。
5. N3 的 `ndisc < nc` 判据尚未证明语义正确。RIPL header 的 `nol`、`nmax`、`nc` 不可互换；必须依据 RIPL-3 格式定义与 CGMF 转换器实际使用字段逐项验证，不能仅凭变量名判定截断。
6. 数据路径硬编码 Windows 本机目录，不适合 CI/仓库复现；应使用显式 CLI 参数或相对仓库路径。
7. 读取器对 malformed/truncated records 多处静默跳过，可能把解析失败伪装成数据缺失；应输出 parse-error ledger 并在关键输入损坏时失败。

### `event_admission.py`

1. 只按 `event_id` 分组，未按 `run_id`/seed/source file 分区；不同运行 event_id 重复会串组。
2. 同一 event_id 同一 fragment_side 重复出现时，字典赋值会静默覆盖，必须判为 duplicate/error。
3. 仅检查 LF/HF 是否成对和核素等级；E3（无不可映射桥接/隔离状态）与 E4（A/Z/U/J/pi、TKE/TXE 完整）没有实现。
4. 未区分 ADMITTED、CONDITIONAL、REJECTED、INCOMPLETE、SKIPPED、PARSE_ERROR 等事件状态；不能将被 skip 的事件简单从分母消失。
5. 输出文件名仅由父目录 basename 决定，存在覆盖风险；应包含 run id / input stem / manifest hash。

## 4. 89Br 来源裁定（当前可支持的范围）

NNDC/ENSDF 的 ⁸⁹Br adopted level 页面将基态列为 `(5/2−)`。页面注释指出 Jπ 依据 2021 年 shell-model 预测以及 ⁸⁷Br 实验能级结构和其他 Br 同位素基态的类比；另提到理论计算曾提出 1/2+。因此：
- ZIP correction CSV 的 5/2− 与当前 NNDC adopted 页面一致；
- ZIP public reference CSV 的 3/2− 与当前 adopted 页面冲突，应标记 SOURCE_CONFLICT / stale-or-mis-sourced，不能继续作为 N2 参考；
- 5/2− 的括号与赋值依据必须保留；它不是本轮独立实验测得的无条件确定自旋；
- 89Br 修正可进入 PROVISIONAL/ADOPTED-EVALUATION 层，不应因此直接把该核素的完整离散谱或 E1 bridge 标记为已修复。

来源：NNDC ENSDF ⁸⁹Br adopted levels（Evaluated Nov 2021 页面）及 ⁸⁹Br ENSDF dataset index。当前 ENSDF 数据体系持续更新，正式导入时必须固定下载版本和文件 hash。

## 5. 建议的后续实施顺序

1. 修复 89Br public reference CSV 来源冲突，增加 source metadata；不直接改生产 `discreteLevels.dat`。
2. 先把 N1–N4 分类器改成可复现 CLI 工具，并建立单元测试：even-even 0+、odd-A half-integer、odd-odd integer、括号 Jπ、source conflict、RIPL missing/malformed。
3. 明确 RIPL `nol/nmax/nc` 语义并重跑全库核素级审计；在此之前不采信 527/2762/554 等包内汇总数字为已复现结果。
4. 重写事件准入器，以 `(run_id, global_event_index, rng_seed, fragment_side)` 唯一键，检查重复、缺失、E3 bridge status、E4 初态和事件变量。
5. 对 Patch A 做实际 `git apply --check`、编译和事务隔离测试；修正 skip log 的全局事件/seed 元数据后，作为独立 opt-in commit。
6. Patch B 仅建立对照配置和诊断，不改变默认生产参数。
7. Patch C 仅在逐核来源审核完成后测试，默认不加载。
8. 以上通过后才生成新的可信 G2 matrix；skip 样本不得进入 audited-seed 竞争；不更新旧 golden 来掩盖变化。

## 6. 当前状态

- ZIP 文件清单与源代码已检查：**COMPUTATION_VERIFIED（静态审阅）**。
- 四个 patch 目标源文件与包基线 blob 一致：**SOURCE_HASH_VERIFIED**。
- `git apply --check`、编译、运行时行为：**NOT RUN**。
- 89Br 当前 NNDC adopted 页面值：**SOURCE_VERIFIED as (5/2−), with model/systematics basis noted**。
- 89Br public CSV 3/2−：**CONFLICTED / NOT ACCEPTED**。
- 其余 14 个 Jπ 修正：**REPORTED_UNVERIFIED**。
- 527 个截断核素及全库准入汇总：**REPORTED_UNVERIFIED**。
- Patch A/B/C 生产合并：**NOT AUTHORIZED / NOT DONE**。
- P/H/O 与气论映射：**UNCHANGED / BLOCKED pending trusted matrix**。
