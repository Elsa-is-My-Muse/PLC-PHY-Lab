# BROKENWIRE：CP–PE 电磁耦合与功率测量阅读笔记

整理日期：2026-11-25。状态：文献阅读，未开展发射实验、干扰测试或现场复现。

论文：Sebastian Köhler、Richard Baker、Martin Strohmeier、Ivan Martinovic，*Brokenwire: Wireless Disruption of CCS Electric Vehicle Charging*，NDSS 2023。用户截图对应会议版 PDF 第 6 页的实验装置描述及功率测量说明；第 5 页图 5 给出实验架构。arXiv v2 更新于 2024-03-26，阅读时记录版本，避免页码混淆。

## 和本项目的关系

论文研究外部射频信号耦合进入充电通信线路后，对 HomePlug Green PHY 通信可用性的影响。当前项目的首要目标是用 HackRF 接收、保存并分析 CP–PE 上的 PLC 信号。论文适合作为电磁耦合、测量方法及接收行为的阅读材料；本笔记的结论均为引用或学习问题，没有新增硬件实测证据。

## 截图中的器件与作用

| 器件／软件 | 在论文中的作用 | 阅读时需要分清的概念 |
| --- | --- | --- |
| LimeSDR | 发射端 SDR | 论文配套代码面向 LimeSDR，不能据此认定可以直接在 HackRF 上运行。 |
| GNU Radio | 控制 SDR、处理待发射信号 | 软件平台不等于已实现完整 Green PHY 收发 PHY。 |
| Mini-Circuits ZX60-100VH+ | 提升发射端射频功率的放大器 | 厂家当前资料列出 0.3–100 MHz、典型增益 36 dB、典型输出 1 dB 压缩点 +30 dBm（12 V，25 °C 条件）。 |
| 1:9 balun | 同轴与平衡天线之间的转换及阻抗变换 | 通常标的是阻抗比；匝数比与阻抗比不同。仅凭该标注不能确认电气安全隔离。 |
| 两根 24 AWG 铜线组成的偶极天线 | 将发射信号耦合到空间 | 论文将天线描述为 7 m；长度与波长的关系随频率变化，不据此生成本项目的天线设计。 |

放大器的 +30 dBm 对应 1 W，但这里的典型压缩点不是任意输入下固定输出 1 W 的承诺。论文也另行测量 LimeSDR 不同增益设置的输出。阅读结果图时应查明功率测量参考面，不把 SDR 端口功率、放大器输出、天线辐射及线路接收功率视为同一量。

## 与已有接收器件如何对应

本项目接收链的抽象结构是：

```text
适用于实际线路的 PLC 耦合前端
  → 经验证的衰减／保护链
  → HackRF 接收
  → IQ 记录与离线分析
```

- 耦合器用于从被测线路获取信号，其实际型号、频带及使用接法仍需按实物核实。
- 衰减器降低进入后级的信号电平；限幅器在超过其阈值时进入非线性限制状态。它们与论文中提高发射功率的放大器用途不同。
- 本项目不由这篇论文推导新增放大器的采购需求。保护链的顺序、输入能力和残余电平仍按 [测量链路](../MEASUREMENT_CHAIN.md) 的待核实项处理。
- HackRF 官方最高采样率为 20 MS/s；不能一次记录完整的 2–30 MHz 连续频段。分时采样可以比较不同频段，不能拼成同一帧的全带宽 IQ。

## 适合纳入学习计划的三个问题

1. **参考面与校准：** 给每张图写清测的是哪个端口、什么阻抗、什么带宽，以及平均值还是峰值。未经标定的 HackRF 数字 PSD 保持相对单位，不直接标成 dBm。
2. **传播与接收：** 阅读论文中的耦合和接收行为分析，画出“外部场 → 线路 → PLC 接收机”的概念路径；把论文结论、自己的假设和实测结果分别标注。
3. **离线证据关联：** 在获得自己的真实 IQ 与协议日志后，分析突发、本底及链路事件的时间关系，报告时间对齐误差。通信超时不能单凭这篇论文归因于某一种射频干扰。

以上任务当前是阅读／分析计划。目前的设备清单未确认拥有 LimeSDR、该型号放大器、功率计或 VNA；没有产生本论文的复现数据。

## 原始资料

- [NDSS 2023 正式论文 PDF](https://www.ndss-symposium.org/wp-content/uploads/2023-251-paper.pdf)：截图所在实验装置、输出功率测量及后续分析。
- [arXiv v2 HTML，2024-03-26](https://arxiv.org/html/2202.02104v2)：便于搜索段落的作者论文版本。
- [作者配套仓库 ssloxford/brokenwire](https://github.com/ssloxford/brokenwire)：论文评估代码及环境说明；参考 README 的实验组织与测量对象。它不是完整 Green PHY 协议栈或通用 HackRF 解码器。
- [Mini-Circuits ZX60-100VH+ 数据表](https://www.minicircuits.com/WebStore/dashboardPdf?model=ZX60-100VH%2B)：以数据表条件解释放大器指标。
- [Mini-Circuits：RF 变压器原理与测量](https://www.minicircuits.com/appdoc/AN20-001.html)：匝数比、阻抗比、端接与反射。
- [Marki Microwave：Balun Basics Primer](https://markimicrowave.com/technical-resources/white-papers/balun-basics-primer/)：平衡／不平衡转换和阻抗比的定义。
- [HackRF One 官方规格](https://hackrf.readthedocs.io/en/latest/hackrf_one.html)：采样率、输入限制与接收测量边界。

仅链接和自行撰写阅读笔记，未复制作者代码、波形或论文图片。外部仓库采用其自身许可（作者仓库标注 GPL-3.0），本项目的 MIT 许可不改变外部资料的权利归属。
