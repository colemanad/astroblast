from constantly import ValueConstant, Values

# Message type constants
class MESSAGES(Values):
    NONE = ValueConstant("0")
    TEST = ValueConstant("1")
    TERMINATE = ValueConstant("-1")

# Base class for server & client modules
class GameModule():
    name = "unknown"
    shouldTerminate = False
    running = True

    def __init__(self, inQueue, outQueue):
        self.inQueue = inQueue
        self.outQueue = outQueue
    
    # Stub method for processing messages
    def processMsg(self, msg):
        pass
    
    # Stuf method for cleanup before termination
    def cleanup(self):
        pass
    
    def sendMsg(self, msg):
        print("%s: sending %s - %d" % (self.name, msg[0].name, msg[1]))
        self.outQueue.put(msg,True)
    
    def checkMsgs(self):
        while not self.inQueue.empty():
            # Check queue for new messages & respond to each
            msgType = MESSAGES.NONE
            msgContent = 0

            msgType, msgContent = self.inQueue.get_nowait()
            print("%s: received %s - %d" % (self.name, msgType.name, msgContent))
            self.inQueue.task_done()

            self.processMsg((msgType, msgContent))

            if msgType == MESSAGES.TERMINATE:
                self.shouldTerminate = True

            if self.shouldTerminate:
                self.cleanup()
                self.running = False

    def run(self):
        while self.running:
            self.checkMsgs()