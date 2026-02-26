#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COURSE_DIR="$(dirname "$SCRIPT_DIR")"
MD_DIR="$COURSE_DIR/reference_docs/markdown"
PDF_DIR="$COURSE_DIR/reference_docs/pdf"

mkdir -p "$PDF_DIR"

for md_file in "$MD_DIR"/*.md; do
  [ -f "$md_file" ] || continue
  filename="$(basename "$md_file" .md)"
  echo "Converting: $filename.md -> $filename.pdf"
  npx md-to-pdf "$md_file"
  mv "$MD_DIR/$filename.pdf" "$PDF_DIR/$filename.pdf"
done

echo "Done. PDFs written to $PDF_DIR"
