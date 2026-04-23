#!/usr/bin/env bash
set -e

# Colors
G='\033[0;32m'    # green
D='\033[0;90m'    # dim
Y='\033[0;33m'    # gold
R='\033[0;31m'    # red
B='\033[1m'       # bold
N='\033[0m'       # reset

clear

echo -e "${D}"
cat << 'BANNER'

     ██████╗  ██████╗ ███╗   ███╗██╗███╗   ██╗██╗ ██████╗ ███╗   ██╗
     ██╔══██╗██╔═══██╗████╗ ████║██║████╗  ██║██║██╔═══██╗████╗  ██║
     ██║  ██║██║   ██║██╔████╔██║██║██╔██╗ ██║██║██║   ██║██╔██╗ ██║
     ██║  ██║██║   ██║██║╚██╔╝██║██║██║╚██╗██║██║██║   ██║██║╚██╗██║
     ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██║╚██████╔╝██║ ╚████║
     ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝

BANNER
echo -e "${N}"

DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo -e "  ${D}───────────────────────────────────${N}"
    echo -e "  ${Y}⚔${N}  ${B}The kingdom falls silent.${N}"
    echo -e "  ${D}───────────────────────────────────${N}"
    echo ""
    [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null
    [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null
    wait 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- Backend ---
echo -e "  ${D}···${N} ${B}Summoning the server${N}"

cd "$DIR/backend"
if [[ ! -d .venv ]]; then
    echo -e "  ${D}···${N} Creating venv..."
    uv venv --quiet
    uv pip install -e . --quiet
fi

source .venv/bin/activate
python server.py > /tmp/dominion-backend.log 2>&1 &
BACKEND_PID=$!
sleep 1

if kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "  ${G} ✓ ${N} Server listening on ${Y}:7478${N}"
else
    echo -e "  ${R} ✗ ${N} Server failed to start. Check ${D}/tmp/dominion-backend.log${N}"
    exit 1
fi

# --- Frontend ---
echo -e "  ${D}···${N} ${B}Raising the banners${N}"

cd "$DIR/frontend"
if [[ ! -d node_modules ]]; then
    echo -e "  ${D}···${N} Installing dependencies..."
    npm install --silent 2>/dev/null
fi

npx vite dev --host 2>/dev/null > /tmp/dominion-frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 2

if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    PORT=$(grep -oP 'localhost:\K[0-9]+' /tmp/dominion-frontend.log | head -1)
    PORT=${PORT:-5173}
    echo -e "  ${G} ✓ ${N} UI ready on ${Y}http://localhost:${PORT}${N}"
else
    echo -e "  ${R} ✗ ${N} Frontend failed. Check ${D}/tmp/dominion-frontend.log${N}"
    cleanup
fi

# --- Ready ---
echo ""
echo -e "  ${D}───────────────────────────────────${N}"
echo -e "  ${Y}♛${N}  ${B}The kingdom awaits.${N}"
echo -e "  ${D}   Ctrl+C to abdicate${N}"
echo -e "  ${D}───────────────────────────────────${N}"
echo ""

wait
