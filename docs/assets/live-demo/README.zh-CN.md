# 同一句话，不同上下文。

[返回项目首页](../../../README.zh-CN.md)

这是 MLXJ 虚构桌面 Morrow Studio 的一次连续真实模型录制：八条预先确定的英文请求、四次明确标注的手动准备操作，以及模型选中后实际发生的 DOM 点击。它用于展示集成方式，不是独立的质量或性能 benchmark。

![真实本地模型录制，保持原速](preview.gif)

[完整 MP4](full-run.mp4) · [原始 WebM](original.webm) · [未修改的采集记录](transcript.json) · [媒体哈希](provenance.json)

## 实际发生了什么

本次唯一一次尝试中，八条请求的模型选择与执行检查均通过，没有浏览器 JavaScript 错误。录制脚本在请求完成后报告了一次视频收尾错误；完整的原始视频已恢复，详情见下文。没有为改善答案或耗时而重跑任何请求。

| 场景 | 请求 | 模型原始选择 | 实际结果 | 决策耗时 |
| --- | --- | --- | --- | ---: |
| 空桌面 | Close it | `__no_match__` | 不执行动作 | 4,272.4 ms |
| 笔记已打开 | Close it | `close.notes` | 关闭笔记 | 1,811.7 ms |
| Science 筛选、Z–A 排序 | First one | `play.orbit` | 打开 Orbit Field Notes | 2,061.8 ms |
| 播放器就绪 | Pause it | `player.pause` | 暂停播放器 | 2,617.9 ms |
| 播放器已暂停 | Did you just close it? | `__no_match__` | 播放器保持不变 | 1,176.1 ms |
| 播放器打开 | Close it | `close.player` | 返回课程库 | 277.6 ms |
| 课程库打开 | Close it | `close.library` | 返回桌面 | 302.2 ms |
| 再次回到空桌面 | Close it | `__no_match__` | 不执行动作 | 1,494.5 ms |

表中是视频展示的每次 `result.timing.decision_ms`，不是延迟分布统计。录制前已加载权重；首个请求的 KV 是冷的，后续多数场景复用系统前缀，关闭播放器和课程库的请求复用了完整状态前缀。页面变化和屏幕录制使这次负载不同于 benchmark。打字、手动准备和方便阅读的停顿全部保留在视频里，但不计入后端决策计时。视频没有展示或测量模型启动过程。

三次拒绝场景的录制检查允许 `no_match` 或 `abstain`，此次模型均返回 `no_match`。这比独立冻结质量集的判定更宽松。执行保护拦住错误，不能算模型答对。完整方法见[测试说明](../../testing.zh-CN.md)，更广泛的表现与失败见[扩展结果](../../extended-results.zh-CN.md)。

## 环境与来源

- 录制时间为 2026 年 9 月 20 日 13:37 UTC；Apple M2 Max、64 GiB 内存、macOS Darwin 25.6.0、arm64、Python 3.13.2。
- 本地检查点为 `Qwen3.5-9B-OptiQ-4bit`，实际使用混合 4/8-bit 量化，group size 为 64。完整配置、tokenizer 与量化哈希保留在采集记录里。
- MLX 0.31.2、MLX-LM 0.31.3、Transformers 5.9.0、Tokenizers 0.22.2；Playwright 1.63.0 及其隔离的 Chromium 上下文。未使用已有浏览器配置。
- 采集源码提交为 `11eafe7393da1cf9054d4d71146bd041cb1c2d60`；开始录制时工作区干净。运行代码、UI 与录制器文件在采集期间没有变化，前后哈希均保留在记录中。
- 原始 WebM 和 MP4 均为 1280 × 800、62.04 秒。GIF 为 1120 × 700、10 fps、128 色、62.00 秒（帧采样），约 9.9 MB；使用 FFmpeg 7.1.3。两个衍生文件均保留完整时间线和 1× 原速，没有剪片、裁画面、生成补帧或替换结果。MP4 约 1.9 MB。

桌面、课程名、请求与播放器均为虚构、可公开的示例。播放器只模拟播放状态，不下载真实视频。字幕描述场景，不会进入模型输入。集成只选择已有的白名单按钮，不负责任意网站导航或 JavaScript 生成。两种语言文档都保留英文原始实验数据，不翻译或改写证据。

## 视频恢复：保留原始错误

最初的录制器先关闭浏览器，再调用 Playwright 的 `video.save_as`，因此另存失败；但上下文关闭时，完整的原始 WebM 已经写入磁盘。原始记录仍保留该异常与 `video_saved: false`，没有被修改为“采集完全成功”。

我们将唯一的原始文件按字节复制为 `original.webm`。[恢复记录](video-recovery.json) 包含视频 SHA-256、未修改采集记录的 SHA-256、恢复方式及探测到的时长；视频保留了末尾画面与全部八次结果。转码会验证这两个哈希。没有第二次模型尝试，没有编辑输出，也没有删掉推理等待。

录制器现已改为关闭上下文后保存视频，最后才关闭浏览器；修复后的顺序已用独立空白浏览器实际验证，不调用模型。本次公开材料继续保留旧错误。

## 复现

先按[本地安装与录制说明](../../http-and-demo.zh-CN.md#interactive-showcase)操作。每次尝试使用新目录，失败结果也要保留。普通媒体构建会直接核对成功采集的视频哈希。要使用附带的恢复记录，重新生成本次视频的衍生文件：

```sh
python scripts/build_showcase_media.py \
  --capture-dir docs/assets/live-demo \
  --recovery-manifest docs/assets/live-demo/video-recovery.json \
  --output output/playwright-showcase/rebuilt-media \
  --width 1120 --fps 10
```

这条命令只转换已有视频。新的交互决策需要本地 MLX 服务；GIF 和 MP4 可以作为静态文件在 GitHub 上查看。
