from __future__ import annotations

import argparse
from pathlib import Path

import pypdfium2 as pdfium


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path, nargs="?",
                        help="可指定当前任务临时目录；默认写入临时存储/pdf_to_docx/<PDF名>/pages")
    parser.add_argument("--dpi", type=int, default=144)
    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = Path(__file__).resolve().parents[1] / "临时存储" / "pdf_to_docx" / args.pdf.stem / "pages"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(str(args.pdf))
    scale = args.dpi / 72
    for index, page in enumerate(document, 1):
        bitmap = page.render(scale=scale)
        bitmap.to_pil().save(args.output_dir / f"第{index}.png")
    print(f"{args.pdf.name}: {len(document)} pages")


if __name__ == "__main__":
    main()
