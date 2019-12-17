import json
import time
import socket


class addr:
    def __init__(self, ip, mask:int, port:int):
        self.ip = ip
        self.mask = mask
        self.port = port

    def __eq__(self, another):
        return self.ip == another.ip and self.mask == another.mask and self.port == another.port


class message:
    def __init__(self, src: addr=None, dest: addr=None, payload=None, ptype: int=None):
        self.src = src
        self.dest = dest
        self.payload = payload
        self.ptype = ptype

    def dodump(self):
        return json.dumps(self, default=lambda obj: obj.__dict__)

    def changedump(self, serialization):
        d = json.loads(serialization)
        self.src = addr(d['src']['ip'], d['src']['mask'], d['src']['port'])
        self.dest = addr(d['dest']['ip'], d['dest']['mask'], d['dest']['port'])
        self.payload = d['payload']
        self.ptype = int(d['ptype'])


class sosftable():
    def __init__(self, dest: str=None, nextone: str=None):
        self.dest = dest
        self.nextone = nextone

    def __str__(self):
        return "dest: " + str(self.dest) + ", next hop: " + str(self.nextone)


class sriptable():
    def __init__(self, dest:str=None, nextone:str=None, distance:int=0):
        self.dest = dest
        self.nextone = nextone
        self.distance = distance

    def __str__(self):
        return "dest: " + str(self.dest) + ", next hop: " + str(self.nextone) + ", hops-to-dest: " + str(self.distance)




def add_name(addr: addr):
    for routerName in {'1', '2', '3', '4', '5', '6'}:  # ...................
        if addr == name_add(routerName):
            return routerName


def name_add(name):    
    with open('../Settings/' + name + '.txt', 'r') as f:
        f.readline()

        ip = f.readline().strip()
        mask = int(f.readline().strip())
        port = int(f.readline().strip())
        return addr(ip, mask, port)


def find_neigh(name):
    neighbors = {}

    with open('../Settings/cost.txt', 'r') as f:
        line = ''
        for i in range(ord(name) - ord('1') + 1):
            line = f.readline().strip()

        count = 0
        for n in line.split():
            if int(n) > 0:
                neighbors[chr(49 + count)] = (name_add(chr(49 + count)), int(n))
            count += 1
    return neighbors


class Router():
    def __init__(self, name):
        self.name = name
        self.address = name_add(name)
        self.neighbors = find_neigh(name)
        
        self.rsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rsocket.bind((self.address.ip, self.address.port))
        self.ssocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.os_ftable = []
        self.ri_ftable = []


    def messagetime(self):
        print(time.strftime("%H:%M:%S", time.localtime()) + ' ', end='')


    def ospfforwardtable(self):
        print('forward table', self.name, ':')
        for i in range(len(self.os_ftable)):
            print(self.os_ftable[i])


    def ripforwardtable(self):
        print('forward table', self.name, ':')
        for i in range(len(self.ri_ftable)):
            print(self.ri_ftable[i])


    def sendtext(self, dest:addr, payload, ptype):
        sendpkt = message(self.address, dest, payload, ptype)
        self.forwardtext(sendpkt)


    def forwardtext(self, packetr: message):
        destp = add_name(packetr.dest)
        srcp = add_name(packetr.src)

        if destp == self.name:
            self.messagetime()
            print('Receiving a text from', srcp)
            print('The text is ', packetr.payload)
        else:
            if self.os_ftable:
                for i in range(len(self.os_ftable)):

                    if self.os_ftable[i].dest == destp:
                        hopn = name_add(self.os_ftable[i].nextone)
                        self.ssocket.sendto(packetr.dodump().encode(), (hopn.ip, hopn.port))

                        self.messagetime()
                        if srcp == self.name:
                            print('Sending a text to', destp)
                            print('The text is', packetr.payload)
                            print('Next hop is', self.os_ftable[i].nextone)
                        else:
                            print('Forwarding a text ', 'from ', srcp)
                            print('To ', destp)
                            print('Next hop is', self.os_ftable[i].nextone)

            elif self.ri_ftable:
                for i in range(len(self.ri_ftable)):

                    if self.ri_ftable[i].dest == destp:
                        hopn = name_add(self.ri_ftable[i].nextone)
                        self.ssocket.sendto(packetr.dodump().encode(), (hopn.ip, hopn.port))

                        self.messagetime()
                        if srcp == self.name:
                            print('Sending a text to ', destp)
                            print('The text is ', packetr.payload)
                            print('Next hop is', self.ri_ftable[i].nextone)
                        else:
                            print('Forwarding a text ', 'from ', srcp)
                            print('To ', destp)
                            print('Next hop is', self.ri_ftable[i].nextone)

