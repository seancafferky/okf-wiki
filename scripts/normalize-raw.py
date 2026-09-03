#!/usr/bin/env python3
"""
normalize-raw.py — turn every binary source under a bundle's raw/ into plain text.

The wiki only ever reads text. Binary originals (video, audio, PDF, EPUB, Office
documents, text-bearing images) are an ingest-time input, not a durable asset:
they are large, opaque to grep, and hostile to git. This script extracts the
text, verifies the extraction is substantive, and — with --purge — deletes the
original.

Naming: output is always "<original filename>.txt", extension included, e.g.

    Playing to Win.epub   ->  Playing to Win.epub.txt
    lecture-3.mp4         ->  lecture-3.mp4.txt

Keeping the original extension in the name preserves provenance after the
original is gone, and makes migrating a `source:` frontmatter field a matter of
appending ".txt".

An expanded EPUB (a *directory* named *.epub) is handled as a single unit and
collapses to one .txt.

Usage:
    normalize-raw.py --doctor
    normalize-raw.py PATH                     # dry run: report what would happen
    normalize-raw.py PATH --apply             # write .txt files
    normalize-raw.py PATH --apply --purge     # ...and delete converted originals
    normalize-raw.py PATH --apply --sweep-junk  # also remove tool scratch files
    normalize-raw.py PATH --apply --only pdf,epub

Exit codes: 0 all handled, 1 one or more failures, 2 preflight failed.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

# --------------------------------------------------------------------------- #
# External tools
# --------------------------------------------------------------------------- #

CALIBRE_CANDIDATES = (
    "ebook-convert",
    "/Applications/calibre.app/Contents/MacOS/ebook-convert",
)
WHISPER_CANDIDATES = ("whisper-cli", "whisper-cpp", "main")
MODEL_DIRS = (
    Path.home() / "whisper-models",
    Path.home() / ".cache" / "whisper.cpp",
    Path("/opt/homebrew/share/whisper-cpp"),
    Path("/usr/local/share/whisper-cpp"),
)
MODEL_PREFERENCE = (
    "ggml-large-v3-turbo.bin",
    "ggml-large-v3.bin",
    "ggml-medium.bin",
    "ggml-small.bin",
    "ggml-base.bin",
)


def which(*names: str) -> str | None:
    for n in names:
        if os.path.sep in n:
            if Path(n).is_file() and os.access(n, os.X_OK):
                return n
        elif (p := shutil.which(n)):
            return p
    return None


def find_model() -> Path | None:
    for d in MODEL_DIRS:
        if not d.is_dir():
            continue
        for name in MODEL_PREFERENCE:
            if (d / name).is_file():
                return d / name
    return None


def run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, errors="replace"
    )


# --------------------------------------------------------------------------- #
# Text hygiene
# --------------------------------------------------------------------------- #

_WS_RUN = re.compile(r"[ \t   ]+")
_BLANK_RUN = re.compile(r"\n{3,}")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def tidy(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CTRL.sub("", text)
    text = "\n".join(_WS_RUN.sub(" ", line).rstrip() for line in text.split("\n"))
    text = _BLANK_RUN.sub("\n\n", text)
    return text.strip() + "\n"


class _Stripper(HTMLParser):
    """HTML -> text. Drops non-content elements, keeps block structure."""

    DROP = {"script", "style", "noscript", "head", "svg", "iframe", "form"}
    BLOCK = {
        "p", "div", "br", "li", "tr", "section", "article", "blockquote", "pre",
        "h1", "h2", "h3", "h4", "h5", "h6", "table", "hr", "figcaption",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.DROP:
            self.depth += 1
        elif tag in self.BLOCK:
            self.out.append("\n")
        if tag in {"h1", "h2", "h3"}:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.DROP and self.depth:
            self.depth -= 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.depth:
            self.out.append(data)

    def text(self) -> str:
        return "".join(self.out)


def html_to_text(markup: str) -> str:
    p = _Stripper()
    try:
        p.feed(markup)
        p.close()
    except Exception:
        pass
    return tidy(p.text())


def decode(raw: bytes) -> str:
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# EPUB (file or expanded directory)
# --------------------------------------------------------------------------- #

_NS_CONTAINER = "{urn:oasis:names:tc:opendocument:xmlns:container}"
_NS_OPF = "{http://www.idpf.org/2007/opf}"


class _Epub:
    """Uniform reader over a zipped .epub and an expanded .epub directory."""

    def __init__(self, root: Path):
        self.root = root
        self.zf = zipfile.ZipFile(root) if root.is_file() else None
        if self.zf is not None:
            self._names = set(self.zf.namelist())

    def close(self) -> None:
        if self.zf is not None:
            self.zf.close()

    def read(self, name: str) -> bytes:
        name = name.lstrip("/")
        if self.zf is not None:
            if name in self._names:
                return self.zf.read(name)
            # Some producers percent-encode or case-shift spine hrefs.
            from urllib.parse import unquote
            alt = unquote(name)
            if alt in self._names:
                return self.zf.read(alt)
            raise KeyError(name)
        return (self.root / name).read_bytes()

    def exists(self, name: str) -> bool:
        try:
            self.read(name)
            return True
        except Exception:
            return False

    def walk(self) -> list[str]:
        if self.zf is not None:
            return sorted(n for n in self._names if not n.endswith("/"))
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*")
            if p.is_file()
        )

    # -- spine resolution ---------------------------------------------------

    def opf_path(self) -> str | None:
        try:
            container = ET.fromstring(self.read("META-INF/container.xml"))
        except Exception:
            for name in self.walk():
                if name.endswith(".opf"):
                    return name
            return None
        rootfile = container.find(f".//{_NS_CONTAINER}rootfile")
        if rootfile is not None and rootfile.get("full-path"):
            return rootfile.get("full-path")
        for name in self.walk():
            if name.endswith(".opf"):
                return name
        return None

    def documents(self) -> list[str]:
        """Content documents in reading order, best effort."""
        opf = self.opf_path()
        if opf:
            try:
                base = str(Path(opf).parent)
                tree = ET.fromstring(self.read(opf))
                manifest = {}
                for item in tree.iter(f"{_NS_OPF}item"):
                    manifest[item.get("id")] = (
                        item.get("href", ""),
                        item.get("media-type", ""),
                    )
                ordered = []
                for ref in tree.iter(f"{_NS_OPF}itemref"):
                    href, mtype = manifest.get(ref.get("idref"), ("", ""))
                    if not href or "html" not in mtype:
                        continue
                    path = os.path.normpath(os.path.join(base, href)) if base not in ("", ".") else href
                    ordered.append(path.split("#")[0])
                if ordered:
                    return ordered
            except Exception:
                pass
        # Fallback: every markup file, in path order.
        return [
            n for n in self.walk()
            if n.lower().endswith((".xhtml", ".html", ".htm"))
        ]


def extract_epub(path: Path) -> str:
    book = _Epub(path)
    try:
        docs = book.documents()
        if not docs:
            raise RuntimeError("no content documents found")
        chunks = []
        for name in docs:
            try:
                chunks.append(html_to_text(decode(book.read(name))))
            except Exception:
                continue
        if not chunks:
            raise RuntimeError("no content document could be read")
        return tidy("\n\n".join(c for c in chunks if c.strip()))
    finally:
        book.close()


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def _page_count(path: Path) -> int:
    if not which("pdfinfo"):
        return 0
    r = run(["pdfinfo", str(path)], timeout=120)
    m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
    return int(m.group(1)) if m else 0


def extract_pdf(path: Path) -> str:
    if not which("pdftotext"):
        raise RuntimeError("pdftotext (poppler) not installed")
    r = run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"], timeout=900)
    text = tidy(r.stdout or "")
    pages = _page_count(path)
    # A born-digital PDF yields hundreds of characters per page. Far less means
    # the page images carry the text, and only OCR will get it out.
    if pages and len(text) / pages >= 120:
        return text
    if len(text) >= 4000 and not pages:
        return text
    ocr = _ocr_pdf(path, pages)
    if ocr and len(ocr) > len(text):
        return ocr
    if text.strip():
        return text
    raise RuntimeError("no extractable text (scanned PDF and OCR unavailable)")


def _ocr_pdf(path: Path, pages: int) -> str:
    if not (which("pdftoppm") and which("tesseract")):
        return ""
    out: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        stem = Path(td) / "pg"
        r = run(["pdftoppm", "-r", "200", "-gray", "-png", str(path), str(stem)],
                timeout=3600)
        if r.returncode != 0:
            return ""
        for img in sorted(Path(td).glob("pg*.png")):
            t = run(["tesseract", str(img), "stdout", "--psm", "1", "-l", "eng"],
                    timeout=300)
            if t.returncode == 0:
                out.append(t.stdout)
    return tidy("\n\n".join(out))


def extract_image(path: Path) -> str:
    if not which("tesseract"):
        raise RuntimeError("tesseract not installed")
    r = run(["tesseract", str(path), "stdout", "--psm", "1", "-l", "eng"], timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"tesseract failed: {r.stderr.strip()[:200]}")
    return tidy(r.stdout)


# --------------------------------------------------------------------------- #
# Office Open XML
# --------------------------------------------------------------------------- #

_A_T = re.compile(r"<a:t[^>]*>(.*?)</a:t>", re.S)
_W_T = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.S)
_TAG = re.compile(r"<[^>]+>")


def _slide_key(name: str) -> tuple[int, str]:
    m = re.search(r"(\d+)", Path(name).stem)
    return (int(m.group(1)) if m else 0, name)


def extract_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        slides = sorted(
            (n for n in z.namelist()
             if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=_slide_key,
        )
        notes = {
            _slide_key(n)[0]: n for n in z.namelist()
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)
        }
        out = []
        for i, name in enumerate(slides, 1):
            xml = z.read(name).decode("utf-8", "replace")
            body = [html.unescape(t) for t in _A_T.findall(xml)]
            block = [f"--- Slide {i} ---"] + [b for b in body if b.strip()]
            if (nn := notes.get(_slide_key(name)[0])):
                nx = z.read(nn).decode("utf-8", "replace")
                nt = [html.unescape(t) for t in _A_T.findall(nx) if t.strip()]
                if nt:
                    block += ["", "[speaker notes]"] + nt
            out.append("\n".join(block))
    return tidy("\n\n".join(out))


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        if "word/document.xml" not in z.namelist():
            raise RuntimeError("no word/document.xml")
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    lines = ["".join(html.unescape(t) for t in _W_T.findall(chunk))
             for chunk in xml.split("\n")]
    return tidy("\n".join(lines))


def extract_xlsx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            sx = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            for si in re.findall(r"<si>(.*?)</si>", sx, re.S):
                shared.append(html.unescape(_TAG.sub("", si)))
        sheets = sorted(n for n in z.namelist()
                        if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
        out = []
        for i, name in enumerate(sheets, 1):
            sx = z.read(name).decode("utf-8", "replace")
            rows = []
            for row in re.findall(r"<row[^>]*>(.*?)</row>", sx, re.S):
                cells = []
                for cell in re.findall(r"<c\b([^>]*)>(.*?)</c>", row, re.S):
                    attrs, body = cell
                    v = re.search(r"<v>(.*?)</v>", body, re.S)
                    if v is None:
                        inline = re.search(r"<is>(.*?)</is>", body, re.S)
                        cells.append(html.unescape(_TAG.sub("", inline.group(1)))
                                     if inline else "")
                        continue
                    val = html.unescape(v.group(1))
                    if 't="s"' in attrs:
                        idx = int(val) if val.isdigit() else -1
                        val = shared[idx] if 0 <= idx < len(shared) else ""
                    cells.append(val)
                if any(c.strip() for c in cells):
                    rows.append("\t".join(cells))
            if rows:
                out.append(f"--- Sheet {i} ---\n" + "\n".join(rows))
    return tidy("\n\n".join(out))


# --------------------------------------------------------------------------- #
# Web captures
# --------------------------------------------------------------------------- #

def extract_html(path: Path) -> str:
    return html_to_text(decode(path.read_bytes()))


def extract_mhtml(path: Path) -> str:
    import email
    from email import policy
    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    best = ""
    for part in msg.walk():
        if part.get_content_type() != "text/html":
            continue
        try:
            payload = part.get_payload(decode=True) or b""
        except Exception:
            continue
        text = html_to_text(decode(payload))
        if len(text) > len(best):
            best = text
    if not best:
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                best = tidy(decode(part.get_payload(decode=True) or b""))
                break
    if not best:
        raise RuntimeError("no HTML or plain part in archive")
    return best


# --------------------------------------------------------------------------- #
# Ebook formats calibre handles better than we would
# --------------------------------------------------------------------------- #

def extract_via_calibre(path: Path) -> str:
    ec = which(*CALIBRE_CANDIDATES)
    if not ec:
        raise RuntimeError("calibre ebook-convert not installed")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out.txt"
        r = run([ec, str(path), str(out), "--enable-heuristics"], timeout=1800)
        if not out.is_file():
            raise RuntimeError(f"ebook-convert failed: {r.stderr.strip()[-300:]}")
        return tidy(decode(out.read_bytes()))


# --------------------------------------------------------------------------- #
# Audio / video
# --------------------------------------------------------------------------- #

def extract_media(path: Path) -> str:
    ff = which("ffmpeg")
    wh = which(*WHISPER_CANDIDATES)
    model = find_model()
    if not ff:
        raise RuntimeError("ffmpeg not installed")
    if not wh:
        raise RuntimeError("whisper.cpp not installed")
    if not model:
        raise RuntimeError("no ggml whisper model found")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        r = run([ff, "-nostdin", "-loglevel", "error", "-i", str(path),
                 "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                 str(wav)], timeout=7200)
        if not wav.is_file() or wav.stat().st_size < 1024:
            raise RuntimeError(f"ffmpeg produced no audio: {r.stderr.strip()[-300:]}")
        stem = Path(td) / "asr"
        r = run([wh, "-m", str(model), "-f", str(wav), "-otxt", "-nt",
                 "-of", str(stem), "-l", "en", "-t", str(os.cpu_count() or 4)],
                timeout=21600)
        txt = stem.with_suffix(".txt")
        if not txt.is_file():
            raise RuntimeError(f"whisper produced no transcript: {r.stderr.strip()[-300:]}")
        out = tidy(decode(txt.read_bytes()))
    if _looks_like_asr_loop(out):
        raise RuntimeError("transcript is a degenerate repetition loop")
    return out


def _looks_like_asr_loop(text: str) -> bool:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 40:
        return False
    return len(set(lines)) / len(lines) < 0.08


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Handler:
    fn: object
    kind: str
    min_chars: int = 200


HANDLERS: dict[str, Handler] = {
    ".pdf":   Handler(extract_pdf, "pdf", 150),
    ".epub":  Handler(extract_epub, "epub", 2000),
    ".azw3":  Handler(extract_via_calibre, "ebook", 2000),
    ".azw":   Handler(extract_via_calibre, "ebook", 2000),
    ".mobi":  Handler(extract_via_calibre, "ebook", 2000),
    ".fb2":   Handler(extract_via_calibre, "ebook", 2000),
    ".lit":   Handler(extract_via_calibre, "ebook", 2000),
    ".rtf":   Handler(extract_via_calibre, "ebook", 200),
    ".pptx":  Handler(extract_pptx, "office", 100),
    ".docx":  Handler(extract_docx, "office", 100),
    ".xlsx":  Handler(extract_xlsx, "office", 40),
    ".html":  Handler(extract_html, "web", 40),
    ".htm":   Handler(extract_html, "web", 40),
    ".xhtml": Handler(extract_html, "web", 40),
    ".mhtml": Handler(extract_mhtml, "web", 40),
    ".mht":   Handler(extract_mhtml, "web", 40),
    ".mp4":   Handler(extract_media, "media", 200),
    ".mov":   Handler(extract_media, "media", 200),
    ".mkv":   Handler(extract_media, "media", 200),
    ".webm":  Handler(extract_media, "media", 200),
    ".avi":   Handler(extract_media, "media", 200),
    ".wav":   Handler(extract_media, "media", 200),
    ".mp3":   Handler(extract_media, "media", 200),
    ".m4a":   Handler(extract_media, "media", 200),
    ".flac":  Handler(extract_media, "media", 200),
    ".ogg":   Handler(extract_media, "media", 200),
    ".jpg":   Handler(extract_image, "image", 120),
    ".jpeg":  Handler(extract_image, "image", 120),
    ".png":   Handler(extract_image, "image", 120),
    ".tif":   Handler(extract_image, "image", 120),
    ".tiff":  Handler(extract_image, "image", 120),
}

# Scratch left behind by transcription and by macOS. Never a source.
JUNK_DIRS = {".transcribe", "__MACOSX", ".ipynb_checkpoints"}
JUNK_FILES = {".DS_Store", "Thumbs.db", ".lock"}
JUNK_SUFFIXES = (".stderr", ".log", ".lock")


def existing_transcript(path: Path) -> Path | None:
    """A sibling .txt that already covers this file, under either convention."""
    for cand in (path.with_name(path.name + ".txt"), path.with_suffix(".txt")):
        if cand.is_file() and cand.stat().st_size > 0:
            return cand
    return None


@dataclass
class Result:
    path: Path
    kind: str
    status: str           # converted | already | failed | skipped
    detail: str = ""
    bytes_freed: int = 0


def tree_size(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


# --------------------------------------------------------------------------- #

def walk_units(root: Path):
    """Yield convertible units. An expanded *.epub directory is one unit."""
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        dirnames[:] = [n for n in dirnames if n not in JUNK_DIRS]
        # An expanded epub is a unit, not a container to descend into.
        for name in list(dirnames):
            if name.lower().endswith(".epub"):
                dirnames.remove(name)
                yield d / name
        for name in filenames:
            yield d / name


def convert(unit: Path, apply: bool, purge: bool, force: bool) -> Result:
    if unit.is_dir():
        ext = ".epub"
    else:
        ext = unit.suffix.lower()
    handler = HANDLERS.get(ext)
    if handler is None:
        return Result(unit, "-", "skipped", "no handler")

    out = unit.with_name(unit.name + ".txt")
    if not force and (found := existing_transcript(unit)):
        size = tree_size(unit)
        if apply and purge:
            _remove(unit)
            return Result(unit, handler.kind, "already",
                          f"transcript exists: {found.name}", size)
        return Result(unit, handler.kind, "already",
                      f"transcript exists: {found.name}", size)

    if not apply:
        return Result(unit, handler.kind, "converted", "(dry run)", tree_size(unit))

    try:
        text = handler.fn(unit)
    except Exception as e:  # noqa: BLE001 — every failure keeps the original
        return Result(unit, handler.kind, "failed", f"{type(e).__name__}: {e}")

    if len(text.strip()) < handler.min_chars:
        return Result(unit, handler.kind, "failed",
                      f"only {len(text.strip())} chars extracted "
                      f"(min {handler.min_chars})")

    out.write_text(text, encoding="utf-8")
    size = tree_size(unit)
    if purge:
        _remove(unit)
    return Result(unit, handler.kind, "converted",
                  f"{len(text):,} chars -> {out.name}", size if purge else 0)


def _remove(p: Path) -> None:
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()


def sweep_junk(root: Path, apply: bool) -> tuple[int, int]:
    n = freed = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        d = Path(dirpath)
        for name in list(dirnames):
            if name in JUNK_DIRS:
                target = d / name
                freed += tree_size(target)
                n += 1
                dirnames.remove(name)
                if apply:
                    shutil.rmtree(target)
        for name in filenames:
            if name in JUNK_FILES or name.endswith(JUNK_SUFFIXES):
                target = d / name
                freed += target.stat().st_size
                n += 1
                if apply:
                    target.unlink()
    return n, freed


def prune_empty(root: Path, apply: bool) -> int:
    n = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        d = Path(dirpath)
        if d == root:
            continue
        if not any(d.iterdir()):
            n += 1
            if apply:
                d.rmdir()
    return n


def doctor() -> int:
    rows = [
        ("pdftotext (poppler)", which("pdftotext"), "PDF text"),
        ("pdftoppm  (poppler)", which("pdftoppm"), "scanned-PDF rasterise"),
        ("pdfinfo   (poppler)", which("pdfinfo"), "PDF page count"),
        ("tesseract", which("tesseract"), "OCR for scans and infographics"),
        ("ebook-convert", which(*CALIBRE_CANDIDATES), "AZW3/MOBI/RTF"),
        ("ffmpeg", which("ffmpeg"), "audio extraction"),
        ("whisper.cpp", which(*WHISPER_CANDIDATES), "speech to text"),
        ("ggml model", str(find_model() or ""), "whisper weights"),
    ]
    missing = 0
    for name, found, why in rows:
        ok = "OK " if found else "-- "
        if not found:
            missing += 1
        print(f"  {ok} {name:22} {why:34} {found or 'NOT FOUND'}")
    print()
    print("  EPUB, PPTX, DOCX, XLSX, HTML and MHTML need no external tool.")
    return 0 if missing == 0 else 2


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:,.1f} {unit}" if unit != "B" else f"{n:,} B"
        n /= 1024.0
    return str(n)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert binary sources under raw/ to plain text.")
    ap.add_argument("path", nargs="?", help="file or directory to normalize")
    ap.add_argument("--apply", action="store_true",
                    help="write files (default is a dry run)")
    ap.add_argument("--purge", action="store_true",
                    help="delete an original once its text is verified")
    ap.add_argument("--force", action="store_true",
                    help="re-extract even when a sibling .txt exists")
    ap.add_argument("--sweep-junk", action="store_true",
                    help="also remove tool scratch files and empty directories")
    ap.add_argument("--only", default="",
                    help="comma-separated kinds: pdf,epub,ebook,office,web,media,image")
    ap.add_argument("--doctor", action="store_true", help="report tool availability")
    args = ap.parse_args()

    if args.doctor:
        return doctor()
    if not args.path:
        ap.error("path is required unless --doctor")

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"no such path: {root}", file=sys.stderr)
        return 2
    kinds = {k.strip() for k in args.only.split(",") if k.strip()}

    if root.is_file() or root.name.lower().endswith(".epub"):
        units = [root]
    else:
        units = sorted(walk_units(root))
    results: list[Result] = []
    for unit in units:
        if unit.name.endswith(".txt") or unit.name.endswith(".md"):
            continue
        ext = ".epub" if unit.is_dir() else unit.suffix.lower()
        h = HANDLERS.get(ext)
        if h is None:
            continue
        if kinds and h.kind not in kinds:
            continue
        r = convert(unit, args.apply, args.purge, args.force)
        results.append(r)
        flag = {"converted": "+", "already": "=", "failed": "!", "skipped": " "}[r.status]
        rel = unit.relative_to(root) if unit != root else unit.name
        print(f"{flag} [{r.kind:6}] {rel}"
              + (f"\n      {r.detail}" if r.detail else ""), flush=True)

    junk_n = junk_freed = 0
    pruned = 0
    if args.sweep_junk and root.is_dir():
        junk_n, junk_freed = sweep_junk(root, args.apply)
        pruned = prune_empty(root, args.apply)

    by_status: dict[str, int] = {}
    freed = 0
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        freed += r.bytes_freed
    print()
    print("  " + "  ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    if args.sweep_junk:
        print(f"  junk={junk_n} ({human(junk_freed)})  empty-dirs-pruned={pruned}")
    print(f"  reclaimed{'' if args.apply and args.purge else ' (would reclaim)'}: "
          f"{human(freed + junk_freed)}")
    failures = [r for r in results if r.status == "failed"]
    if failures:
        print(f"\n  {len(failures)} failure(s) — originals kept:")
        for r in failures:
            print(f"    {r.path}\n      {r.detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
