# IQ 数据与分析约定

## 支持格式

| 格式名 | 磁盘布局 | 字节／复样本 | 工具中的处理 |
| --- | --- | --- | --- |
| `cf32_le` | 小端 float32，I、Q 交错，无头 | 8 | 保留输入数字单位 |
| `cs8` | signed int8，I、Q 交错，无头 | 2 | I、Q 各除以 128 转为浮点 |

本项目 GNU Radio 采集流程输出 `cf32_le`。20 MS/s 时一秒是 160,000,000 字节，0.25 秒是 40,000,000 字节。浮点存储不会提高 HackRF ADC 的有效位数。

## 为真实采集补齐元数据

下面是命令格式示例，执行前用实际采集设置替换参数：

```powershell
python -m tools.capture_metadata data/raw/your_capture.cf32 --source hardware --format cf32_le --sample-rate 20000000 --center-frequency 10000000 --if-gain 0 --vga-gain 0 --analog-bandwidth 20000000 --external-attenuation-db 40
python -m tools.analyze_iq data/raw/your_capture.cf32 --metadata data/raw/your_capture.metadata.json --output-dir data/processed/your-capture
```

元数据包括格式、采样率、中心频率、数据来源、字节／样本数与 SHA-256，以及可选的接收设置。未提供的硬件参数保持 null。填写了外部衰减不代表已经标定，也不会自动修正 PSD 为 dBm。工具拒绝覆盖已有元数据与分析输出。

## 分析含义

- 默认仅分析文件开头最多 2,000,000 个样本；结果同时记录总样本数和已分析样本数。可用 `--max-samples` 调整。
- 使用双边 Welch PSD，再 fftshift，并以中心频率换算到 RF 频率轴。
- 纵轴为 `dB re 1 unit²/Hz`，未经接收链功率标定。
- 输出包络、PSD、时频图和 JSON 统计；标出数据来源。
- `papr_db` 是已分析样本的数字功率峰均比，包含噪声与空闲段，会受取样窗口影响。
- `near_unit_component_fraction` 仅统计 I／Q 接近或超过 ±1 的比例。浮点量程依赖来源，不能仅凭此判断 ADC 削顶。
- 文件大小和 SHA-256 能核对数据完整性；它们不能证明 USB 采集中没有丢样。应同时保存接收端错误日志和实验条件。
- `.metadata.json` 是本项目自有格式，不宣称符合 SigMF。以后迁移标准格式时应单独验证。

## 仓库与数据分工

原始采集保存 `data/raw/`，处理结果默认保存在 `data/processed/`，均被 Git 忽略。可审阅的小型图表、摘要和脱敏元数据放到对应实验目录后再提交。`examples/synthetic/` 只发布合成数据的分析结果，原始波形可通过固定随机种子重建。
