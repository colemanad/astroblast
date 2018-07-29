#!/usr/bin/env python3

from os import path
import pygame

from gamemodule import GameModule
from constants import GAME, MESSAGES

# Paths
ASSETSDIR = path.join(path.dirname(__file__), 'assets')

class GameClient(GameModule):
    """Contains all game client and pyGame functionality."""
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = 'Client'

        # Initialize pyGame
        pygame.init()
        self.screen = pygame.display.set_mode((GAME.WIDTH, GAME.HEIGHT))
        pygame.display.set_caption('AstroBlast!')
        self.clock = pygame.time.Clock()

        # Create a sprite to draw on the screen
        ship = pygame.sprite.Sprite()
        image = self.load_image('ship.png')
        ship.image = image
        ship.rect = image.get_rect()
        ship.rect.x = 10
        ship.rect.y = 10
        self.ship_sprite = ship
        self.sprites = pygame.sprite.RenderPlain(self.ship_sprite)
    
    def load_image(self, name, colorkey=None):
        """Load an image with the specified filename."""
        filename = path.join(ASSETSDIR, name)
        try:
            image = pygame.image.load(filename)
        except pygame.error as message:
            print('Cannot load image: %s' % name)
            raise SystemExit from message
        image = image.convert()
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

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
        event_str = 'pyGame events: '
        for event in pygame.event.get():
            events_found = True
            event_str += pygame.event.event_name(event.type) + ', '
            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
            elif event.type == pygame.QUIT:
                self.quit()
        
        if events_found:
            print(event_str)
        
        # Draw something to the screen
        self.sprites.update()
        self.sprites.draw(self.screen)

        # Update pyGame
        pygame.display.update()
        pygame.display.flip()

        # Handles quitting/etc.
        super().update()
