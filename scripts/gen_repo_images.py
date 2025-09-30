#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera imagens JPEG baseline para testes em repo/"
    )
    p.add_argument("--count", type=int, default=3, help="Quantidade de imagens")
    p.add_argument("--width", type=int, default=1080, help="Largura")
    p.add_argument("--height", type=int, default=1076, help="Altura")
    p.add_argument(
        "--prefix",
        type=str,
        default="campanha_teste",
        help="Prefixo do nome do arquivo",
    )
    p.add_argument(
        "--filenames",
        type=str,
        default="",
        help="Lista de nomes (separados por vírgula) a serem usados (sem caminho)",
    )
    p.add_argument(
        "--progressive",
        action="store_true",
        help="Força JPEG progressivo (padrão é baseline)",
    )
    p.add_argument(
        "--text",
        type=str,
        default="I9 SMART TEST",
        help="Texto sobreposto nas imagens",
    )
    return p.parse_args()


def ensure_repo_dir() -> Path:
    repo = Path("repo")
    repo.mkdir(parents=True, exist_ok=True)
    return repo


def pick_font(size: int = 28) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        # Tenta fontes comuns do sistema (não falha se não existir)
        for path in (
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ):
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
    except Exception:
        pass
    return ImageFont.load_default()


def render_image(w: int, h: int, text: str, idx: int) -> Image.Image:
    # Fundo em gradiente simples
    img = Image.new("RGB", (w, h), (230, 230, 220))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        c = 200 + int(40 * (y / max(h - 1, 1)))
        draw.line([(0, y), (w, y)], fill=(c, 20 + (y % 50), 30))

    # Moldura
    draw.rectangle([(8, 8), (w - 9, h - 9)], outline=(255, 255, 255), width=4)

    # Texto
    font_big = pick_font(48)
    font_small = pick_font(28)
    title = f"TEST IMG #{idx}"
    subtitle = f"{w}x{h} JPEG {'PROG' if idx % 2 == 1 else 'BASE'}"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tb = draw.textbbox((0, 0), title, font=font_big)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.text(((w - tw) / 2, (h - th) / 2 - 40), title, fill=(255, 255, 255), font=font_big)

    sb = draw.textbbox((0, 0), subtitle, font=font_small)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    draw.text(((w - sw) / 2, (h - sh) / 2 + 10), subtitle, fill=(255, 230, 180), font=font_small)

    tb2 = draw.textbbox((0, 0), text, font=font_small)
    tw2, th2 = tb2[2] - tb2[0], tb2[3] - tb2[1]
    draw.text(((w - tw2) / 2, (h - th2) / 2 + 48), text, fill=(255, 255, 0), font=font_small)

    draw.text((16, h - 40), ts, fill=(0, 0, 0), font=font_small)
    return img


def save_jpeg(img: Image.Image, path: Path, progressive: bool) -> None:
    # Garante baseline por padrão; progressive quando solicitado
    img.convert("RGB").save(
        str(path),
        format="JPEG",
        quality=85,
        optimize=True,
        progressive=bool(progressive),
    )


def main() -> None:
    args = parse_args()
    repo = ensure_repo_dir()

    filenames: List[str] = []
    if args.filenames:
        filenames = [x.strip() for x in args.filenames.split(",") if x.strip()]
        if len(filenames) < args.count:
            # completa com gerados
            base = len(filenames)
            for i in range(base, args.count):
                filenames.append(f"{args.prefix}_{i+1}.jpg")
    else:
        filenames = [f"{args.prefix}_{i+1}.jpg" for i in range(args.count)]

    for i in range(args.count):
        name = filenames[i]
        dst = repo / name
        img = render_image(args.width, args.height, args.text, i + 1)
        save_jpeg(img, dst, progressive=args.progressive)
        print(f"✓ Gerado: {dst} ({args.width}x{args.height}) progressive={args.progressive}")


if __name__ == "__main__":
    main()
