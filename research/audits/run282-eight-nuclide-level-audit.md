# Run #282：八个失败核素的 RIPL → CGMF 离散能级数量链核验

**分支**：`qi/fix-discrete-start-index`  
**输入版本**：
- `data/ripl3-levels.dat` blob SHA: `c3c3a816730deef172ccbd11b0dfd58b6d197d90`
- `data/discreteLevels.dat` blob SHA: `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`
**方法**：直接读取当前分支两个数据文件中的八个核素记录头和逐级记录；不是对包内汇总数字的转述。

## 1. 本轮关键结论

八个失败核素的运行时 `ndisc=1`，与 `discreteLevels.dat` 对应记录头一致；并且八个核素的 `CGMF_ndisc=1` 全部与 RIPL 头字段 `Nmax=1` 一致。

**这八例目前不支持“RIPL 有更多完整离散能级，但 CGMF 预处理意外裁掉”的解释。** 更符合数据文件按 RIPL 的完整性截止 `Nmax` 只收录到第 1 级。它解释了为什么 RIPL 的 `Nol` 可以大于 1，而 CGMF 的专用离散文件仍为 1 级。

这是一项数据数量链核验，不代表 E1 bridge 已有可达候选，也不代表基态 Jπ 推断一定正确。

## 2. RIPL 字段口径：已由 IAEA 手册核实

RIPL 离散能级记录头字段顺序是：
`SYMB, A, Z, Nol, Nog, Nmax, Nc, Sn, Sp`

IAEA RIPL handbook 对字段的定义：
- `Nol`: 衰变能级方案中的能级数；
- `Nog`: 衰变方案中的 gamma-ray 数；
- `Nmax`: 能级方案被认为完整的最高能级序号（对应能量 Emax）；
- `Nc`: 实验自旋/宇称赋值唯一的最高能级序号。

因此 `Nol` 不是 CGMF 应无条件纳入的完整能级数；`Nog` 更不是能级数；`Nc` 也不是离散能级数量上限。不能用 `ndisc < Nc` 作为通用截断判据。

来源：IAEA RIPL handbook, “Format of the Discrete Level Schemes Library”, https://www-nds.iaea.org/RIPL-3/handbook/ripl2-feb2005.pdf。<Cite refs={["turn811386search23","turn811386search24"]}/>

## 3. 八个失败核素逐项对照

| 核素 | Nol | Nog | Nmax | Nc | RIPL 记录数 | RIPL 未知 J/π 数 | CGMF ndisc | RIPL 基态 Jπ | CGMF 基态 Jπ |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| ¹³⁶I | 11 | 19 | 1 | 1 | 11 | 6 | 1 | 1− | 1− |
| ¹³⁷I | 15 | 23 | 1 | 1 | 15 | 0 | 1 | 7/2+ | 7/2+ |
| ¹⁰⁵Zr | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 未赋值 | 4+ |
| ⁸⁹Br | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 未赋值 | 2+ |
| ¹⁰⁵Nb | 6 | 9 | 1 | 1 | 6 | 0 | 1 | 5/2+ | 5/2+ |
| ⁹⁶Y | 7 | 15 | 1 | 3 | 7 | 2 | 1 | 0− | 0− |
| ¹³⁸Te | 7 | 7 | 1 | 1 | 7 | 1 | 1 | 0+ | 0+ |
| ¹³²I | 6 | 6 | 1 | 1 | 6 | 0 | 1 | 4+ | 4+ |

逐条记录的机器可读输出见 [run282-eight-nuclide-level-audit.csv](run282-eight-nuclide-level-audit.csv)。

### 解释边界

