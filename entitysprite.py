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

class SpriteInfo():
    def __init__(self, entity_type, frames, max_frame, frame_ticks):
        self.entity_type = entity_type
        self.frames = frames
        self.max_frame = max_frame
        self.frame_ticks = frame_ticks

class EntitySprite(pygame.sprite.Sprite):
    """Represents a sprite (2D image) displayed on the screen."""
    def __init__(self, info, initial_pos=(0, 0), initial_rot=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        pygame.sprite.Sprite.__init__(self)
        self.ticks = 0
        self.image = None
        self.rect = None
        self.initialize(info, initial_pos, initial_rot, entity_id, entity_type)

    def initialize(self, info, initial_pos=(0, 0), initial_rot=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        self.current_frame = 0
        self.last_ticks = pygame.time.get_ticks()
        if info is not None:
            self.frames = info.frames
            self.max_frame = info.max_frame
            self.frame_ticks = info.frame_ticks
            if self.frames is not None:
                self.image, self.rect = self.frames[self.current_frame][int(initial_rot)]
        self.position = initial_pos
        self.rotation = initial_rot
        self.entity_id = entity_id
        self.entity_type = entity_type

    def update(self):
        """Update sprite position, rotation, etc."""
        try:
            self.image, self.rect = self.frames[self.current_frame][int(self.rotation)]
        except IndexError:
            print(str(self.current_frame)+' '+str(self.rotation))
        self.rect = self.image.get_rect(center=self.position)

        if self.entity_type == GAME.ENTITY_EXPLOSION:
            if self.current_frame < self.max_frame:
                current_ticks = pygame.time.get_ticks()
                diff = current_ticks - self.last_ticks
                self.ticks += diff
                if self.ticks >= self.frame_ticks:
                    self.ticks = 0
                    self.current_frame += 1

