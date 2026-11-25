# Current Affairs：真实 PLC 调制解调器上的 SLAC 与抓包

整理日期：2026-11-25。状态：论文与核心源码阅读，未执行安装、SLAC 交互或现场测量。

论文：*Current Affairs: A Security Measurement Study of CCS EV Charging Deployments*，USENIX Security 2025。

本次检出作者仓库提交 `2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687`（提交时间 2025-02-13），并核对其固定的 `ssloxford/open-plc-utils` 子模块 `ba4805d1a8e517d6ae62d4921d26360f389687a3`。阅读重点为 README、SLAC Python 流程、抓包封装、会话控制、硬件接口、结果保存及子模块的 C 包装层。未执行作者程序。

## 它如何获取 SLAC 数据

项目以车辆端身份连接充电设备，执行自己的 SLAC 会话。作者 README 要求 Raspberry Pi 4、配置为 EV 模式的 HomePlug Green PHY 调制解调器，以及处理 CP／PP 基本信号的定制 PCB。调制解调器经以太网连接树莓派。

```text
充电设备的 CP／PE 通信线路
  → 适用的 PLC 接口／耦合电路
  → HomePlug Green PHY 调制解调器（完成物理层收发）
  → 以太网接口
  → SLAC 主机程序 + tcpdump
  → 结构化 SLAC 结果与 PCAP

CP／PP 基本信号
  → 定制板的检测／控制电路
  → 树莓派 GPIO／ADC 接口
  → CP 高低电平、占空比与 PP 状态记录
```

这能回答“作者如何得到 SLAC 数据”：从自己参与的 PLC 会话中读取已由调制解调器处理的协议消息，并保存主机接口抓包。该架构不要求在主机软件里从 HackRF IQ 重新实现 Green PHY 解调，也不能据此推断任意接在旁边的网卡都能看到第三方会话。

## 逐项对应到源码

