import json
import time

import localrsa
import switchcore
import uuid
import requests
import struct

rflag = True


def split_dev_info(devi):
    return devi.split(',')

# Change file string to binary and save or load
class binaryrw():
    def waittobinary(self,_path,_content):
        with open(_path, 'wb') as info:
            for x in _content:
                a = format(ord(x), 'b')
                info.write(a)

    def readfrombinary(self,_path):
        with open(_path, 'rb') as info:
            s = info.read()
            print(s)


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

_sysbootstr = '~ System bootup is start ~'

if __name__ == '__main__':
    print(_sysbootstr)
    # Init system
    sh = switchcore.EveusbShell()
    actbindflag = True  #is local file test to use vif
    actflag = True  #is have and not have skp to test use vif
    signalkey = ''  #skp port use no
    bindskma = ''  #use vm server info
    local_shared = False
    # vif local Dev sta
    sh.todols('local')
    loc = sh.zip_dev_dict()
    loct = json.dumps(loc)
    locj = json.loads(loct)
    for key in locj:
        if key == '1-1.1.2' or key == '1-1.1.3':
            print('is sys open port,can`t use to skp')
            continue
        if locj[key] == 'USBFlashDisk Aisino 64':
            signalkey = key
            actflag = False
    # Vif local file to back check shared port
    while actbindflag:
        sysstr = localrsa.viflocalstatus()
        tss = json.dumps(sysstr)
        gg = json.loads(tss)
        if gg['stacode'] == 404:
            # error file context
            template = '{"macno": "", "taxno": "", "initno": 0, "intno": ""}'
            print('file 404 error')
            localrsa.writtodiskuseoi(template)
        elif gg['stacode'] == 99:
            if len(gg['intno']) == 32:
                if actflag:
                    actbindflag = False
                    continue
                # all context is ok
                skma = localrsa.test_post(localrsa.baseaddr + localrsa.getvmcmd, {'blackBoxKey': gg['intno'], 'usbPort': signalkey})
                if(len(skma) < 1):
                    # Don`t have reg any vm
                    skma = localrsa.test_post(localrsa.baseaddr + localrsa.findfreevmcmd, {'blackBoxKey': gg['intno']})
                    try:
                        jcc = json.loads(skma)
                        print('have vm server to bind')
                        skma = localrsa.test_post(localrsa.baseaddr + localrsa.bindvmcmd, {'id': jcc['id'], 'blackBoxKey': gg['intno'], 'usbPort': signalkey})
                        # return '1' is bind ok
                    except ValueError, e:
                        if e.message == 'No JSON object could be decoded':
                            print('no vm server can be to use')
                else:
                    # Have reg vm info
                    print('have vm and ok vmwip port')
                    bindskma = skma
                    actbindflag = False
            else:
                # error intno update intno
                print('error intno -n71')
                cu = uuid.uuid1()
                cb = cu.__str__().split('-')
                cu = ''.join(cb)
                skma = localrsa.test_post(localrsa.baseaddr + localrsa.regkeycmd, {'blackBoxKey': cu.__str__(), 'macCode': localrsa.get_mac_address()})
                if skma == '0':
                    ccc = 'is error add led red'
                elif skma == '1':
                    ccc = 'is ok add led green'
                    jsonstr = json.loads('{"intno":"' + cu.__str__() + '","macno":"' + localrsa.get_mac_address() + '","initno":1}')
                    gg.update(jsonstr)
                    localrsa.writtodiskuseoi(json.dumps(gg))
                else:
                    ccc = 'unknow error led red'
        else:
            print('unknow error')


    # Check local shared Dev
    sh.todols('shared')
    tt = sh.show_ports()
    for tst in tt:
        ssr=split_dev_info(tst.__str__())
        if ssr[4] == signalkey:
            local_shared = True
            break

    if not local_shared:
        bs = json.loads(bindskma)
        sh.do_share2(bs['vmwip'], bs['port'], signalkey)





