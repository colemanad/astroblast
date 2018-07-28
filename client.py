from os import path
import pygame

from gamemodule import GameModule
from constants import GAME, MESSAGES

# Paths
ASSETSDIR = path.join(path.dirname(__file__), 'assets')

class GameClient(GameModule):
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Client"

        # Initialize pyGame
        pygame.init()
        self.screen = pygame.display.set_mode((GAME.WIDTH, GAME.HEIGHT))
        pygame.display.set_caption("AstroBlast!")
        self.clock = pygame.time.Clock()
    
    # Sends quit message
    def quit(self):
        self.send_msg((MESSAGES.TERMINATE, -1))
        self.running = False
    
    def processMsg(self, msg):
        pass
    
    # Update game state/input state
    def update(self):
        self.clock.tick(GAME.FPS)

        # Handle pyGame events
        events_found = False
        event_str = "pyGame events: "
        for event in pygame.event.get():
            events_found = True
            event_str += pygame.event.event_name(event.type) + ", "
            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
            elif event.type == pygame.QUIT:
                self.quit()
        
        if events_found:
            print(event_str)

        # Update pyGame
        pygame.display.update()
        pygame.display.flip()

        # Handles quitting/etc.
        super().update()
