#!/usr/bin/env Python
# @Author: Andrew Coleman

from queue import Queue
from threading import Thread

# Base class for server & client modules
class GameModule(Thread):
    def __init__(self, inQueue, outQueue):
        Thread.__init__(self)
        self.inQueue = inQueue
        self.outQueue = outQueue

class GameServer(GameModule):
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
    
    def run(self):
        while True:
            pass

class GameClient(GameModule):
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
    
    def run(self):
        while True:
            pass

def main():
    # queue of messages for the server
    serverQueue = Queue()
    # queue of messages for the client
    clientQueue = Queue()

    server = GameServer(serverQueue, clientQueue)
    client = GameClient(clientQueue, serverQueue)

if __name__ == '__main__':
    main()