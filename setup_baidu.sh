#!/usr/bin/env bash
# =============================================================================
# Setup script: Download BaiduPCS-Go binary for your platform
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"
VERSION="v4.0.1"
REPO="qjfoidnh/BaiduPCS-Go"

# --- Detect platform ---
detect_platform() {
    local os arch
    case "$(uname -s)" in
        Linux)  os="linux" ;;
        Darwin) os="darwin" ;;
        MINGW*|MSYS*|CYGWIN*) os="windows" ;;
        *) echo "Unsupported OS: $(uname -s)"; exit 1 ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64) arch="amd64" ;;
        arm64|aarch64) arch="arm64" ;;
        *) echo "Unsupported arch: $(uname -m)"; exit 1 ;;
    esac

    echo "${os}-${arch}"
}

PLATFORM=$(detect_platform)
FILENAME="BaiduPCS-Go-${VERSION}-${PLATFORM}.zip"
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${VERSION}/${FILENAME}"

echo "=== BaiduPCS-Go Setup ==="
echo "Platform:  ${PLATFORM}"
echo "Version:   ${VERSION}"
echo "Download:  ${DOWNLOAD_URL}"
echo "Target:    ${BIN_DIR}"
echo ""

# --- Download ---
cd "${BIN_DIR}"

if [ -f "BaiduPCS-Go" ] || [ -f "BaiduPCS-Go.exe" ]; then
    echo "[SKIP] BaiduPCS-Go binary already exists. Delete it to re-download."
    echo "       Run: rm ${BIN_DIR}/BaiduPCS-Go*"
    exit 0
fi

echo "[DOWNLOAD] Fetching ${FILENAME}..."
if command -v wget &> /dev/null; then
    wget -q --show-progress "${DOWNLOAD_URL}" -O "${FILENAME}"
elif command -v curl &> /dev/null; then
    curl -L --progress-bar "${DOWNLOAD_URL}" -o "${FILENAME}"
else
    echo "ERROR: Neither wget nor curl found. Please install one."
    exit 1
fi

# --- Extract ---
echo "[EXTRACT] ${FILENAME}..."
unzip -o "${FILENAME}"
rm "${FILENAME}"

# --- Set permissions ---
if [ -f "BaiduPCS-Go" ]; then
    chmod +x "BaiduPCS-Go"
    echo "[OK] Binary: ${BIN_DIR}/BaiduPCS-Go"
elif [ -f "BaiduPCS-Go.exe" ]; then
    echo "[OK] Binary: ${BIN_DIR}/BaiduPCS-Go.exe"
else
    echo "ERROR: Binary not found after extraction. Check archive contents."
    exit 1
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Set environment variables:"
echo "     export COURSERA_CAUTH='your-cauth-cookie'"
echo "     export BAIDU_BDUSS='your-bduss'"
echo "     export BAIDU_STOKEN='your-stoken'"
echo ""
echo "  2. Review config.yaml and adjust course list"
echo ""
echo "  3. Run: python sync.py"
