# 本地 HTTP API 与浏览器演示

[返回项目首页](../README.zh-CN.md)

使用独立的本地检查点启动真实 MLX 后端：

```sh
jev-mlx serve --model /path/to/local/mlx-model --port 8765
```

在浏览器打开 `http://127.0.0.1:8765`。服务器只绑定回环地址，不会为演示下载脚本、字体、图片或模型权重。这是一个单用户开发服务：所有标签页共享同一个虚构桌面和状态版本。它不是面向生产环境的多租户服务器。

## 演示实际做了什么

Morrow Studio 是原创的虚构桌面，包含课程库、野外笔记和模拟视频播放器。自然语言请求始终交给配置的本地模型。没有正则意图路由、预设的语言回复或最终答案缓存。

模型对当前允许的动作 ID 评分。选中的 ID 会转换为受约束的浏览器操作，例如：

```json
{
  "type": "click",
  "action_id": "player.pause",
  "selector": "[data-action=\"player.pause\"]",
  "ticket": "opaque-single-use-id",
  "state_version": 4
}
```

浏览器定位这个已有的 DOM 按钮，并调用其真实点击处理函数。同一个处理函数也接受手动点击。模型点击会将发出的票据交给执行器；执行器检查原始选择、当前状态版本与单次使用要求，再应用状态转换。回执记录已执行动作与前后版本；浏览器随后渲染返回的状态。浏览器还会派发 `jev-mlx:receipt` 事件，包含回执和观察到的视图，供集成测试使用。

这是在边界明确的本地应用上进行的真实浏览器交互。它不是任意网站导航、JavaScript 代码生成、视觉计算机操作模型或开放式参数生成。播放器模拟播放状态与进度，不会下载或播放真实课程视频。

检查面板将模型选择与实际执行分开显示，分别报告实测模型耗时和浏览器往返耗时，并展示候选分数、原始 logit 分差、缓存元数据与完整响应。受限 softmax 分数不是经过校准的正确概率。

<a name="interactive-showcase"></a>

## 实时交互展示与 README 录像

