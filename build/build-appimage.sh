#!/bin/bash
# =============================================================================
# build-appimage.sh — Build PythonScriptRunner AppImage for Linux x86_64
#
# Run this on an x86_64 Linux machine (Ubuntu 20.04+ recommended).
# Required packages:  curl  tar  tcl8.6  tk8.6  (fuse2 to test the result)
#
#   sudo apt install curl tar tcl8.6 tk8.6        # Debian/Ubuntu
#   sudo dnf install curl tar tcl tk              # Fedora/RHEL
#
# Usage:
#   cd build
#   bash build-appimage.sh
#
# Output:
#   ../PythonScriptRunner-x86_64.AppImage
# =============================================================================
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
APP_NAME="PythonScriptRunner"
APP_VERSION="1.0"

# Python build-standalone: https://github.com/astral-sh/python-build-standalone
# Update these three values if you want a newer Python release.
PYTHON_VERSION="3.12.9"
PYTHON_RELEASE="20250317"
PYTHON_ARCH="x86_64-unknown-linux-gnu"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PYTHON_RELEASE}/cpython-${PYTHON_VERSION}+${PYTHON_RELEASE}-${PYTHON_ARCH}-install_only_stripped.tar.gz"

APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APPDIR="$SCRIPT_DIR/AppDir"
OUTPUT="$PROJECT_ROOT/${APP_NAME}-x86_64.AppImage"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"
PYTHON_TARBALL="$SCRIPT_DIR/python-standalone.tar.gz"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
log()   { echo -e "${GREEN}[BUILD]${NC} $*"; }
warn()  { echo -e "${YELLOW}[ WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

# ── Guards ────────────────────────────────────────────────────────────────────
[[ "$(uname -s)" == "Linux" ]]       || error "Must run on Linux x86_64."
[[ "$(uname -m)" == "x86_64" ]]      || error "Must run on an x86_64 machine."
command -v curl >/dev/null 2>&1       || error "'curl' is required. Install it first."
command -v tar  >/dev/null 2>&1       || error "'tar' is required. Install it first."

echo -e "\n${BOLD}Building $APP_NAME v$APP_VERSION AppImage${NC}"
echo    "  Python   : $PYTHON_VERSION"
echo    "  Output   : $OUTPUT"

# ── Clean previous build ──────────────────────────────────────────────────────
step "Cleaning previous build"
rm -rf "$APPDIR"
rm -f  "$OUTPUT"
mkdir -p "$APPDIR"/{app,python,lib,share/tcltk}

# ── Download Python standalone ────────────────────────────────────────────────
step "Python standalone"
if [ ! -f "$PYTHON_TARBALL" ]; then
    log "Downloading Python $PYTHON_VERSION (this will be ~30 MB)..."
    curl -L --progress-bar -o "$PYTHON_TARBALL" "$PYTHON_URL"
else
    log "Using cached: $(basename "$PYTHON_TARBALL")"
fi

log "Extracting..."
tar -xzf "$PYTHON_TARBALL" -C "$APPDIR"

# The tarball extracts a 'python/' directory at the target location.
[ -d "$APPDIR/python/bin" ] || error "Python extraction failed — expected $APPDIR/python/bin"

# Ensure the 'python3' symlink exists regardless of minor-version naming.
PYTHON_BIN="$APPDIR/python/bin"
if [ ! -f "$PYTHON_BIN/python3" ]; then
    PY_REAL=$(ls "$PYTHON_BIN"/python3.* 2>/dev/null | head -1)
    [ -n "$PY_REAL" ] || error "No python3.x binary found in $PYTHON_BIN"
    ln -sf "$(basename "$PY_REAL")" "$PYTHON_BIN/python3"
fi

BUNDLED_PYTHON="$PYTHON_BIN/python3"
log "Bundled Python: $($BUNDLED_PYTHON --version)"

# ── Bundle Tcl/Tk shared libraries ────────────────────────────────────────────
# tkinter dynamically links against libTcl/libTk — copy them into the AppDir
# so the AppImage works on machines that don't have them installed.
step "Tcl/Tk libraries"
TCL_FOUND=0; TK_FOUND=0

# Candidate library locations (covers Debian/Ubuntu/Fedora/Arch)
LIB_DIRS=(/usr/lib/x86_64-linux-gnu /usr/lib64 /usr/lib /lib/x86_64-linux-gnu)

for d in "${LIB_DIRS[@]}"; do
    for f in "$d"/libtcl8.6.so.1 "$d"/libtcl8.6.so "$d"/libtcl8*.so*; do
        if [ -f "$f" ]; then
            cp -P "$f" "$APPDIR/lib/" && log "  Bundled $(basename "$f")"
            TCL_FOUND=1; break 2
        fi
    done
done
for d in "${LIB_DIRS[@]}"; do
    for f in "$d"/libtk8.6.so.1 "$d"/libtk8.6.so "$d"/libtk8*.so*; do
        if [ -f "$f" ]; then
            cp -P "$f" "$APPDIR/lib/" && log "  Bundled $(basename "$f")"
            TK_FOUND=1; break 2
        fi
    done
done

[ "$TCL_FOUND" -eq 1 ] || warn "libtcl8.6 not found — install: sudo apt install tcl8.6"
[ "$TK_FOUND"  -eq 1 ] || warn "libtk8.6 not found  — install: sudo apt install tk8.6"

# Tcl/Tk script data directories (widget definitions, fonts, etc.)
for d in /usr/share/tcltk/tcl8.6 /usr/lib/tcl8.6 /usr/share/tcl8.6; do
    [ -d "$d" ] && { cp -r "$d" "$APPDIR/share/tcltk/"; log "  Bundled tcl data: $d"; break; }
done
for d in /usr/share/tcltk/tk8.6 /usr/lib/tk8.6 /usr/share/tk8.6; do
    [ -d "$d" ] && { cp -r "$d" "$APPDIR/share/tcltk/"; log "  Bundled tk data:  $d"; break; }
done

# ── Copy application source ───────────────────────────────────────────────────
step "Application source"
cp    "$PROJECT_ROOT/PythonScriptRunner.py" "$APPDIR/app/"
cp    "$PROJECT_ROOT/requirements.txt"       "$APPDIR/app/"
cp -r "$PROJECT_ROOT/runner"                 "$APPDIR/app/"
cp -r "$PROJECT_ROOT/scripts"               "$APPDIR/app/"

# Strip __pycache__ artefacts before bundling
find "$APPDIR/app" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Pre-compile to .pyc for faster first launch
log "Pre-compiling source..."
PYTHONHOME="$APPDIR/python" "$BUNDLED_PYTHON" -m compileall -q "$APPDIR/app/" 2>/dev/null || true

# ── Icon ──────────────────────────────────────────────────────────────────────
step "Icon"
ICON_OUT="$APPDIR/$APP_NAME.png"
if [ -f "$PROJECT_ROOT/icon.png" ]; then
    cp "$PROJECT_ROOT/icon.png" "$ICON_OUT"
    log "Using project icon.png"
else
    warn "No icon.png found in project root — generating a placeholder."
    warn "Replace $PROJECT_ROOT/icon.png with a real 256×256 PNG and re-run to use it."
    PYTHONHOME="$APPDIR/python" "$BUNDLED_PYTHON" - "$ICON_OUT" <<'PYEOF'
import struct, sys, zlib

def make_solid_png(path: str, size: int = 256, r: int = 74, g: int = 158, b: int = 255) -> None:
    """Write a minimal solid-colour PNG (no external dependencies)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)

    ihdr  = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    row   = b'\x00' + bytes([r, g, b] * size)   # filter=None, then RGB pixels
    raw   = row * size                            # repeat for every scanline
    png   = b'\x89PNG\r\n\x1a\n'
    png  += chunk(b'IHDR', ihdr)
    png  += chunk(b'IDAT', zlib.compress(raw, level=9))
    png  += chunk(b'IEND', b'')
    with open(path, 'wb') as fh:
        fh.write(png)
    print(f"Placeholder icon written to {path}")

make_solid_png(sys.argv[1])
PYEOF
fi

# ── AppRun + desktop entry ────────────────────────────────────────────────────
step "AppRun & desktop entry"
cp "$SCRIPT_DIR/AppRun"               "$APPDIR/AppRun"
cp "$SCRIPT_DIR/$APP_NAME.desktop"    "$APPDIR/"
chmod +x "$APPDIR/AppRun"

# ── Download appimagetool ─────────────────────────────────────────────────────
step "appimagetool"
if [ ! -f "$APPIMAGETOOL" ]; then
    log "Downloading appimagetool..."
    curl -L --progress-bar -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL"
    chmod +x "$APPIMAGETOOL"
else
    log "Using cached: $(basename "$APPIMAGETOOL")"
fi

# ── Build AppImage ────────────────────────────────────────────────────────────
step "Packaging AppImage"
log "Running appimagetool..."
ARCH=x86_64 "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUTPUT" 2>&1

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}✓  Build complete!${NC}"
echo "   Output : $OUTPUT"
echo "   Size   : $(du -sh "$OUTPUT" 2>/dev/null | cut -f1)"
echo ""
echo "   To run :"
echo "     chmod +x PythonScriptRunner-x86_64.AppImage"
echo "     ./PythonScriptRunner-x86_64.AppImage"
echo ""
echo "   App data lives in:  ~/.local/share/PythonScriptRunner/"
echo "   Drop your scripts into that folder's scripts/ sub-directory."
echo ""
echo "   NOTE: FUSE must be available on the target machine."
echo "   On older distros: sudo apt install fuse  OR  sudo dnf install fuse"
