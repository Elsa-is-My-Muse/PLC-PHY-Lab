# 日常学习与实验记录

## 一次学习

1. 从学习路线选一个具体问题，例如“为什么接收滤波带宽要显式设置”。
2. 在 `journal/` 建立当天的 Markdown，写下原理图位置、源码路径、资料链接和自己的解释。
3. 把未确认的解释列为假设，设计能推翻或支持它的实验。

## 一次实验

1. 用 `tools.new_experiment` 创建编号，先填写问题、设备连接和计划参数。
2. 执行前确认输入条件；实际操作后将计划参数改为实际值，记录错误信息和意外现象。
3. 原始 IQ 放到 `data/raw/`；保存接收控制台输出。使用 `tools.capture_metadata` 记录完整设置与 SHA-256。
4. 用 `tools.analyze_iq` 生成图和统计，阅读 `analyzed_samples`，确认分析窗口覆盖了目标事件。
5. 将允许公开的小型结果复制到该实验目录，写明单位、数据来源和未解释现象。
6. 更新实验笔记与 `experiments/index.json` 中的状态。完成日期使用真实执行日期。
7. 在 `journal/` 写一段“今天学到什么、证据是什么、下一步是什么”。

## 保存到 GitHub

从项目根目录查看改动，只提交准备公开的记录：

```powershell
git status --short
git add journal experiments docs hardware
git diff --cached
git commit -m "docs: record the next PLC experiment"
git push
```

代码或示例改动按需加入提交。原始 IQ、PCAP 和本地分析目录默认被忽略；不要用强制添加绕过数据约定。提交后查看 GitHub Actions 是否通过。
