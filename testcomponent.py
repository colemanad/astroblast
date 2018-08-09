#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

class TestComponent():
    def update(self, parent):
        parent.rotation += 1
        while parent.rotation >= 360 or parent.rotation < 0:
            if parent.rotation >= 360:
                parent.rotation -= 360
            elif parent.rotation < 0:
                parent.rotation += 360