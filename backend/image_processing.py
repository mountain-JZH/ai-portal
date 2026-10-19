"""Shared safe decoding for section and tool cover uploads; Banner stays unchanged."""

from io import BytesIO
import struct
import warnings

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from upload_api import MAX_IMAGE_SIZE

ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
MAX_DIMENSION = 8192
MAX_PIXELS = 16_000_000


def validate_and_encode_image(content: bytes, content_type: str) -> bytes:
    """Verify structure, then fully decode. Never persist untrusted original bytes."""
    if content_type not in ALLOWED_FORMATS.values():
        raise HTTPException(400, "只允许 JPEG、PNG 或 WebP 图片")
    if not content or len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "图片不能为空且不能超过 5MB")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content), formats=list(ALLOWED_FORMATS)) as image:
                width, height = image.size
                if (
                    width < 1 or height < 1
                    or max(width, height) > MAX_DIMENSION
                    or width * height > MAX_PIXELS
                ):
                    raise HTTPException(400, "图片尺寸不得超过 8192px，像素总量不得超过 1600 万")
                if ALLOWED_FORMATS.get(image.format) != content_type:
                    raise HTTPException(400, "图片真实格式与声明类型不一致")
                if getattr(image, "n_frames", 1) != 1:
                    raise HTTPException(400, "请使用静态图片，不支持动画图片")
                image.verify()

            with Image.open(BytesIO(content), formats=list(ALLOWED_FORMATS)) as image:
                image.load()
                # Strip metadata/trailing payloads; keep alpha and decoded colours.
                mode = "RGBA" if image.mode in {"RGBA", "LA", "P"} else "RGB"
                with Image.new(mode, image.size) as clean:
                    clean.paste(image.convert(mode))
                    result = BytesIO()
                    clean.save(result, format="WEBP", lossless=True, method=4)
                    encoded = result.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, EOFError,
            OverflowError, struct.error,
            Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise HTTPException(400, "图片无法完整解码、文件已损坏或像素数量异常") from error

    if len(encoded) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "图片安全处理后超过 5MB，请降低图片尺寸后重试")
    return encoded
