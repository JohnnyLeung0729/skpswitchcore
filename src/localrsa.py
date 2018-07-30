import os
import json
import struct
import uuid
import urllib
import urllib2


oslocfile_='/etc/loc.dat'

baseaddr='http://www.taxinfo123.com:8081'
findkeycmd='/tcis/blackBox/queryBlackBoxExistence'
regkeycmd='/tcis/blackBox/insertEquipment'
getvmcmd='/tcis/blackBox/queryByBlackBoxKey'
findfreevmcmd='/tcis/blackBox/queryIdleVirtualMachine'
bindvmcmd='/tcis/blackBox/binDingVirtualMachineIpPort'
bindusbport='/tcis/blackBox/inserBinDingNsrsbh'

def encode(s):
    return ' '.join([bin(ord(c)).replace('0b', '') for c in s])

def decode(s):
    return ''.join([chr(i) for i in [int(b, 2) for b in s.split(' ')]])

def getstatuscode(s):
    return '{"stacode":' + str(s) + '}'

def get_mac_address():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

def cmd_post_27ver(urls, args):
    print("recive args :" + args)
    header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
                   "Content-Type": "application/json"}
    req = urllib2.Request(url=urls, data=args, headers=header_dict)
    res = urllib2.urlopen(req)
    res = res.read()
    print("get report :" + res)

def test_post(urls, args):
    # request = urllib2.Request(urls, args)
    # response = urllib2.urlopen(request)
    # file = response.read()
    # res = json.loads(file)
    # if response.code != 200:
    #     return('error code' + response.code)
    # else:
    #     return res
    req = urllib2.Request(urls)
    data = urllib.urlencode(args)
    #enable cookie
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()



def cmd_get_27ver(urls, args):
    print("recive args :" + args)
    # output:password=admin&user=admin
    req = urllib2.Request(url='%s%s%s' % (urls, '?', args))
    res = urllib2.urlopen(req)
    res = res.read()
    print("get report :" + res)
    # output:login access

def writtodiskuseoi(j):
    # j = '{"initno":1,"taxno":"130982198307299115","intno":"xxxx-xxxx-xxxx-yyyy","macno":"1234-5678-9999"}'
    bb = encode(j)
    # print(bb)
    # print(decode(bb))
    bfile = open('/etc/loc.dat','wb')
    bfile.write(bb)
    bfile.close()

def viflocalstatus():
    # vif//locdat//  if not have then is illegal machine
    if not os.path.exists(oslocfile_):
        return json.loads(getstatuscode(404))

    # vif intno and initno
    # if can go and to return status code
    # {initno:1,taxno:"",intno:"",macno:""}
    # status code
    # //404  illegal machine
    # //118  illegal intno
    # //99  is ok
    # //11  unknow error
    # //00  don`t binding

    bfile = open(oslocfile_,'rb')
    keycontext = decode(bfile.read())
    bfile.close()
    # print(keycontext)
    try:
        osj = json.loads(keycontext)
        osdj = json.loads('{"stacode":99}')
        osj.update(osdj)
        return osj
    except ValueError, e:
        if e.message == 'No JSON object could be decoded':
            return json.loads(getstatuscode(404))
    except KeyError, e:
        if e.message == 'intno':
            return json.loads(getstatuscode(118))
        if e.message == 'initno':
            return json.loads(getstatuscode(00))
        if e.message == 'taxno':
            return json.loads(getstatuscode(00))
        if e.message == 'macno':
            return json.loads(getstatuscode(11))
        print(e.message)
    return

def opbodyfornet():
    # send to server vif intno\macno
    # get taxno\initno\server ip\server port\status code
    return

class localmain():
    locadic={}

    def __init__(self):
        return