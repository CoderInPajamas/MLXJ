# 浏览器决策录制回放

[返回项目首页](../../README.zh-CN.md)

直接用浏览器打开 `index.html` 即可，包括通过 `file://` 打开。这是离线的中英文**录制回放**，不是实时模型演示。观看时不需要 Python、模型、HTTP 服务、CDN 或网络连接。

页面展示公开[浏览器记录](../assets/browser-demo/browser-transcript.json)中的全部 16 个场景及独立的状态变化检查。原始英文话语、候选 ID、logits、分数、实测耗时、缓存信息和执行回执都予以保留。界面语言随主页入口确定：中文主页进入中文回放，英文主页进入英文回放。语言参数为 `?lang=en` 或 `?lang=zh-CN`；不带语言参数直接打开时默认英文。语言只影响界面，不翻译原始输入或结果；缺失字段仍保持缺失。

原始材料保留项目旧称，没有改写或修图。回放界面使用当前 MLXJ 展示名称。Python 和 CLI 标识仍为 `jev_mlx` 与 `jev-mlx`。

这一次浏览器冒烟运行独立于留出的模型 benchmark；参见[实测结果与限制](../results.zh-CN.md)。

## 截图与场景的准确对应

| 记录的场景 | 原始截图 |
| --- | --- |
| `open-feature-without-playing-content` | `02-library.png` |
| `first-follows-filtered-reversed-visible-order` | `03-course-player.png` |
| `pause-ready-player` | `03b-player-control.png` |
| 独立的 `state_change_check` | `04-stale-protection.png` |

`01-desktop.png` 显示**任何决策发生之前**的初始桌面，另行提供链接。其他场景都明确说明没有单独截图。不能用相邻场景的截图冒充当前场景证据。完整原始 WebM 录像可直接查看，没有编造逐场景时间戳。

并发检查没有保存原始话语、变化前状态或执行回执。页面如实展示缺失项，不重建这些数据。记录中的 `old_result_not_executed` 检查与原始模型选择分开展示。候选分数不是经过校准的正确概率。

## 重建离线数据包

```sh
python docs/demo/build_data.py
```

这个标准库脚本只读取公开记录和材料来源信息。它核验每个原始材料的 SHA-256，省略无必要的采集回环 URL，拒绝意外的本地用户路径或凭据标记，并写入 `data.js`。它不修改源证据。页面不使用 `fetch`，因此双击文件或静态托管均可运行。页面 CSP 禁止网络连接（`connect-src 'none'`）。
