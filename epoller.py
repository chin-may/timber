import os
import sys
import time
import Queue
import select
import socket
import threading
import tornado.ioloop
import multiprocessing
from tornado.web import logging as logger

WRITE = tornado.ioloop.IOLoop._EPOLLOUT
READ = tornado.ioloop.IOLoop._EPOLLIN | tornado.ioloop.IOLoop._EPOLLPRI
ERROR = tornado.ioloop.IOLoop._EPOLLERR | tornado.ioloop.IOLoop._EPOLLHUP

READ_ONLY = READ
READ_WRITE = READ | WRITE

fd_to_socket = {}
def exit(server, poller):
    logger.error("Quitting Server")
    for sock in fd_to_socket.itervalues():
        poller.unregister(sock)
        sock.close()

def process(poller, s, queues):
    queues[s].put("[Ok]")
    time.sleep(5)
    poller.modify(s, READ_WRITE)

def main(server):
    logger.warn("Serving on %s" % server)
    fd_to_socket[server.fileno()] = server
    try:
        poller = select.epoll()
    except:
        poller = tornado.ioloop._KQueue()

    poller.register(server, READ_ONLY)
    message_queues = {}

    while True:
        try:
            events = poller.poll(1)
        except KeyboardInterrupt:
            exit(server, poller)
            break

        for fd, flag in events:
            s = fd_to_socket[fd]
            if flag & READ:
                if s is server:
                    try:
                        connection, client_address = s.accept()
                    except Exception, e:
                        continue

                    logger.warn('New connection from %s' % str(client_address))
                    connection.setblocking(0)
                    fd_to_socket[connection.fileno()] = connection
                    poller.register(connection, READ_ONLY)
                    message_queues[connection] = Queue.Queue()

                else:
                    data = s.recv(1024)
                    if data:
                        process(poller, s, message_queues)
                    else:
                        poller.unregister(s)
                        del fd_to_socket[s.fileno()]
                        s.close()
                        del message_queues[s]

            elif flag & ERROR:
                poller.unregister(s)
                s.close()

            elif flag & WRITE:
                try:
                    next_msg = message_queues[s].get_nowait()
                except Queue.Empty:
                    poller.modify(s, READ_ONLY)
                else:
                    s.send(next_msg)

            elif flag & select.POLLERR:
                poller.unregister(s)
                del fd_to_socket[s.fileno()]
                s.close()
                del message_queues[s]

if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    server_address = ('0.0.0.0', 10001)
    server.bind(server_address)
    server.listen(1)
    #os.fork()
    #os.fork()
    main(server)
    #for i in xrange(3):
    #    p = multiprocessing.Process(target=main, args=(server,))
    #    p.start()
