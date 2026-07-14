#!/usr/bin/env bash
# Downloads a local, non-system JDK (Eclipse Temurin 17) needed to run engine.jar,
# for machines that don't already have `java` on PATH (e.g. this dev environment,
# where /usr/bin/java is a macOS stub that isn't a real JRE).
#
# This does NOT require sudo/admin and does not touch system Java. It only
# extracts a JDK into tools/jdk-*/ which is gitignored (redownload as needed).
#
# Usage:
#   ./tools/setup_java.sh
#   source ./tools/java_env.sh   # to load JAVA_HOME/PATH into your current shell
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v java >/dev/null 2>&1 && java -version >/dev/null 2>&1; then
  echo "A working 'java' is already on PATH:"
  java -version
  echo "Skipping JDK download. (Delete/rename it first if you want to force a local install.)"
  exit 0
fi

OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
  Darwin) PLATFORM="mac" ;;
  Linux) PLATFORM="linux" ;;
  *) echo "Unsupported OS: $OS. Install a JDK 17+ manually." >&2; exit 1 ;;
esac
case "$ARCH" in
  arm64|aarch64) JARCH="aarch64" ;;
  x86_64|amd64) JARCH="x64" ;;
  *) echo "Unsupported arch: $ARCH. Install a JDK 17+ manually." >&2; exit 1 ;;
esac

URL="https://api.adoptium.net/v3/binary/latest/17/ga/${PLATFORM}/${JARCH}/jdk/hotspot/normal/eclipse"
echo "Downloading Temurin JDK 17 for ${PLATFORM}/${JARCH} ..."
curl -fL -C - --retry 10 --retry-delay 3 --connect-timeout 10 -o jdk17.tar.gz "$URL"

echo "Extracting..."
tar -xzf jdk17.tar.gz
rm -f jdk17.tar.gz

JDK_DIR="$(find . -maxdepth 1 -type d -name 'jdk-17*' | head -1)"
if [ -z "$JDK_DIR" ]; then
  echo "Could not find extracted JDK directory." >&2
  exit 1
fi

if [ "$PLATFORM" = "mac" ]; then
  JAVA_HOME_PATH="$SCRIPT_DIR/$JDK_DIR/Contents/Home"
else
  JAVA_HOME_PATH="$SCRIPT_DIR/$JDK_DIR"
fi

cat > "$SCRIPT_DIR/java_env.sh" <<EOF
export JAVA_HOME="$JAVA_HOME_PATH"
export PATH="\$JAVA_HOME/bin:\$PATH"
EOF

echo "Done. Run: source tools/java_env.sh"
"$JAVA_HOME_PATH/bin/java" -version
