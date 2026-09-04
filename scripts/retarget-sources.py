#!/usr/bin/env python3
"""
retarget-sources.py — point a bundle's references at the extracted text.

After normalize-raw.py converts a binary original to "<original name>.txt" and
deletes the original, every reference to that original is dangling: the `source:`
frontmatter field, and the `# Citations` entries naming the same file in prose.

Both what to rewrite and what to protect are read off the disk rather than
guessed from the page text. An original was purged exactly when "<X>.txt" exists
and "<X>" does not, so a reference to it must gain the ".txt". Every path still
present maps to itself, which is what stops a purged "Report.pdf" from eating the
"Report.pdf.bak" beside it — the longer real name matches first and is left
alone. Neither rule needs a list of formats or an assumption about which
characters a filename may contain, the two things a pattern-matching version gets
wrong, silently, on names like "Backtesting (2013).pdf" and on every .html.

Usage:
    retarget-sources.py BUNDLE            # dry run
    retarget-sources.py BUNDLE --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAW_DIR = "raw"

# raw/ is immutable by spec, and log.md is a write-once record whose entries
# describe what was true at ingest time — a path named there is narrative, not a
# live pointer. Neither is rewritten; everything else in the bundle is.
SKIP_DIRS = {RAW_DIR}
SKIP_FILES = {"log.md"}

SOURCE_LINE = re.compile(r"^source:\s*(.+?)\s*$", re.M)

# Stripping ".txt" reveals an original only if what remains ends in something
# extension-shaped: "Report.pdf.txt" yields its .pdf, while "lecture 3.txt" (a
# transcript, never a binary) and "Vol 1.25.txt" are correctly left alone. The
# same test tells a `source:` naming a file from one naming a directory or a
# prose summary of several.
EXTENSION = re.compile(r"^\.[A-Za-z][A-Za-z0-9]{1,4}$")


def raw_rewrites(bundle: Path) -> dict[str, str]:
    """Every raw/ path, mapped to what a reference to it should say."""
    rewrites: dict[str, str] = {}
    for path in (bundle / RAW_DIR).rglob("*"):
        extracted = str(path.relative_to(bundle))
        rewrites[extracted] = extracted
        original = path.with_suffix("")
        if path.suffix == ".txt" and EXTENSION.match(original.suffix) and not original.exists():
            rewrites[str(original.relative_to(bundle))] = extracted
    return rewrites


def build_pattern(rewrites: dict[str, str]) -> re.Pattern[str] | None:
    """Match every known raw path, preferring the longest at any position."""
    if not rewrites:
        return None
    forms = sorted(rewrites, key=len, reverse=True)
    return re.compile("|".join(re.escape(f) for f in forms))


def unresolved_sources(text: str, bundle: Path) -> list[str]:
    """`source:` entries naming a raw *file* that is not on disk. Reported, never rewritten."""
    m = SOURCE_LINE.search(text)
    if not m:
        return []
    value = m.group(1).strip("\"'")
    if (bundle / value).exists():
        return []
    # A value that is not itself a path may still be several joined with ";".
    # Only an entry shaped like a filename is checked — one naming a directory,
    # or summarising a group in prose, has no single file to resolve to.
    return [
        entry
        for entry in (e.strip(" \"'") for e in value.split(";"))
        if entry.startswith(f"{RAW_DIR}/")
        and EXTENSION.match(Path(entry).suffix)
        and not (bundle / entry).exists()
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="bundle root, e.g. bundles/main")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    bundle = Path(args.bundle).resolve()
    rewrites = raw_rewrites(bundle)
    pattern = build_pattern(rewrites)
    purged = sum(1 for ref, target in rewrites.items() if ref != target)

    retargeted = touched = unresolved = 0

    for page in sorted(bundle.rglob("*.md")):
        relative = page.relative_to(bundle)
        if relative.parts[0] in SKIP_DIRS or relative.name in SKIP_FILES:
            continue
        text = page.read_text(encoding="utf-8")
        found = [m.group(0) for m in pattern.finditer(text)] if pattern else []
        hits = [ref for ref in found if rewrites[ref] != ref]
        new_text = pattern.sub(lambda m: rewrites[m.group(0)], text) if hits else text

        if hits:
            retargeted += len(hits)
            touched += 1
            print(f"  {relative}")
            for ref in sorted(set(hits)):
                print(f"    {ref}\n -> {rewrites[ref]}")
            if args.apply:
                page.write_text(new_text, encoding="utf-8")

        for entry in unresolved_sources(new_text, bundle):
            unresolved += 1
            print(f"  ! {relative}: no target for {entry}")

    print(f"\n  purged={purged} retargeted={retargeted} pages={touched}"
          f" unresolved={unresolved}{'' if args.apply else '  (dry run)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
