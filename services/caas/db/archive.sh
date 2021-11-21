#!/bin/bash

# init
mc -q alias set s3 http://s3:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc -q mb -p s3/wal
mc -q policy set download s3/wal

# archive
cat "$1" | gzip | mc -q pipe "s3/wal/$2.gz"
