import threading
import time
import socket
from DS import *

global router_graph, alive_graph, cost_graph, receive_graph


def receiving(router: Router):
    while True:
        data, addr = router.rsocket.recvfrom(1024)
        packetr = message()
        packetr.changedump(bytes.decode(data))

        if packetr.ptype == 0:
            receiving_text(router, packetr)
        elif packetr.ptype == 1:
            receiving_ospf(router, packetr)
        elif packetr.ptype == 2:
            receiving_call(router, packetr)


def receiving_ospf(router: Router, packetr: message):
    router_recv_from = addr_to_end(packetr.src)

    lock.acquire()
    try:
        receive_graph[router_recv_from] = time.time()

        router.messagetime()
        print('receive a OSPF packet from end-system ', router_recv_from)

        alive_graph.add(router_recv_from)
        router.messagetime()
        print('alive end-systems ', alive_graph)

        cost_graph[router_recv_from] = {}
        for n in packetr.payload.keys():
            cost_graph[router_recv_from][n] = packetr.payload[n][1]
    finally:
        lock.release()

    dijkstra(router)


def dijkstra(router: Router):
    visited = set()
    to_visited = alive_graph.copy()
    dis = {}
    before_hop = {}
    for v in to_visited:
        dis[v] = 99999
    dis[router.name] = 0

    while len(to_visited) > 0:
        min_router = ''
        min_cost = 99999
        for v in to_visited:
            if dis[v] <= min_cost:
                min_cost = dis[v]
                min_router = v

        to_visited.remove(min_router)
        visited.add(min_router)

        for v in to_visited:
            if v in cost_graph[min_router]:
                if dis[v] > dis[min_router] + cost_graph[min_router][v]:
                    dis[v] = dis[min_router] + cost_graph[min_router][v]
                    before_hop[v] = min_router
            elif min_router in cost_graph[v]:
                if dis[v] > dis[min_router] + cost_graph[v][min_router]:
                    dis[v] = dis[min_router] + cost_graph[v][min_router]
                    before_hop[v] = min_router

    fowardtable(router, before_hop)

    # print the new forwarding table
    # router.messagetime()
    # print('Updating the forward table ')
    router.ospfforwardtable()


def fowardtable(router: Router, before_hop: dict):
    # construct forwarding table of the parameter'router'
    next_step_from_current_router = {}

    for x in before_hop.keys():
        if before_hop[x] == router.name:
            next_step_from_current_router[x] = x
        else:
            temp = x
            while before_hop[temp] != router.name:
                temp = before_hop[temp]
            next_step_from_current_router[x] = temp

    router.os_ftable.clear()
    for k in next_step_from_current_router.keys():
        router.os_ftable.append(sosftable(dest=k, nextone=next_step_from_current_router[k]))


def alivetable(router: Router):
    while True:
        lock.acquire()
        try:

            aliveRouters = alive_graph.copy()

            for routerName in aliveRouters:
                if routerName != router.name:
                    if time.time() - receive_graph[routerName] > 60:
                        alive_graph.remove(routerName)
                        router.messagetime()
                        print('periodcally check...,', routerName, 'is down...')
                        dijkstra(router)
        finally:
            lock.release()

        time.sleep(20)


def receiving_call(router: Router, packetr: message):
    router.sendtext(name_add(packetr.payload), 'Hello, I\'m ' + str(router.name) + '.', 0)


def receiving_text(router: Router, packetr: message):
    router.forwardtext(packetr)


def broadcast(router: Router):
    while True:
        router.messagetime()
        print(' this end-system is broadcasting its link state')

        for n in router_graph:
            if n != router.name:
                n_addr = name_add(n)
                sendpkt = message(router.address, n_addr, router.neighbors, 1)
                router.ssocket.sendto(sendpkt.dodump().encode(), (n_addr.ip, n_addr.port))

        time.sleep(20)


def addr_to_end(addr: addr):
    for routerName in router_graph:
        if addr == name_add(routerName):
            return routerName


if __name__ == "__main__":
    router_graph = set(['1', '2', '3', '4', '5', '6'])
    alive_graph = set()
    cost_graph = {}
    receive_graph = {}

    routerName = input('name of this activate end-system: ')
    a = Router(routerName)
    print('about this end-system ', a.name)
    print('ip:', a.address.ip)
    print('port:', a.address.port)

    alive_graph.add(routerName)
    cost_graph[routerName] = {}
    for n in a.neighbors.keys():
        cost_graph[routerName][n] = a.neighbors[n][1]

    lock = threading.Lock()

    t1 = threading.Thread(target=broadcast, args=(a,), name='broadcast')
    t1.start()
    t2 = threading.Thread(target=receiving, args=(a,), name='listen')
    t2.start()
    t3 = threading.Thread(target=alivetable, args=(a,), name='check_alive')
    t3.start()
    