"""minimal pure-python clone of
      https://github.com/travisghansen/fanout/

   For use with sparkleshare.  I haven't tested it with sparkleshare
   yet though.

   dedicated under cc0; see doc/cc0.txt for more info.
"""

import time

class Subscriptions(object):
    def __init__(self):
        self._subscriptions = {} # maps subscription-key to set of client.
        self._clients = {} #maps client to set of subscription-keys

    def addClient(self, client):
        self._clients[client] = set()
        self.addSubscription("all", client)

    def rmClient(self, client):
        for key in self._clients[client]:
            s = self._subscriptions[key]
            s.remove(client)
            if len(s) == 0:
                del self._subscriptions[key]
        del self._clients[client]

    def addSubscription(self, key, client):
        self._clients[client].add(key)
        self._subscriptions.setdefault(key, set()).add(client)

    def rmSubscription(self, key, client):
        try:
            s = self._subscriptions[key]
        except KeyError:
            return
        s.remove(client)
        if len(s) == 0:
            del self._subscriptions[key]
        self._clients[client].remove(key)

    def announce(self, key, message):
        try:
            s = self._subscriptions[key]
        except KeyError:
            return
        msg = "{0}!{1}\n".format(key, message)
        for client in s:
            client.send(msg)


class PubSubClient(object):
    COMMANDS = {"ping" : 0, "info" : 0,
                "subscribe" : 1, "unsubscribe" : 1,
                "announce" : 2}

    RESERVED_CHANNELS = ("all", "debug")
    def __init__(self, subscriptions):
        self._subs = subscriptions

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def run_command(self, command):
        c = command.strip().split(None, 2) # 2 is a kludge.
        if len(c) == 0:
            self.send("debug!empty_command\n")
        elif c[0] not in self.COMMANDS:
            self.send("debug!unknown_command\n")
        elif len(c) != self.COMMANDS[c[0]] + 1:
            self.send("debug!bad_num_arguments\n")
        else:
            getattr(self, "do_cmd_"+c[0])(*c[1:])

    def do_cmd_ping(self):
        self.send("{0}\n".format(int(time.time())))

    def do_cmd_info(self):
        self.send("implementation: pyfanout\n")

    def do_cmd_subscribe(self, key):
        if key in self.RESERVED_CHANNELS:
            self.send("debug!reserved_channel\n")
            return
        self._subs.addSubscription(key, self)

    def do_cmd_unsubscribe(self, key):
        if key in self.RESERVED_CHANNELS:
            self.send("debug!reserved_channel\n")
            return
        self._subs.rmSubscription(key, self)

    def do_cmd_announce(self, key, message):
        self._subs.announce(key, message)