- ¹³⁶I、¹³⁷I、¹⁰⁵Nb、⁹⁶Y、¹³⁸Te、¹³²I：RIPL 的 `Nol>1`，但 `Nmax=1`。CGMF 仅保留第 1 级与 RIPL 完整性截止一致。不能将其描述成意外丢失 5–14 个“完整能级”。
- ¹⁰⁵Zr、⁸⁹Br：RIPL 本身只有一个记录级，且原始 J/π 字段为未知（J=-1, parity=0）；CGMF 文件分别写入 4+、2+。CGMF 文件头注释称缺失自旋/宇称按 CGMF manual 规则补齐。这是**基态赋值来源/规则审计**，不是能级数量截断。
- ⁹⁶Y 的 `Nc=3` 而 `Nmax=1`，直接说明 Nc 和 Nmax 不可互换；本例仍只有第 1 级处于完整性截止。

## 4. 对此前判断的修订

此前将“RIPL `nol/nmax/nc` 语义尚未核实”列为主要阻塞。现已通过 IAEA 手册确认字段语义，并对八个失败核素逐条核验。

**修订结论**：
1. 对这八个核素，`ndisc=1` 与 RIPL `Nmax=1` 一致；数据数量链不再是“未知是否误裁剪”。
2. 当前最重要的数据问题转为：¹⁰⁵Zr 和 ⁸⁹Br 的基态 Jπ 在 RIPL 原始记录中缺失，CGMF 按内部规则补值的依据与版本需要审计；尤其 ⁸⁹Br 的 2+ 与外部 ENSDF adopted (5/2−) 值存在冲突。
3. ¹³⁶I 的事件初态 Jπ=7+、3−、4− 高于或不满足唯一第 1 级基态桥接的 E1 条件；其失败首先是“运行时只有一个完整离散态”下的 E1-only 桥接不可达问题，而不是已证实的 RIPL 数据误裁剪。
4. ¹⁰⁵Zr 的失败初态 6−，唯一 CGMF 离散态 4+，E1 角动量条件 `|6−4|=2` 不满足；仅靠将 Jπ 记录补全不能解决此角动量差。
5. 不得据此直接增加 M1/E2，也不得恢复 nearest-J fallback；需要单独完成 bridge 物理设计审计。

## 5. 本轮新增可复现工具

新增 `scripts/audit_nuclide_level_coverage.py`：
- 分开解析 RIPL `Nol/Nog/Nmax/Nc`；
- 从 CGMF `discreteLevels.dat` 解析 `ndisc`；
- 对照记录数、RIPL 未知 J/π 数和基态 Jπ；
- 只输出诊断状态，不擅自决定物理准入；
- 不将 `Nc` 当作 level count，也不将 `Nol` 当作 Nmax。

新增 `tests/test_audit_nuclide_level_coverage.py`，覆盖 RIPL 字段分离及未知基态 Jπ 被 CGMF 推断赋值的对照场景。

运行方式：
```bash
python scripts/audit_nuclide_level_coverage.py \
  --ripl data/ripl3-levels.dat \
  --cgmf data/discreteLevels.dat \
  --nuclides 136I 137I 105Zr 89Br 105Nb 96Y 138Te 132I \
  --output run282-eight-nuclide-level-audit.csv
python -m unittest discover -s tests -p 'test_audit_nuclide_level_coverage.py'
```

## 6. 状态更新

- RIPL 字段语义（Nol/Nog/Nmax/Nc）：**SOURCE_VERIFIED**（IAEA handbook）。
- 八个核素的 RIPL 记录头、level records 与 CGMF 专用文件 ndisc：**COMPUTATION_VERIFIED**（直接读取当前分支 blob）。
- 八例 `ndisc=1` 与 `Nmax=1` 一致：**COMPUTATION_VERIFIED**。
- ¹⁰⁵Zr、⁸⁹Br 基态 Jπ 补值规则与数据来源：**BLOCKED / NEEDS SOURCE AUDIT**。
- E1-only bridge 设计是否足以覆盖这些状态：**BLOCKED**。
- P/H/O 竞争识别：**BLOCKED**；本轮未使用失败前部分事件数据。
- 气论映射：**UNCHANGED**。
