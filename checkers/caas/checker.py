#!/usr/bin/env python3

import grpc
import caas_pb2
import caas_pb2_grpc

import json
import random
import sys
import time
import traceback
import io
import uuid

import numpy
from PIL import Image

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

def verdict(exit_code, public="", private=""):
    if public:
        print(public)
    if private:
        print(private, file=sys.stderr)
    sys.exit(exit_code)

def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag is a comment in user's profile, Flag ID is a user name")

def check(host):
    verdict(OK)

def put(host, flag_id, flag, vuln):

    channel = grpc.insecure_channel(host + ':50051')
    curl_stub = caas_pb2_grpc.curlStub(channel)
    user_stub = caas_pb2_grpc.userStub(channel)

    image = b''
    with io.BytesIO() as output:
        imarray = numpy.random.rand(50, 50, 3) * 255
        im = Image.fromarray(imarray.astype("uint8")).convert("RGBA")
        im.save(output, format="PNG")
        image = output.getvalue()

    name = uuid.uuid4().hex
    state = {"public_flag_id": name}

    try:
        response = user_stub.Register(caas_pb2.UserRegisterRequest(
            name=name,
            image=image,
            comment=flag
        ))
        state["token"] = response.token

        state["url"] = "https://www.rfc-editor.org/rfc/rfc" + str(random.randint(1000, 1500)) + ".txt"
        response = curl_stub.Enqueue(caas_pb2.EnqueueRequest(
            token=state["token"],
            method="GET",
            url=state["url"]
        ))
        state["task_id"] = response.task_id
    except grpc.RpcError as e:
        s = DOWN if e.code() == grpc.StatusCode.UNAVAILABLE else MUMBLE
        verdict(s, e.details(), traceback.format_exc())

    verdict(OK, json.dumps(state))

def get(host, flag_id, flag, vuln):

    channel = grpc.insecure_channel(host + ':50051')
    curl_stub = caas_pb2_grpc.curlStub(channel)
    user_stub = caas_pb2_grpc.userStub(channel)

    state = json.loads(flag_id)

    try:
        user_result = user_stub.Info(caas_pb2.ResultRequest(token=state["token"]))
        if user_result.name != state["public_flag_id"]:
            verdict(MUMBLE, "Info: invalid name for token", "Info: invalid name for token")
        if user_result.comment != flag:
            verdict(CORRUPT, "Info: invalid comment for token", "Info: invalid comment for token")
        for attempt in range(5):
            task_result = curl_stub.GetReulst(caas_pb2.ResultRequest(token=state["token"], task_id=state["task_id"]))
            if task_result.result and len(task_result.data) == 0:
                verdict(MUMBLE, "GetResult: empty data", "GetResult: empty data")
            if not (task_result.result or task_result.message):
                if attempt == 4:
                    verdict(MUMBLE, "GetResult: task not finished", "GetResult: task not finished")
                time.sleep(5)
            else:
                break
    except grpc.RpcError as e:
        s = DOWN if e.code() == grpc.StatusCode.UNAVAILABLE else MUMBLE
        verdict(s, e.details(), traceback.format_exc())

    verdict(OK)

def main(args):
    CMD_MAPPING = {
        "info": (info, 0),
        "check": (check, 1),
        "put": (put, 4),
        "get": (get, 4),
    }

    if not args:
        verdict(CHECKER_ERROR, "No args", "No args")

    cmd, args = args[0], args[1:]
    if cmd not in CMD_MAPPING:
        verdict(CHECKER_ERROR, "Checker error", "Wrong command %s" % cmd)

    handler, args_count = CMD_MAPPING[cmd]
    if len(args) != args_count:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for %s" % cmd)

    try:
        handler(*args)
    except ConnectionRefusedError as E:
        verdict(DOWN, "Connect refused", "Connect refused: %s" % E)
    except ConnectionError as E:
        verdict(MUMBLE, "Connection aborted", "Connection aborted: %s" % E)
    except OSError as E:
        verdict(DOWN, "Connect error", "Connect error: %s" % E)
    except Exception as E:
        verdict(CHECKER_ERROR, "Checker error", "Checker error: %s" % traceback.format_exc())
    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
