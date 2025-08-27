PYDBR="$(cd "$(dirname "$1")/.."; pwd)" docker compose -f compose.yaml down -v
PYDBR="$(cd "$(dirname "$1")/.."; pwd)" docker compose -f compose.yaml up -d --force-recreate
sleep 10

docker exec -it pydbr-mysql bash -c "mysql --host=localhost --password=root --user=root < /data/tests/db_init.sql"
while [ $? -ne 0 ]; do
    echo "waiting for mysql to finish loading"
    sleep 2
    docker exec -it pydbr-mysql bash -c "mysql --host=localhost --password=root --user=root < /data/tests/db_init.sql"
done
echo "done"
PYDBR="$(cd "$(dirname "$1")/.."; pwd)" docker compose -f compose.yaml logs -f
