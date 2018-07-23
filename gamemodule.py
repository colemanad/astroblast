from threading import Thread
from constantly import ValueConstant, Values
from random import randint

# Message type constants
class MESSAGES(Values):
    TEST = ValueConstant("1")
    TERMINATE = ValueConstant("-1")

# Base class for server & client modules
class GameModule(Thread):
    name = "unknown"
    shouldTerminate = False

    def __init__(self, inQueue, outQueue):
        Thread.__init__(self)
        self.inQueue = inQueue
        self.outQueue = outQueue
    
    # Stub method for processing messages
    def process(self, msg):
        pass
    
    # Stuf method for cleanup before termination
    def cleanup(self):
        pass
    
    def sendMsg(self, msg):
        print("%s: sending %s - %d" % (self.name, msg[0].name, msg[1]))
        self.outQueue.put(msg,True)

    def run(self):
        while True:
            # Check queue for new messages & respond to each
            msgType, msgContent = self.inQueue.get()
            print("%s: received %s - %d" % (self.name, msgType.name, msgContent))
            self.inQueue.task_done()
            outMsg = (MESSAGES.TEST, randint(0, 64))
            self.sendMsg(outMsg)

            self.process((msgType, msgContent))

            if msgType == MESSAGES.TERMINATE:
                self.shouldTerminate = True

            if self.shouldTerminate:
                self.cleanup
                break