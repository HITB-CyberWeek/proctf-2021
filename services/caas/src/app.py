#!/usr/bin/env python3

from concurrent import futures

from base64 import b64encode, b64decode
import ipaddress
import logging
import os
import psycopg2
from psycopg2.extras import Json
import socket
from urllib.parse import urlparse

from minio import Minio

import grpc
import grpc.experimental
import caas_pb2
import caas_pb2_grpc

logging.basicConfig(
    format="%(asctime)s [%(process)d] %(levelname)-8s %(message)s", level=logging.DEBUG)

pg_connection = psycopg2.connect(host="db", user=os.getenv('POSTGRES_USER'), password=os.getenv(
    'POSTGRES_PASSWORD'), dbname=os.getenv('POSTGRES_DB'))

s3_client = Minio("s3:9000", os.getenv('MINIO_ROOT_USER'),
                  os.getenv('MINIO_ROOT_PASSWORD'), secure=False)

if not s3_client.bucket_exists("curl"):
    s3_client.make_bucket("curl")


class user(caas_pb2_grpc.userServicer):
    def Register(self, request, context):
        vars = {
            "name": request.name,
            "profile": Json({
                "image": b64encode(request.image).decode("ascii"),
                "comment": request.comment
            })
        }

        token = None
        with pg_connection:
            with pg_connection.cursor() as cursor:
                cursor.execute("""
                    insert into users (name, profile) values (%(name)s, %(profile)s) returning token
                """, vars)
                token = cursor.fetchone()[0]
                pg_connection.commit()
        return caas_pb2.UserRegisterReply(token=token)

    def Info(self, request, context):
        with pg_connection:
            with pg_connection.cursor() as cursor:
                cursor.execute("select name, profile from users where token = %s", [request.token])
                user = cursor.fetchone()
                if user is None:
                    raise Exception("Invalid token")

                name, profile = user
        return caas_pb2.UserInfoReply(name=name, image=b64decode(profile["image"]), comment=profile["comment"])


class curl(caas_pb2_grpc.curlServicer):
    def Enqueue(self, request, context):

        logging.info(request)
        host = urlparse(request.url).hostname
        try:
            ip = ipaddress.IPv4Address(host)
        except:
            ip = ipaddress.IPv4Address(socket.gethostbyname(host))
        if ip.is_private:
            raise Exception("Invalid hostname")

        task_id = None
        with pg_connection:
            with pg_connection.cursor() as cursor:
                cursor.execute("select id from users where token = %s", [request.token])
                user = cursor.fetchone()
                if user is None:
                    raise Exception("Invalid token")

                user_id = user[0]
                cursor.execute("""
                    insert into tasks (user_id, method, url)
                    values (%s, %s, %s)
                    returning id
                """, (user_id, request.method, request.url)
                )
                task_id = cursor.fetchone()[0]
                pg_connection.commit()
        return caas_pb2.EnqueueResponse(task_id=task_id)

    def GetReulst(self, request, context):
        with pg_connection:
            with pg_connection.cursor() as cursor:
                cursor.execute("select id from users where token = %s", [request.token])
                user = cursor.fetchone()
                if user is None:
                    raise Exception("Invalid token")

                user_id = user[0]
                cursor.execute("""
                    select status, result, message from tasks
                    where user_id = %s and id = %s
                """, [user_id, request.task_id]
                )
                task = cursor.fetchone()
                if task is None:
                    raise Exception("Invalid task_id")

                status, result, message = task
                data = b''
                if status == 'FINISHED':
                    try:
                        r = s3_client.get_object("curl", "_" + str(request.task_id))
                        data = r.read()
                    except Exception as e:
                        logging.debug(e)
                    finally:
                        r.close()
                        r.release_conn()
        return caas_pb2.Result(result=result, message=message, data=data)


server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
caas_pb2_grpc.add_curlServicer_to_server(curl(), server)
caas_pb2_grpc.add_userServicer_to_server(user(), server)
server.add_insecure_port('0.0.0.0:50051')
server.start()
server.wait_for_termination()
