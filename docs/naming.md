# Project name and earlier naming research

[Back to home](../README.md)

The project is **JEV MLX**, hosted at [CoderInPajamas/JEV-MLX](https://github.com/CoderInPajamas/JEV-MLX). The name makes the JEV inspiration and MLX runtime explicit. The distribution and CLI are `jev-mlx`; the Python import is `jev_mlx`.

The public display name changed from MLXJ on 2026-09-20. Existing recordings and benchmark records retain their original names and bytes. This rename does not change the package, CLI, Python API, or measured model behavior.

This is an independent project inspired by Jev, not an official TypeSafe AI release or the existing [bnsd55/jevmlx](https://github.com/bnsd55/jevmlx) project. It does not use Jev weights or reproduce its unpublished training method.

## Earlier research

Research date: 2026-09-19. The table below preserves the earlier public-search snapshot, not the current naming decision, a reservation, or a guarantee that a registry will accept a name.

| Candidate | Findings at the time | Assessment |
| --- | --- | --- |
| JEV MLX / jevmlx | [bnsd55/jevmlx](https://github.com/bnsd55/jevmlx) already exists in the same field | Similar names exist; identify this project by its owner and repository URL |
| JF | [jf on PyPI](https://pypi.org/project/jf/) is already a JSONL query tool | Too short and loses the MLX identity |
| JF MLX | GitHub repository-name searches for `jf-mlx` / `jfmlx` returned no matches | The specific remembered project was not identified; this does not prove uniqueness |
| MLXJ | GitHub `mlxj in:name` returned partial matches, with no exact `mlxj` repository basename found; the [MLXJ account](https://github.com/MLXJ) already exists | Earlier display name; replaced by JEV MLX to make the inspiration explicit |

At the time, the [PyPI mlxj JSON API](https://pypi.org/pypi/mlxj/json) returned 404; the corresponding `jf-mlx` and `jev-mlx` APIs also returned 404. This only means no public project record was found, not that registration is guaranteed. No account, repository, or package was created or published.

GitHub repository-name queries can be repeated through the [official repository search API](https://api.github.com/search/repositories?q=mlxj+in%3Aname). Search results can change.

## README references

The page structure was informed by these first-party READMEs, without copying their graphics, branding, or prose:

- [LobeHub](https://github.com/lobehub/lobehub#readme): centered visual title, language choice, community and support links.
- [RAGFlow](https://github.com/infiniflow/ragflow#readme): separate language READMEs, documentation navigation, and clear sections.
- [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev#readme): identity, language entry points, and sponsorship information.

Language is chosen on the homepage: the default English homepage is `README.md`, and the Chinese homepage is `README.zh-CN.md`. Each leads to a complete set of documents in that language, with no language switch on individual documents. Relative links work on GitHub without JavaScript. New visual assets are original project SVGs.

Public social and sponsorship links use owner-provided destinations. The Xiaohongshu card for 里奥YetAnotherLeo (ID `6236648830`) is included unchanged. The owner updated X to [@YetAnotherLeo](https://x.com/YetAnotherLeo) on 2026-09-20; [social provenance](assets/social/README.md) retains the source history. A sponsorship destination remains unconfigured; no payment link is invented.