本地服务启动后，打开[实时交互展示](http://127.0.0.1:8765/?showcase=1)。这个紧凑布局与普通演示使用相同的真实模型、允许动作、DOM 控件和执行检查，针对 1280 × 800 浏览器视口设计。输入、最近一次模型选择和执行回执被放大；检查面板仍可查看完整分数、耗时、状态和缓存信息。场景说明描述准备步骤，独立的交互标签则区分手动准备、模型推理和实际执行的模型点击。

你可以在这个**本地实时演示**中输入新请求。README 内嵌的 GIF 和可下载视频都是**录像**：观看它们不会运行模型，也不能提交新输入。上传这些静态资源不等于托管 Python 推理服务。

要复现录像，请使用独立项目环境、已验证的本地检查点，以及可选浏览器依赖：

```sh
python -m pip install -e '.[mlx,browser]'
export PLAYWRIGHT_BROWSERS_PATH=.cache/playwright
python -m playwright install chromium --only-shell
```

媒体转换还需要单独安装 **ffmpeg 和 ffprobe**，并确保它们在 `PATH` 中；在 macOS 上，可以使用 `brew install ffmpeg`。启动真实后端并保持运行：

```sh
export JEV_MLX_MODEL=/path/to/local/mlx-model
jev-mlx serve --model "$JEV_MLX_MODEL" --port 8765
```

在使用同一项目环境的第二个终端中，单次录制预先定义的八条请求，然后生成展示媒体：

```sh
export PLAYWRIGHT_BROWSERS_PATH=.cache/playwright
python examples/record_showcase.py --output output/playwright-showcase/my-run
python scripts/build_showcase_media.py \
  --capture-dir output/playwright-showcase/my-run \
  --output output/playwright-showcase/my-run-media
```

每次尝试都使用新的空输出目录。录制脚本使用独立浏览器上下文，将准备点击标记为手动操作，不会为了得到更好的答案而重试模型推理。录制期间请勿操作其他演示标签页，因为它们共享同一个应用状态。捕获产物保留模型错误、拒绝、完整 HTTP 响应、执行回执，以及原始 `original.webm`。失败的运行仍是证据，不会被算作成功演示。

媒体构建器保留原始视频与记录，并生成 `full-run.mp4`、`preview.gif`，以及包含产物哈希的来源说明。两种衍生媒体均以 **1× 原速**保留完整时间线，不剪掉片段，也不裁剪画面。GIF 为便于分发而降低帧率、尺寸和调色板大小，不替换模型输出，也不生成缺失画面。这是用于说明交互过程的浏览器录像，**不是性能基准或独立的准确率样本**。实际录制结果与限制见[录像和媒体来源说明](assets/live-demo/README.zh-CN.md)。

## 交互检查

以下是复现步骤，不代表每个模型都会通过每条请求。实测准确率请参阅已发布的评测报告。

1. 在桌面输入 **Open the course library**。打开功能入口应显示课程库，而不播放课程。
2. 输入 **Only science courses**，然后点击 **Z–A**。输入 **First one**。当前第一个可见课程应为 **Orbit Field Notes**，而非未筛选列表中的第一门课程。
3. 在 1.6 秒的加载状态中，只有 **close.player** 可执行。播放器报告就绪后，暂停、继续和回退才可用。
4. 依次输入 **Pause it**、**Resume it**、**Go back ten seconds** 和 **Close it**。每次决策后检查回执和播放器的最终状态。
5. 在课程库、笔记窗口、播放器和空桌面分别输入 **Close it**。允许的关闭动作随当前聚焦对象变化；空桌面上没有可用的关闭动作。
6. 尝试 **Did you just close it?**、**Don't close it**、含糊的请求和不存在的课程。即使执行被拦截，模型错误仍应按错误检查。
7. 提交请求，然后在模型运行期间立即点击其他页面控件。旧结果不得执行。推理期间手动控件始终可用。取消选中 **Execute click** 后，也可以暂存选中的结果，再通过手动状态变化使其在执行前失效。

自动加载完成会改变状态版本。因此，加载期间开始的请求可能在推理完成前过期，这是预期行为。

## 无状态 API

`POST /v1/decide` 接受与 `DecisionRequest.from_dict` 相同的请求字段：

```sh
curl --fail-with-body http://127.0.0.1:8765/v1/decide \
  -H 'Content-Type: application/json' \
  --data-binary @examples/decision.json
```

它返回 `DecisionResult` 对象，包含 `candidate_id`、`status`、`raw_selected_id`、`raw_scores`、`scores`、`margin`、`state_version`、`model`、`timing`、`cache`、`request_id` 和 `selected_value`。枚举请求可以使用空候选数组，以便模型返回 no-match 或 abstain。布尔请求必须分别包含一个 true 值候选和一个 false 值候选。

通用端点只计算决策。请求中的状态版本属于调用方；调用方必须根据自己的当前状态验证执行。应用集成应使用 `DecisionSession` 或具有同等原子性的执行器。这个无状态端点的结果不是演示的执行票据。

## 有状态演示 API

| 方法与路由 | 请求 | 行为 |
| --- | --- | --- |
| `GET /health` | — | 就绪状态与当前演示状态版本 |
| `GET /api/demo/state` | — | 状态、候选、可见课程、模型身份 |
| `POST /api/demo/decide` | `{"utterance":"Close it"}` | 捕获当前状态快照、推理，返回结果与可选浏览器操作；不执行 |
| `POST /api/demo/execute` | `{"ticket":"issued-id","action_id":"close.notes"}` | 验证并消费选中的操作，然后返回实际执行回执 |
| `POST /api/demo/action` | `{"action_id":"open.notes","state_version":0}` | 按精确版本应用白名单内的手动操作 |
| `POST /api/demo/player-ready` | `{"state_version":2}` | 版本仍为当前版本时，应用模拟加载完成事件 |

`409` 表示执行被拒绝，响应包含当前状态。`429` 表示已有另一个推理在运行。`400` 表示请求格式错误。请求体上限为 64 KiB，演示中的用户话语上限为 4,096 个字符。未知字段会被拒绝。Host、Origin 和 Fetch Metadata 检查会拒绝跨源浏览器访问；服务不返回宽松的 CORS 响应头。该服务应始终使用回环地址。

## CLI

命令名是 `jev-mlx`，在可执行文件名中同时保留 JEV 与 MLX。

```sh
jev-mlx decide --model /path/to/local/mlx-model --request examples/decision.json
cat examples/decision.json | jev-mlx decide --model /path/to/local/mlx-model
JEV_MLX_MODEL=/path/to/local/mlx-model jev-mlx serve
```

`--no-cache` 会禁用该 CLI 请求的前缀复用。一次性 CLI 命令会启动新进程加载模型；要测量模型已加载后的表现，应使用持续运行的 Python 引擎或 HTTP 服务。

## 自动化覆盖

```sh
python -m pytest tests/test_demo.py tests/test_server.py -q
```

这些控制器与 HTTP 测试有意注入模拟的数值分数，用于测试状态转换、单次授权、并发、输入验证以及动作映射。它们**不测量模型语义质量**。真实模型评测与浏览器证据单独报告。

## 记录一次真实浏览器运行

真实模型服务器启动后，使用独立的 Playwright Chromium 实例操作 UI，并保存全部结果：

```sh
python -m pip install -e '.[browser]'
export PLAYWRIGHT_BROWSERS_PATH=.cache/playwright
python -m playwright install chromium --only-shell
python examples/browser_smoke.py --url http://127.0.0.1:8765 \
  --output output/playwright
```

脚本使用全新的浏览器上下文，不改变现有浏览器配置和标签页。它保存 `browser-transcript.json`、截图和 WebM 视频。JSON 分开记录模型原始结果正确性、实际执行正确性、观察到的 DOM 状态与准备步骤中的点击。失败案例会保留，运行失败时以非零退出码结束。模型驱动的动作通过演示的真实浏览器控件执行；准备操作明确记录为手动点击。

竞争条件检查会启动推理，再通过手动 DOM 点击切换页面。它报告页面状态是否在决策请求完成前变化；并未单独测量该变化是否与 GPU 计算重叠。如果模型完成太快，无法证明重叠，就会报告该限制，同时继续验证页面更新后暂存决策会被拒绝。加载状态检查记录变化中的动作集合，并将过期结果与其原始语义选择分开。执行器拒绝或浏览器防护都不能把模型的错误答案算作正确。

要使用 `--headed`，请先运行 `python -m playwright install chromium` 安装完整浏览器。使用 `--no-video` 可以跳过录像，使用 `--executable-path /path/to/chromium` 可以在隔离上下文中使用现有 Chromium 可执行文件。浏览器依赖是可选的；SDK 与 HTTP 服务不需要它。公开产物前，请检查记录的模型元数据与本地 URL。
