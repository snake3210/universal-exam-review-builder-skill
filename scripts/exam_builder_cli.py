# Copyright 2026
# Universal Exam Review Builder CLI Script
# Follows the multi-command argparse CLI pattern with file-based outputs and rate-limiting.

"""Multi-command CLI tool for the `universal-exam-review-builder` skill.

Subcommands:
- fetch-urls: Downloads exam PDFs from a JSON list of URLs with 1 req/s rate limiting.
- extract-pdf: Extracts text per page from a folder of PDFs and flags figure/scanned pages.
- crop-images: Crops bounding boxes from PDF pages at 250 DPI into images/<id>.png.
- validate-json: Validates the 4-dimensional question bank JSON schema.
- build-spa: Generates index.html, exam_data.js, and the single-file offline HTML bundle.
"""

import argparse
import base64
import json
import os
import sys
import tempfile
import time
import unicodedata
from urllib import error as urllib_error
from urllib import request as urllib_request

sys.stdout.reconfigure(encoding="utf-8")


class RateLimitError(Exception):
    """Raised when an HTTP 429 rate limit is exceeded."""


class ExamDownloadClient:
    """HTTP downloader with cross-process file-lock rate limiting (1 req/sec)."""

    REQUESTS_PER_SECOND = 1.0

    def __init__(self):
        self.delay = 1.0 / self.REQUESTS_PER_SECOND
        self.last_request_time = 0.0
        self.lock_file = os.path.join(
            tempfile.gettempdir(), "universal_exam_builder_ratelimit.lock"
        )

    def _wait_for_rate_limit(self):
        elapsed = time.monotonic() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def download_file(self, url: str, dest_path: str, retries: int = 3) -> int:
        for attempt in range(retries):
            self._wait_for_rate_limit()
            try:
                req = urllib_request.Request(
                    url,
                    headers={"User-Agent": "UniversalExamReviewBuilder/1.0"},
                )
                with urllib_request.urlopen(req, timeout=30) as response:
                    self.last_request_time = time.monotonic()
                    content = response.read()
                    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
                    with open(dest_path, "wb") as f:
                        f.write(content)
                    return len(content)
            except urllib_error.HTTPError as e:
                self.last_request_time = time.monotonic()
                if e.code == 429:
                    wait = 2**attempt
                    print(
                        f"Rate limited (429) on {url}, retrying in {wait}s "
                        f"(attempt {attempt + 1}/{retries})...",
                        file=sys.stderr,
                    )
                    if attempt == retries - 1:
                        raise RateLimitError(
                            f"HTTP 429 Too Many Requests from {url}. "
                            f"Rate limit ({self.REQUESTS_PER_SECOND} req/s) exceeded."
                        ) from e
                    time.sleep(wait)
                    continue
                if e.code >= 500:
                    wait = 2**attempt
                    print(
                        f"Server error {e.code} on {url}, retrying in {wait}s "
                        f"(attempt {attempt + 1}/{retries})...",
                        file=sys.stderr,
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"Server error {e.code} from {url} after {retries} retries."
                        ) from e
                    time.sleep(wait)
                    continue
                try:
                    body = e.read().decode("utf-8", errors="replace")[:1000]
                except OSError:
                    body = str(e.reason)
                raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from e
            except urllib_error.URLError as e:
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Failed to connect to {url} after {retries} attempts: {e}"
                    ) from e
                time.sleep(2**attempt)
        return 0


