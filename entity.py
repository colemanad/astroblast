#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from constants import GAME
from helperfuncs import distance

class Entity():
    def __init__(self, pos=[0, 0], rot=0, vel=(0, 0), angular_vel=0, radius=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        self.initialize(pos, rot, vel, angular_vel, radius, entity_id, entity_type)

    def initialize(self, pos=[0, 0], rot=0, vel=(0, 0), angular_vel=0, radius=0, entity_id=0, entity_type=GAME.ENTITY_NONE):
        self.position = pos
        self.rotation = rot
        self.radius = radius
        self.velocity = vel
        self.angular_velocity = angular_vel
        self.visible = False
        self.active = False
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.components = []
        self.should_destroy = False
    
    def add_component(self, component):
        self.components.append(component)
    
    def update(self, delta_time):
        for c in self.components:
            c.update(self, delta_time)
    
    def collide(self, other):
        if distance(self.position, other.position) <= self.radius + other.radius:
            return True
        else:
            return False
