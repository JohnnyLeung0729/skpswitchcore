
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
        self.sh=switchcore.EveusbShell() # init Eveusb 2 server


    def run(self):

        j=random.randint(10,20)
        time.sleep(j)
        self.q.put("i`m a thread,sleep %d s" % (j))