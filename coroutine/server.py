# -*- coding: utf-8 -*-

import asyncore
import socket
import rpc_helpers
import timer


class ServerHandler(asyncore.dispatcher, object):

    def __init__(self, socket):
        super(ServerHandler, self).__init__(socket)
        self.buff = ''
        self.caller = rpc_helpers.RpcProxy(self)
        self.caller.own_client_hello('hello from server')

    def handle_read(self):
        data = self.recv(1024)
        if data:
            self.caller.parse_rpc(data)


    def writable(self):
        return bool(len(self.buff) > 0)


    def handle_write(self):
        sent = self.send(self.buff)
        self.buff = self.buff[sent:]

    
    def send_to(self, message):
        self.buff = self.buff + message

    @rpc_helpers.rpc_method
    def server_hello(self, hello, co_callback):
        print 'server', hello
        timer.timer_mgr.add_timer(6, self.caller.rpc_return, co_callback, 'ret_value')
        print 'rpc return'
        self.caller.rpc_return(co_callback, 'ret_value')
        # self.caller.own_client_hello('hello from server')


class Server(asyncore.dispatcher):
    
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setblocking(False)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            handler = ServerHandler(sock)


if __name__ == '__main__':
    server = Server('localhost', 13000)
    print 'start server'
    while True:
        asyncore.loop(timeout=0.1, count=1)
        timer.timer_mgr.update()


