# GNU Radio 接收流程

源文件位于 `gnuradio/`，由此前已编译的接收流程整理而来。项目不提供 RF 发射流程。

## 频谱观察

打开 `homeplug_spectrum.grc`，先确认接收输入与保护条件，再运行。采样率与模拟带宽均为 20 MHz；中心频率选择 10 MHz 或 22 MHz，RF 放大关闭，IF/VGA 默认为 0。

显示的频带边缘不等于保证平坦的模拟通带。图形电平未经功率标定，不能直接当作 dBm。

## 定时采集

先停止占用同一设备的其他流程。打开 `homeplug_capture.grc`，设置 `capture_seconds`、`center_freq` 和已验证的增益。默认 1 秒；首次可改为 0.25 秒。

输出为无头、小端 float32 I/Q（`cf32_le`）。默认保存到用户目录下的 `PLC-PHY-Lab-data/`，自动创建目录；文件名包括中心频率、采样率和微秒时间戳。

若希望输出在项目 `data/raw/`，应在启动 GNU Radio Companion 的同一个进程环境设置：

```powershell
$env:PLC_PHY_DATA_DIR = Join-Path (Get-Location).Path 'data/raw'
```

然后从该环境启动 GRC。已经打开的 GRC 不会自动继承后来设置的环境变量。也可直接在 GRC 修改输出表达式为已存在的目录。

采集结束后填写 [元数据](../docs/DATA_FORMAT.md)，同时记录控制台中的错误／溢出提示。Head 限定样本数不能证明接收时间连续。

## 不打开硬件的编译检查

```powershell
.\scripts\compile_gnuradio.ps1 -RadiocondaRoot 'D:/000_soft/radioconda'
```

编译结果进入 `build/gnuradio/`，不提交生成文件。
