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

import time

import pygame

from gamemodule import GameModule
from constants import MESSAGES, MSGCONTENT, GAME

class GameServer(GameModule, Thread):
    """Implements the server module which manages the internal game state."""
    def __init__(self, inQueue, outQueue):
        Thread.__init__(self)
        GameModule.__init__(self, inQueue, outQueue)
        self.name = "Server"
        self.rot = 0
        self.ms_per_frame = 1.0 / (GAME.FPS / 2.0) * 1000.0
        self.last_ticks = 0
        self.ticks_since_last_update = 0

        self.clients = set()

        self.id = int(GAME.SERVER_ID.value)
        self.next_id = 1

    def run(self):
        """Gets called at thread start"""
        while self.running:
            self.check_msgs()
            self.update()
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""
        if msg_type == MESSAGES.REQCONNECT:
            if sender_id == int(GAME.INVALID_ID.value):
                # This is a new client, assign a new ID
                self.log("Registering new client with ID %d" % self.next_id)
                self.clients.add(self.next_id)
                # TODO: create game state object and associate it with new ID?
                self.send_msg(MESSAGES.CONNECT_ACCEPT, (MSGCONTENT.SET_ID, self.next_id))
                self.next_id += 1
            
            else:
                # Client already exists, reject connection attempt
                self.log("Client with ID %d already exists, rejecting connection request" % sender_id)
                # TODO: recipient ID/address?
                self.send_msg(MESSAGES.CONNECT_REJECT)
        
        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.log("Received disconnect signal from client %d" % sender_id)
            self.clients.discard(sender_id)

    
    def update(self):
        """Update internal game state"""
        current_ticks = pygame.time.get_ticks()
        diff = current_ticks - self.last_ticks
        self.ticks_since_last_update += diff
        # print(self.ticks_since_last_update)
        if self.ticks_since_last_update >= self.ms_per_frame:
            self.ticks_since_last_update -= self.ms_per_frame
            for client in self.clients:
                self.rot += 1
                while self.rot >= 360 or self.rot < 0:
                    if self.rot >= 360:
                        self.rot -= 360
                    elif self.rot < 0:
                        self.rot += 360
                self.send_msg(MESSAGES.UPDATEROT, (MSGCONTENT.ROTATION, self.rot))

            self.last_ticks = current_ticks
        
        else:
            # sleep the thread until it's time for the next update
            time.sleep(diff/1000.0)

        super().update()