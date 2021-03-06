# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import caas_pb2 as caas__pb2


class userStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Register = channel.unary_unary(
                '/caas.user/Register',
                request_serializer=caas__pb2.UserRegisterRequest.SerializeToString,
                response_deserializer=caas__pb2.UserRegisterReply.FromString,
                )
        self.Info = channel.unary_unary(
                '/caas.user/Info',
                request_serializer=caas__pb2.UserInfoRequest.SerializeToString,
                response_deserializer=caas__pb2.UserInfoReply.FromString,
                )


class userServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Register(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_userServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Register': grpc.unary_unary_rpc_method_handler(
                    servicer.Register,
                    request_deserializer=caas__pb2.UserRegisterRequest.FromString,
                    response_serializer=caas__pb2.UserRegisterReply.SerializeToString,
            ),
            'Info': grpc.unary_unary_rpc_method_handler(
                    servicer.Info,
                    request_deserializer=caas__pb2.UserInfoRequest.FromString,
                    response_serializer=caas__pb2.UserInfoReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'caas.user', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class user(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Register(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/caas.user/Register',
            caas__pb2.UserRegisterRequest.SerializeToString,
            caas__pb2.UserRegisterReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Info(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/caas.user/Info',
            caas__pb2.UserInfoRequest.SerializeToString,
            caas__pb2.UserInfoReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class curlStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Enqueue = channel.unary_unary(
                '/caas.curl/Enqueue',
                request_serializer=caas__pb2.EnqueueRequest.SerializeToString,
                response_deserializer=caas__pb2.EnqueueResponse.FromString,
                )
        self.GetReulst = channel.unary_unary(
                '/caas.curl/GetReulst',
                request_serializer=caas__pb2.ResultRequest.SerializeToString,
                response_deserializer=caas__pb2.Result.FromString,
                )


class curlServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Enqueue(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetReulst(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_curlServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Enqueue': grpc.unary_unary_rpc_method_handler(
                    servicer.Enqueue,
                    request_deserializer=caas__pb2.EnqueueRequest.FromString,
                    response_serializer=caas__pb2.EnqueueResponse.SerializeToString,
            ),
            'GetReulst': grpc.unary_unary_rpc_method_handler(
                    servicer.GetReulst,
                    request_deserializer=caas__pb2.ResultRequest.FromString,
                    response_serializer=caas__pb2.Result.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'caas.curl', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class curl(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Enqueue(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/caas.curl/Enqueue',
            caas__pb2.EnqueueRequest.SerializeToString,
            caas__pb2.EnqueueResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetReulst(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/caas.curl/GetReulst',
            caas__pb2.ResultRequest.SerializeToString,
            caas__pb2.Result.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
