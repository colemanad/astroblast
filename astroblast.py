#!/usr/bin/env Python
# @Author: Andrew Coleman

from queue import Queue
from threading import Thread
from constantly import ValueConstant, Values
from random import randint

# Message type constants
class MESSAGES(Values):
    TEST = ValueConstant("1")

# Base class for server & client modules
class GameModule(Thread):
    name = "unknown"

    def __init__(self, inQueue, outQueue):
        Thread.__init__(self)
        self.inQueue = inQueue
        self.outQueue = outQueue

    def run(self):
        while True:
            # Check queue for new messages & respond to each
            msgType, msgContent = self.inQueue.get()
            print("%s: received %s - %d" % (self.name, msgType.name, msgContent))
            self.inQueue.task_done()
            outMsg = (MESSAGES.TEST, randint(0, 64))
            print("%s: sending %s - %d" % (self.name, outMsg[0].name, outMsg[1]))
            self.outQueue.put(outMsg,True)

class GameServer(GameModule):
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"

class GameClient(GameModule):
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Client"

def main():
    # queue of messages for the server
    serverQueue = Queue()
    # queue of messages for the client
    clientQueue = Queue()
    # put a message in the client queue to get execution started
    clientQueue.put((MESSAGES.TEST, -1),True)

    server = GameServer(serverQueue, clientQueue)
    client = GameClient(clientQueue, serverQueue)

    server.start()
    client.start()

    # Just infinitely loop for now
    while True:
        pass

if __name__ == '__main__':
    main()