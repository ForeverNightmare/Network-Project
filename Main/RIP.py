import threading, time
from DS import *

global recmes


def dealwithmessageone(router: Router):
    while True:
        data, addr = router.rsocket.recvfrom(1024)
        packetr = message()
        packetr.changedump(bytes.decode(data))

        if packetr.ptype == 0:
            dealwithmessagetwo(router, packetr)
        elif packetr.ptype == 1:
            dealwithmessagethree(router, packetr)
        elif packetr.ptype == 2:
            dealwithmessagefour(router, packetr)


def dealwithmessagetwo(router: Router, packetr: message):
    router.forwardtext(packetr)


def sdvp(router: Router):
    while True:
        router.messagetime()
        print('This end-system is sending its distance vector')

        lock.acquire()
        try:
            for n in router.neighbors:
                if n != router.name:
                    n_addr = name_add(n)
                    sendpkt = message(router.address, n_addr, router.ri_ftable, 1)
                    router.ssocket.sendto(sendpkt.dodump().encode(), (n_addr.ip, n_addr.port))
        finally:
            lock.release()

        time.sleep(30)

def sdv(router:Router):
    router.messagetime()
    print('This end-system is sending its distance vector after updating')

    for n in router.nalive:

        if n != router.name:
            n_addr = name_add(n)
            sendpkt = message(router.address, n_addr, router.ri_ftable, 1)
            router.ssocket.sendto(sendpkt.dodump().encode(), (n_addr.ip, n_addr.port))


def dealwithmessagethree(router: Router, packetr: message):
    router_recv_from = add_name(packetr.src)

    router.messagetime()
    print('Receiving a DV packet from end-system:', router_recv_from)

    lock.acquire()
    try:

        if router_recv_from in router.neighbors.keys():
            router.nalive.add(router_recv_from)

        recmes[router_recv_from] = time.time()

        tempTable = router.ri_ftable.copy()
        changeft = False

        for i in range(len(packetr.payload)):
            inft = False
            getrec = sriptable(packetr.payload[i]['dest'], packetr.payload[i]['nextone'], packetr.payload[i]['distance'])

            for j in range(len(tempTable)):

                if getrec.dest == tempTable[j].dest:
                    inft = True

                    if getrec.distance < tempTable[j].distance-1:
                        router.ri_ftable[j].nextone = add_name(packetr.src)
                        router.ri_ftable[j].distance = getrec.distance + 1
                        changeft = True
                    else:
                        if tempTable[j].nextone == add_name(packetr.src):
                            if router.ri_ftable[j].distance != getrec.distance + 1:
                                router.ri_ftable[j].distance = getrec.distance + 1
                                changeft = True
                                
                                if router.ri_ftable[j].distance > 16:
                                    router.ri_ftable[j].distance = 16


            if not inft:
                getrec.nextone = router_recv_from
                getrec.distance += 1

                if getrec.distance > 16:
                    getrec.distance = 16

                router.ri_ftable.append(getrec)
                changeft = True

        if changeft:
            sdv(router)

            router.ripforwardtable()

    finally:
        lock.release()


def dealwithmessagefour(router: Router, packetr: message):
    router.sendtext(name_add(packetr.payload), 'Hello, I\'m ' + str(router.name) + '.', 0)


def isalive(router: Router):
    while True:
        lock.acquire()
        try:

            ralive = router.nalive.copy()

            for name in ralive:
                if time.time() - recmes[name] > 60:

                    router.messagetime()
                    print('The end-system finds that ,', name, 'is deactivated.')
                    router.nalive.remove(name)

                    for i in range(len(router.ri_ftable)):
                        if router.ri_ftable[i].dest == name or router.ri_ftable[i].nextone == name:
                            router.ri_ftable[i].distance = 16

                    sdv(router)
                    router.ripforwardtable()

        finally:
            lock.release()

        time.sleep(16)


if __name__ == "__main__":
    recmes = {}

    name = input('name of this activate end-system: ')
    a = Router(name)
    print('about this end-system ', a.name)
    print('ip:', a.address.ip)
    print('port:', a.address.port)

    a.ri_ftable.append(sriptable(dest=name, nextone='-', distance=0))
    
    a.nalive = set()

    lock = threading.Lock()
    t1 = threading.Thread(target=sdvp, args=(a,), name='send_dv')
    t1.start()
    t2 = threading.Thread(target=dealwithmessageone, args=(a,), name='listen')
    t2.start()
    t3 = threading.Thread(target=isalive, args=(a,), name='check_alive')
    t3.start()


