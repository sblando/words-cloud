
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# English-only helpers from your text_clean.py (normalize/tokenize/stopwords/strip_references)
from text_clean import normalize_text, tokenize, get_stopwords, strip_references

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
    - Filters out very short tokens (<= 2 chars)
    - Returns a pandas Series[int] indexed by token
    """
    toks = [t for t in tokens if t not in stopwords and len(t) > 2]
    if not toks:
        return pd.Series(dtype="int64")
    return pd.Series(toks, dtype="string").value_counts()


def build_bigrams(tokens: list[str], stopwords: set[str], min_freq: int = 3) -> pd.Series:
    """
    Create _joined bigrams (a_b) from consecutive tokens:
      - Ignore stopwords
      - Ignore short tokens (<= 2)
      - Keep only those with frequency >= min_freq
    """
    pairs: list[str] = []
    for a, b in zip(tokens, tokens[1:]):
        if len(a) <= 2 or len(b) <= 2:
            continue
        if a in stopwords or b in stopwords:
            continue
        pairs.append(f"{a}_{b}")
    if not pairs:
        return pd.Series(dtype="int64")
    s = pd.Series(pairs, dtype="string").value_counts()
    return s[s >= int(min_freq)]


def make_wordcloud(freq: pd.Series, out_path: Path) -> None:
    """
    Render and save a word cloud PNG from a frequency Series.

    - collocations=False avoids WordCloud forming its own bigrams
    """
    if freq.empty:
        return

    wc = WordCloud(
        width=1600,
        height=1000,
        background_color="white",
        collocations=False,
    )
    img = wc.generate_from_frequencies(freq.to_dict())
    plt.figure(figsize=(12, 7))
    plt.imshow(img)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def process_issue(
    input_dir: Path,
    output_dir: Path,
    top: int,
    extra_stop: list[str],
    cut_refs: bool,
    use_bigrams: bool,
    min_bigram_freq: int,
) -> None:
    """
    Process all supported files in input_dir and write per-file & overall outputs.

    Outputs:
      - <stem>_top_terms.csv                 (per file)
      - <stem>_wordcloud.png                 (per file)
      - <stem>_top_bigrams.csv               (per file, when --bigrams)
      - <stem>_wordcloud_bigrams.png         (per file, when --bigrams)
      - overall_top_terms.csv                (corpus-wide)
      - overall_wordcloud.png                (corpus-wide)
      - overall_top_bigrams.csv              (corpus-wide, when --bigrams)
      - overall_wordcloud_bigrams.png        (corpus-wide, when --bigrams)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stopwords = get_stopwords(set(extra_stop))

    files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED])
    if not files:
        print(f"No files found in {input_dir}. Supported: PDF/DOCX/TXT")
        return

    overall_unigrams = pd.Series(dtype="int64")
    overall_bigrams = pd.Series(dtype="int64")

    for f in files:
        print(f"[+] {f.name}")
        raw = read_any(f)
        if not raw:
            print(f"    [warn] could not read or empty: {f.name}")
            continue

        # Optionally strip references/bibliography tail; normalize CRLF -> LF first
        if cut_refs:
            raw = strip_references(raw.replace("\r\n", "\n"))

        # Normalize + tokenize
        norm = normalize_text(raw)
        toks = tokenize(norm)

        # Per-file unigrams
        uni = build_vocab(toks, stopwords)

        # Optional per-file bigrams
        if use_bigrams:
            bi = build_bigrams(toks, stopwords, min_bigram_freq)
        else:
            bi = pd.Series(dtype="int64")

        # Per-file exports
        if not uni.empty:
            uni_top = uni.head(top)
            (output_dir / f"{f.stem}_top_terms.csv").write_text(
                uni_top.to_csv(header=["freq"]), encoding="utf-8"
            )
            make_wordcloud(uni_top, output_dir / f"{f.stem}_wordcloud.png")

        if use_bigrams and not bi.empty:
            bi_top = bi.head(top)
            (output_dir / f"{f.stem}_top_bigrams.csv").write_text(
                bi_top.to_csv(header=["freq"]), encoding="utf-8"
            )
            make_wordcloud(bi_top, output_dir / f"{f.stem}_wordcloud_bigrams.png")

        # Accumulate overall
        if not uni.empty:
            overall_unigrams = uni.add(overall_unigrams, fill_value=0).astype("int64")
        if use_bigrams and not bi.empty:
            overall_bigrams = bi.add(overall_bigrams, fill_value=0).astype("int64")

    # Overall exports
    if not overall_unigrams.empty:
        overall_uni_top = overall_unigrams.sort_values(ascending=False).head(top)
        (output_dir / "overall_top_terms.csv").write_text(
            overall_uni_top.to_csv(header=["freq"]), encoding="utf-8"
        )
        make_wordcloud(overall_uni_top, output_dir / "overall_wordcloud.png")

    if use_bigrams and not overall_bigrams.empty:
        overall_bi_top = overall_bigrams.sort_values(ascending=False).head(top)
        (output_dir / "overall_top_bigrams.csv").write_text(
            overall_bi_top.to_csv(header=["freq"]), encoding="utf-8"
        )
        make_wordcloud(overall_bi_top, output_dir / "overall_wordcloud_bigrams.png")

    print(f"[✓] Done. Outputs in: {output_dir}")


def main() -> None:
    """Parse CLI arguments and run the issue processor."""
    ap = argparse.ArgumentParser(
        "Generate word clouds (unigrams/bigrams) from a folder (PDF/DOCX/TXT)."
    )
    ap.add_argument("--input", required=True, help="Input folder with files (PDF/TXT/DOCX)")
    ap.add_argument("--output", default="output", help="Output folder for CSV/PNG")
    ap.add_argument("--top", type=int, default=100, help="Top N terms to export/plot")
    ap.add_argument("--stop", nargs="*", default=[], help="Extra stopwords (space-separated)")
    ap.add_argument("--strip-refs", action="store_true", help="Drop everything after References/Bibliography")
    ap.add_argument("--bigrams", action="store_true", help="Also build bigram clouds (e.g., machine_learning)")
    ap.add_argument("--min-bigram-freq", type=int, default=3, help="Minimum frequency to keep a bigram")
    args = ap.parse_args()

    process_issue(
        Path(args.input),
        Path(args.output),
        args.top,
        args.stop,
        args.strip_refs,
        args.bigrams,
        args.min_bigram_freq,
    )


if __name__ == "__main__":
    main()
