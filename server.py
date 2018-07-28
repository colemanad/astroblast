from threading import Thread

from gamemodule import GameModule
from constants import MESSAGES

class GameServer(GameModule, Thread):
    def __init__(self, inQueue, outQueue):
        Thread.__init__(self)
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"

    # Gets called at thread start
    def run(self):
        while self.running:
            self.check_msgs()
            self.update()
    
    def processMsg(self, msg):
        pass
    
    # Update game state
    def update(self):
        super().update()