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
from entity import Entity

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

        self.module_id = int(GAME.SERVER_ID.value)
        self.next_id = self.module_id + 1
        self.ids = [ self.module_id ]

        self.entities = {}

    def run(self):
        """Gets called at thread start"""
        self.create_entity(GAME.ENTITY_TEST, (400, 300))
        while self.running:
            self.check_msgs()
            self.update()
    
    def get_id(self):
        for an_id in range(self.next_id):
            if an_id not in self.ids:
                # Found an unused id less than next_id
                self.log('Reusing id %d' % an_id)
                return an_id
        # didn't find any unused ids below next_id
        an_id = self.next_id
        self.ids.append(an_id)
        self.next_id += 1
        self.log('Generated id %d' % an_id)
        return an_id

    def release_id(self, an_id):
        if an_id in self.ids:
            self.ids.remove(an_id)
            self.log('Released id %d' % an_id)
        else:
            self.log('Tried to release id %d, but it was not taken' % an_id)
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""
        # self.log('received %s' % msg_type.name)
        if msg_type == MESSAGES.REQCONNECT:
            if sender_id == int(GAME.INVALID_ID.value):
                # This is a new client, assign a new ID
                an_id = self.get_id()
                self.log("Registering new client with ID %d" % an_id)
                self.clients.add(an_id)
                # TODO: create game state object and associate it with new ID?
                self.send_msg(MESSAGES.CONNECT_ACCEPT, (MSGCONTENT.SET_ID, an_id))

            else:
                # Client already exists, reject connection attempt
                self.log("Client with ID %d already exists, rejecting connection request" % sender_id)
                # TODO: recipient ID/address?
                self.send_msg(MESSAGES.CONNECT_REJECT)
        
        elif msg_type == MESSAGES.CONNECT_SUCCESS:
            # Tell new client about all existing entities
            for e in self.entities.values():
                self.send_msg(MESSAGES.CREATE_ENTITY, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ENTITY_TYPE, e.entity_type), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]), (MSGCONTENT.ROTATION, e.rotation))

        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.log("Received disconnect signal from client %d" % sender_id)
            self.clients.discard(sender_id)
            self.release_id(sender_id)

    def update(self):
        """Update internal game state"""
        # Timing logic; ensure that update is no frequent than value specified by GAME.FPS
        #   (ticks are in ms)
        current_ticks = pygame.time.get_ticks()
        diff = current_ticks - self.last_ticks
        self.ticks_since_last_update += diff

        # Run update logic if enough time has elapsed
        if self.ticks_since_last_update >= self.ms_per_frame:
            self.ticks_since_last_update -= self.ms_per_frame

            # Update entities
            for e in self.entities.values():
                e.rotation += 1
                while e.rotation >= 360 or e.rotation < 0:
                    if e.rotation >= 360:
                        e.rotation -= 360
                    elif e.rotation < 0:
                        e.rotation += 360
            
            # Update clients
            # Send entity state to clients
            for e in self.entities.values():
                self.send_msg_all_clients(MESSAGES.UPDATEPOS, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]))
                self.send_msg_all_clients(MESSAGES.UPDATEROT, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ROTATION, e.rotation))

            # Reset ticks counter
            self.last_ticks = current_ticks
        
        else:
            # sleep the thread until it's time for the next update
            # not doing this can cause the main thread to become too busy with processing messages,
            #   preventing pygame from updating/drawing to the screen
            time.sleep(diff/1000.0)

        super().update()

    def send_msg_all_clients(self, msg_type, *msg_content):
        for client in self.clients:
            self.send_msg(msg_type, *msg_content)

    def create_entity(self, entity_type, pos=(0, 0), rot=0, bounds=pygame.Rect(-0.5, -0.5, 1, 1)):
        if entity_type == GAME.ENTITY_TEST:
            e = Entity(pos, rot, bounds, self.get_id(), entity_type)

        e.visible = True
        e.active = True
        self.entities[e.entity_id] = e
        self.send_msg_all_clients(MESSAGES.CREATE_ENTITY, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ENTITY_TYPE, e.entity_type), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]), (MSGCONTENT.ROTATION, e.rotation))
        self.log('Created entity %d of type %s' % (e.entity_id, e.entity_type.name))
    
    def destroy_entity(self, entity_id):
        e = self.entities.pop(entity_id, None)
        if e is not None:
            self.send_msg_all_clients(MESSAGES.DESTROY_ENTITY, (MSGCONTENT.ENTITY_ID, e.entity_id))
            self.release_id(e.entity_id)
