import socket
from DS import *


src = input("The src: ")
dest =  input("The des: ")

sadd = name_add(src)

csck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

payload = dest
sendpkt = message(addr('127.1.2.1', 0, 12343), sadd, payload, 2)
csck.sendto(sendpkt.dodump().encode(), (sadd.ip, sadd.port))
