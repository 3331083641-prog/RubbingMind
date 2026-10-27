# 验收矩阵（ACCEPTANCE_MATRIX）

> **恢复说明**（2026-10-25 16:51 Asia/Shanghai）：tip@21a3dc7门禁追加时误截断(~78KB)；已从REVIEW_FINDINGS.md的tip@章节重建。损毁剪影：wt/qa-tmp/qa-report-21a3dc7/ACCEPTANCE_MATRIX.DAMAGED_1043B.md

### 报告前端门禁 tip@044b059（agent/report-frontend；相对 feature@e9ce60e）— RM-红队QA @ 2026-10-25 12:52 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `044b059` | 自 FINDINGS |
| 1 | tip / log -1 | **确认** |
| 2 | 含 e9ce60e | **是** |
| 3 | merge-tree vs e9ce60e | **0 冲突** |
| 4 | G1 / api.ts | **PASSED（非 xfail）** |
| 5 | 最差 6 条 + failureRetention | **有代码证据** |
| 6 | P1-4 / P1-11 | **有改动证据；勿关单** |
| 7 | npm run build | **通过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 金石文档窄门禁 tip@ec70f56（JS-4/JS-5 开项台账；对齐 feature@0654d13）— RM-红队QA @ 2026-10-25 13:16 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `ec70f56` | 自 FINDINGS |
| 1 | tip / log -1 | **确认** |
| 2 | vs 0654d13 | **已含 / FF** |
| 3 | merge-tree vs 0654d13 | **冲突 0** |
| 4 | diff 性质 | **仅 docs/脚本/台账** |
| 5 | claims 树 | **未改** |
| 6 | check_claims_open_issues --check | **ok** |
| 7 | 相关 pytest | **200 passed** |
| 8 | conflict / C-08 | **仍开 / 禁 apply** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 报告前端门禁 tip@b200567（agent/report-frontend；对齐 feature@0654d13）— RM-红队QA @ 2026-10-25 13:16 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `b200567` | 自 FINDINGS |
| 1 | tip SHA | b200567e481c9b7259a73caee03efbbff642b2ba |
| 2 | vs feature@0654d13 | **已含 / FF** |
| 3 | merge-tree vs 0654d13 | **冲突 0** |
| 4 | MECHANISM_HEAD_NOTE（P1-4 落后 tip 提示） | **有代码证据** |
| 5 | reportStatus 全路径文案 | **有代码证据** |
| 6 | glyphEvaluationText（not_evaluated 禁伪 Top-k） | **有代码+逻辑证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 合入后冒烟 tip@00a5c85（含 jinshi@ec70f56 + report@b200567）— RM-红队QA @ 2026-10-25 13:25 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `00a5c85` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 全量 pytest | **709 passed / 1 xfailed** |
| 3 | G1 + Phase2 ROI | **21 passed** |
| 4 | Phase2 路由 | **ALL_200** |
| 5 | claims / museum 抽样 | **205 passed** |
| 6 | open-issues --check | **ok** |
| 7 | validate_museum_v3 | **passed** |
| 8 | npm run build | **通过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **|** | 自 FINDINGS |

### 评测 tip 门禁 tip@9aa52b6（agent/eval-sci；基线 feature@0654d13）— RM-红队QA @ 2026-10-25 13:27 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `9aa52b6` | 自 FINDINGS |
| 1 | tip / log -1 | **确认** |
| 2 | vs 0654d13 | **已含 / FF 祖先** |
| 3 | merge-tree vs 0654d13 | **冲突 0** |
| 4 | merge-tree vs feature@00a5c85（附注） | **冲突 0** |
| 5 | 全量 pytest | **712 passed / 1 xfailed** |
| 6 | xfail = A24 | **确认** |
| 7 | G1 | **仍绿** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 架构 tip 门禁 tip@3d7239c（AB-8 / RT-002/003/004 + SPEC §12/§13；基于 feature@00a5c85）— RM-红队QA @ 2026-10-25 13:30 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `3d7239c` | 自 FINDINGS |
| 1 | tip SHA | 3d7239cb60394cb3f9279c6b1ea86ceddb92c34f |
| 2 | vs feature@00a5c85 | **已含 / 基于** |
| 3 | merge-tree vs 00a5c85 | **冲突 0** |
| 4 | RT-002 samples/health | **有代码+测试证据** |
| 5 | RT-003 拒默认端口 + browser_target | **有代码+测试证据** |
| 6 | RT-004 conftest/tmp | **有代码+测试证据** |
| 7 | SPEC §12 / §13 | **有文档证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 合入后冒烟 tip@c761d54（feature = 8a266b4 + AB-8@3d7239c）—— RM-红队QA @ 2026-10-25 13:34 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `c761d54` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 含 AB-8 | **是** |
| 3 | 全量 pytest | **726 passed / 1 xfailed** |
| 4 | xfail = A24 | **确认** |
| 5 | G1 | **正式绿** |
| 6 | Phase2 + RT | **49 passed / 1 xfailed** |
| 7 | RT-002/003/004 抽样 | **14 passed** |
| 8 | ES-3/4/5 抽样 | **23 passed** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 架构 tip 门禁 tip@12fc96e（RT-005/007/009/011 + RT-006 部分；相对 feature@c761d54）—— RM-红队QA @ 2026-10-25 13:54 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `12fc96e` | 自 FINDINGS |
| 1 | tip | **确认** |
| 2 | merge-tree vs c761d54 | **冲突 0** |
| 3 | museum_processing | **未改** |
| 4 | 变更面 | **10 文件** |
| 5 | RT-005 | **有缓解证据；产品单仍开** |
| 6 | RT-006 | **仅部分缓解；勿标全关** |
| 7 | RT-007 | **有缓解证据；产品单仍开** |
| 8 | RT-009 | **有缓解证据；产品单仍开** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 报告 tip 门禁 tip@0301aad（P1-4 MechanismPanel captionNote + slice7 证据）相对 feature@c761d54；作者 RM-红队QA @ 2026-10-25 13:56 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `0301aad` | 自 FINDINGS |
| 1 | tip / 相对 c761d54 | **确认** |
| 2 | merge-tree | **冲突 0** |
| 3 | P1-4 captionNote | **有代码证据，未关单** |
| 4 | slice7 / P1-9 Playwright 首屏 | **有路径证据，未重跑全量，未关单** |
| 5 | RF-8 / Phase1 | **仍开** |
| 6 | pytest ES-4 contracts | **17 passed** |
| 7 | pytest 窄抽样 | **254 passed** |
| 8 | npm run build | **通过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 评测 tip 门禁 tip@5ba8bef（含交付 9eb8406；相对 feature@c761d54）· RM-红队QA @ 2026-10-25 13:59 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `5ba8bef` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | 交付 tip 9eb8406 | **在 ancestry** |
| 3 | vs feature@c761d54 | **已含 / FF** |
| 4 | merge-tree vs c761d54 | **冲突 0** |
| 5 | 全量 pytest | **730 passed / 1 xfailed** |
| 6 | xfail = A24 | **确认仍 xfail** |
| 7 | ES 子集 | **27 passed / 1 xfailed** |
| 8 | ES-3 | **有证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 合入后冒烟 tip@4f57eb5（合入 arch@12fc96e + report@0301aad + eval@5ba8bef）—作者 RM-红队QA @ 2026-10-25 14:24 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `4f57eb5` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 含 arch/report/eval | **是** |
| 3 | 全量 pytest | **742 passed / 1 xfailed** |
| 4 | xfail = A24 | **确认** |
| 5 | G1 | **23 passed** |
| 6 | RT-002..011 抽样 | **26 passed** |
| 7 | Phase2+AB8 相关 | **36 passed / 1 xfailed** |
| 8 | ES 抽样 | **41 passed** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 评测 tip 门禁 tip@89ff1db（docs：R7 lag=141；相对 feature@4f57eb5）—— RM-红队QA @ 2026-10-25 14:33 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `89ff1db` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | vs feature@4f57eb5 | **已合 / FF** |
| 3 | 是否仅文档 | **是** |
| 4 | R7 lag=141 | **有证据** |
| 5 | R7 / G7 仍开 | **确认** |
| 6 | A24 仍 xfail | **确认** |
| 7 | 全量 pytest | **跳过** |
| 8 | 主库 SHA | **始=终不变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 架构 tip 门禁 tip@7d5f333（RT-008/010/013 + RT-006 remaining；相对 feature@063e0e3）—— RM-红队QA @ 2026-10-25 14:39 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `7d5f333` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | vs feature@063e0e3 | **可合 / 需 rebase 底** |
| 3 | vs 4f57eb5（对照） | 冲突 **0** / ahead 1 |
| 4 | museum_processing | **仅 soft-delete 路径** |
| 5 | RT-008 | **有缓解证据；产品单仍开** |
| 6 | RT-010 | **有缓解证据；产品单仍开** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 合入后冒烟 tip@063e0e3（合入 eval@89ff1db docs stamp）—作者 RM-红队QA @ 2026-10-25 14:41 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `063e0e3` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 含 89ff1db | **是** |
| 3 | 全量 pytest | **742 passed / 1 xfailed** |
| 4 | xfail = A24 | **确认** |
| 5 | AB-8 /api/health | **通过** |
| 6 | claims/museum | **通过** |
| 7 | G1 / RT / ES / npm | **本轮窄冒烟跳过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 合入后冒烟 tip@b60d556（合入 arch@7d5f333；含 RT-008/010/013）—作者 RM-红队QA @ 2026-10-25 14:49 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `b60d556` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 含 7d5f333 | **是** |
| 3 | 全量 pytest | **747 passed / 1 xfailed** |
| 4 | xfail = A24 | **确认** |
| 5 | G1 | **23 passed** |
| 6 | RT（含 008/010/013） | **31 passed** |
| 7 | Phase2+AB8 | **36p / 1xfail** |
| 8 | ES 抽样 | **39 passed** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

