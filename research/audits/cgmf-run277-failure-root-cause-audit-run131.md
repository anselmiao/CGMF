# Run #277 失败根因审计（Run #131）

**Run**：#277 / `44724366375`  
**Commit**：`1f0ad5e4e57b2d8135df6da55dbdd46eae1adfa8`  
**Branch**：`qi/fix-discrete-start-index`  
**范围**：Actions job log、CTest artifact、G2 matrix artifact、当前分支 `libcgmf/src/specmc.cpp`。  
**性质**：计算失败定位；不构成物理规则修复或气论正向证据。

## 1. 结论

Run #277 的失败已定位到两条共享同一 E1-only 离散桥接选择器的代码路径：

- `mcFindNext()` 在连续态/离散态总体均未抽中时，调用 E1 bridge 作为离散 fallback；
- `mcHistoryLoop()` 在连续态落到 lower-cut 以下时，调用同一 E1 bridge 映射到离散态。

当前 `mcSelectE1DiscreteBridge()` 要求：
1. 候选离散态能量严格低于初态；
2. `|J_i-J_f| <= 1`，并排除 `J_i=J_f=0`；
3. 初末态宇称相反。

没有满足条件的候选时返回 -1，调用方标记 unmappable 并终止。当前实现没有 M1/E2 候选路径。

**直接失败机制：COMPUTATION_VERIFIED + SOURCE_AUDITED。**  
**E1-only fallback 是否符合设计意图、是否应有 M1/E2 或其他离散态来源：BLOCKED / DESIGN AUDIT REQUIRED。**  
不允许仅为让 CI 通过而放宽选择规则。

## 2. Run #277 的测试结果

- Configure、Build：通过。
- G2 合成 fixture 测试：通过。
- RNG seed matrix 单元测试：通过；31 个 case 的 seed ranges 无同条件重叠。
- Native CTest：99 项中 75 项通过；12 项 `*_exec` 真正失败，另 12 项依赖这些执行结果的 `*_diff` 未运行。CTest 退出码 8。
- Workflow 的 native test step 显示 success 是因为 `continue-on-error: true`；最终 native regression enforcement 读取到 `steps.native_tests.outcome=failure`，因此正确地失败。
- G2 sidecar matrix：第一个 case `cf252-sf` 的 on-run 失败；后续分析步骤均 skipped。

## 3. Native 12 条执行失败诊断

所有 12 条诊断均为 `ndisc=1`、`rejected_invalid=0`、`rejected_energy=0`、`accepted=0`。11 条因角动量拒绝，1 条因宇称拒绝。

| 核素 | event | site | 初态能量 MeV | 初态 Jπ | 拒绝 |
|---|---:|---|---:|---|---|
| ¹³⁶I | 6 | lower_cut | 0.0793032525585 | 7⁺ | 角动量 |
| ¹³⁶I | 2 | mc_find_next | 0.0205396718986 | 3⁻ | 角动量 |
| ¹⁰⁵Nb | 9 | lower_cut | 0.282517921521 | 11/2⁺ | 角动量 |
| ⁹⁶Y | 24 | lower_cut | 0.186721099290 | 8⁻ | 角动量 |
| ¹³⁷I | 7 | lower_cut | 0.132297895188 | 23/2⁻ | 角动量 |
| ¹⁰⁵Zr | 12 | lower_cut | 1.17999760336 | 6⁻ | 角动量 |
| ¹³⁸Te | 20 | lower_cut | 0.177690546270 | 11⁻ | 角动量 |
| ¹³⁶I | 15 | lower_cut | 0.0811649573049 | 4⁻ | 角动量 |
| ¹³⁷I | 16 | lower_cut | 0.0773941099933 | 15/2⁺ | 角动量 |
| ¹³²I | 20 | lower_cut | 0.277058766924 | 8⁺ | 角动量 |
| ¹⁰⁵Zr | 12 | lower_cut | 1.17999760336 | 6⁻ | 角动量 |
| ⁸⁹Br | 34 | mc_find_next | 0.0232161113767 | 3⁺ | 宇称 |

