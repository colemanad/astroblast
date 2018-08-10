#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

import pygame

from constants import GAME

class EntitySprite(pygame.sprite.Sprite):
    """Represents a sprite (2D image) displayed on the screen."""
    def __init__(self, images, initial_pos=(0, 0), initial_rot=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        pygame.sprite.Sprite.__init__(self)
        self.initialize(images, initial_pos, initial_rot, entity_id, entity_type)

    def initialize(self, images, initial_pos=(0, 0), initial_rot=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        self.images = images
        if self.images is not None:
            self.image, self.rect = self.images[int(initial_rot)]
        self.position = initial_pos
        self.rotation = initial_rot
        self.entity_id = entity_id
        self.entity_type = entity_type

    # TODO: delta time
    def update(self):
        """Update sprite position, rotation, etc."""
        self.image, self.rect = self.images[int(self.rotation)]
        self.rect = self.image.get_rect(center=self.position)

