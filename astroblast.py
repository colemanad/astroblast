#!/usr/bin/env Python
# @Author: Andrew Coleman

from queue import Queue
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

class GameServer(GameModule):
    def __init__(self, inQueue, outQueue, mainQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"
        self.mainQueue = mainQueue
    
    def process(self, msg):
        if msg[0] == MESSAGES.TERMINATE:
            self.mainQueue.put((MESSAGES.TERMINATE, -1), True)

class GameClient(GameModule):
    MSGLIMIT = 256
    msgCount = 0
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Client"
    
    def process(self, msg):
        self.msgCount += 1
        if self.msgCount >= self.MSGLIMIT:
            self.sendMsg((MESSAGES.TERMINATE, -1))
            self.shouldTerminate = True

def main():
    # queue of server->main process messages
    mainQueue = Queue()
    # queue of messages for the server
    serverQueue = Queue()
    # queue of messages for the client
    clientQueue = Queue()
    # put a message in the client queue to get execution started
    clientQueue.put((MESSAGES.TEST, -1),True)

    server = GameServer(serverQueue, clientQueue, mainQueue)
    client = GameClient(clientQueue, serverQueue)

    server.start()
    client.start()

    # Just infinitely loop for now
    while True:
        msgType, msgContent = mainQueue.get()
        if msgType == MESSAGES.TERMINATE:
            print("Exiting...")
            break

if __name__ == '__main__':
    main()