def write_output(data, output_file: str):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Success! Data written to: {output_file}")
    except (OSError, TypeError) as e:
        print(f"Error writing to file {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_fetch_urls(args):
    with open(args.urls_file, "r", encoding="utf-8") as f:
        items = json.load(f)[: args.limit]
    client = ExamDownloadClient()
    results = []
    for item in items:
        url = item["url"]
        dest = item["dest_path"]
        size_bytes = client.download_file(url, dest)
        results.append({"id": item.get("id", ""), "url": url, "dest_path": dest, "bytes": size_bytes})
    write_output({"downloaded": results, "count": len(results)}, args.output)


def cmd_extract_pdf(args):
    import pymupdf

    pdf_files = sorted(
        f for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")
    )
    extracted = []
    figure_keywords = ("如圖", "下圖", "右圖", "左圖", "圖一", "圖二", "圖1", "圖2")

    for fname in pdf_files:
        if len(extracted) >= args.limit:
            break
        fpath = os.path.join(args.pdf_dir, fname)
        doc = pymupdf.open(fpath)
        pages_info = []
        for page_idx, page in enumerate(doc):
            raw_text = unicodedata.normalize("NFKC", page.get_text("text"))
            has_fig_kw = any(kw in raw_text for kw in figure_keywords)
            img_list = page.get_images(full=True)
            is_scanned = len(raw_text.strip()) < 30 and len(img_list) > 0
            pages_info.append(
                {
                    "page_number": page_idx + 1,
                    "char_count": len(raw_text),
                    "image_count": len(img_list),
                    "has_figure_keyword": has_fig_kw,
                    "is_likely_scanned": is_scanned,
                    "text": raw_text,
                }
            )
        extracted.append({"file": fname, "page_count": len(doc), "pages": pages_info})
    write_output({"files": extracted}, args.output)


def cmd_crop_images(args):
    import pymupdf

    with open(args.config, "r", encoding="utf-8") as f:
        crop_specs = json.load(f)

    results = []
    for spec in crop_specs:
        qid = spec["id"]
        pdf_path = spec["pdf_path"]
        page_num = spec["page"]  # 1-based
        rect = pymupdf.Rect(*spec["bbox"])  # [x0, y0, x1, y1]
        out_path = spec.get("output_path", os.path.join("images", f"{qid}.png"))

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        doc = pymupdf.open(pdf_path)
        page = doc[page_num - 1]
        pix = page.get_pixmap(clip=rect, dpi=250)
        pix.save(out_path)
        results.append(
            {
                "id": qid,
                "output_path": out_path,
                "width": pix.width,
                "height": pix.height,
            }
        )
    write_output({"cropped_images": results, "count": len(results)}, args.output)


def cmd_validate_json(args):
    with open(args.input, "r", encoding="utf-8") as f:
        questions = json.load(f)[: args.limit]

    required_keys = {
        "id",
        "question",
        "options",
        "answer",
        "category",
        "algorithm_path",
        "key_triggers",
        "confusion_trap",
        "guideline_check",
    }
    errors = []
    for q in questions:
        qid = q.get("id", "<missing-id>")
        missing = required_keys - set(q.keys())
        if missing:
            errors.append({"id": qid, "error": f"Missing keys: {sorted(missing)}"})
            continue
        if not isinstance(q["options"], list) or len(q["options"]) < 2:
            errors.append({"id": qid, "error": "options must be a list of choices"})
        if not isinstance(q["algorithm_path"], list) or len(q["algorithm_path"]) < 2:
            errors.append({"id": qid, "error": "algorithm_path must have >= 2 steps"})
        if not str(q["confusion_trap"]).strip().startswith("• "):
            errors.append({"id": qid, "error": "confusion_trap must start with '• '"})
        if not str(q["guideline_check"]).strip().startswith("• "):
            errors.append({"id": qid, "error": "guideline_check must start with '• '"})
        if "image" in q and q["image"] and not str(q["image"]).startswith("data:"):
            if not os.path.exists(q["image"]):
                errors.append({"id": qid, "error": f"Image file not found: {q['image']}"})

    report = {
        "valid": len(errors) == 0,
        "checked_count": len(questions),
        "error_count": len(errors),
        "errors": errors,
    }
    write_output(report, args.output)
    if errors:
        sys.exit(1)


def _encode_image_base64(img_path: str, quality: int = 76) -> str:
    import pymupdf

    if img_path.startswith("data:"):
        return img_path
    pix = pymupdf.Pixmap(img_path)
    if pix.alpha:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix, False)
    if pix.width > 1200:
        scale = 1150.0 / pix.width
        pix = pymupdf.Pixmap(pix, int(pix.width * scale), int(pix.height * scale))
    jpg_bytes = pix.tobytes("jpeg", jpg_quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(jpg_bytes).decode("ascii")


def cmd_build_spa(args):
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(skill_root, "resources", "spa_template.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()
    with open(args.questions, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(args.subject_config, "r", encoding="utf-8") as f:
        subject_config = json.load(f)

    out_dir = os.path.dirname(os.path.abspath(args.output))
    index_out = os.path.join(out_dir, "index.html")
    data_js_out = os.path.join(out_dir, "exam_data.js")
    bundle_name = subject_config.get("bundleFilename", "Exam_Review_終極單一獨立版.html")
    bundle_out = os.path.join(out_dir, bundle_name)

    # 1. Write exam_data.js & index.html
    data_js_content = (
        "// Auto-generated by universal-exam-review-builder\n"
        f"window.EXAM_SUBJECT_CONFIG = {json.dumps(subject_config, ensure_ascii=False, indent=2)};\n"
        f"window.EXAM_QUESTIONS = {json.dumps(questions, ensure_ascii=False, indent=2)};\n"
    )
    with open(data_js_out, "w", encoding="utf-8") as f:
        f.write(data_js_content)
    with open(index_out, "w", encoding="utf-8") as f:
        f.write(template_html)

    # 2. Build Single-File Offline Bundle
    inlined_questions = json.loads(json.dumps(questions))
    for q in inlined_questions:
        if q.get("image"):
            img_abs = os.path.join(out_dir, q["image"]) if not os.path.isabs(q["image"]) else q["image"]
            if os.path.exists(img_abs):
                q["image"] = _encode_image_base64(img_abs)

    tailwind_path = os.path.join(out_dir, "tailwind.min.js")
    if os.path.exists(tailwind_path):
        with open(tailwind_path, "r", encoding="utf-8") as f:
            tw_script = f"<script>\n{f.read()}\n</script>"
    else:
        tw_script = '<script src="https://cdn.tailwindcss.com"></script>'

    bundle_html = template_html.replace('<script src="tailwind.min.js"></script>', tw_script)
    inline_data = (
        "<script>\n"
        f"window.EXAM_SUBJECT_CONFIG = {json.dumps(subject_config, ensure_ascii=False)};\n"
        f"window.EXAM_QUESTIONS = {json.dumps(inlined_questions, ensure_ascii=False)};\n"
        "</script>"
    )
    bundle_html = bundle_html.replace('<script src="exam_data.js"></script>', inline_data)
    with open(bundle_out, "w", encoding="utf-8") as f:
        f.write(bundle_html)

    write_output(
        {
            "index_html": index_out,
            "exam_data_js": data_js_out,
            "single_file_bundle": bundle_out,
            "question_count": len(questions),
        },
        args.output,
    )


def main():
    parser = argparse.ArgumentParser(description="Universal Exam Review Builder CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_fetch = subparsers.add_parser("fetch-urls", help="Download exam PDFs with rate limiting")
    p_fetch.add_argument("--urls-file", required=True, help="JSON file of URLs")
    p_fetch.add_argument("--limit", type=int, required=True, help="Max files to download")
    p_fetch.add_argument("--output", required=True, help="Output JSON report path")

    p_ext = subparsers.add_parser("extract-pdf", help="Extract text and figure flags from PDFs")
    p_ext.add_argument("--pdf-dir", required=True, help="Directory containing PDF files")
    p_ext.add_argument("--limit", type=int, required=True, help="Max PDF files to process")
    p_ext.add_argument("--output", required=True, help="Output JSON path")

    p_crop = subparsers.add_parser("crop-images", help="Crop figures from PDFs at 250 DPI")
    p_crop.add_argument("--config", required=True, help="JSON crop specification path")
    p_crop.add_argument("--output", required=True, help="Output JSON report path")

    p_val = subparsers.add_parser("validate-json", help="Validate structured question bank JSON")
    p_val.add_argument("--input", required=True, help="Input question bank JSON path")
    p_val.add_argument("--limit", type=int, required=True, help="Max questions to validate")
    p_val.add_argument("--output", required=True, help="Output validation JSON path")

    p_spa = subparsers.add_parser("build-spa", help="Build Dual-Theme SPA and Single-File Bundle")
    p_spa.add_argument("--questions", required=True, help="Validated questions JSON path")
    p_spa.add_argument("--subject-config", required=True, help="Subject configuration JSON path")
    p_spa.add_argument("--output", required=True, help="Output manifest JSON path")

    args = parser.parse_args()
    if args.command == "fetch-urls":
        cmd_fetch_urls(args)
    elif args.command == "extract-pdf":
        cmd_extract_pdf(args)
    elif args.command == "crop-images":
        cmd_crop_images(args)
    elif args.command == "validate-json":
        cmd_validate_json(args)
    elif args.command == "build-spa":
        cmd_build_spa(args)


if __name__ == "__main__":
    main()
