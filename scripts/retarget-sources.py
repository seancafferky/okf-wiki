#!/usr/bin/env python3
"""
retarget-sources.py — point `source:` frontmatter at the extracted text.

After normalize-raw.py converts a binary original to "<original name>.txt" and
deletes the original, every source-summary page whose `source:` field named that
original is pointing at a file that no longer exists. Because the extractor
appends rather than replaces the extension, the repair is exact: append ".txt"
and check the result is on disk.

Usage:
    retarget-sources.py BUNDLE            # dry run
    retarget-sources.py BUNDLE --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOURCE_LINE = re.compile(r"^(source:\s*)(['\"]?)(.+?)\2\s*$", re.M)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="bundle root, e.g. bundles/main")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    bundle = Path(args.bundle).resolve()
    pages = sorted(bundle.rglob("*.md"))
    changed = missing = ok = 0

    for page in pages:
        text = page.read_text(encoding="utf-8")
        m = SOURCE_LINE.search(text)
        if not m:
            continue
        prefix, quote, ref = m.groups()
        target = bundle / ref
        if target.exists():
            ok += 1
            continue
        candidate = bundle / (ref.rstrip("/") + ".txt")
        if candidate.exists():
            changed += 1
            print(f"  {page.relative_to(bundle)}\n"
                  f"    {ref}\n"
                  f" -> {ref}.txt")
            if args.apply:
                new = text[:m.start()] + f"{prefix}{quote}{ref}.txt{quote}" + text[m.end():]
                page.write_text(new, encoding="utf-8")
        else:
            missing += 1
            print(f"  ! {page.relative_to(bundle)}: no target for {ref}")

    print(f"\n  resolved={ok} retargeted={changed} unresolved={missing}"
          f"{'' if args.apply else '  (dry run)'}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
