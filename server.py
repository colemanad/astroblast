#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from threading import Thread

from gamemodule import GameModule
from constants import MESSAGES

class GameServer(GameModule, Thread):
    """Implements the server module which manages the internal game state."""
    def __init__(self, inQueue, outQueue):
        Thread.__init__(self)
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"

    def run(self):
        """Gets called at thread start"""
        while self.running:
            self.check_msgs()
            self.update()
    
    def processMsg(self, msg):
        """Process an incoming message"""
        pass
    
    def update(self):
        """Update internal game state"""
        super().update()