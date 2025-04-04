#!/bin/sh
set -e

host="$1"
port="$2"
shift 2

echo "Ожидание подключения к PostgreSQL на $host:$port..."
until pg_isready -h "$host" -p "$port" -U "postgres"; do
  >&2 echo "PostgreSQL не готов, ждем..."
  sleep 2
done

echo "PostgreSQL готов, запускаем команду: $*"
exec "$@"
