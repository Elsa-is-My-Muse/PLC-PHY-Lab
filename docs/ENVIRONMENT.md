# 环境与检查记录

## 既有环境（会话记录导入）

- Windows，PowerShell。
- radioconda，GNU Radio 3.10.12.0，Python 3.12。
- SoapySDR HackRF Source；已报告能够识别设备并接收短时样本。
- `hackrf_info` 报告 HackRF One、固件 2024.02.1（API 1.08）。不公开设备序列号。

## 本仓库的两条运行路径

离线分析只需 Python 与 `requirements.txt`。GNU Radio 流程需另行准备包含 Soapy HackRF 的 GNU Radio 环境；在普通 Python 中安装本项目依赖不会自动安装 GNU Radio 或设备驱动。

编译现有流程的 Windows 辅助脚本：

```powershell
.\scripts\compile_gnuradio.ps1 -RadiocondaRoot 'D:/000_soft/radioconda'
```

它设置进程内 PATH 与 GRC block 搜索路径，输出到被 Git 忽略的 `build/gnuradio/`，随后做 Python 语法编译检查，不打开接收设备。

不要把 GRC 编译成功记作实际收到 PLC，也不要把“USB 识别成功”记作长期采样连续性已验证。
