# Preparing and publishing a release

JEV MLX is distributed as `jev-mlx`, imported as `jev_mlx`, and invoked with
the `jev-mlx` CLI. Version 0.1 artifacts can be prepared
locally without choosing an external account. Building a distribution does not
publish it. The local project directory
does not reserve a package name, and installation examples currently use the
source checkout or local wheel rather than PyPI.

## Verify release contents

1. Review the working tree, version in `pyproject.toml` and `__init__.py`, license,
   notice, README, changelog, model support, and results together.
2. Verify public, fictional provenance for fixtures and demonstration artifacts.
   Exclude usernames/private paths, credentials, model weights, environments,
   local caches, and unrelated application data.
3. Preserve upstream licenses/attribution. Project MIT licensing does not
   relicense dependencies or weights.
4. Run core tests/lint and appropriate opt-in model/parity checks for each
   checkpoint advertised as verified. Label failures and unrun checks.
5. Reproduce published benchmark cohorts with fixture/source/model identities,
   commands, hardware, every attempt, and failures. Match claims to evidence.

```sh
python -m pytest -m 'not model'
python -m ruff check src tests benchmarks scripts
JEV_TEST_MODEL="$JEV_MLX_MODEL" python -m pytest tests/test_model.py
python scripts/check_parity.py --model "$JEV_MLX_MODEL" \
  --output results/release-parity.json
```

Parity tools record their own tolerances and decision-agreement checks. Report
the actual check and tolerance, rather than treating all cache tests as
equivalent. See [evaluation](evaluation.md).

## Build and inspect distributions

From a clean, reviewed checkout with `'.[dev]'` installed:

```sh
python -m build
python -m zipfile -l dist/jev_mlx-0.1.0-py3-none-any.whl
tar -tzf dist/jev_mlx-0.1.0.tar.gz
shasum -a 256 dist/*
```

The wheel must include the package, browser assets, typing marker, metadata, and
license material. The source archive should include the public documentation,
examples/tests, and benchmark tools needed for reproduction. Inspect archives;
a successful build alone does not verify their contents.

Test the absolute wheel path in a fresh environment outside the source checkout:

```sh
python3 -m venv /tmp/jev-wheel-check
/tmp/jev-wheel-check/bin/python -m pip install --no-deps \
  /absolute/path/to/dist/jev_mlx-0.1.0-py3-none-any.whl
/tmp/jev-wheel-check/bin/jev-mlx --help
/tmp/jev-wheel-check/bin/python -c \
  'from jev_mlx import __version__; print(__version__)'
```

Choose a fresh directory name if the environment already exists. On Apple
Silicon, install the wheel's `[mlx]` extra in a separate environment and run a
real decision against an explicitly chosen local checkpoint. Confirm packaged
demo assets load and model-selected DOM actions produce receipts. Linux core
CI cannot validate these GPU/browser behaviors.

## Publication requires an explicit destination

Before public push or upload, obtain the intended GitHub owner, repository name,
visibility, and authorized account/access. Before package upload, obtain the
registry, package-name availability, and authorized credentials or configured
trusted publisher. Do not infer destinations from local Git identity or the
account currently signed in.

Once destinations and publication authorization are supplied, review the exact
commit/artifacts, configure that remote, publish reviewed source, and create a
versioned release with wheel, source archive, checksums, changelog, and reproducible
results. Upload to a package registry only when that destination is authorized.
Record resulting URLs and immutable commit/tag in release notes.
Before registry upload, add the chosen public project URLs and resolve README
documentation/image links against that repository so they also render on the registry.

Until then, the complete local source, distributions, checksums, documentation,
and authentic demo evidence are the handoff. Do not invent repository URLs,
badges, successful CI runs, publication dates, upload results, or performance
numbers. The [changelog](../CHANGELOG.md) distinguishes prepared from published.
