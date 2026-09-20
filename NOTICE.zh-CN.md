# 归属与范围

[返回项目首页](README.zh-CN.md)

JEV MLX 是独立维护的 MIT 开源项目。项目名称及带类型、感知状态的决策接口受 [TypeSafe AI 的 Jev](https://docs.typesafe.ai/) 启发。没有官方关联或背书，不包含 Jev 检查点，也不声称复现未公开的 RLCD。

运行时能力由 [MLX](https://github.com/ml-explore/mlx) 和 [MLX-LM](https://github.com/ml-explore/mlx-lm) 提供，版权归 Apple Inc.，使用 MIT 许可证。JEV MLX 调用其公开模型加载器、量化输出头、缓存工厂、LRUPromptCache 和生成接口。这些依赖保留各自许可证，源码未被复制进本仓库。

项目研究了 [jevmlx](https://github.com/bnsd55/jevmlx)、[kev](https://github.com/jaredpalmer/kev) 和 [JEV Ultrafast](https://github.com/browser-use/jev-ultrafast) 等相关公开实现。本仓库不包含这些项目的源文件或权重。

所有应用内容和评测场景均为本项目编写的虚构内容，没有导入 FounderOS 的生产数据、对话、音频、截图或日志。本地模型权重独立存放，保留上游及转换版本的许可证；Python 包不分发这些权重。
