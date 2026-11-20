# Run #284：奇质量数错误自旋如何污染 CGMF 连续态 spin lattice

**范围**：Run #277 失败事件中的 ⁸⁹Br、¹⁰⁵Zr；只做源码追踪和数学/代码路径核验，不修改生产行为。  
**当前分支数据**：`discreteLevels.dat` blob `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`。  
**相关源码 blobs**：
- `libcgmf/include/cgm.h`: `09d47a2c85d1d727283516ca2915bf8d447e67c`
- `libcgmf/src/popinit.cpp`: `433f5fed2f076e561525019cad098a1641d1519a`
- `libcgmf/src/specmc.cpp`: `3c283dff4bfecb821c168301025f7be1f66b614a`
- `libcgmf/include/mchf.h`: `a730902b991b104c43526297bb53725a218c85d0`

## 1. 直接机制：离散基态 J 决定连续态 spin lattice 的整数/半整数偏移

### 1.1 `halfint` 的实现

`libcgmf/include/cgm.h` 定义：

```cpp
#define halfint(x) ( (((int)(x*2.0+0.001) % 2)==1) ? 0.5 : 0.0 )
```

该宏只根据输入基态 spin 的两倍值奇偶性返回 0 或 0.5：
- 基态 J 为整数 → offset = 0；
- 基态 J 为半整数 → offset = 0.5。

它没有独立读取核素质量数 A 来校验这个 offset 是否正确。

### 1.2 连续态 spin population 使用这个 offset

`libcgmf/src/popinit.cpp` 的 `statPopinitLevden()`：

```cpp
for(int j=0 ; j<MAX_J ; j++){
    sd = ldSpinDistribution(j+halfint(n->lev[0].spin),
                            n->ldp.spin_cutoff,n->ldp.sigma0);
```

所以连续态可采样的自旋格点为：
\[
J_j=j+\operatorname{halfint}(J_{\rm ground}),\quad j=0,1,2,\ldots
\]

`statPopinitTransmission()` 同样使用 `halfint(n0->lev[0].spin)` 构造 CN 自旋索引起点。

### 1.3 Monte Carlo history 把格点索引还原为物理 J 时使用同一 offset

`libcgmf/src/specmc.cpp` 的 G2 population diagnostic 使用：
`parent_J = mcurr.getJ() + spinOffset`，其中 `spinOffset = halfint(ncl[c0].lev[0].spin)`；对 population bins 也使用 `J = j + spinOffset`。

`MCPoint::getJ()` 在 `libcgmf/include/mchf.h` 中返回的是 `j` 数组索引，而不是完整物理 J。物理自旋由索引加 ground-state offset 恢复。

因此，只要 ground-state J 的整数/半整数类型错误，整个连续态自旋格点就会选错。它不只是一个离散基态显示错误。

## 2. 与 Run #277 两个失败核素的直接对应

| 核素 | A | 当前 CGMF ground Jπ | 正确自旋类型 | `halfint` offset | Run #277 初态 |
|---|---:|---|---|---:|---|
| ⁸⁹Br | 89 | 2+ | 半整数 | 0.0 | 3+（整数） |
| ¹⁰⁵Zr | 105 | 4+ | 半整数 | 0.0 | 6−（整数） |

两条失败事件的初态自旋与错误 ground-state offset 完全一致：代码将它们放在整数自旋格点上。对于奇质量数核，这不符合总角动量量子化。

与之相对，¹³⁶I（A 偶数）、¹³⁷I/¹⁰⁵Nb（A 奇数）等核素当前 ground-state spin 的整数/半整数类型与 A 奇偶性一致。

## 3. 为什么这会影响 E1 bridge 失败

当前 E1 bridge 接收 `MCPoint` 的 spin-array index，并根据同一个 `halfint(ncl[c0].lev[0].spin)` offset 还原物理自旋。如果 ground J 错误：
1. 连续态 spin population 在错误的整数/半整数格点上生成；
2. 事件初态 J 也在错误格点上抽样；
3. bridge 用错误的 Ji 与离散候选 Jf 比较 `|Ji-Jf|<=1`；
4. 即使后续补入正确的离散能级，也不能自动修复已经错误的连续态 spin lattice。

因此，先修复/审定 ground-state Jπ 数据类型，再讨论 E1 bridge 候选，是严格的依赖顺序。

## 4. 数据修正边界

- ¹⁰⁵Zr：RIPL-4 ground numeric Jπ 为 1/2+，原始 spin 字符串 `1/2+#`。CGMF manual 对完全未知 ground state 的 odd-A even-odd 核给出 1/2+ 默认规则；RIPL-4 的 # 标记仍须保留为非实验来源。该项可进入 PROVISIONAL correction review，但不直接标为实验 PROVED。
- ⁸⁹Br：RIPL-4 ground Jπ 未唯一确定，原始候选 `(3/2-,5/2-)`。5/2− 不能仅凭一个候选列表升级为唯一值；需固定版本 ENSDF adopted 记录及评估依据。
- 在 ⁸⁹Br Jπ 未定前，不得把任一候选静默写入生产文件；可考虑在核素准入时 fail-closed。
- 不恢复 nearest-J fallback；不添加 M1/E2；不改变 lower cut；不跳过失败事件来产生“完整”矩阵。

## 5. 建议的最小下一步

1. 将 A 奇偶性与 J 整数/半整数一致性作为核素准入硬规则：`2J` 必须为整数且 `(2J mod 2) = (A mod 2)`。
2. 为 ⁸⁹Br、¹⁰⁵Zr 添加单元测试：错误旧值应被拒绝；候选新值仅按来源等级进入候选/暂定状态。
3. 在 CGMF 初始化阶段增加可选诊断/验证模式，输出 ZAID、A、ground Jπ、offset、source provenance；先不改变默认生产行为。
4. 独立核验 ⁸⁹Br ENSDF adopted 与 RIPL-4/NUBASE 的冲突后，才决定是否更新 ⁸⁹Br ground Jπ。
5. 以正确自旋格点重新运行固定 seed 的最小 case；比较事件初态 J、population bins 和 bridge 候选。若初态分布改变，必须作为物理输入变化记录，不得覆盖旧 golden。

## 6. 状态

- `halfint` 宏和 spin offset 路径：**SOURCE_AUDITED**。
- ¹⁰⁵Zr/⁸⁹Br ground J 整数导致 offset=0：**COMPUTATION_VERIFIED**（直接代入宏定义）。
- 连续态 population 使用该 offset：**SOURCE_AUDITED**。
- Run #277 事件初态整数 J 与错误 offset 相符：**SOURCE_AUDITED + COMPUTATION_VERIFIED**。
- 该错误是 Run #277 失败的唯一根因：**NOT CLAIMED**；E1-only 可达性仍是独立的后续阻塞。
- 生产数据/源码修复：**NOT DONE**。
- P/H/O 与气论映射：**BLOCKED / UNCHANGED**。

## Sources

- CGMF halfint macro: https://github.com/anselmiao/CGMF/blob/qi/fix-discrete-start-index/libcgmf/include/cgm.h
- CGMF spin population: https://github.com/anselmiao/CGMF/blob/qi/fix-discrete-start-index/libcgmf/src/popinit.cpp
- CGMF Monte Carlo state handling: https://github.com/anselmiao/CGMF/blob/qi/fix-discrete-start-index/libcgmf/src/specmc.cpp
- CGMF MCPoint: https://github.com/anselmiao/CGMF/blob/qi/fix-discrete-start-index/libcgmf/include/mchf.h
- CGMF discrete-level guidance: https://cgmf.readthedocs.io/en/stable/discreteLevels.html
