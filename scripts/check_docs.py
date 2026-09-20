"""Check published documentation pairs, local links, and language-preserving routes.

Uses only the standard library and reads source files, not generated preview HTML.
Run from any directory with ``python /path/to/repo/scripts/check_docs.py``.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/locales.json"
LANGUAGES = {"en", "zh-CN"}
EXCLUDED_DIRS = {
    "artifacts", "build", "dist", "htmlcov", "models", "output", "runs", "venv",
}


class HTMLReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[int, str]] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value is None:
                continue
            if name in {"href", "src"}:
                self.links.append((self.getpos()[0], value))
            if name == "id" or (tag == "a" and name == "name"):
                self.anchors.add(value)


def without_code(text: str) -> str:
    """Mask fenced and inline code while preserving line numbers for diagnostics."""
    lines = text.splitlines(keepends=True)
    fence: tuple[str, int] | None = None
    for index, line in enumerate(lines):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1]:
                if not line[marker.end():].strip():
                    fence = None
            lines[index] = "\n" if line.endswith("\n") else ""
        elif marker:
            fence = (marker[1][0], len(marker[1]))
            lines[index] = "\n" if line.endswith("\n") else ""
    return re.sub(
        r"(`+)([^`]|(?!\1)`)*?\1",
        lambda match: "\n" * match[0].count("\n"),
        "".join(lines),
    )


def markdown_references(text: str) -> list[tuple[int, str]]:
    """Read inline destinations and reference definitions, including image links."""
    links: list[tuple[int, str]] = []
    for marker in re.finditer(r"\]\(\s*", text):
        start = marker.end()
        end = start
        depth = 0
        if start < len(text) and text[start] == "<":
            closing = text.find(">", start + 1)
            if closing == -1:
                continue
            destination = text[start + 1:closing]
        else:
            while end < len(text):
                char = text[end]
                if char == "\\" and end + 1 < len(text):
                    end += 2
                    continue
                if char.isspace() or (char == ")" and depth == 0):
                    break
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                end += 1
            destination = text[start:end]
        links.append((text.count("\n", 0, marker.start()) + 1, destination))
    definitions = re.compile(
        r"^ {0,3}\[(?!\^)[^\]\n]+\]:[ \t]*(<[^>\n]*>|\S+)", re.MULTILINE
    )
    for match in definitions.finditer(text):
        links.append((text.count("\n", 0, match.start()) + 1, match[1].strip("<>")))
    return [(line, re.sub(r"\\([\\()\[\]<> ])", r"\1", url)) for line, url in links]


def source_files(suffix: str) -> set[Path]:
    files = set(ROOT.glob(f"*{suffix}"))
    for directory in ("docs", "benchmarks/fixtures", "examples"):
        files.update((ROOT / directory).rglob(f"*{suffix}"))
    return {
        path for path in files
        if path.is_file() and not any(
            part.startswith(".") or part in EXCLUDED_DIRS or part.endswith(".egg-info")
            for part in path.relative_to(ROOT).parts[:-1]
        )
    }


def audit() -> tuple[Counter, list[str]]:
    counts: Counter = Counter()
    errors: list[str] = []
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return counts, [f"docs/locales.json: {error}"]
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        return counts, ["docs/locales.json: expected catalog schema_version 1"]
    if set(catalog.get("languages", [])) != LANGUAGES:
        errors.append("docs/locales.json: languages must be en and zh-CN")
    documents = catalog.get("documents")
    homepages = catalog.get("homepages")
    if not isinstance(documents, list) or not isinstance(homepages, dict):
        return counts, errors + ["docs/locales.json: documents/homepages have invalid types"]

    locales: dict[Path, str] = {}
    for index, pair in enumerate(documents):
        if not isinstance(pair, dict) or set(pair) != LANGUAGES:
            errors.append(f"docs/locales.json: pair {index + 1} must contain both languages")
            continue
        counts["pairs"] += 1
        for language, relative in pair.items():
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
                errors.append(f"docs/locales.json: invalid path in pair {index + 1}")
                continue
            path = (ROOT / relative).resolve()
            if not path.is_relative_to(ROOT):
                errors.append(f"docs/locales.json: path escapes repository: {relative}")
                continue
            if path in locales:
                errors.append(f"docs/locales.json: duplicate document: {relative}")
            locales[path] = language
            if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                errors.append(f"{relative}: missing or empty catalogued document")

    homes: set[Path] = set()
    for language in sorted(LANGUAGES):
        relative = homepages.get(language)
        if not isinstance(relative, str):
            errors.append(f"docs/locales.json: missing {language} homepage")
            continue
        home = (ROOT / relative).resolve()
        if locales.get(home) != language:
            errors.append(f"docs/locales.json: {language} homepage is not catalogued correctly")
        homes.add(home)

    markdown = source_files(".md")
    for path in sorted(markdown - locales.keys()):
        errors.append(f"{path.relative_to(ROOT)}: source Markdown is not in docs/locales.json")
    sources = markdown | source_files(".html") | set(locales)
    counts["documents"] = len(locales)
    for source in sorted(sources):
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT)
        text = source.read_text(encoding="utf-8")
        is_html = source.suffix == ".html"
        content = text if is_html else without_code(text)
        html = HTMLReferences()
        html.feed(content)
        references = html.links + ([] if is_html else markdown_references(content))
        counts["files_checked"] += 1
        if source in homes and "quick-start" not in html.anchors:
            errors.append(f"{relative}: homepage is missing explicit quick-start anchor")
        for line, url in references:
            counts["references"] += 1
            try:
                parsed = urlsplit(url)
            except ValueError:
                errors.append(f"{relative}:{line}: invalid URL: {url}")
                continue
            if parsed.scheme or parsed.netloc:
                continue
            counts["local_references"] += 1
            target_path = unquote(parsed.path)
            if not target_path:
                target = source
            elif target_path.startswith("/"):
                target = (ROOT / target_path.lstrip("/")).resolve()
            else:
                target = (source.parent / target_path).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"{relative}:{line}: local target does not exist: {url}")
                continue
            source_language = locales.get(source)
            target_language = locales.get(target)
            if source_language and target_language:
                counts["document_edges"] += 1
                home_switch = source in homes and target in homes
                if source_language != target_language and not home_switch:
                    errors.append(f"{relative}:{line}: cross-language document link: {url}")
            if source_language and target == ROOT / "docs/demo/index.html":
                langs = parse_qs(parsed.query, keep_blank_values=True).get("lang", [])
                if langs != [source_language]:
                    errors.append(
                        f"{relative}:{line}: replay must use lang={source_language}: {url}"
                    )
            if parsed.fragment == "quick-start" and target.is_file():
                target_html = HTMLReferences()
                target_html.feed(without_code(target.read_text(encoding="utf-8")))
                if "quick-start" not in target_html.anchors:
                    errors.append(f"{relative}:{line}: missing quick-start anchor: {url}")
    return counts, errors


def main() -> int:
    counts, errors = audit()
    print(json.dumps({"ok": not errors, **counts, "errors": errors}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
