#!/usr/bin/env python3

import os
import logging
import random
import subprocess
import time

from minio import Minio

import psycopg2

logging.basicConfig(
    format="%(asctime)s [%(process)d] %(levelname)-8s %(message)s", level=logging.DEBUG)

pg_connection = psycopg2.connect(host="db", user=os.getenv('POSTGRES_USER'), password=os.getenv(
    'POSTGRES_PASSWORD'), dbname=os.getenv('POSTGRES_DB'))

s3_client = Minio("s3:9000", os.getenv('MINIO_ROOT_USER'),
                  os.getenv('MINIO_ROOT_PASSWORD'), secure=False)

while True:
    time.sleep(random.uniform(0.05, 0.3))
    with pg_connection:
        with pg_connection.cursor() as cursor:
            cursor.execute("""
                update tasks
                    set status = 'RUNNING', started = now()
                where id = (
                    select id from tasks
                    where status = 'PENDING'
                    order by id limit 1
                    for update skip locked
                )
                returning id, method, url
            """)

            task = cursor.fetchone()
            pg_connection.commit()

            if task is None:
                continue

            logging.debug(task)
            task_id, method, url = task
            result, message = False, None
            output = "/tmp/_" + str(task_id)

            opts = ["-X", method, "--no-progress-meter", "-o", output,
                    "--proto", "=http,https", "--max-time", "4", "--max-filesize", "10M"]
            cmd = ["/usr/bin/curl", *opts, url]
            try:
                res = subprocess.run(cmd, timeout=5, shell=False, capture_output=True)

                if res.returncode:
                    message = res.stderr.decode("utf-8")
                else:
                    if os.path.getsize(output) > 10 * 1024 * 1024:
                        message = "worker: Exceeded the maximum file size"
                    else:
                        result = True
                        s3_client.fput_object("curl", "_" + str(task_id), output)

                    os.remove(output)
            except Exception as e:
                logging.fatal(e)

            cursor.execute("""
                update tasks
                    set finished = now(), status = 'FINISHED',
                    result = %(result)s, message = %(message)s
                where id = %(id)s
            """, {"id": task_id, "result": result, "message": message})
            pg_connection.commit()
