import pygame

from os import path
from random import randint

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

        # Initialize pyGame
        # self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        # pygame.display.set_caption("AstroBlast!")
        self.clock = pygame.time.Clock()
    
    # Sends quit message
    def quit(self):
        self.sendMsg((MESSAGES.TERMINATE, -1))
        self.shouldTerminate = True
    
    def processMsg(self, msg):
        pass
    
    # Update game state/input state
    def update(self):
        self.clock.tick(FPS)
        # print(self.clock.get_time())
        # print(self.clock.get_fps())
        # Handle pyGame events
        for event in pygame.event.get():
            print("event")
            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
            elif event.type == pygame.QUIT:
                self.quit()
        
        # Update pyGame
        pygame.display.update()
        pygame.display.flip()

        # self.msgCount += 1
        # if self.msgCount >= self.MSGLIMIT:
        #     self.quitGame()
        # else:
        # if not self.shouldTerminate:
        #     outMsg = (MESSAGES.TEST, randint(0, 64))
        #     self.sendMsg(outMsg)