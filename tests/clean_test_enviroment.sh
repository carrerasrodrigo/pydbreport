PYDBR="$(cd "$(dirname "$1")/.."; pwd)" docker compose -f compose.yaml stop
PYDBR="$(cd "$(dirname "$1")/.."; pwd)" docker compose -f compose.yaml rm