### 报告 tip 门禁 tip@be5e43d（merge feature@b60d556 atop 32195ce ES-3/5 UI）—作者 RM-红队QA @ 2026-10-25 14:58 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `be5e43d` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | commits 范围（原批次） | **7 commits** |
| 3 | merge-tree vs **4f57eb5**（原基线） | 冲突 **0** |
| 4 | merge-tree vs **b60d556**（当前 feature） | 冲突 **0** |
| 5 | 相对 b60d556 变更 | **7 files / +161/-24** |
| 6 | annotated → 禁伪「提升」 | **有证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 评测 tip 门禁 tip@cc1e1da（docs：R7 lag=145；相对 feature@b60d556）—— RM-红队QA @ 2026-10-25 14:59 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `cc1e1da` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | vs feature@b60d556 | **已合 / FF 可合** |
| 3 | 是否仅文档 | **是** |
| 4 | R7 lag=145 | **有证据** |
| 5 | A24 | **仍 xfail / 勿伪绿** |
| 6 | 全量 pytest | **跳过（docs-only）** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **之上）** | 自 FINDINGS |

### 报告 tip 门禁 tip@ffb9138（相对 be5e43d：P1-11/P1-8/DER 文案 + slice9；vs feature@c027714）—— RM-红队QA @ 2026-10-25 15:05 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `ffb9138` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | 当前 feature tip | **确认** |
| 3 | commits 范围（相对 be5e43d） | **4 commits** |
| 4 | 文件范围 | **6 files / +70/-4** |
| 5 | merge-tree vs **feature@c027714** | 冲突 **0** |
| 6 | merge-tree vs **be5e43d**（批次基线，可选） | 冲突 **0** |
| 7 | P1-11 打印空值不拼单位 | **有证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **之上）** | 自 FINDINGS |

### 合入后冒烟 tip@c027714（合入 eval@cc1e1da；含 report@be5e43d）——作者 RM-红队QA @ 2026-10-25 15:09 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `c027714` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 含 be5e43d / cc1e1da | **是** |
| 3 | 全量 pytest | **747 passed / 1 xfailed** |
| 4 | xfail = A24 | **确认** |
| 5 | G1 | **23 passed** |
| 6 | RT（含 008/010/013） | **31 passed** |
| 7 | Phase2+AB8 | **36p / 1xfail** |
| 8 | ES 抽样 | **41 passed** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **之上）** | 自 FINDINGS |

### 合入后冒烟 tip@e53929f（合入 report@ffb9138；parents c027714+ffb9138）——作者 RM-红队QA @ 2026-10-25 15:13 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `e53929f` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 含 c027714 / ffb9138 | **是** |
| 3 | 全量 pytest | **747 passed / 1 xfailed** |
| 4 | xfail = A24 | **确认** |
| 5 | G1 | **23 passed** |
| 6 | RT（含 008/010/013） | **31 passed** |
| 7 | Phase2+AB8 | **36p / 1xfail** |
| 8 | ES 抽样 | **41 passed** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **之上）** | 自 FINDINGS |

### 评测 tip 门禁 tip@3b0c47b（docs；R7 lag=161；相对 feature@e53929f）—— RM-红队QA @ 2026-10-25 15:15 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `3b0c47b` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | vs feature@e53929f | **干净 / FF 可合** |
| 3 | 是否纯文档 | **是** |
| 4 | R7 lag=161 | **已验证** |
| 5 | A24 | **仍 xfail / 未伪绿** |
| 6 | 全量 pytest | **跳过（docs-only）** |
| 7 | R7 / A24 产品项 | **仍开 / 未关** |
| 8 | 主库 SHA | **始=终不变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **之外）** | 自 FINDINGS |

### 合入后窄冒烟 tip@3b0c47b（FF 合入 docs；parent e53929f）——作者 RM-红队QA @ 2026-10-25 15:23 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `3b0c47b` | 自 FINDINGS |
| 1 | tip / parent | **确认** |
| 2 | docs-only vs parent | **是** |
| 3 | A24 | **仍 1p/1xfail / 未伪绿** |
| 4 | G1 抽检 | **23 passed** |
| 5 | 主库 SHA | **始=终不变** |
| 6 | 开项 P1/RF-8/R7/A24/conflict/产品 RT | **仍开 / 未关** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 评测 tip 门禁 tip@51fa1ba（docs §12 核验；R7 lag=162；相对 feature@3b0c47b）—— RM-红队QA @ 2026-10-25 15:30 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `51fa1ba` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | vs feature@3b0c47b | **干净 / 可合** |
| 3 | 是否纯文档 | **是** |
| 4 | §12 / R7 lag=162 | **已核验仍开** |
| 5 | A24 | **仍 xfail / 未伪绿** |
| 6 | 全量 pytest | **跳过（docs-only）** |
| 7 | R7 / A24 产品单 | **仍开 / 未关** |
| 8 | 主库 SHA | **始=终不变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **之外）** | 自 FINDINGS |

### 报告 tip 门禁 tip@49002cc（含 21cb82b export liftClaims、slice10、merge 3b0c47b；vs feature@3b0c47b）—— RM-红队QA @ 2026-10-25 15:32 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `49002cc` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | ancestry | **齐** |
| 4 | 文件范围 | **9 files / +203/-2** |
| 5 | merge-tree vs **feature@3b0c47b** | 冲突 **0** |
| 6 | export liftClaims（ES-3） | **有证据** |
| 7 | slice10 证据目录 | **存在** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **之外）** | 自 FINDINGS |

