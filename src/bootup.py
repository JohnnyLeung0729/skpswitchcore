# import switchcore
import uuid
import requests

# Get Rispi mac address uuid
def get_mac_address():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

# To deal with some base web exchange switch
class http_get_post():
    def do_get(self, uri, content):
        r = requests.get(uri, params=content)
        # print(r.url)          DebugInfo_print out
        # print(r.status_code)
        # print(r.text)
        return r

    def do_post(self, uri, content):
        r = requests.post(uri, data= content)
        # print(r.url)          DebugInfo_pring out
        # print(r.status_code)
        # print(r.text)
        return r


if __name__ == '__main__':
    # sh = switchcore.EveusbShell()
    # sh.do_ls("local")
    # sh.do_wait(2)

    hgp = http_get_post()
    rg = hgp.do_get("http://114.67.47.37:9418/tcis/blackBox/httpGet",{'pa1': 'hello world','pa2':99})
    rp = hgp.do_post("http://114.67.47.37:9418/tcis/blackBox/httpPost",{'pa1': 'hello world','pa2':88})
    print(rg.text)
    print(rp.text)






