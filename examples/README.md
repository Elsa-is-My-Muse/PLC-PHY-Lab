# 可复现示例

`python -m tools.generate_demo` 生成固定随机种子的复数合成信号，并建立本项目格式的元数据。它包含两个已知频率的突发与噪声，用来验证频率轴、PSD 和时域图。

它不是 HomePlug 调制波形，不用于证明真实 PLC 解码能力。

仓库发布 `synthetic/` 中的小型分析图与 JSON 摘要；原始 IQ 在本地生成并被 Git 忽略。
