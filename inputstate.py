#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

class InputState:
    def __init__(self):
        self.left = False
        self.right = False
        self.thrust = False
        self.down = False
        self.shoot = False

class ClientInputState(InputState):
    def __init__(self, client_id):
        InputState.__init__(self)
        self.client_id = client_id
