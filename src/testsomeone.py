from psutil import net_if_addrs
import uuid


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
    print(get_mac_address())