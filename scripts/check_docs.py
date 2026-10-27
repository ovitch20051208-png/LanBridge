"""Validate repository documentation links, section anchors and screenshot files."""

from __future__ import annotations

import html
import re
import struct
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\n)]+)\)")
HTML_LINK = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)


def anchors(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    result = set(re.findall(r"<(?:a|[^ >]+)\b[^>]*\b(?:id|name)=[\"']([^\"']+)[\"']", source))
    counts: dict[str, int] = {}
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", source, re.MULTILINE):
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", title)
        title = re.sub(r"<[^>]*>", "", html.unescape(title))
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(f"{slug}-{count}" if count else slug)
    return result


def main() -> None:
    documents = sorted([*ROOT.glob("README*.md"), *(ROOT / "docs").rglob("*.md")])
    errors = []
    checked = 0
    images: set[Path] = set()
    anchor_cache: dict[Path, set[str]] = {}
    for document in documents:
        source = document.read_text(encoding="utf-8")
        for match in [*LINK.finditer(source), *HTML_LINK.finditer(source)]:
            value = html.unescape(match.group(1).strip())
            value = value[1 : value.index(">")] if value.startswith("<") else value.split()[0]
            address = urlsplit(value)
            if address.scheme or address.netloc:
                continue
            checked += 1
            target = (document.parent / unquote(address.path)).resolve() if address.path else document
            label = f"{document.relative_to(ROOT).as_posix()}:{source.count(chr(10), 0, match.start()) + 1}"
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"{label}: missing local target {value}")
                continue
            if address.fragment and target.suffix.lower() == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(target)
                if unquote(address.fragment) not in anchor_cache[target]:
                    errors.append(f"{label}: missing section {value}")
            if target.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                images.add(target)
    for path in images:
        try:
            width, height = image_size(path)
            if not width or not height:
                raise ValueError("Empty image")
        except (ValueError, struct.error) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"Documentation passed: {len(documents)} Markdown files, {checked} local links, {len(images)} images"
    )


def image_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
        if path.suffix.lower() == ".png" and header[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack("!II", header[16:24])
        if path.suffix.lower() in {".jpg", ".jpeg"} and header[:2] == b"\xff\xd8":
            stream.seek(2)
            while True:
                if stream.read(1) != b"\xff":
                    raise ValueError("Invalid JPEG marker")
                marker = stream.read(1)
                while marker == b"\xff":
                    marker = stream.read(1)
                if not marker or marker in {b"\xd9", b"\xda"}:
                    break
                length = struct.unpack("!H", stream.read(2))[0]
                if length < 2:
                    break
                if marker[0] in {
                    0xC0,
                    0xC1,
                    0xC2,
                    0xC3,
                    0xC5,
                    0xC6,
                    0xC7,
                    0xC9,
                    0xCA,
                    0xCB,
                    0xCD,
                    0xCE,
                    0xCF,
                }:
                    _, height, width = struct.unpack("!BHH", stream.read(5))
                    return width, height
                stream.seek(length - 2, 1)
    raise ValueError("Image format or dimensions invalid")


if __name__ == "__main__":
    main()