### 合入后冒烟 tip@ed9f1a0（合入 report@49002cc；parents 51fa1ba+49002cc；含 eval docs）—— RM-红队QA @ 2026-10-25 15:42 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `ed9f1a0` | 自 FINDINGS |
| 1 | tip HEAD / parents | **确认** |
| 2 | 全量 pytest | **747 passed / 1 xfailed** |
| 3 | G1 | **23 passed** |
| 4 | RT | **31 passed** |
| 5 | Phase2+AB8 | **36 passed / 1 xfailed** |
| 6 | ES | **41 passed** |
| 7 | claims | **ok / 仍开** |
| 8 | museum | **通过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 评测 tip 门禁 tip@2a553f9（ES-3/4/5 再核 + R7 lag=169；相对 feature@ed9f1a0）——作者 RM-红队QA @ 2026-10-25 15:48 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `2a553f9` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 | **docs-only 3 files / +41/-4** |
| 4 | merge-tree vs **feature@ed9f1a0** | 冲突 **0** |
| 5 | ES-3/4/5 再核 | **有证据** |
| 6 | R7 lag=169 | **已核验仍开** |
| 7 | A24 | **仍 xfail / 未关** |
| 8 | museum_processing / 业务代码 | **未改** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **之外）** | 自 FINDINGS |

