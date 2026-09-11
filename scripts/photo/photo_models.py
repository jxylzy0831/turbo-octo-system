#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
photo_models.py —— 确认中转站到底开了哪些模型（尤其是图像编辑的准确 id）

修图失败最常见的两个原因：
  1) 站点只开了文生图 /images/generations，没开图生图 /images/edits；
  2) 模型 id 猜错了。
先把这个打出来，比反复试错快得多。

用法：
  set OPENAI_BASE_URL=https://api.xxx.com/v1
  set OPENAI_API_KEY=sk-...
  python photo_models.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def main() -> None:
    load_env_file(HERE / ".env")

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("PHOTO_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("PHOTO_BASE_URL")
    if not api_key or not base_url:
        print("请先设置 OPENAI_BASE_URL 和 OPENAI_API_KEY（或写 scripts/photo/.env）", file=sys.stderr)
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("没装 openai SDK：python -m pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0, max_retries=1)
    print(f"base_url: {base_url}\n")

    try:
        page = client.models.list()
        ids = sorted({m.id for m in page.data})
    except Exception as exc:  # noqa: BLE001
        print(f"[失败] {type(exc).__name__}: {exc}", file=sys.stderr)
        print("\n401/403 = key 不对；404 = base_url 少了或多写了 /v1", file=sys.stderr)
        sys.exit(1)

    print(f"共 {len(ids)} 个模型：\n")
    for i in ids:
        print(f"  {i}")

    vision = [i for i in ids if any(k in i.lower() for k in ("gpt-4o", "gpt-4.1", "gpt-5", "claude", "gemini", "qwen-vl", "vision", "vl-"))]
    image = [i for i in ids if any(k in i.lower() for k in ("image", "seedream", "flux", "kontext", "banana", "dall"))]

    print("\n" + "=" * 58)
    print("看图模型候选（诊断用）:")
    for i in vision or ["  （没找到，可能要问站点）"]:
        print(f"  {i}")
    print("\n图像模型候选（修图用）:")
    for i in image or ["  （没找到 —— 该站点可能没开图像接口）"]:
        print(f"  {i}")
    print("=" * 58)

    flare = [i for i in ids if "flare" in i.lower()]
    sun = [i for i in ids if "sunburst" in i.lower()]
    if flare or sun:
        print("\n探测到 gpt-image-2.5 双档：")
        if flare:
            print(f"  快档 flare    : {flare[0]}")
        if sun:
            print(f"  慢档 sunburst : {sun[0]}")
        print("  修图建议：先用 flare 试方向，方向定了再用 sunburst 出成品。")

    if not image:
        print("\n注意：列表里没有图像模型。若你确定站点支持，可能是站点未开放 /models 列表权限，"
              "直接拿一个 id 试调用即可。")


if __name__ == "__main__":
    main()
