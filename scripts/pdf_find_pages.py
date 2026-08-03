from __future__ import annotations

import argparse
import re
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("patterns", nargs="+")
    args = parser.parse_args()

    compiled = [re.compile(pattern) for pattern in args.patterns]
    reader = PdfReader(str(args.pdf))
    print(f"pages={len(reader.pages)}")
    for number, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").replace(" ", "")
        matches = [pattern.pattern for pattern in compiled if pattern.search(text)]
        if matches:
            excerpt = text[:160].replace("\n", " / ")
            print(f"page {number}: {','.join(matches)} :: {excerpt}")


if __name__ == "__main__":
    main()
