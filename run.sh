
#!/usr/bin/env bash
# Ejecución del LMS (backend FastAPI + frontend React/Vite).
# Uso:  ./run.sh [all|backend|frontend|test|setup]    (por defecto: all)
# Colocar este archivo en la raíz del proyecto (junto a lms_backend/ y lms_frontend/).
# En Windows: ejecutar desde Git Bash o WSL.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/lms_backend"
FRONTEND="$ROOT/lms_frontend"
VENV="$BACKEND/venv"
PORT_API="${PORT_API:-8000}"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
err() { printf '\033[1;31mError: %s\033[0m\n' "$*" >&2; exit 1; }

find_python() {
  for p in python3 python py; do
    if command -v "$p" >/dev/null 2>&1; then echo "$p"; return; fi
  done
  err "No se encontró Python 3. Instálalo desde python.org."
}

activate_venv() {
  # Linux/macOS: bin/activate — Windows (Git Bash): Scripts/activate
  if [ -f "$VENV/bin/activate" ]; then . "$VENV/bin/activate"
  elif [ -f "$VENV/Scripts/activate" ]; then . "$VENV/Scripts/activate"
  else err "No existe el entorno virtual. Ejecuta: ./run.sh setup"; fi
}

setup_backend() {
  [ -d "$BACKEND" ] || err "No existe $BACKEND"
  if [ ! -d "$VENV" ]; then
    log "Creando entorno virtual"
    "$(find_python)" -m venv "$VENV"
  fi
  activate_venv
  log "Instalando dependencias del backend"
  pip install -q --upgrade pip
  pip install -q -r "$BACKEND/requirements.txt"
}

setup_frontend() {
  [ -d "$FRONTEND" ] || err "No existe $FRONTEND"
  command -v npm >/dev/null 2>&1 || err "No se encontró npm. Instala Node.js (nodejs.org)."
  if [ ! -d "$FRONTEND/node_modules" ]; then
    log "Instalando dependencias del frontend"
    (cd "$FRONTEND" && npm install)
  fi
}

run_backend() {
  setup_backend
  log "Backend en http://127.0.0.1:$PORT_API  (Swagger: /docs)"
  cd "$BACKEND"
  exec uvicorn app.main:app --reload --port "$PORT_API"
}

run_frontend() {
  setup_frontend
  log "Frontend en http://localhost:5173"
  cd "$FRONTEND"
  exec npm run dev
}

run_tests() {
  setup_backend
  log "Ejecutando pruebas del backend"
  cd "$BACKEND"
  python -m pytest -q
}

run_all() {
  setup_backend
  setup_frontend
  PIDS=()
  trap 'log "Deteniendo servidores..."; kill "${PIDS[@]}" 2>/dev/null || true; exit 0' INT TERM EXIT

  log "Iniciando backend (http://127.0.0.1:$PORT_API)"
  (cd "$BACKEND" && uvicorn app.main:app --reload --port "$PORT_API") &
  PIDS+=($!)

  log "Iniciando frontend (http://localhost:5173)"
  (cd "$FRONTEND" && npm run dev) &
  PIDS+=($!)

  log "Todo listo. Presiona Ctrl+C para detener ambos."
  wait
}

case "${1:-all}" in
  all)       run_all ;;
  backend)   run_backend ;;
  frontend)  run_frontend ;;
  test)      run_tests ;;
  setup)     setup_backend; setup_frontend; log "Instalación completa" ;;
  *)         echo "Uso: $0 [all|backend|frontend|test|setup]"; exit 1 ;;
esac
