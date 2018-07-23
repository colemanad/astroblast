from gamemodule import GameModule, MESSAGES

class GameServer(GameModule):
    def __init__(self, inQueue, outQueue, mainQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"
        self.mainQueue = mainQueue
    
    def process(self, msg):
        if msg[0] == MESSAGES.TERMINATE:
            self.mainQueue.put((MESSAGES.TERMINATE, -1), True)