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

class Entity():
    def __init__(self, pos=(0, 0), rot=0, bounds=pygame.Rect(-0.5, -0.5, 1, 1), entity_id=0, entity_type=GAME.ENTITY_NONE):
        self.position = pos
        self.rotation = rot
        self.bounds = bounds
        self.visible = False
        self.active = False
        self.entity_id = entity_id
        self.entity_type = entity_type

