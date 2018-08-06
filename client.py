#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from os import path
import pygame

from gamemodule import GameModule
from constants import GAME, MESSAGES, MSGCONTENT

# Paths
ASSETSDIR = path.join(path.dirname(__file__), 'assets')

def load_image(name, colorkey=None):
    """Load an image with the specified filename."""
    filename = path.join(ASSETSDIR, name)
    try:
        image = pygame.image.load(filename).convert_alpha()
    except pygame.error as message:
        print('Cannot load image: %s' % name)
        raise SystemExit from message
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image, image.get_rect()

class EntitySprite(pygame.sprite.Sprite):
    """Represents a sprite (2D image) displayed on the screen."""
    def __init__(self, image_name, initial_pos=(0, 0)):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(image_name)
        self.rect.topleft = initial_pos
        self.original = self.image
        self.rotation = 0

    # TODO: delta time
    def update(self):
        """Update sprite position, rotation, etc."""
        # clamp rotation within [0, 360), but allow it to "wrap around"
        # while self.rotation >= 360 or self.rotation < 0:
            # if self.rotation >= 360:
                # self.rotation -= 360
            # elif self.rotation < 0:
                # self.rotation += 360
        center = self.rect.center
        # self.image = pygame.transform.rotate(self.original, self.rotation)
        self.image = pygame.transform.rotozoom(self.original, self.rotation, 1)
        self.rect = self.image.get_rect(center=center)

class GameClient(GameModule):
    """Contains game client and pyGame functionality."""
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = 'Client'

        # Initialize pyGame
        pygame.init()
        self.screen = pygame.display.set_mode((GAME.WIDTH, GAME.HEIGHT))
        pygame.display.set_caption('AstroBlast!')
        self.clock = pygame.time.Clock()

        # Create a sprite to draw on the screen
        ship = EntitySprite('ship.png', (400, 300))
        self.ship_sprite = ship
        self.sprites = pygame.sprite.Group(self.ship_sprite)

    def quit(self):
        """Sends quit message and halts client"""
        self.send_msg(MESSAGES.TERMINATE)
        self.running = False
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""
        if msg_type == MESSAGES.CONNECT_ACCEPT:
            if self.assert_msg_content_size(msg_type, msg_content, 1):
                new_id_content = msg_content[0]
                if self.assert_msg_content_type(msg_type, new_id_content[0], MSGCONTENT.SET_ID):
                    self.id = new_id_content[1]
                    self.log("Connection to server successful, received client ID %d" % self.id)
        
        elif msg_type == MESSAGES.CONNECT_REJECT:
            self.log("Connection to server unsuccessful; connection rejected")
        
        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.disconnect(False)

        elif msg_type == MESSAGES.UPDATEROT:
            self.ship_sprite.rotation = msg_content[0][1]

    def disconnect(self, should_send_signal=True):
        """Disconnect this client from a server"""
        # TODO: Check if connected before proceeding
        if should_send_signal:
            self.send_msg(MESSAGES.SIGNAL_DISCONNECT)

        self.log("Disconnected from server")
        self.id = int(GAME.INVALID_ID.value)

    def update(self):
        """Update game state/input state"""
        self.clock.tick(GAME.FPS)

        # Handle pyGame events
        events_found = False
        event_str = 'pyGame events: '
        for event in pygame.event.get():
            # Cache the event name for logging
            events_found = True
            event_str += pygame.event.event_name(event.type) + ', '

            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_SPACE:
                    self.send_msg(MESSAGES.REQCONNECT)
                elif event.key == pygame.K_BACKSPACE:
                    self.disconnect()
            elif event.type == pygame.QUIT:
                self.quit()
        
        # Print the event name to stdout
        if events_found and GAME.PRINTEVENTS:
            print(event_str)
        
        # Clear surface
        self.screen.fill(GAME.BLACK)

        # Draw sprites on the surface
        # self.ship_sprite.rotation += 10
        self.sprites.update()
        self.sprites.draw(self.screen)

        # Display surface to the screen
        pygame.display.flip()

        # Handles quitting/etc.
        super().update()
