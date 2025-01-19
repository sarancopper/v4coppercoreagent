#!/bin/sh
# wait-for-mysql.sh

set -e

host="$1"
shift
cmd="$@"

until mysql -h"$host" -P3306 -uroot -p"$MYSQL_ROOT_PASSWORD" -e 'select 1' &>/dev/null; do
  echo "MySQL is unavailable - waiting..."
  sleep 2
done
echo "MySQL is up - executing command"
exec $cmd