| 阅读入口 | 源码证据 | 学习问题 |
| --- | --- | --- |
| [code/interface/slac_hw.py](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/code/interface/slac_hw.py) | `ev_init()` 初始化接口；`ev_run()` 调用参数、Sounding、衰减特征和匹配流程；`finally` 中记录 SLAC 结果 | 失败发生在哪个阶段？部分结果是否仍可保存？ |
| [code/interface/slac_common.py](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/code/interface/slac_common.py) | `SlacResult` 包含 RUN_ID、PEV／EVSE MAC、NMK、NID、AAG 等字段，`to_json()` 定义输出格式 | 哪些是身份／会话字段？哪些是衰减结果？ |
| [子模块 slac_wrapper.c](https://github.com/ssloxford/open-plc-utils/blob/ba4805d1a8e517d6ae62d4921d26360f389687a3/slac_python_module/slac_wrapper.c) | Python 扩展调用 `pev_cm_slac_param()`、`pev_cm_mnbc_sound()`、`pev_cm_atten_char()`、`pev_cm_slac_match()` 等 C 实现 | Python 状态机和 HomePlug 管理消息怎样对应？ |
| [code/pcap_wrapper.py](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/code/pcap_wrapper.py) | 启动 `tcpdump`，指定网络接口、快照长度和输出文件 | PCAP 中的报文与程序日志如何对齐？ |
| [code/controller.py](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/code/controller.py) | 会话上下文中启动抓包，输出名为 `pcap.pcap` | 抓包覆盖哪段测试？什么时候开始与结束？ |
| [code/utils/data_saver.py](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/code/utils/data_saver.py) | 日志有 UTC 时间及层级；输出 `result.json` 和逐行备份 | 异常、阶段和测量值如何保留证据？ |
| [code/interface/hal_v2.py](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/code/interface/hal_v2.py) | GPIO 控制继电器与 CP／PP 状态，ADC 接口读取基本信号 | 硬件连接状态怎样触发协议流程？ |

## AAG 衰减数据来自哪里

`slac_hw.py` 在完成衰减特征流程后调用 `read_aag()`。子模块的 `pev_cm_atten_char.c` 从收到的 `CM_ATTEN_CHAR.IND` 中把 AAG 写入会话结构；`slac_wrapper.c` 再把这个数组返回给 Python。

该实现的 `slac.h` 定义 `SLAC_GROUPS = 58`；包装层按 `NumGroups` 与缓冲区大小的较小值返回。这里读取的是协议中的分组衰减结果，没有在 Python 中对 IQ 做 FFT 来计算它。与 VNA S21 或 HackRF 的相对谱比较前，需要核对频率分组、参考条件和测量定义。

## 与现有 HackRF 平台如何配合

| 研究目标 | 本项目已有路线 | Current Affairs 提供的参考 |
| --- | --- | --- |
| 看实际射频突发、频谱与噪声 | 耦合器、待验证的保护链、HackRF、IQ 离线分析 | 协议程序日志可作为事件时间参考 |
| 确认具体 SLAC 消息和结果 | 尚需协议侧数据来源 | Green PHY 调制解调器、主机 SLAC 程序与接口 PCAP |
| 关联衰减数组和射频现象 | 计划中 | 结合 RUN_ID、双方 MAC、阶段日志与时间戳设计关联方法 |

当前设备清单未确认拥有该项目所需的树莓派、EV 模式 PLC 调制解调器和 CP／PP 控制板。现有 HackRF 与无源接收器件不能直接代替这些协议端设备。初期可先阅读源码与设计数据结构，不把硬件复现记为已完成。

后续在自己的隔离测试台架上形成“同步 IQ + PCAP + 日志”时，需记录时钟差、延迟和丢样；不能只按文件生成时间把每个突发直接认作某条消息。

## 硬件与安装资料的边界

- `pcb/` 提供 EasyEDA PCB JSON、Gerber、BOM、贴片坐标及 PCB 视图 PDF。检出的 JSON 文档类型是 PCB；不要把这些文件直接称为完整的 Green PHY 调制解调器设计或已经核实的隔离测量前端。
- 自制板的 ADC 读 CP／PP 基本信号；C ADC 代码注明面向 1 kHz PWM。它不承担 2–30 MHz PLC 波形的宽带采样与解调。
- `open-plc-utils` 指向作者的 fork，并包含 `slac_python_module`；不能默认换成上游 `qca/open-plc-utils` 后仍有相同 Python 接口。
- README 中一处提到 `code/hal_v2.py`，本次检出文件实际位于 `code/interface/hal_v2.py`。
- 完整上层通信功能还依赖修改的 V2GDecoder 和相关 schema；README 明确说明 schema 不随仓库分发。安装脚本会安装系统软件并构建子模块，本次仅阅读，未在本机执行。

## 阅读任务与完成条件

- [ ] 画出 `ev_run()` → C 包装层 → 对应 HomePlug 管理消息的调用关系。
- [ ] 从 `CM_ATTEN_CHAR.IND` 一路追踪 AAG 到 JSON，说明实际分组数量与数组长度。
- [ ] 解释 PCAP、结构化结果与 IQ 分别能证明什么，列出时间对齐字段。
- [ ] 硬件条件确认后，在自己的测试台架完成一份同步记录；保留失败阶段及缺失字段。

## 原始来源

- [作者仓库](https://github.com/ssloxford/current-affairs)
- [USENIX Security 2025 论文与演讲入口](https://www.usenix.org/conference/usenixsecurity25/presentation/szakaly)
- [正式论文 PDF](https://www.usenix.org/system/files/usenixsecurity25-szakaly.pdf)
- [固定版本 README](https://github.com/ssloxford/current-affairs/blob/2abd97e39d2bbeecda52f9d0ffdc0bed8c6cd687/readme.md)
- [子模块 pev_cm_atten_char.c](https://github.com/ssloxford/open-plc-utils/blob/ba4805d1a8e517d6ae62d4921d26360f389687a3/slac/pev_cm_atten_char.c)
- [子模块 slac.h](https://github.com/ssloxford/open-plc-utils/blob/ba4805d1a8e517d6ae62d4921d26360f389687a3/slac/slac.h)
- [子模块 ADC 实现](https://github.com/ssloxford/open-plc-utils/blob/ba4805d1a8e517d6ae62d4921d26360f389687a3/slac_python_module/adc_wrapper.c)

本笔记为独立撰写，只链接外部资料，没有复制作者源码、设计或抓包。作者主仓库采用 GPL-3.0；本学习仓库的 MIT 许可不改变外部材料的许可。
