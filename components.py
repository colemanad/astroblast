#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

import math

from constants import GAME
import helperfuncs

class TestComponent():
    """Just a component for testing out the entity-component model"""
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

class PlayerComponent():
    """Contains (most of) the behavior specific to a the player ship"""

    def update(self, parent, delta_time):
        avel = 240
        acceleration = 10.0
        # friction = acceleration / 20.0
        friction = acceleration / 1600.0

        # Update rotation
        parent.angular_velocity = parent.turn_direction * avel
        parent.rotation += parent.angular_velocity*delta_time
        while parent.rotation >= 360 or parent.rotation < 0:
            if parent.rotation >= 360:
                parent.rotation -= 360
            elif parent.rotation < 0:
                parent.rotation += 360

        # Update velocity
        parent.forward = helperfuncs.angle_vector(math.radians(parent.rotation+90))
        if parent.thrust:
            parent.velocity[0] += parent.forward[0] * acceleration
            parent.velocity[1] += parent.forward[1] * acceleration
        
        # Apply friction
        parent.velocity[0] *= (1 - friction)
        parent.velocity[1] *= (1 - friction)

        # Update position
        parent.position[0] = (parent.position[0] + parent.velocity[0]*delta_time) % GAME.WIDTH
        parent.position[1] = (parent.position[1] + parent.velocity[1]*delta_time) % GAME.WIDTH

class AsteroidComponent():
    """Contains the behavior for an asteroid."""

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
    """Contains the behavior for a bullet"""
    def update(self, parent, delta_time):
        # Update position
        parent.position[0] = (parent.position[0] + parent.velocity[0]*delta_time) % GAME.WIDTH
        parent.position[1] = (parent.position[1] + parent.velocity[1]*delta_time) % GAME.WIDTH

class ExplosionComponent():
    """Contains the behavior (animation, that is) of an explosion"""
    def __init__(self, lifetime):
        self.lifetime = lifetime
        self.elapsed = 0

    def update(self, parent, delta_time):
        #Check lifetime
        self.elapsed += delta_time
        if self.elapsed >= self.lifetime:
            parent.should_destroy = True
