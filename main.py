import multiprocessing
import epoller
import queueprocessor
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)
server_address = ('0.0.0.0', 10001)
server.bind(server_address)
server.listen(1)
q = multiprocessing.Queue()
printproc = multiprocessing.Process(target=queueprocessor.processdata, args=(q,))
printproc.start()
epoller.main(server,q)
