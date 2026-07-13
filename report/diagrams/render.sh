#!/usr/bin/env bash
# Render every report/diagrams/*.mmd source into report/img/*.png via
# minlag/mermaid-cli (dockerised mmdc). Self-contained: resolves paths from
# its own location, so it can be invoked from anywhere, e.g.:
#   bash report/diagrams/render.sh
#   ./render.sh                       (from inside report/diagrams/)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMG_DIR="$REPORT_DIR/img"

mkdir -p "$IMG_DIR"

shopt -s nullglob
mmd_files=("$SCRIPT_DIR"/*.mmd)
shopt -u nullglob

if [ ${#mmd_files[@]} -eq 0 ]; then
    echo "No .mmd files found in $SCRIPT_DIR" >&2
    exit 1
fi

# Mount the report/ directory root (not just diagrams/) so the -o output
# path (img/<name>.png) stays inside the mounted volume instead of trying
# to escape it with a literal ../img path.
for mmd in "${mmd_files[@]}"; do
    name="$(basename "$mmd" .mmd)"
    echo "Rendering $name.mmd -> img/$name.png"
    docker run --rm -u "$(id -u)" -v "$REPORT_DIR":/data minlag/mermaid-cli \
        -i "/data/diagrams/$name.mmd" \
        -o "/data/img/$name.png" \
        -w 1600 -b white
done

echo "Done. Rendered ${#mmd_files[@]} diagram(s) into $IMG_DIR"
