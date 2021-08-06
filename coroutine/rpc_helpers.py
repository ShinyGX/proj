# -*- coding: utf-8 -*-
import coroutine
import json
import uuid

def rpc_method(func):
    func.__rpc_method__ = True
    return func


class RpcProxy(object):

    def __init__(self, caller):
        self.caller = caller

    def __getattr__(self, name):
        def call_rpc(*args, **kwarg):
            method_info = {
                'name': name,
                'args': args,
                'kwargs': kwarg
            }
            self.caller and self.caller.send_to(json.dumps(method_info))

        setattr(self, name, call_rpc)
        return getattr(self, name)


    def parse_rpc(self, info):
        method_info = json.loads(info)
        if method_info.get('name', None):
            method = getattr(self.caller, method_info['name'], None)
            if method and getattr(method, '__rpc_method__', False):
                method(*method_info['args'], **method_info['kwargs'])
        elif method_info.get('guid', None):
            coroutine.co_manager.resume_coroutine(uuid.UUID(method_info['guid']), method_info['ret_value'])


    def rpc_return(self, guid, ret_value):
        ret_info = {
            'guid': guid,
            'ret_value': ret_value
        }
        self.caller and self.caller.send_to(json.dumps(ret_info))

