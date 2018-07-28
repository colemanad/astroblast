from random import randint
from threading import Thread

from gamemodule import GameModule, MESSAGES

class GameServer(GameModule, Thread):
    def __init__(self, inQueue, outQueue, mainQueue):
        Thread.__init__(self)
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"
        self.mainQueue = mainQueue
    
    def processMsg(self, msg):
        if msg[0] == MESSAGES.TERMINATE:
            self.mainQueue.put((MESSAGES.TERMINATE, -1), True)
        # else:
        #     outMsg = (MESSAGES.TEST, randint(0, 64))
        #     self.sendMsg(outMsg)