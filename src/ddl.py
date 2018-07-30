
__author__="Johnny leung"
import threading
import random
import time
import switchcore
# import Queue
#
# q=Queue.Queue()

class monitoringThread(threading.Thread):
    def __init__(self,q,msg):
        super(monitoringThread,self).__init__()
        self.q=q
        self.msg=msg
        print(msg)
        self.sh=switchcore.EveusbShell() # init Eveusb to server


    def run(self):
        # j=random.randint(10,20)
        # time.sleep(j)
        # self.q.put("i`m a thread,sleep %d s" % (j))

        # List Drive for USB, every 3 seconds, if have change,then Op
        while True:
            # self.sh.todols('local')
            self.sh.todols('local')
            # get USB SKP Port and send code to Server
            diclst = self.sh.zip_dev_dict()  # Get USB List
            # Judge USB State
            print("dict len size is:" + str(len(diclst)))

            for k, v in diclst.items():
                print(k)
                print(v)
            # Server report status and give port number

            # Connect one by one to Server

            time.sleep(3)
            # break


        # Return to List Drive for USB