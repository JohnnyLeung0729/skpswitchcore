from psutil import net_if_addrs
import uuid
import ddl
import time
import Queue


q=Queue.Queue()

def getlist():
    return 'helloworld'

def testformac():
    for k,v in net_if_addrs().items():
        for item in v:
            address = item[1]
            if '-' in address and len(address) == 17:
                print(address)

def get_mac_address():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

if __name__ == '__main__':
    # print(get_mac_address())

    # mt=ddl.monitoringThread(q,'hello')
    # mt.start()
    # print("start time:" + time.ctime())
    # while True:
    #     if not q.empty():
    #         print q.get()
    #         break

    st = "192.168.1.1:8888" + " " + "2-3.1"
    print(st)
    lst = st.split(None,5)
    print(lst)
    ips,sets,ports = lst.pop(0).rpartition(':')
    print(ips)
    print(sets)
    print(ports)