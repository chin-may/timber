import Queue
import select
import socket

READ = select.POLLIN | select.POLLPRI
WRITE = select.POLLOUT
ERROR = select.POLLERR | select.POLLHUP


fd_to_socket = {}
message_queues = {}
servsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servsoc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servsoc.bind(('0.0.0.0',10001))
servsoc.listen(1)
poller = select.poll()
poller.register(servsoc,READ)
fd_to_socket[servsoc.fileno()] = servsoc
servsoc.setblocking(0)
print 'server started'
while True:
    try:
        events = poller.poll()
    except KeyboardInterrupt:
        print 'quitting'
        for soc in fd_to_socket.itervalues():
            poller.unregister(soc)
            soc.close()
        break
    for fd, flags in events:
        s = fd_to_socket[fd]
        if flags & READ:
            if s is servsoc:
                conn,addr = s.accept()
                poller.register(conn,READ)
                fd_to_socket[conn.fileno()] = conn
                conn.setblocking(0)
                message_queues[conn] = Queue.Queue()
                print 'connection received from', addr
            else:
                data = s.recv(1024)
                if data:
                    print data,'  received'
                    poller.modify(s,READ | WRITE)
                    try:
                        message_queues[s].put(data.upper())
                    except Queue.FULL:
                        print 'que full'
                        continue
                else:
                    print s,' closed'
                    poller.unregister(s)
                    del fd_to_socket[s.fileno()]
                    s.close()
                    del message_queues[s]
        elif flags & WRITE:
            try:
               nextmsg = message_queues[s].get_nowait()
            except Queue.Empty:
                poller.modify(s, READ)
            else:
                s.send(nextmsg)
                print nextmsg, ' sent'
        elif flags & ERROR:
            print s,' error. closing.'
            poller.unregister(s)
            del fd_to_socket[s]
            s.close()
            del message_queues[s]
