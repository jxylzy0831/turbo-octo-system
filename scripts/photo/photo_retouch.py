#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
photo_retouch.py —— 用官方 openai SDK 调 gpt-image-2.5 做修图（保持内容，只改光色质感）

为什么用官方 SDK 而不是自己拼 HTTP：
  中转站就是 OpenAI 兼容接口。SDK 只改一个 base_url 就能用，重试、超时、超限、
  错误码解析全都现成。自己拼 multipart 只会在这三件事上反复踩坑。

支持：
  - Flare（快档）/ Sunburst（慢档）切换
  - 多张参考图（官方参数是 image=[file1, file2]）
  - mask 局部修（可选）
  - 调用前等比缩图（Pillow），避免超出接口尺寸限制
  - 每次调用落一份 run-*.json 记录（不含 key）

用法示例见 scripts/photo/README-修图工具.md
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 两个档位，必须显式选一个；不要用模糊的 "gpt-image-2.5"
MODELS = {
    "flare": "gpt-image-2.5-flare",       # 快档：草稿、批量试方向
    "sunburst": "gpt-image-2.5-sunburst",  # 慢档：高质量，交付用
}

# 修图专用默认指令。核心是"不许改内容"，只允许动光色与质感。
DEFAULT_PROMPT = (
    "Retouch this photograph professionally while keeping the content identical. "
    "Preserve the subject's identity, facial features, bone structure, body shape, hair, "
    "clothing design and every object's position and count exactly as in the original. "
    "Keep the original lighting direction, light ratio and shadow direction unchanged; "
    "only refine the quality of light. "
    "Steps: correct exposure and white balance, set clean black and white points, "
    "lift and shape the subject's light with local dodging and burning while holding highlight "
    "detail with a soft roll-off, apply a restrained single-direction color grade, "
    "then finish texture: natural skin with pores and fine hair kept (no plastic smoothing), "
    "accurate fabric texture, mild capture sharpening only. "
    "No added or removed objects, no text, no watermark, no frame, no relighting from a new "
    "direction, no face reshaping, no slimming, no HDR halos, no heavy vignette, "
    "no oversaturation, same aspect ratio as the input."
)


def die(msg: str) -> "None":
    print(f"\n[错误] {msg}\n", file=sys.stderr)
    sys.exit(1)


def load_env_file(path: Path) -> None:
    """从 .env 里补环境变量（已存在的环境变量优先，不覆盖）。"""
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


def prepare_input(path: Path, max_side: int, work_dir: Path) -> Path:
    """等比缩到长边 max_side 以内，控制请求体积。原图不动。"""
    if max_side <= 0:
        return path
    try:
        from PIL import Image
    except ImportError:
        print("[提示] 没装 Pillow，跳过缩图。装一下：pip install Pillow")
        return path

    with Image.open(path) as im:
        w, h = im.size
        long_side = max(w, h)
        if long_side <= max_side:
            return path
        scale = max_side / long_side
        new_size = (round(w * scale), round(h * scale))
        out = work_dir / f"input-{new_size[0]}x{new_size[1]}.png"
        im.convert("RGB").resize(new_size, Image.LANCZOS).save(out, "PNG")
        print(f"[缩图] {w}x{h} -> {new_size[0]}x{new_size[1]}  ({out.name})")
        return out


def extract_bytes(item) -> bytes | None:
    """从 SDK 返回的 image 对象里取字节，兼容 b64_json / url / 直接 bytes。"""
    b64 = getattr(item, "b64_json", None)
    if b64:
        return base64.b64decode(b64)
    url = getattr(item, "url", None)
    if url:
        if url.startswith("data:"):
            return base64.b64decode(url.split(",", 1)[1])
        import urllib.request

        print("[下载] 接口返回的是 URL，正在取回……")
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.read()
    data = getattr(item, "data", None)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return None


