# 准备与发布版本

[返回项目首页](../README.md)

JEV MLX 的发行包名为 `jev-mlx`，导入名为 `jev_mlx`，CLI 命令为 `jev-mlx`。无需选定外部账户，即可在本地准备 0.1 版产物。构建发行包不等于发布。本地项目目录不会预留包名；当前安装示例使用源码检出目录或本地 wheel，而非 PyPI。

最新证据包括：已完成的三模型／四方法 [36 题暖缓存对比](extended-results.zh-CN.md)、单独进行的 [Gemma 原始测试集与进程冷启动测试](gemma4-results.zh-CN.md)，以及 [161 项通过的核心测试](../benchmarks/results/extended-release-checks/core-tests.json)。Gemma 额外的扩展缓存阶段完成了 108 次决策，72 次缓存／全新计算对照全部通过。该次重新构建的 wheel 已在安装 MLX 依赖的全新独立环境中验证：全部 14 个运行时文件都与源码和归档字节一致，公开示例通过真实 Gemma CLI 调用选中了 `player.pause`。参见 [wheel 验证记录](../benchmarks/results/extended-release-checks/distribution.json)。源码归档内容检查和发行包哈希随本地产物保存在 `dist/extended-v1/verification.json` 与 `SHA256SUMS` 中；为避免记录自身哈希，构建后的这份记录位于源码归档外。历史 wheel 检查仍作为独立记录保留。基准完成和审计成功并不意味着模型选择正确：扩展测试中直接评分的枚举动作误选分别为 Gemma 1/30、Qwen 1/30、GLM 8/30。布尔分类指标应单独统计，并在发行说明中保留这些失败。

## 核实发行内容

1. 一并审查工作区、`pyproject.toml` 与 `__init__.py` 中的版本号、许可证、归属声明、README、更新日志、模型支持与结果。
2. 核实测试数据与演示产物为虚构且可公开的来源。排除用户名／私有路径、凭据、模型权重、环境、本地缓存和无关应用数据。
3. 保留上游许可证／归属说明。项目采用 MIT 不会改变依赖或权重的许可证。
4. 对每个声明已验证的检查点，运行核心测试／lint 以及适当的显式启用模型／一致性检查。标注失败与未运行的检查。
5. 复现公开基准中的各评测组，记录测试数据／源码／模型身份、命令、硬件、每次尝试与失败。声明必须与证据一致。原始与扩展清单应分开，审计时传入正确的 `--fixtures-dir`，并将扩展测试的主要评测组描述为仅同页面条件。保留另行完成的 Gemma 缓存阶段及其一致性证据；不要暗示 Qwen／GLM 在扩展测试集上运行过该阶段。

```sh
python -m pytest -m 'not model'
python -m ruff check src tests benchmarks scripts
JEV_TEST_MODEL="$JEV_MLX_MODEL" python -m pytest tests/test_model.py
python scripts/check_parity.py --model "$JEV_MLX_MODEL" \
  --output results/release-parity.json
```

一致性工具记录各自的容差和决策一致性检查。应报告实际使用的检查与容差，不要将所有缓存测试视为等价。参见[评测说明](evaluation.zh-CN.md)。

## 构建与检查发行包

从已经审查、工作区干净且安装了 `'.[dev]'` 的检出目录运行：

```sh
python -m build
python -m zipfile -l dist/jev_mlx-0.1.0-py3-none-any.whl
tar -tzf dist/jev_mlx-0.1.0.tar.gz
shasum -a 256 dist/*
```

wheel 必须包含软件包、浏览器资源、类型标记、元数据和许可证材料。源码归档应包含公开文档、示例／测试，以及复现所需的基准工具。请检查归档内容；仅构建成功不能证明内容正确。

在源码检出目录之外的新环境中，使用 wheel 的绝对路径测试：

```sh
python3 -m venv /tmp/jev-wheel-check
/tmp/jev-wheel-check/bin/python -m pip install --no-deps \
  /absolute/path/to/dist/jev_mlx-0.1.0-py3-none-any.whl
/tmp/jev-wheel-check/bin/jev-mlx --help
/tmp/jev-wheel-check/bin/python -c \
  'from jev_mlx import __version__; print(__version__)'
```

如果该环境目录已存在，请另选新的目录名。在 Apple Silicon 上，在独立环境中安装 wheel 的 `[mlx]` 可选依赖，并针对明确选定的本地检查点运行真实决策。确认随包分发的演示资源能加载，模型选中的 DOM 动作能产生回执。Linux 核心 CI 无法验证这些 GPU／浏览器行为。

## 发布需要明确目标

公开推送或上传前，应确认目标 GitHub 所有者、仓库名称、可见性，以及获得授权的账户／访问权限。上传软件包前，应确认注册表、包名可用性，以及已授权凭据或配置好的受信任发布者。不要根据本地 Git 身份或当前登录账户推断发布目标。

提供目标与发布授权后，审查精确的提交／产物，配置对应远程仓库，发布已审查的源码，并创建带版本号的发行版本，包含 wheel、源码归档、校验和、更新日志与可复现结果。只有软件包注册表目标获得授权后才上传。将结果 URL 与不可变的提交／标签记录在发行说明中。在上传注册表前，补充选定的公开项目 URL，并将 README 文档／图片链接解析到该仓库，使其也能在注册表正常显示。

在此之前，完整本地源码、发行包、校验和、文档与真实演示证据就是交付内容。不要编造仓库 URL、徽章、成功的 CI 运行、发布日期、上传结果或性能数字。[更新日志](../CHANGELOG.zh-CN.md)会区分已准备与已发布。
