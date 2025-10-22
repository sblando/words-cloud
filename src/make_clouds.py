
import argparse
from pathlib import Path
import pandas as pd

# English-only helpers from your text_clean.py (normalize/tokenize/stopwords)
from text_clean import normalize_text, tokenize, get_stopwords

# Readers for supported formats
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

# Supported file extensions (lowercased)
SUPPORTED = {".pdf", ".txt", ".docx"}


def read_txt(path: Path) -> str:
    """Read a plain text file as UTF-8 (ignoring undecodable bytes)."""
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf(path: Path) -> str:
    """
    Extract text from a PDF. If extraction fails (encrypted, malformed, etc.),
    return an empty string so the caller can skip it gracefully.
    """
    try:
        return pdf_extract_text(str(path))
    except Exception:
        return ""


def read_docx(path: Path) -> str:
    """
    Extract paragraph text from a DOCX file. If anything goes wrong, return
    an empty string to keep the pipeline robust.
    """
    try:
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def read_any(path: Path) -> str:
    """
    Dispatch to the appropriate reader based on file extension.
    Unknown extensions return an empty string.
    """
    ext = path.suffix.lower()
    if ext == ".txt":
        return read_txt(path)
    if ext == ".pdf":
        return read_pdf(path)
    if ext == ".docx":
        return read_docx(path)
    return ""


def build_vocab(tokens: list[str], stopwords: set[str]) -> pd.Series:
    """
    Build a unigram frequency Series from tokens.

    - Filters out stopwords
    - Filters out very short tokens (<= 2 chars) to reduce noise like 'an', 'to'
    - Returns a pandas Series[int] indexed by token, sorted by value when using .head()
    """
    toks = [t for t in tokens if t not in stopwords and len(t) > 2]
    if not toks:
        return pd.Series(dtype="int64")
    return pd.Series(toks, dtype="string").value_counts()


def process_issue(
    input_dir: Path,
    output_dir: Path,
    top: int,
    extra_stop: list[str],
) -> None:
    """
    Process all supported files in input_dir and write per-file & overall CSV outputs.

    Outputs:
      - <stem>_top_terms.csv            (per file)
      - overall_top_terms.csv           (corpus-wide)
    """
    # Ensure output directory exists (won't fail if it already does)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Merge base English stopwords + user-provided extras
    stopwords = get_stopwords(set(extra_stop))

    # Collect candidate files
    files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED])
    if not files:
        print(f"No files found in {input_dir}. Supported: PDF/DOCX/TXT")
        return

    # Accumulator for overall (corpus-wide) counts
    overall_unigrams = pd.Series(dtype="int64")

    # Process each file independently
    for f in files:
        print(f"[+] {f.name}")

        # 1) Read raw text
        raw = read_any(f)
        if not raw:
            print(f"    [warn] could not read or empty: {f.name}")
            continue

        # 2) Normalize (lowercase, URLs/emails/digits removal, punctuation trim, unidecode)
        norm = normalize_text(raw)

        # 3) Tokenize (whitespace-based)
        toks = tokenize(norm)

        # 4) Build per-file vocabulary (unigrams)
        uni = build_vocab(toks, stopwords)

        # 5) Export per-file CSV (top-N terms to keep outputs compact)
        if not uni.empty:
            uni_top = uni.head(top)

            # Save CSV
            (output_dir / f"{f.stem}_top_terms.csv").write_text(
                uni_top.to_csv(header=["freq"]), encoding="utf-8"
            )

            # Accumulate to overall counts (sum frequencies by token)
            overall_unigrams = uni.add(overall_unigrams, fill_value=0).astype("int64")

    # 6) Export overall CSV
    if not overall_unigrams.empty:
        overall_uni_top = overall_unigrams.sort_values(ascending=False).head(top)
        (output_dir / "overall_top_terms.csv").write_text(
            overall_uni_top.to_csv(header=["freq"]), encoding="utf-8"
        )

    print(f"[✓] Done. Outputs in: {output_dir}")


def main() -> None:
    """Parse CLI arguments and run the issue processor."""
    ap = argparse.ArgumentParser(
        "Generate unigram frequency CSVs from a folder (PDF/DOCX/TXT)."
    )
    ap.add_argument("--input", required=True, help="Input folder with files (PDF/TXT/DOCX)")
    ap.add_argument("--output", default="output", help="Output folder for CSVs")
    ap.add_argument("--top", type=int, default=100, help="Top N terms to export")
    ap.add_argument("--stop", nargs="*", default=[], help="Extra stopwords (space-separated)")
    args = ap.parse_args()

    process_issue(
        Path(args.input),
        Path(args.output),
        args.top,
        args.stop,
    )


if __name__ == "__main__":
    main()
