# -*- coding: utf-8 -*-

import asyncore
import socket
import json
import rpc_helpers
import coroutine
import timer
import threading

class Client(asyncore.dispatcher, object):

    def __init__(self, host, port):
        super(Client, self).__init__()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.setblocking(False)
        self.buff = ''

        self.caller = rpc_helpers.RpcProxy(self)

    def send_to(self, message):
        self.buff = self.buff + message
    
    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(1024)
        if data:
            self.caller.parse_rpc(data)


    def writable(self):
        return bool(len(self.buff) > 0)


    def handle_write(self):
        sent = self.send(self.buff)
        self.buff = self.buff[sent:]

    @rpc_helpers.rpc_method
    @coroutine.coroutine
    def own_client_hello(self, hello):
        print 'client', hello
        yield coroutine.wait_sec(1)
        print 'call rpc'
        ret = yield coroutine.CallRpc(self.caller.server_hello, 'hello from client')
        print 'co wait_return_value', ret
        yield coroutine.WaitFrame(10)
        print 'wait 10 frame'

if __name__ == '__main__':
    client = Client('localhost', 13000)
    print 'client start'
    while True:
        asyncore.loop(timeout=0.1, count=1)
        timer.timer_mgr.update()

        