¹⁰⁵Zr 的重复诊断来自两个不同 native test case，保留为两条测试记录，不当作两个不同核素状态。

## 4. 源码路径核验

当前 `libcgmf/src/specmc.cpp`：

- `mcSelectE1DiscreteBridge()` 约第 420–500 行：计算初态自旋，逐个检查离散候选的能量、角动量、宇称；候选集合为空时输出拒绝计数并返回 -1。
- `mcFindNext()` 约第 650–740 行：总体抽样未选出状态时，以 `ncl[c0].max_energy` 调用 E1 bridge。
- `mcHistoryLoop()` 约第 600–630 行：lower-cut 情况以当前态能量调用 E1 bridge。
- 两条路径都只调用同一个 E1 selector，没有 M1/E2 分支。

这与 native log 中两种终止文本完全对应：
- `next-state selection returned an invalid state`
- `lower-cut transition has no mappable discrete state`

## 5. G2 artifact 完整性

Run #277 的 matrix artifact 只含第一个 case `cf252-sf/on` 的部分产物：

| 文件 | 内容 | 状态 |
|---|---|---|
| `mixed-history.jsonl` | 10 条，event 1–5，每个 event 两个 fragment sides | 部分 |
| `neutron-transition.jsonl` | 21 条，event 1–5 | 部分 |
| `rng-audit.tsv` | 0 bytes | 无 RNG 审计记录 |
| `histories.cgmf.0` | 3149 bytes | 中途输出 |
| `sidecar-on.stdout` | 74638 bytes | 含 event 6 bridge 失败诊断 |

具体首个 G2 阻塞：
- event 6，HF，ⁱ³⁶I（Z=53,A=136）；
- 初态能量 0.079303252558488524 MeV，Jπ=7⁺；
- `ndisc=1`；
- 唯一离散候选因角动量条件被拒绝；
- 随后 `lower-cut transition has no mappable discrete state`。

因此 200-event case、31-case matrix 均未完成。以上 10 条 mixed-history 与 21 条 neutron-transition 只用于失败定位，不能用于 P/H/O、conditional-history 或高阶统计分析。

## 6. 数据来源边界

本轮确认的是运行时对象 `ndisc=1` 以及 bridge 的筛选结果；并未证明这等于 RIPL 原始数据库只有一个能级，也未恢复历史预处理转换器。此前 ⁸⁹Br、¹⁰⁵Zr 的 Jπ 转换差异仍需沿 RIPL → 转换中间态 → `discreteLevels.dat` → runtime object 逐级追溯。

## 7. 禁止的捷径

在设计和数据来源未厘清前：
- 不放宽 E1 角动量/宇称选择条件；
- 不把 E1 selector 改成任意低于初态能量的离散态选择；
- 不自行增加 M1/E2 分支或自造跃迁强度；
- 不改变 lower cut、删除失败事件、缩小测试集；
- 不覆盖生产 `discreteLevels.dat`，不改 golden 以追求 CI 变绿。

## 8. 下一轮工作

### A. E1 bridge 设计审计
追溯上游 CGMF 历史实现、提交与文档，确认 E1-only fallback/lower-cut bridge 的设计来源。若讨论 M1/E2，必须同时明确选择规则、强度/概率来源及适用范围；没有强度数据就保持 BLOCKED。

### B. 单能级数据链审计
优先对 ¹³⁶I、¹³⁷I、¹⁰⁵Zr、⁸⁹Br、¹⁰⁵Nb、⁹⁶Y、¹³⁸Te、¹³²I 做 RIPL 原始记录 → 转换中间态 → 专用离散文件 → runtime `ncl[].lev[]` 对照，确定 `ndisc=1` 的形成环节。

### C. 最小定向复核
固定上述 event/case/seed，分别覆盖 `mc_find_next` 与 `lower_cut` 两条路径，记录唯一候选 E/J/π 与逐项拒绝原因。只有 A/B 得到可复现结论后，才提出最小 patch。

