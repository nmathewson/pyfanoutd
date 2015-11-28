
import asyncore
import asynchat

import fanoutd
import socket


class AsynchatPubSubClient(asynchat.async_chat, fanoutd.PubSubClient):
    def __init__(self, sock, subscriptions):
        asynchat.async_chat.__init__(self, sock=sock)
        fanoutd.PubSubClient.__init__(self, subscriptions)
        self.inbuf = []
        self.set_terminator("\n")

    def collect_incoming_data(self, data):
        self.inbuf.append(data)

    def found_terminator(self):
        inp = "".join(self.inbuf)
        self.inbuf = []
        self.run_command(inp)

    def handle_close(self):
        self._subs.rmClient(self)
        self.close()

class AsyncoreFanoutServer(asyncore.dispatcher):
    def __init__(self, family, host, port, subs):
        asyncore.dispatcher.__init__(self)
        self._subs = subs
        self.create_socket(family, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(127)

    def handle_accept(self):
        pair = self.accept()
        if pair == None:
            return
        sock, addr = pair
        handler = AsynchatPubSubClient(sock, self._subs)
        self._subs.addClient(handler)

s = fanoutd.Subscriptions()
f = AsyncoreFanoutServer(socket.AF_INET, "localhost", 9999, s)

asyncore.loop()