def main() -> None:
    here = Path(__file__).resolve().parent

    p = argparse.ArgumentParser(
        description="用 gpt-image-2.5 修图（保持内容，只调光色质感）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("images", nargs="+", help="一张或多张原图路径")
    p.add_argument("-o", "--outdir", default=None, help="输出目录（默认 <仓库根>/photo_out/<第一张图名>）")
    p.add_argument("-v", "--variant", choices=sorted(MODELS), default="sunburst",
                   help="flare=快档(草稿/试方向)，sunburst=慢档(交付)。默认 sunburst")
    p.add_argument("-m", "--model", default=None, help="直接指定模型 id，覆盖 --variant")
    p.add_argument("-p", "--prompt", default=None, help="修图指令；不给就用内置的保守修图指令")
    p.add_argument("--prompt-file", default=None, help="从文件读修图指令（UTF-8）")
    p.add_argument("--mask", default=None, help="PNG 蒙版：透明区域=要重绘的部分")
    p.add_argument("--size", default="auto", help="auto / 1024x1024 / 1536x1024 等")
    p.add_argument("--quality", default="high", help="low / medium / high")
    p.add_argument("--background", default="auto", help="auto / transparent / opaque")
    p.add_argument("--input-fidelity", default=None, help="high=更贴原图（部分档位支持）")
    p.add_argument("--max-side", type=int, default=1536, help="调用前缩图长边，0=不缩")
    p.add_argument("--timeout", type=float, default=600.0, help="单次请求超时秒数")
    p.add_argument("--retries", type=int, default=3, help="失败重试次数")
    p.add_argument("--n", type=int, default=1, help="出几张")
    args = p.parse_args()

    load_env_file(here / ".env")

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("PHOTO_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("PHOTO_BASE_URL")
    if not api_key:
        die("缺少 key。设 OPENAI_API_KEY（或写 scripts/photo/.env）")
    if not base_url:
        die("缺少 base_url。设 OPENAI_BASE_URL，例如 https://api.xxx.com/v1")

    try:
        from openai import OpenAI
    except ImportError:
        die("没装 openai SDK。先执行：python -m pip install openai")

    model = args.model or MODELS[args.variant]
    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not prompt:
        prompt = os.environ.get("PHOTO_PROMPT_EN", "").strip() or DEFAULT_PROMPT

    src_paths = [Path(x).resolve() for x in args.images]
    for sp in src_paths:
        if not sp.is_file():
            die(f"找不到原图：{sp}")

    work_dir = here / "_tmp"
    work_dir.mkdir(exist_ok=True)

    out_dir = Path(args.outdir).resolve() if args.outdir else (
        here.parent.parent / "photo_out" / src_paths[0].stem
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    print("=" * 62)
    print(f"  模型    : {model}  ({args.variant})")
    print(f"  base_url: {base_url}")
    print(f"  原图    : {', '.join(sp.name for sp in src_paths)}")
    print(f"  输出    : {out_dir}")
    print(f"  尺寸    : {args.size}   质量: {args.quality}")
    print("=" * 62)

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=args.timeout, max_retries=args.retries)

    sized_paths = [prepare_input(sp, args.max_side, work_dir) for sp in src_paths]

    handles = [open(sp, "rb") for sp in sized_paths]
    try:
        kwargs = {
            "model": model,
            "image": handles if len(handles) > 1 else handles[0],
            "prompt": prompt,
            "size": args.size,
            "quality": args.quality,
            "background": args.background,
            "n": args.n,
        }
        if args.input_fidelity:
            kwargs["input_fidelity"] = args.input_fidelity
        if args.mask:
            mask_path = Path(args.mask).resolve()
            if not mask_path.is_file():
                die(f"找不到蒙版：{mask_path}")
            mask_h = open(mask_path, "rb")
            kwargs["mask"] = mask_h
        else:
            mask_h = None

        print("\n[1/2] 提交修图请求（Sunburst 档可能要等 1-3 分钟）……")
        t0 = time.time()
        try:
            result = client.images.edit(**kwargs)
        except TypeError as exc:
            # 中转站/SDK 版本差异：某些参数不支持就摘掉重试
            if "input_fidelity" in kwargs:
                print(f"[降级] 该站点不支持 input_fidelity（{exc}），去掉重试。")
                kwargs.pop("input_fidelity")
                result = client.images.edit(**kwargs)
            else:
                raise
        finally:
            if mask_h:
                mask_h.close()
        elapsed = time.time() - t0
    except Exception as exc:  # noqa: BLE001
        print(f"\n[失败] {type(exc).__name__}: {exc}\n", file=sys.stderr)
        print("排查顺序：", file=sys.stderr)
        print("  1) 模型 id 是否真的叫这个：python Get-PhotoModels.py 打一遍列表", file=sys.stderr)
        print("  2) 站点是否开了 /images/edits（图生图），只开文生图的话修不了图", file=sys.stderr)
        print("  3) 是不是 429 限流 / 余额不足", file=sys.stderr)
        print("  4) 换 flare 档或把 --size 降到 1024x1024 再试", file=sys.stderr)
        sys.exit(1)
    finally:
        for h in handles:
            h.close()

    print(f"[2/2] 返回 {len(result.data)} 张图，用时 {elapsed:.1f}s")

    written = []
    for i, item in enumerate(result.data, 1):
        raw = extract_bytes(item)
        if not raw:
            print(f"[警告] 第 {i} 张取不到图像数据，跳过。")
            continue
        suffix = ".png" if raw[:4] == b"\x89PNG" else ".jpg"
        name = f"retouched-{stamp}" + (f"-{i}" if len(result.data) > 1 else "") + suffix
        dst = out_dir / name
        dst.write_bytes(raw)
        written.append(dst)
        print(f"  -> {dst}  ({len(raw) / 1024:.0f} KB)")

    if not written:
        die("接口返回里没有可用图像。")

    if getattr(result, "usage", None):
        print(f"[用量] {result.usage}")

    record = {
        "when": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "variant": args.variant,
        "base_url": base_url,
        "inputs": [str(sp) for sp in src_paths],
        "sized_inputs": [str(sp) for sp in sized_paths],
        "size": args.size,
        "quality": args.quality,
        "prompt": prompt,
        "outputs": [str(w) for w in written],
    }
    rec = out_dir / f"run-{stamp}.json"
    rec.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[记录] {rec}")

    print("\n提醒：模型一定会顺手改细节。把成品和原图并排放大到 100% 逐区核对"
          "（五官、手、文字、纹样、边缘），别只看缩略图。")


if __name__ == "__main__":
    main()
