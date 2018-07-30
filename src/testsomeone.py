from psutil import net_if_addrs
import uuid
import ddl
import time
import Queue
import switchcore
import struct
import json
import os
import localrsa


q=Queue.Queue()



if __name__ == '__main__':
    # print(get_mac_address())

    # mt=ddl.monitoringThread(q,'hello')
    # mt.start()
    # print("start time:" + time.ctime())
    # while True:
    #     if not q.empty():
    #         print q.get()
    #         break





    # jd = '{"a":1,"b":2,"c":3,"d":4,"e":5}'
    # jl = json.loads(jd)
    # print(jl)
    # print(type(jl))
    # print(jl['e'])
    # jd2 = '{"macno":"123-123-123-123"}'
    # jl2 = json.loads(jd2)
    # jd3 = '{"a":99}'
    # jl3 = json.loads(jd3)
    # jl.update(jl2)
    # jl.update(jl3)
    # jdu = json.dumps(jl)
    # print(jdu)
    # print(type(jdu))


    # ope = os.path.exists('/etc/loc.dat')
    # print(ope)
    # if not ope:
    #     print('is false')
    # else:
    #     print('is true')


    # icode = localrsa.viflocalstatus()
    # print(icode)



    # sh=switchcore.EveusbShell()
    # # sh.do_ls('local')
    # sh.todols('local')
    # dicl = sh.zip_dev_dict()
    # print('dic len is :'+str(len(dicl)))


    # sh = switchcore.EveusbShell()
    # sh.do_share2('114.67.47.37', 30001, '1-1')
    # while True:
    #     sto = '123'


    # ,114.67.47.37,30001,usb1,1-1,,USB Flash Disk,,,,,
    # sh = switchcore.EveusbShell()
    # sh.do_unshare(',114.67.47.37,30001,usb1,1-1,,USB Flash Disk,,,,,')
    # sh.todols('shared')
    # sh.show_ports()
    # while True:
    #     so = 'so'

    # print(sh.do_license2('Beijing Zhongshui Information Network Co., Ltd.', 'F3X43DNK-4TG88NUI-3MSTX39F-MH3C77QK-9V8WZWLH-IPBIUCFC'))

    # print(localrsa.get_mac_address())
    # {"id": "1db081b329e848ff9a8067238f171b1f", "status": 0}   0 wait send
    # skma = localrsa.test_post(localrsa.baseaddr+localrsa.findkeycmd, {'blackBoxKey':'1db081b329e848ff9a8067238f171b1f'})
    # return 1 is add ok
    # skma = localrsa.test_post(localrsa.baseaddr+localrsa.regkeycmd, {'blackBoxKey':'1db081b329e848ff9a8067238f171b1f','macCode':'12319999-Xman'})

    # null is no vm
    # skma = localrsa.test_post(localrsa.baseaddr+localrsa.getvmcmd, {'blackBoxKey':'1db081b329e848ff9a8067238f171b1f','usbPort':'1'})

    # skma = localrsa.test_post(localrsa.baseaddr+localrsa.findfreevmcmd, {'blackBoxKey':'1db081b329e848ff9a8067238f171b1f'})

    skma = localrsa.test_post(localrsa.baseaddr+localrsa.bindvmcmd, {'id':'2222','blackBoxKey':'1db081b329e848ff9a8067238f171b2g','usbPort':'1'})

    # skma = localrsa.test_post(localrsa.baseaddr + localrsa.bindusbport, {'status': '', 'blackBoxKey': '1db081b329e848ff9a8067238f171b2g', 'usbPort': '2'})
    print(skma)

    # st = "192.168.1.1:8888" + " " + "2-2.1"
    # print(st)
    # lst = st.split(None,5)
    # print(lst)
    # ips,sets,ports = lst.pop(0).rpartition(':')
    # print(ips)
    # print(sets)
    # print(ports)