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

from constants import GAME

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
    def __init__(self, image_name, initial_pos=(0, 0), initial_rot=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(image_name)
        self.rect.topleft = initial_pos
        self.original = self.image
        self.rotation = initial_rot
        self.entity_id = entity_id
        self.entity_type = entity_type

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
