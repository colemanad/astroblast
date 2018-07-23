#import pygame
from os import path

from gamemodule import GameModule, MESSAGES

# Paths
assets_dir = path.join(path.dirname(__file__), 'assets')

# Constants
# Will use fixed screen dimensions for now
WIDTH = 800
HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

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