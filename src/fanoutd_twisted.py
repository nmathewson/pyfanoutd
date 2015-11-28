
import fanoutd

import twisted.protocols.basic
import twisted.internet.protocol

class FanoutdProtocol(fanoutd.PubSubClient,
                      twisted.protocols.basic.LineReceiver):

    MAX_LENGTH = 256
    def __init__(self, subs):
        fanoutd.PubSubClient.__init__(self, subs)
        subs.addClient(self)

    def lineReceived(self, line):
        self.run_command(line)

    def send(self, data):
        self.transport.write(data)

    def connectionLost(self, *a, **k):
        self._subs.rmClient(self)

class FanoutdProtocolFactory(twisted.internet.protocol.ServerFactory):
    protocol = FanoutdProtocol
    def __init__(self, subs):
        self._subs = subs

    def buildProtocol(self, addr):
        return FanoutdProtocol(self._subs)

import twisted.internet.reactor

s = fanoutd.Subscriptions()
twisted.internet.reactor.listenTCP(9999, FanoutdProtocolFactory(s))
twisted.internet.reactor.run()