### 报告 tip 窄门禁 tip@12e8ce6（docs-only slice11 inventory；无可叠 feat）相对 feature@ed9f1a0；作者 RM-红队QA @ 2026-10-25 15:52 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `12e8ce6` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 | **docs-only 5 files / +98** |
| 4 | 无可叠 feat | **确认** |
| 5 | merge-tree vs **feature@ed9f1a0** | 冲突 **0** |
| 6 | RF-8 | **仍开 / 未自关** |
| 7 | algorithmOutputMode | **缺口仅记录** |
| 8 | npm build | **跳过（无前端改动）** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 金石 tip 窄门禁 tip@5bf3836（人工复核提示按核对队列 + 证据缺口；相对 feature@ed9f1a0）——作者 RM-红队QA @ 2026-10-25 15:52 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `5bf3836` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 | **docs + ledger 脚本 2 files / +341/-147** |
| 4 | claims/* 数据文件 | **未改** |
| 5 | merge-tree vs **feature@ed9f1a0** | 冲突 **0** |
| 6 | 人工复核提示 / 证据缺口 | **有证据** |
| 7 | claims --check | **ok / 仍开** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **之外）** | 自 FINDINGS |

### 金石 tip 窄门禁 tip@5bf3836 · feature base 更新补记（vs feature@2a553f9）——作者 RM-红队QA @ 2026-10-25 15:53 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `5bf3836` | 自 FINDINGS |
| A | tip / feature@2a553f9 关系 | **同父兄弟** |
| B | merge-tree vs **feature@2a553f9** | 冲突 **0** |
| C | 文件重叠 tip∩2a553f9（各相对 ed9f1a0） | **无** |
| D | merge-tree vs ed9f1a0（附） | 冲突 **0** |
| E | claims --check / conflict | **ok / 20 仍开** |
| F | 主库 SHA | **始=终不变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 合入后窄冒烟 tip@2a553f9（FF 合入 eval docs；parent ed9f1a0）—— RM-红队QA @ 2026-10-25 15:55 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `2a553f9` | 自 FINDINGS |
| 1 | tip / parent | **确认** |
| 2 | docs-only vs parent | **是** |
| 3 | A24 | **仍 1p/1xfail / 未假绿** |
| 4 | G1 抽检 | **23 passed** |
| 5 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 架构 tip 门禁 tip@847e7f1（algorithmOutputMode / AdaptiveDiagnostics 契约；相对 feature@ac8f83c）——红队QA @ 2026-10-25 15:56 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `847e7f1` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 | **4 files / +39/-5** |
| 4 | merge-tree vs **feature@ac8f83c** | 冲突 **0** |
| 5 | 附带 merge-tree | 冲突 **0** |
| 6 | AlgorithmOutputMode 契约 | **有证据** |
| 7 | AdaptiveDiagnostics / api.ts | **有证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 合入后窄冒烟 tip@ac8f83c（合入 report@12e8ce6；parents f7a1d72+12e8ce6；含 eval@2a553f9 + jinshi@5bf3836）—— RM-红队QA @ 2026-10-25 15:57 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `ac8f83c` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | 变更范围 vs ed9f1a0 | **docs/台账/脚本** |
| 3 | A24 | **仍 1p/1xfail / 未假绿** |
| 4 | G1 抽检 | **23 passed** |
| 5 | claims | **ok / conflict 仍开** |
| 6 | museum | **passed** |
| 7 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 合入后冒烟 tip@25aa898（合入 arch@847e7f1；parents ac8f83c+847e7f1；含 eval/jinshi/report + algorithmOutputMode 契约）—— RM-红队QA @ 2026-10-25 16:02 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `25aa898` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | vs ac8f83c | **4 files / +39/-5** |
| 3 | A24 | **仍 1p/1xfail / 未假绿** |
| 4 | G1 | **23 passed** |
| 5 | RT | **31 passed** |
| 6 | Phase2/AB8 | **35p / 1xfail** |
| 7 | ES 抽检 | **45 passed** |
| 8 | claims | **ok / conflict 仍开** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 评测 tip 门禁 tip@b3452d2（R7 lag=177 证据戳；rebase 取代 a1ae0cc）相对 feature@25aa898；作者 RM-红队QA @ 2026-10-25 16:05 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `b3452d2` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 | **docs-only 2 files / +16/-4** |
| 4 | merge-tree vs **feature@25aa898** | 冲突 **0** |
| 5 | 取代 a1ae0cc | **确认** |
| 6 | R7 lag 证据 | **有戳 / 仍开** |
| 7 | A24 | **仍开 / xfail** |
| 8 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 合入后窄冒烟 tip@b3452d2（FF 合入 eval docs；parent 25aa898；R7 lag=177 证据戳）—— RM-红队QA @ 2026-10-25 16:09 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `b3452d2` | 自 FINDINGS |
| 1 | tip / parent | **确认** |
| 2 | 变更范围 vs 25aa898 | **docs-only** |
| 3 | A24 | **仍 1p/1xfail / 未假绿** |
| 4 | claims | **ok / conflict 仍开** |
| 5 | museum | **passed** |
| 6 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 架构 tip 门禁 tip@89a3f6e（HealthResponse/getHealth samples_* + reportData algorithmOutputMode + AB 开项盘点）相对 feature@b3452d2；作者 RM-红队QA @ 2026-10-25 16:10 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `89a3f6e` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 vs 25aa898 | **3 files / +53/-1** |
| 4 | merge-tree vs **feature@b3452d2** | 冲突 **0** |
| 5 | 附带 vs 25aa898 | 冲突 **0** |
| 6 | HealthResponse / getHealth samples_* | **有证据 / 契约对齐** |
| 7 | reportData algorithmOutputMode | **有证据** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 报告 tip 门禁 tip@5195b5b（algorithmOutputMode UI；相对 feature@b3452d2；附带 vs 25aa898）—— RM-红队QA @ 2026-10-25 16:11 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `5195b5b` | 自 FINDINGS |
| 1 | tip HEAD | **确认** |
| 2 | feature base | **确认** |
| 3 | 文件范围 vs b3452d2 | **7 UI/证据 + 2 docs 差** |
| 4 | merge-tree vs **feature@b3452d2** | 冲突 **0** |
| 5 | merge-tree vs 25aa898 | 冲突 **0** |
| 6 | algorithmOutputMode UI | **有证据** |
| 7 | api.ts / stele.ts / HomePage | **未改** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |

### 合入后冒烟 tip@5a7b20c（merge report@5195b5b into feature；parents 9de0bab+5195b5b；含 algoMode UI + getHealth/samples_*）—— RM-红队QA @ 2026-10-25 16:20 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `5a7b20c` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | ancestry | **确认** |
| 3 | A24 | **仍 1p/1xfail / 未关** |
| 4 | G1 / Phase2 ROI | **通过** |
| 5 | Phase2+AB8 | **通过** |
| 6 | ES spot | **通过** |
| 7 | claims | **ok / conflict 仍开** |
| 8 | museum | **passed** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 评测 tip 门禁 tip@c6de56e（R7 lag=182 证据戳；rebase 取代 802d51d）相对 feature@5a7b20c—— RM-红队QA @ 2026-10-25 16:21 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `c6de56e` | 自 FINDINGS |
| 1 | tip 存在 | **确认** |
| 2 | vs 旧 802d51d | **rebase 取代** |
| 3 | vs feature@5a7b20c merge-tree | **冲突 0** |
| 4 | feature 分支 tip | **=5a7b20c** |
| 5 | docs-only | **是** |
| 6 | R7 lag=182 | **证据有 / 仍开** |
| 7 | A24 | **仍开 / xfail 未假绿** |
| 8 | npm/tsc | **跳过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **可合并** | 自 FINDINGS |

### 合入后冒烟 tip@7e080c5（merge AB-8 arch@12f8883 into feature；parents 5a7b20c+12f8883；含 health-samples-banner）—— RM-红队QA @ 2026-10-25 16:29 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `7e080c5` | 自 FINDINGS |
| 1 | tip / parents | **确认** |
| 2 | AB-8 banner | **有证据** |
| 3 | A24 | **仍 1p/1xfail / 未关** |
| 4 | museum | **passed** |
| 5 | npm/tsc build | **通过** |
| 6 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 评测 tip 门禁 tip@19255db（R7 lag=184 证据戳；rebase 取代 c6de56e/802d51d；相对 feature@7e080c5）—— RM-红队QA @ 2026-10-25 16:35 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `19255db` | 自 FINDINGS |
| 1 | tip 身份 | **确认** |
| 2 | vs 旧 tip | **rebase 取代** |
| 3 | vs feature@7e080c5 merge-tree | **冲突 0** |
| 4 | feature 分支 tip | **=7e080c5** |
| 5 | docs-only | **是** |
| 6 | R7 lag=184 | **证据齐 / 仍开** |
| 7 | A24 | **仍开 / xfail 未伪绿** |
| 8 | npm/tsc | **跳过** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **可合并** | 自 FINDINGS |

### 合入后窄冒烟 tip@19255db（ff-only eval docs onto feature@7e080c5；parent=7e080c5；docs-only +20/-7）—— RM-红队QA @ 2026-10-25 16:36 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `19255db` | 自 FINDINGS |
| 1 | tip / parent | **确认** |
| 2 | docs 合入 | **已进** |
| 3 | AB-8 仍在 | **验证静** |
| 4 | A24 | **仍 1p/1xfail / 未关** |
| 5 | museum | **passed** |
| 6 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 自 FINDINGS |

### 报告 tip 门禁 tip@21a3dc7（slice13 inventory docs-only；相对 feature@19255db）—— RM-红队QA @ 2026-10-25 16:45 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `21a3dc7` | 自 FINDINGS |
| 1 | tip / parent | **确认** |
| 2 | vs feature@19255db merge-tree | **冲突 0** |
| 3 | docs-only | **是** |
| 4 | 证据目录 slice13 | **有** |
| 5 | RF-8 | **仍开 / 未假关** |
| 6 | npm/tsc | **跳过** |
| 7 | museum | **passed** |
| 8 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **可合并** | 自 FINDINGS |

### 评测 tip 门禁 tip@6f25bfc（R7 lag=185 证据戳；docs-only；相对 feature@19255db）— @ RM-红队QA @ 2026-10-25 16:50 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `6f25bfc` | 自 FINDINGS |
| 1 | tip / parent | **确认** |
| 2 | vs feature@19255db merge-tree | **冲突 0** |
| 3 | docs-only | **是** |
| 4 | R7 lag=185 | **证据齐 / 仍开** |
| 5 | A24 | **仍开 / xfail 未伪绿** |
| 6 | museum | **passed** |
| 7 | 主库 SHA | **始=终未动** |
| 8 | 开项 | **仍开** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **可合并** | 自 FINDINGS |
### 合入后窄冒烟 tip@6f25bfc（ff-only eval docs；parent=19255db）—— RM-红队QA @ 2026-10-25 16:56 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | 6f25bfc897f5b3c1c444e52b0e384bda84c11d83 | parent=19255db |
| vs 19255db | 2 files / +63/-15 | ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE docs-only |
| AB-8 banner | **仍在（抽检）** | health-samples-banner + samples_* + degraded |
| docs | **已进** | R7 lag=185 仍开 |
| A24 | **仍开 1p/1xfail** | 未假绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（勿假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-6f25bfc |

### 报告 tip 门禁 tip@bd7303e（slice13 inventory docs-only rebase；取代 21a3dc7；相对 feature@6f25bfc）—— RM-红队QA @ 2026-10-25 17:00 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `bd7303e` | parent=`6f25bfc`；取代旧 21a3dc7 |
| 1 | tip / parent | **确认** |
| 2 | vs feature@6f25bfc merge-tree | **冲突 0**（FF 0 behind / 1 ahead） |
| 3 | docs-only | **是**（slice13 2 files +45） |
| 4 | 证据目录 slice13 | **有** |
| 5 | RF-8 | **仍开 / 未假关** |
| 6 | npm/tsc | **跳过** |
| 7 | 主库 SHA | **始=终未变** |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **可合并** | FF 可合入；日志 qa-tmp/qa-report-bd7303e |
### 合入后窄冒烟 tip@bd7303e（ff-only report docs；parent=6f25bfc）—— RM-红队QA @ 2026-10-25 17:04 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | bd7303e828c8e18988872712765b5c1dcfff6711 | parent=6f25bfc |
| vs 6f25bfc | 2 files / +45 | slice13 evidence + inventory docs-only |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | awaiting user screenshot；HomePage 未改 |
| R7 | **仍开** | lag=186 |
| A24 | **仍开 1p/1xfail** | 未假绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未自关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-bd7303e |
### 评测 tip 门禁 tip@fa5bf1c（R7 lag stamp docs-only；对照 feature@bd7303e）— @ RM-红队QA @ 2026-10-25 17:19 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | `fa5bf1c4a50a984ffb993a8f7a9787c07cb15e4e` | parent=bd7303e；subj=R7 lag=186 stamp after feature@bd7303e |
| 主仓 feature tip | `bd7303e828c8e18988872712765b5c1dcfff6711` | 门禁时记实（期望 bd7303e） |
| vs feature@bd7303e | **冲突 0** | merge-tree clean；tree `1dc8b66fffb07d9328926293d4bb339caa57162e`；FF 单提交 ahead=1 / behind=0 |
| docs-only | **是** | 2 files / +34/-18；ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE；museum_processing 未改 |
| R7 lag | **有条件 / 仍开** | tip HEAD rev-list=**187**；parent=**186**；正文 stamp=186 与 HEAD 计数差 1 |
| A24 | **仍开** | pytest -k a24 → 1p/1xfail；未伪绿 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| P1/RF-8/conflict/RT | **仍开** | 闸门未收口 |
| **门禁结论** | **有条件可合并** | 条件：修正 lag stamp 口径（HEAD=187 或明确相对 bd7303e=186） |
### 评测 tip 窄门禁 tip@46c7ded（R7 lag stamp 校正 docs-only；取代 fa5bf1c；对齐 feature@bd7303e）— @ RM-红队QA @ 2026-10-25 17:31 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | 46c7ded94c7244a8fd410501a672f9a7c28cc963 | parent=bd7303e；subj=fix R7 lag stamp to measured HEAD rev-list |
| 当时 feature tip | bd7303e828c8e18988872712765b5c1dcfff6711 | 门禁时实测（期望 bd7303e） |
| vs feature@bd7303e | **冲突 0** | merge-tree clean；tree 1928ab326b12f51248ff2cc8d92eace378d4655b；FF 单提交 ahead=1 / behind=0 |
| docs-only | **是** | 2 files / +34/-18；ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE；museum_processing 未动 |
| R7 lag | **一致 / 仍开** | tip HEAD rev-list=**187**；parent=**186**；正文 stamp=187 与实测一致 |
| A24 | **仍开** | pytest -k a24 → 1p/1xfail；未伪关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=末未变** | 8408DBC3…323D / 854DF859…BABD3 |
| P1/RF-8/conflict/RT | **仍开** | 栅栏未收口 |
| **门禁结论** | **可合并** | 旧 fa5bf1c 作废；stamp/实测均为 187 |
### 合入后窄冒烟 tip@46c7ded（ff-only eval docs；parent=bd7303e）—— RM-红队QA @ 2026-10-25 17:39 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | 46c7ded94c7244a8fd410501a672f9a7c28cc963 | parent=bd7303e |
| vs bd7303e | 2 files docs-only | ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE |
| lag stamp | **187 一致** | 实测 rev-list=187；取代 fa5bf1c |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | awaiting user screenshot；HomePage 未改 |
| R7 | **仍开** | lag=187 |
| A24 | **仍开 1p/1xfail** | 未假绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-46c7ded |

### 完整门禁 tip@e662631（ES-3/4/5 非窄 docs；parent=46c7ded）— @ RM-红队QA @ 2026-10-25 17:49 Asia/Shanghai

| 项 | 状态 | 说明 |
|---|---|---|
| tip | e66263185036b18c45682d1b980ced73bcf61898 | parent=46c7ded94c7244a8fd410501a672f9a7c28cc963；subj=ES-3/4/5 paired-ref gate + full caption/NLC asserts |
| 当时 feature tip | 46c7ded94c7244a8fd410501a672f9a7c28cc963 | 门禁时实测（期望 46c7ded） |
| vs feature@46c7ded | **冲突 0 / FF** | merge-tree clean；tree 164a106758e7613da415aa97f06675972cd2473f；ahead=1 / behind=0 |
| 变更面 | **4 files +207/−2** | eval_export_contract.py / test_es_derived_contracts.py / ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE；museum_processing 未改 |
| ES-3/4/5 | **有证据** | paired-ref 门禁 + PSNR 主口径；全量图注；display↔NLC 1:1；pytest 覆盖 |
| pytest | **756p / 1xfail** | pytest tests/ -q 实跑；+9 新测；exit=0 |
| R7 lag | **一致 / 仍开** | tip HEAD rev-list=**188**；stamp=188；未关 R7 |
| A24 | **仍开** | pytest -k a24 → 1p/1xfail；未假绿 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| P1/RF-8/conflict/RT | **仍开** | 栅栏未改关 |
| **门禁结论** | **可合并** | 非窄 docs 完整门禁通过；日志 qa-tmp/qa-eval-e662631 |
### 合入后冒烟 tip@e662631（ff-only eval；parent=46c7ded；非窄 docs）—— RM-红队QA @ 2026-10-25 17:56 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | e66263185036b18c45682d1b980ced73bcf61898 | parent=46c7ded |
| vs 46c7ded | 4 files（非纯 docs） | contract + tests + ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE |
| 契约测 | **30 passed** | test_es_derived_contracts.py |
| 全量 pytest | **756p / 0 fail / 1 xfail** | A24 仍 xfail |
| lag stamp | **188 一致** | 实测 rev-list=188 |
| AB-8 banner | **仍在（静态核）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | awaiting user screenshot；HomePage 未改 |
| R7 | **仍开** | lag=188 |
| A24 | **仍开 1p/1xfail** | 未假绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **结论** | **通过** | 合入后冒烟；日志 qa-tmp/qa-smoke-post-e662631 |


### 窄门禁 tip@7e99080（jinshi Top15；parent=e662631；docs-only；并行 arch@d6f434d）—— RM-红队QA @ 2026-10-25 18:11 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | 7e9908042811f4a8ace880ced8190687abb7c1ff | parent=e662631 |
| merge-tree | **冲突 0 / 可 FF** | ahead=1 behind=0 |
| diff | **docs-only +83** | 仅 CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md |
| Top15 | **优先级队列非关单** | 禁写 claims / 禁抬 Verification / 禁 C-08；异文并列 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **结论** | **可合并** | 日志 qa-tmp/qa-jinshi-7e99080 |

### 窄门禁 tip@d6f434d（arch RT-010 CI draft；parent=e662631；docs-only）—— RM-红队QA @ 2026-10-25 18:12 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | d6f434dd62938b95187da5877875f7cdcd55b2bd | parent=e662631；subj=RT-010 draft-feature-gate |
| 当时 feature tip | e66263185036b18c45682d1b980ced73bcf61898 | 门禁时实测（期望 e662631） |
| vs feature@e662631 | **冲突 0 / FF** | merge-tree clean；ahead=1 / behind=0 |
| docs-only | **是** | 2 files / +58；ci-feature.draft.yml + RT010_CI_DRAFT.md |
| 生效 ci.yml | **未碰** | blob 相同；不在 name-status |
| draft 性质 | **草稿** | 不在 .github/workflows/；DRAFT ONLY 头注释 |
| RT-006/RF-8/Tailwind | **未碰生效面** | 仅文档暂缓说明 |
| RT-010 | **仍开** | draft≠关单 |
| 主库 SHA | **未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **门禁结论** | **可合并** | 窄门禁通过；日志 qa-tmp/qa-arch-d6f434d |
### 窄门禁 tip@4ef251e（report P1+RF-8 截图清单；parent=e662631；docs-only；并行 arch/jinshi）—— RM-红队QA @ 2026-10-25 18:13 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | `4ef251eaeea5e933df72fd19070a13352e28c8d0` | parent=`e66263185036b18c45682d1b980ced73bcf61898` |
| merge-tree | **冲突 0 / 可 FF** | ahead=1 behind=0；tree=`7de89f340c2dd1e4612c24936c8607d5ca5771d1` |
| diff | **docs-only +118** | 仅 `REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`；未改 HomePage/apps/web |
| RF-8 | **仍开** | 等用户截图确认；禁止自关；禁止改 HomePage |
| 1440 | **待补 / 未伪造** | 无 phase1 RF-8@1440；未造假图 |
| 1920 证据 | **声明一致** | 主证据 1920×1080 在盘；`*_1920w`=1280×455 已标明 |
| P1 开项 | **仍开** | 证据≠关单；矩阵未改「通过」 |
| 主库 SHA | **始=末未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **门禁结论** | **可合并** | 日志 qa-tmp/qa-report-4ef251e |
### 合入后窄冒烟 tip@d6f434d（ff-only arch RT-010 CI draft；parent=e662631）— ✓ RM-红队QA @ 2026-10-25 18:17 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | d6f434dd62938b95187da5877875f7cdcd55b2bd | parent=e662631 |
| vs e662631 | 2 files docs-only | RT010_CI_DRAFT + ci-feature.draft.yml |
| 生效 ci.yml | **未碰** | `.github/workflows/ci.yml` 无 diff |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | inventory/evidence 仍列；HomePage 未改 |
| R7 | **仍开** | lag=189 |
| A24 | **仍开 1p/1xfail** | 未假绿 / 未关 |
| RT-010 | **仍开（draft only）** | 未改生效 workflows |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-010/conflict/产品 RT |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-d6f434d |

### 完整门禁 tip@8e72315（eval ES-3 dry-run + ES-6 E-05；parent=e662631；含代码）— RM-红队QA @ 2026-10-25 18:19 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | `8e7231572229999da5a50fe22eb93666acc0d3c0` | parent=`e66263185036b18c45682d1b980ced73bcf61898` |
| 门禁时 feature | `d6f434dd62938b95187da5877875f7cdcd55b2bd` | 已 FF 至 d6f434d（arch）；base 仍按 e662631 判 |
| merge-tree vs e662631 | **冲突 0 / 可 FF** | tree=`98604554…`；ahead=1 behind=0 |
| vs d6f434d | **diverged 1/1；冲突 0** | **须 rebase 后再窄核/FF**；文件无重叠 |
| 变更 | **8 files +412** | dry-run + skeleton + docs + contract；无 museum_processing |
| dry-run | **只读** | 不写 derived / 不重算 bootstrap / openFindings 保留 |
| pytest | **763p / 1xfail** | EXIT=0；契约+骨架 37p |
| A24 | **仍开** | 3p/1xfail；Top-k 未评测 |
| R7 lag | **189 一致仍开** | stamp=实测 |
| museum | **28/84** | sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/conflict/产品 RT |
| **门禁结论** | **可合并（须 rebase→窄核）** | 日志 qa-tmp/qa-eval-8e72315 |

### 红队窄核 tip@f27719c（jinshi Top15 rebase←d6f434d；旧 7e99080 作废）— RM-红队QA @ 2026-10-25 18:19 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | f27719cc64c3b4683af54bdcb67583cbed69c887 | parent=d6f434d；feature@d6f434d |
| vs d6f434d | 1 file docs-only +83 | CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md |
| blob vs 7e99080 | **相同** | 纯 rebase；旧 tip 作废勿合 |
| merge-tree | **干净 / 可 FF** | ahead1/behind0；struct_conflicts=0 |
| Top15 | **优先队列非关单** | 开项仍开；conflict 仍列；禁抬升/禁写 claims/禁 C-08 |
| RF-8 / R7 / A24 / P1 / conflict | **仍开（未假关）** | 台账栅栏未关 |
| 主库 SHA | **未变** | 8408DBC3…323D / 854DF859…BABD3 |
| **判决** | **可合并** | 窄核；日志 qa-tmp/qa-jinshi-f27719c |

### 窄核 report@60f967c — 2026-10-25 18:21 Asia/Shanghai
| 项 | 结果 |
|---|---|
| 判决 | 可合并（rel d6f434d）；feature→f27719c 则须 rebase 再合 |
| tip/parent | 60f967c / d6f434d |
| merge-tree | CLEAN；FF vs d6f434d |
| 变更 | docs-only +118 RF-8 清单 |
| RF-8 / 1440 | 仍开 / 待补未伪造 |
| HomePage | 未改 |
| SHA | 未变 MATCH |
| 旧 tip | 4ef251e 作废 |
| 日志 | wt/qa-tmp/qa-report-60f967c/ |
### 合入后窄冒烟 tip@f27719c（ff-only jinshi Claims Top15；parent=d6f434d） · RM-红队QA @ 2026-10-25 18:24 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | f27719cc64c3b4683af54bdcb67583cbed69c887 | parent=d6f434d |
| vs d6f434d | 1 file docs-only | CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md +83 |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | inventory/evidence 仍有；HomePage 未改 |
| R7 | **仍开** | lag=190 |
| A24 | **仍开 1p/1xfail** | 未假绿 / 未关 |
| RT-010 | **仍开（draft only）** | 本 tip 未碰 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-010/conflict/产品 RT |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-f27719c |


### 窄核 report@0c1ac0c · 2026-10-25 18:31 Asia/Shanghai
| 项 | 结果 |
|---|---|
| 判决 | **可合并**（rel f27719c；可 FF） |
| tip/parent | 0c1ac0c / f27719c |
| merge-tree | CLEAN；FF vs f27719c |
| 变更 | docs-only +118 RF-8 清单 |
| RF-8 / 1440 | 仍开 / 待补未伪造 |
| HomePage | 未改 |
| SHA | 未变 MATCH |
| 旧 tip | 60f967c / 4ef251e 作废 |
| 日志 | wt/qa-tmp/qa-report-0c1ac0c/ |

### 红队门禁 tip@40acb18（eval ES-3 dry-run + ES-6；rebase←f27719c）· RM-红队QA @ 2026-10-25 18:34 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| 判决 | **可合并（相对 f27719c）** | tip=`40acb18ab934d406dd3e00dbb1cbd731ab86786d`；parent=`f27719cc64c3b4683af54bdcb67583cbed69c887`；ahead 1/0；merge-tree 0 / 可 FF |
| tip 再动 | **条件** | Green 已令 FF report@0c1ac0c；**feature 到 0c1ac0c 后本 tip 须 rebase 再合**；勿合 dfbf8f0/8e72315 |
| 变更 | 8 files +419/−1 | 含代码（dry-run + 契约/骨架测）；无 museum_processing |
| pytest | 763p / 1xfail / 0fail | EXIT=0；契约抽检 37p |
| dry-run | wroteDerived=false | recomputedBootstrap=false；openFindings 保留；未伪绿 |
| ES-6 | 仍开 | 草案/勿伪绿；未关 TASK_BOARD |
| A24 / R7 | 仍开 | A24 xfail；R7 lag=191=stamp |
| museum / SHA | 28/84；SHA 未变 | 8408DBC3…323D / 854DF859…BABD3 |
| 禁令 | 遵守 | 未 push/commit/merge；未 C-08 --apply；未假关开项 |
| 日志 | qa-eval-40acb18 | wt/qa-tmp/qa-eval-40acb18/ |
### 合入后窄冒烟 tip@0c1ac0c（ff-only report P1+RF-8 清单；parent=f27719c） · RM-红队QA @ 2026-10-25 18:39 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | 0c1ac0cf5acc8faa4a066ae26a384dee536a428e | parent=f27719c |
| vs f27719c | 1 file docs-only | REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md +118 |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | inventory/evidence 仍列；1440 待补；HomePage 未改 |
| R7 | **仍开** | lag=191 |
| A24 | **仍开 1p/1xfail** | 未强绿 / 未关 |
| RT-010 | **仍开（draft only）** | 本 tip 未碰 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-010/conflict/红队 RT |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-0c1ac0c |
### 窄门禁 tip@d376dbc（arch CI draft 扩展 + RT-006 备忘；parent=0c1ac0c）— RM-红队QA @ 2026-10-25 18:47 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | d376dbcabced081da22619dbe5a459a5520440df | parent=0c1ac0c；feature 仍=0c1ac0c |
| merge-tree | **CLEAN / 可 FF** | ahead=1 behind=0 |
| vs 0c1ac0c | 3 files docs-only +114/−5 | RT006 brief + RT010 draft + ci-feature.draft.yml |
| 生效 ci.yml | **未碰** | blob 前后相同 |
| DeduceRequest/static | **未碰** | 无业务路径 diff |
| RT-006 brief | **备忘/待拍板** | 不自选 A/B/C；非决策关闭 |
| RT-006 | **仍开** | 未假关 |
| RT-010 | **仍开（draft）** | 未升格生效 workflow |
| 主库 SHA | **未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-006/RT-010/conflict |
| **判决** | **可合并** | 窄门禁；日志 qa-tmp/qa-arch-d376dbc |

### 红队门禁 tip@4b17bc5（eval ES-3 dry-run + ES-6；rebase←0c1ac0c）— RM-红队QA @ 2026-10-25 18:48 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| 判决 | **可合并 / 可 FF（相对 0c1ac0c）** | tip=`4b17bc5556e0eceff6f603465bbf37ba77934c34`；parent=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；ahead 1/0；merge-tree 0 / 可 FF；feature结案=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e` |
| tip 竞速 | **留意并行** | Green 并行 arch@d376dbc；若 tip 先动则本 tip REBASE_REQUIRED；旧 40acb18/dfbf8f0/8e72315 作废 |
| 变更 | 8 files +419/−1 | 含代码（dry-run + 契约/骨架测）；无 museum_processing |
| pytest | 763p / 1xfail / 0fail | EXIT=0；契约抽检 37p |
| dry-run | wroteDerived=false | recomputedBootstrap=false；openFindings 保持；未伪绿 |
| ES-6 | 仍开 | 草案/不伪绿；未关 TASK_BOARD |
| A24 / R7 | 仍开 | A24 xfail；R7 lag=192=stamp |
| museum / SHA | 28/84；SHA 未变 | 8408DBC3…323D / 854DF859…BABD3 |
| 禁令 | 遵守 | 未 push/commit/merge；未 C-08 --apply；未假关开项 |
| 日志 | qa-eval-4b17bc5 | wt/qa-tmp/qa-eval-4b17bc5/ |

### 附注 tip@4b17bc5 REBASE_REQUIRED — RM-红队QA @ 2026-10-25 18:49 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| 最终判决 | **有条件可合并（REBASE_REQUIRED）** | feature现=d376dbcabced081da22619dbe5a459a5520440df；vs d376dbc AB=1/1；无文件重叠 |
| 下一步 | rebase←d376dbc | 旧 4b17bc5/更旧 tip 勿合；QA 未 merge |

### 窄门禁 tip@b16c756（jinshi Top5 复核笔记；parent=0c1ac0c；docs-only） — RM-红队QA @ 2026-10-25 18:52 Asia/Shanghai

| 检查项 | 结果 | 证据 |
|---|---|---|
| tip / parent | b16c756 / 0c1ac0c | docs(jinshi) Top5 notes |
| merge-tree vs 0c1ac0c | CLEAN / 可 FF | tree=31b6227… |
| 变更 | docs-only +191 | NOTES_TOP5 + Top15 指针 |
| NOTES | 并列冲突非关单 | conflict×5 仍开 |
| 主库 SHA | 未变 | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | 仍开 | conflict/P1/RF-8/R7/A24/RT-006/RT-010 |
| feature 现态 | 已到 d376dbc | diverged 1/1 |
| **判决** | **REBASE_REQUIRED ← d376dbc** | 勿合旧 tip；未自行 merge |
### 合入后窄冒烟 tip@d376dbc（ff-only arch CI draft+RT006 brief；parent=0c1ac0c） · RM-红队QA @ 2026-10-25 18:52 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | d376dbcabced081da22619dbe5a459a5520440df | parent=0c1ac0c |
| vs 0c1ac0c | 3 files docs-only +114/-5 | RT006 brief + RT010 draft + ci-feature.draft.yml |
| 生效 ci.yml | **未碰** | blob 前后相同 |
| DeduceRequest/static | **未碰** | 无业务路径 diff |
| RT-006 brief | **备忘/非关单** | 未自选 A/B/C；非决策关闭 |
| RT-006 | **仍开** | 未假关 |
| RT-010 | **仍开（draft）** | 未启用生效 workflow |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | inventory/evidence 仍有；HomePage 未改 |
| R7 | **仍开** | lag=192 |
| A24 | **仍开 1p/1xfail** | 未强绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-006/RT-010/conflict |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-d376dbc |

### 窄核 tip@eba2faf（jinshi Top5 笔记 rebase←d376dbc；parent=d376dbc；docs-only） · RM-红队QA @ 2026-10-25 18:55 Asia/Shanghai

| 检查项 | 结果 | 证据 |
|---|---|---|
| tip / parent | eba2faf / d376dbc | docs(jinshi) Top5 notes；主仓 tip=d376dbc |
| ahead/behind | 1/0 | 可 FF |
| merge-tree vs d376dbc | CLEAN / 可 FF | tree=`2ec791f0058f3090c913e74217c391a2120d7230` |
| 变更 | docs-only +191 | NOTES_TOP5 + Top15 指针；无 claims/主库/馆藏 |
| NOTES | 并列冲突非关单 | conflict×5 仍开；非关闭声明 |
| 主库 SHA | 未变 | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | 仍开 | conflict/P1/RF-8/R7/A24/RT-006/RT-010 |
| 旧 tip | 作废 | b16c756 勿合 |
| **判决** | **可合并** | 窄核通过；日志 qa-tmp/qa-jinshi-eba2faf |

### 完整门禁 tip@6f42ab1（eval@6f42ab1；ES-3/ES-6） — RM-红队QA @ 2026-10-25 18:59 Asia/Shanghai

| 检查项 | 结果 | 证据 |
|---|---|---|
| tip / parent | 6f42ab1 / d376dbc | ES-3 dry-run + ES-6 E-05 draft |
| vs d376dbc | ahead1 / merge-tree0 / 可 FF | parent 吻合 |
| vs feature@eba2faf | **diverged 1/1** | REBASE_REQUIRED ←eba2faf；merge-tree0 仍不可直接 FF |
| diff | 9 files +554/-1 | 含 experiments/tests 代码 |
| pytest | **766p / 1xfail** | A24 xfail 仍开 |
| dry-run | 只读 / 未伪绿 | wroteDerived=false；openFindings=appliedStatus drift |
| R7 lag | 实测193 / stamp192 | 不一致；仍开 |
| museum | 28/84 | sha256Match=84 |
| 主库 SHA | 始=终 MATCH | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | 仍开 | A24/R7/ES-6/ES-3/RF-8/P1/conflict/RT-006/RT-010 |
| 旧 tip | 勿合 | 4b17bc5/40acb18/8e72315/dfbf8f0 |
| **裁决** | **有条件可合并** | 条件=REBASE_REQUIRED←eba2faf；日志 qa-tmp/qa-eval-6f42ab1 |
### 合入后窄冒烟 tip@eba2faf（ff-only jinshi Top5 NOTES；parent=d376dbc）— RM-红队QA @ 2026-10-25 19:01 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | eba2faf505dfa4f79f0fae523d00cc5dadbc6823 | parent=d376dbc |
| vs d376dbc | 2 files docs-only +191 | NOTES_TOP5 + TOP15 指针 |
| 生效 ci.yml | **未碰** | blob 前后相同 |
| claims JSON / museum 数据 | **未碰** | 无业务/数据路径 diff |
| NOTES conflict | **仍开/不假关** | status=conflict ×5 |
| RT-006 | **仍开** | 本 tip 未触 |
| RT-010 | **仍开（draft）** | 未碰生效 workflow |
| AB-8 banner | **仍在（静态）** | health-samples-banner + samples_* + degraded |
| RF-8 | **仍开** | inventory/evidence 仍有；HomePage 未改 |
| R7 | **仍开** | lag=193 |
| A24 | **仍开 1p/1xfail** | 未强绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-006/RT-010/NOTES-conflict/ES-6 |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-eba2faf |

### 窄核 tip@bd15ce0（report RF-8 1440×900 + 清单§E；parent=eba2faf；docs-only）· RM-红队QA @ 2026-10-25 19:01 Asia/Shanghai

| 检查项 | 结果 | 证据 |
|---|---|---|
| tip / parent | bd15ce0 / eba2faf | `bd15ce01fe9467bf23124ca6a4335a987874bfe1`；parent=`eba2faf505dfa4f79f0fae523d00cc5dadbc6823`=当前 feature HEAD |
| ahead/behind | 1/0 | 可 FF；feature 是 tip 祖先 |
| merge-tree vs eba2faf | CLEAN / 可 FF | `<<<<<<<`=0；changed-in-both=0 |
| 变更 | docs-only 3files +95/-1 | M REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md；A rf8_home_core_cards_1440x900.png；A slice16-rf8-verify.json |
| HomePage / apps/web / ci.yml | **未改** | name-status 无业务代码/生效 ci |
| PNG 实测 | 1440×900 | Pillow size=(1440,900)；bytes=1197153；verify.json measured_px=1440x900 |
| RF-8 | **仍开** | 清单§E「待开/待用户确认」；禁止自关；未抬 verification；未关 Phase1 |
| 旧 tip | 作废勿合 | 492d48c / 1c0673b / 60f967c / 4ef251e |
| 主库 SHA | 始=末 MATCH | rubbingmind=`8408DBC3…323D`；evidence-v2=`854DF859…BABD3` |
| 开项 | 仍开（未假关） | P1/RF-8/R7/A24/RT-006/RT-010/conflict |
| **裁决** | **可合并** | 可 FF；日志 qa-tmp/qa-report-bd15ce0 |
### 合入后窄冒烟 tip@bd15ce0（ff-only report RF-8 1440；parent=eba2faf）— RM-红队QA @ 2026-10-25 19:10 Asia/Shanghai

| 项 | 结果 | 备注 |
|----|------|------|
| tip | bd15ce01fe9467bf23124ca6a4335a987874bfe1 | parent=eba2faf |
| vs eba2faf | 3 files docs-only +95/−1 | RF8清单§E + 1440 png + verify json |
| HomePage | **未改** | 无 HomePage* diff |
| 生效 ci.yml | **未碰** | blob 前后相同 |
| _merge_bak_slice16_* | **未入库** | 仅磁盘备份，勿 add |
| claims JSON / museum 数据 | **未改** | 无业务/数据路径 diff |
| RF-8 | **仍开** | inventory/evidence/report 仍列；HomePage 未改 |
| R7 | **仍开** | lag=194 |
| A24 | **仍开 1p/1xfail** | 未强绿 / 未关 |
| museum | **passed** | 28/84 sha256Match=84 |
| 主库 SHA | **始=终 MATCH** | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | **仍开（未假关）** | P1/RF-8/R7/A24/RT-006/RT-010/NOTES-conflict/ES-6 |
| **结论** | **通过** | 合入后窄冒烟；日志 qa-tmp/qa-smoke-post-bd15ce0 |

### 窄核 arch@12cff65（RT-010 draft permissions+checklist + AB_OPEN；parent=bd15ce0；docs-only）· RM-红队QA @ 2026-10-25 19:12 Asia/Shanghai

| 检查项 | 结果 | 证据 |
|---|---|---|
| tip / parent | 12cff65 / bd15ce0 | `12cff65a9285ccac6c7756d83bbbd1070b2c3306`；parent=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`=当前 feature HEAD |
| ahead/behind | 1/0 | 可 FF；feature 为 tip 祖先 |
| merge-tree vs bd15ce0 | CLEAN / 可 FF | write-tree=`d2ef09ed26a1ff2bfcc739b13998e8cefc21310c`；CONFLICT=0 |
| 变更 | docs-only 3files +44/-20 | AB_OPEN / RT010_CI_DRAFT / ci-feature.draft.yml |
| 生效 ci.yml | **未碰** | blob `56f507bcdc7069868fd92f3305df78a2c8804322` parent==tip；name-only 无 `.github/**` |
| RT-006 | **仍开 / 未自选 A/B/C** | static/index.html 仍在；备忘≠拍板 |
| RT-010 | **仍 draft 未上线** | 仅扩 draft permissions+checklist；未迁入 workflows |
| 主库 SHA | 始=终 MATCH | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | 仍开（未假关） | P1/RF-8/R7/A24/RT-006/RT-010/NOTES-conflict/ES-6 |
| 并行 | 先过先 FF | 与 eval@4d93c78 同 parent；另一路或需 rebase |
| **裁决** | **可合并** | 可 FF；日志 qa-tmp/qa-arch-12cff65 |
### 完整门禁 tip@4d93c78（eval@4d93c78；ES-3/ES-6；parent=bd15ce0；含代码）· RM-红队QA @ 2026-10-25 19:12 Asia/Shanghai

| 检查项 | 结果 | 证据 |
|---|---|---|
| tip / parent | 4d93c78 / bd15ce0 | `4d93c787d02859eb8248f2e1728296019ccb10ff`；parent=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`=当前 feature HEAD |
| ahead/behind | 1/0 | 可 FF；feature 为 tip 祖先 |
| merge-tree vs bd15ce0 | CLEAN / 可 FF | write-tree=`676f9a08…`；CONFLICT=0 |
| 变更 | 9 files +554/−1（含代码） | ES-3 dry-run + ES-6 E-05 同族；含 experiments/tests |
| pytest | **766p / 1xfail** | A24 xfail 仍开；EXIT=0 |
| ES contracts | 40 passed | skeletons + derived contracts |
| dry-run | 只读 / 未伪绿 | wroteDerived=false；recomputedBootstrap=false；hasOpenFindings=true；derived 未写 |
| R7 lag | 实测 tip=195 / parent=194 / header stamp=194 | tip+1 漂移；**仍开勿假关** |
| museum | 28/84 | sha256Match=84 |
| 主库 SHA | 始=终 MATCH | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | 仍开（未假关） | A24/R7/ES-6/ES-3/RF-8/P1/conflict/RT-006/RT-010 |
| 旧 tip | 作废勿合 | 43d77b1 / 6f42ab1 / 4b17bc5 等 |
| 并行 | 先过先 FF | 与 arch@12cff65 同 parent；另一路合入后或需 rebase |
| **裁决** | **可合并** | 可 FF；marker=`eval@4d93c78`；日志 qa-tmp/qa-eval-4d93c78 |


### 窄核 tip@04f207e（report 续页 F·P1 开项盘点 vs bd15ce0·docs-only）· RM-红队QA @ 2026-10-25 19:13 Asia/Shanghai

| 核验项 | 结果 | 证据 |
|---|---|---|
| tip / parent | 04f207e / bd15ce0 | `04f207e8c2f13b760fcc94506b43f656ef9e8c6f`；parent=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`=当前 feature HEAD |
| ahead/behind | 1/0 | 可 FF；feature 为 tip 祖先 |
| merge-tree vs bd15ce0 | CLEAN / 可 FF | write-tree=`a7cd011ad4fb830427f7fa4f21271f7de77c75d3`；CONFLICT=0 |
| 变更 | docs-only 1file +45 | M REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md 续页 F |
| HomePage / apps/web / ci.yml | **未改** | name-status 无业务代码/生效 ci |
| RF-8 | **仍开** | F.1 仍开/等用户确认；禁止自关；未改 HomePage |
| 主库 SHA | 始=终 MATCH | 8408DBC3…323D / 854DF859…BABD3 |
| 开项 | 仍开（未假关） | P1/RF-8/R7/A24/RT-006/RT-010/NOTES-conflict/ES-6 |
| 并行 | 先过先 FF | 同 parent arch@12cff65 / eval@4d93c78 |
| **裁决** | **可合并** | 可 FF；日志 qa-tmp/qa-report-04f207e |
