# 参考项目与阅读问题

整理日期：2026-11-25。外部仓库、文件和页面可能变化；本项目不复制外部硬件设计或标准正文。

| 入口 | 重点阅读 | 自己需要回答的问题 |
| --- | --- | --- |
| [uhi22/foccci](https://github.com/uhi22/foccci) | `pcb/qca7000.kicad_sch`、`pdf/foccci_schematic_v5.2p7.pdf`、版本历史 | 高频信号如何耦合到 CP–PE？保护件的寄生参数放在哪里？ |
| [Millisman/QCA7000](https://github.com/Millisman/QCA7000) | 原始 KiCad 设计、README 的验证状态 | 哪些设计已实测？与后续 foccci 有何变化？ |
| [GNU Radio OFDM 示例](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-digital/examples/ofdm/ofdm_loopback.grc) | 发射、信道模型、接收 | 频偏、多径和噪声分别影响哪一步？ |
| [roeebar/gr-plc](https://github.com/roeebar/gr-plc) | `lib/phy_rx_impl.cc`、`lib/lightplc/phy_service.cc` | 前导相关、同步、信道估计如何实现？与标准互通还差什么？ |
| [greatscottgadgets/hackrf](https://github.com/greatscottgadgets/hackrf) | `hardware/`、`firmware/`、`host/libhackrf/` | 软件设置怎样作用于接收链？动态范围受什么限制？ |
| [scikit-rf](https://github.com/scikit-rf/scikit-rf) | Network、S 参数、级联、去嵌入教程 | 测量参考面和端接改变后，解释是否仍成立？ |
| [scikit-rf_workshop](https://github.com/scikit-rf/scikit-rf_workshop) | 教学 Notebook | 能否复现一个 S 参数分析并解释单位？ |
| [NanoVNA-Saver](https://github.com/NanoVNA-Saver/nanovna-saver) | 校准、扫描、Touchstone 导出 | 夹具与校准如何进入误差预算？ |
| [qca/open-plc-utils](https://github.com/qca/open-plc-utils) | `SignalToNoise*.c`、`ToneMaps*.c`、`PhyRates*.c`、`slac/` | 查询返回什么？本机固件是否支持？ |
| [open-plc-com/PLC-modem](https://github.com/open-plc-com/PLC-modem) | 1.84 MHz 耦合、谐振与接收电路 | 窄带方案与宽带 OFDM 的线性要求有何不同？ |
| [ssloxford/brokenwire](https://github.com/ssloxford/brokenwire) | README、论文实验装置与输出功率测量；[阅读笔记](reading/BROKENWIRE.md) | 发射端口功率与线路接收功率有何区别？电磁耦合如何影响通信可用性？ |

`gr-plc` 作者说明其实现不与标准 HomePlug 互通，且安装示例基于较老环境；将其作为算法教材，不能标记为现成 Green PHY 解码器。`open-plc-utils` 是管理／查询工具和相关协议实现，不是芯片内部 PHY／AFE 源码。

## 硬件资料

- [HackRF One 官方规格与最大输入](https://hackrf.readthedocs.io/en/stable/hackrf_one.html)
- [HackRF 连接器说明](https://hackrf.readthedocs.io/en/stable/hackrf_connectors.html)
- [PREMO MICU 商品页](https://grupopremo.com/products/micu-300a-s-lf)
- [PREMO CCS 监听宣传](https://grupopremo.com/blogs/news/premo-release-cutting-edge-inductive-couplers-for-electric-vehicle-sniffing-ccs-listener-applications-revolutionizing-high-voltage-system-monitoring-new-micu-300a-s-lf-series)
- [VLM-33W-2W-S+ 数据表](https://www.minicircuits.com/pdfs/VLM-33W-2W-S%2B.pdf)
- [VAT-30A+ 数据表](https://www.minicircuits.com/pdfs/VAT-30A%2B.pdf)
- [VAT-10A+ 数据表](https://www.minicircuits.com/pdfs/VAT-10A%2B.pdf)

PREMO 两处资料的频带说明不一致，保留为待核实项。其插入损耗不能直接当作已知线路条件下的固定输出功率。
