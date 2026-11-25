# 实验索引

机器可读索引见 [index.json](index.json)。状态含义：

- `reported_prior_session`：从既有会话导入，没有原始证据附件。
- `planned`：计划，尚未执行。
- `in_progress`：进行中。
- `completed`：已执行，结论与数据索引应完整。
- `inconclusive`：已执行，但证据不足以回答问题。

| 编号 | 实验 | 状态 |
| --- | --- | --- |
| EXP-0001 | [HackRF 枚举与短时接收](EXP-0001-device-check/README.md) | 会话导入 |
| EXP-0002 | [防尘帽状态下观察频谱](EXP-0002-capped-input-spectrum/README.md) | 会话导入 |
| EXP-0003 | [首次带元数据的定时 IQ 归档](EXP-0003-first-archived-iq/README.md) | 计划 |

建立新实验：`python -m tools.new_experiment --slug your-test --title "实验标题"`。新目录与 JSON 索引会自动建立；上表为建库时的精选入口，后续记录以 JSON 索引和各实验目录为准。