## 9. 状态

- Run #277 workflow、job log、artifacts 已检查：**COMPUTATION_VERIFIED**。
- 12 条 native 执行失败诊断：**COMPUTATION_VERIFIED**。
- 失败直接由 E1-only selector 无可接受候选触发：**SOURCE_AUDITED + COMPUTATION_VERIFIED**。
- 生产离散能级为何全部 `ndisc=1`：**BLOCKED**。
- E1-only bridge 是否符合物理设计意图：**BLOCKED**。
- 完整 G2 matrix：**NOT GENERATED**。
- P/H/O 竞争识别：**BLOCKED**。
- 气论映射：**CANDIDATE**，本轮没有升级。

## Provenance

- Run #277: https://github.com/anselmiao/CGMF/actions/runs/44724366375
- CTest log artifact SHA-256: `3a7be38eec492ca0a4b32ca363a405ed31008f5ca330aebc0ce84d06689999a5`
- G2 matrix artifact SHA-256: `bdb1cdd13e82c12f51e50a69665ef28b18616c4fdc1bc87d82b647aa4fd651f2`
- Native regression outputs artifact SHA-256: `34cb1364088befc87f7e315749695a7163ecf5252d529a022b0c50512d6ca9ab`
- `specmc.cpp` blob SHA: `3c283dff4bfecb821c168301025f7be1f66b614a`


## 10. 历史实现对照：严格失败是一次有意的行为变化

进一步核对上游 `lanl/CGMF:master` 与本分支的提交历史后，发现：

- 上游当前 `libcgmf/src/specmc.cpp` 在 lower-cut 和 `mcFindNext()` 两处都先尝试 E1 选择；如果没有 E1 候选，随后会执行注释为 `force transition to the closest-j state` 的 nearest-J fallback。
- 本分支提交 `0ccd1dab9a0e2a174fb47b3b30d52d8f2d1b7b27`（`fix: unify reachable E1 discrete bridge selection`）将两处选择统一到 `mcSelectE1DiscreteBridge()`，并删除了 nearest-J fallback。这个改动将原先可能强制进入不满足 E1 规则的最近 J 状态，改为只允许真正满足 E1 条件的候选。
- 后续提交 `9cb0474f6d55b3ac2cfd5ed89df532474580d839`（`fix: fail safely on unmappable cascade states`）增加 unmappable 检查和终止信息；`0dab1a4d77945d628cb462fb0f9abcc91986cb7c` 再增加 fallback index 边界保护。
- `gamma_transition_selection.h` 已定义 E1、M1、E2 的**选择规则谓词**，并有对应单元测试；但谓词只判断允许/不允许，不提供跃迁强度、分支比或选择多极性的概率模型。生产 bridge 当前只调用 E1。

因此 Run #277 的失败不是 CI 新配置造成，也不应简单回滚成上游 nearest-J fallback。它暴露的是严格 E1-only 桥接条件与当前运行时单能级数据之间的不可达状态。恢复 nearest-J fallback 会重引入已被本分支移除的非 E1 强制转移，违背当前证据治理要求。

**设计决策仍未完成**：是否应保留 fail-closed 的 E1-only bridge，还是构建有真实强度依据的 E1/M1/E2 混合桥接模型。仅有 multipolarity selection-rule predicate 不足以定义抽样概率。

### 新增来源
- 上游 `lanl/CGMF/libcgmf/src/specmc.cpp`（master blob `d62b498309ac0ec3f46be80a03ff9e1e318db319`）：保留 nearest-J fallback 的旧实现。
- 本分支 `0ccd1dab`：统一 E1 bridge 并删除 nearest-J fallback。
- 本分支 `9cb0474`：对不可映射状态 fail-safe 终止。
- 本分支 `libcgmf/include/gamma_transition_selection.h` blob `13311828472258327914f0830ef9a37d3cae5392`：E1/M1/E2 selection-rule predicates；不含 transition strengths。
