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

class TestComponent():
    def update(self, parent, delta_time):
        # Update position
        parent.position[0] = (parent.position[0] + parent.velocity[0]*delta_time) % GAME.WIDTH
        parent.position[1] = (parent.position[1] + parent.velocity[1]*delta_time) % GAME.WIDTH

        # Update rotation
        parent.rotation += 1*delta_time
        while parent.rotation >= 360 or parent.rotation < 0:
            if parent.rotation >= 360:
                parent.rotation -= 360
            elif parent.rotation < 0:
                parent.rotation += 360

class AsteroidComponent():
    def update(self, parent, delta_time):
        # Update position
        parent.position[0] = (parent.position[0] + parent.velocity[0]*delta_time) % GAME.WIDTH
        parent.position[1] = (parent.position[1] + parent.velocity[1]*delta_time) % GAME.WIDTH

        # Update rotation
        parent.rotation += parent.angular_velocity*delta_time
        while parent.rotation >= 360 or parent.rotation < 0:
            if parent.rotation >= 360:
                parent.rotation -= 360
            elif parent.rotation < 0:
                parent.rotation += 360

class BulletComponent():
    def update(self, parent, delta_time):
        # Update position
        parent.position[0] = (parent.position[0] + parent.velocity[0]*delta_time) % GAME.WIDTH
        parent.position[1] = (parent.position[1] + parent.velocity[1]*delta_time) % GAME.WIDTH
