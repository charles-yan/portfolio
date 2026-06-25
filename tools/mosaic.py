#!/usr/bin/env python3
"""
图片马赛克处理工具
支持：像素化马赛克、高斯模糊、指定区域打码
用法:
    python mosaic.py <input> <output> --mode pixel --region x,y,w,h
    python mosaic.py <input> <output> --mode gaussian --blur 15
    python mosaic.py --batch <input_dir> <output_dir> --mode pixel --blur 10
"""

import sys
import os
import argparse
from PIL import Image, ImageFilter


def pixelize_region(img, region, pixel_size=10):
    """对指定区域进行像素化马赛克"""
    x, y, w, h = region
    x, y = max(0, x), max(0, y)
    w = min(w, img.width - x)
    h = min(h, img.height - y)
    if w <= 0 or h <= 0:
        return img

    crop = img.crop((x, y, x + w, y + h))
    small = crop.resize((max(1, w // pixel_size), max(1, h // pixel_size)), Image.NEAREST)
    mosaic = small.resize((w, h), Image.NEAREST)
    img.paste(mosaic, (x, y))
    return img


def gaussian_blur_region(img, region, blur_radius=15):
    """对指定区域进行高斯模糊"""
    x, y, w, h = region
    x, y = max(0, x), max(0, y)
    w = min(w, img.width - x)
    h = min(h, img.height - y)
    if w <= 0 or h <= 0:
        return img

    crop = img.crop((x, y, x + w, y + h))
    blurred = crop.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    img.paste(blurred, (x, y))
    return img


def mosaic_full_image(img, mode="pixel", blur_radius=10, pixel_size=10):
    """对整张图片进行马赛克"""
    if mode == "pixel":
        small = img.resize((img.width // pixel_size, img.height // pixel_size), Image.NEAREST)
        return small.resize((img.width, img.height), Image.NEAREST)
    elif mode == "gaussian":
        return img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    else:
        return img


def process_image(input_path, output_path, mode="pixel", region=None, blur_radius=10, pixel_size=10):
    """处理单张图片"""
    img = Image.open(input_path)
    if img.mode == "RGBA":
        img = img.convert("RGB")

    if region:
        if mode == "pixel":
            result = pixelize_region(img, region, pixel_size)
        elif mode == "gaussian":
            result = gaussian_blur_region(img, region, blur_radius)
        else:
            result = img
    else:
        result = mosaic_full_image(img, mode, blur_radius, pixel_size)

    result.save(output_path)
    print(f"✅ 已处理: {input_path} -> {output_path}")
    return output_path


def batch_process(input_dir, output_dir, mode="pixel", blur_radius=10, pixel_size=10):
    """批量处理目录下的图片"""
    os.makedirs(output_dir, exist_ok=True)
    extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    processed = []
    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in extensions:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            process_image(input_path, output_path, mode, None, blur_radius, pixel_size)
            processed.append(output_path)
    return processed


def parse_region(s):
    """解析区域字符串 'x,y,w,h' -> (x, y, w, h)"""
    parts = [int(p.strip()) for p in s.split(',')]
    if len(parts) != 4:
        raise ValueError("区域格式必须是 x,y,w,h")
    return tuple(parts)


def main():
    parser = argparse.ArgumentParser(description="图片马赛克处理工具")
    parser.add_argument("input", help="输入图片路径或目录")
    parser.add_argument("output", nargs="?", help="输出路径或目录")
    parser.add_argument("--batch", action="store_true", help="批量处理目录")
    parser.add_argument("--mode", choices=["pixel", "gaussian"], default="pixel",
                        help="马赛克模式: pixel(像素化) | gaussian(高斯模糊)")
    parser.add_argument("--region", type=str, help="指定区域: x,y,w,h")
    parser.add_argument("--blur", type=int, default=10, help="高斯模糊半径 (默认10)")
    parser.add_argument("--pixel-size", type=int, default=10, help="像素化块大小 (默认10)")
    parser.add_argument("--list", action="store_true", help="列出目录中的图片")

    args = parser.parse_args()

    if args.list:
        if os.path.isdir(args.input):
            for f in sorted(os.listdir(args.input)):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    print(f)
        else:
            print(os.path.basename(args.input))
        return

    if args.batch or os.path.isdir(args.input):
        if not args.output:
            args.output = args.input + "_mosaic"
        batch_process(args.input, args.output, args.mode, args.blur, args.pixel_size)
    else:
        region = parse_region(args.region) if args.region else None
        output_path = args.output or (os.path.splitext(args.input)[0] + "_mosaic" + os.path.splitext(args.input)[1])
        process_image(args.input, output_path, args.mode, region, args.blur, args.pixel_size)


if __name__ == "__main__":
    main()
