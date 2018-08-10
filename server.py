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
from queue import Queue
import random

import pygame

from gamemodule import GameModule
from constants import MESSAGES, MSGCONTENT, GAME
from entity import Entity
from testcomponent import TestComponent

class GameServer(GameModule, Thread):
    """Implements the server module which manages the internal game state."""
    def __init__(self, in_queue, dispatch):
        Thread.__init__(self)
        self.dispatch = dispatch
        self.global_msg_queue = dispatch.global_msg_queue
        GameModule.__init__(self, in_queue, dispatch.in_queue)
        self.name = "Server"
        self.module_id = int(GAME.LOCAL_SERVER_ID.value)

        self.ms_per_frame = 1.0 / (GAME.FPS / 1.0) * 1000.0
        self.last_ticks = 0
        self.ticks_since_last_update = 0
        self.test_auto_spawn_ticks = 0

        self.entities = {}
        self.unused_entities = []

    def run(self):
        """Gets called at thread start"""
        # self.create_entity(GAME.ENTITY_TEST, (400, 300))
        while self.running:
            self.check_msgs()
            self.update()
    
    def send_global_msg(self, msg_type, *content):
        msg_content = self.prepare_msg(*content)
        self.global_msg_queue.put((msg_type, msg_content))
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""
        self.log('received %s' % msg_type.name)
        if msg_type == MESSAGES.REQCONNECT:
            if sender_id not in self.dispatch.clients:
                self.log('Connection accepted for client %d' % sender_id)
                self.dispatch.clients.add(sender_id)
                # TODO: create game state object and associate it with new ID?
                self.send_msg(MESSAGES.CONNECT_ACCEPT, sender_id, (MSGCONTENT.SET_ID, sender_id))
            else:
                self.log('Client %d has already connected, additional connection refused' % sender_id)
                self.send_msg(MESSAGES.CONNECT_REJECT, sender_id)
        
        elif msg_type == MESSAGES.CONNECT_SUCCESS:
            # Tell new client about all existing entities
            for e in self.entities.values():
                self.send_msg(MESSAGES.CREATE_ENTITY, sender_id, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ENTITY_TYPE, e.entity_type), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]), (MSGCONTENT.ROTATION, e.rotation))

        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.log("Received disconnect signal from client %d" % sender_id)
            self.dispatch.clients.discard(sender_id)

    def update(self):
        """Update internal game state"""
        # Timing logic; ensure that update is no frequent than value specified by GAME.FPS
        #   (ticks are in ms)
        current_ticks = pygame.time.get_ticks()
        diff = current_ticks - self.last_ticks
        self.ticks_since_last_update += diff
        self.test_auto_spawn_ticks += diff

        # Run update logic if enough time has elapsed
        if self.ticks_since_last_update >= self.ms_per_frame:
            self.ticks_since_last_update -= self.ms_per_frame
            # self.log('update %d' % current_ticks)

            if self.test_auto_spawn_ticks >= 1000:
                self.test_auto_spawn_ticks = 0
                # destroy a test entity if 20 or more exist
                if len(self.entities) >= 20:
                    entity_id = random.choice(list(self.entities))
                    self.destroy_entity(entity_id)
                
                # spawn a test entity in a random spot
                pos = (random.randrange(800), random.randrange(600))
                self.create_entity(GAME.ENTITY_TEST, pos)

            # Update entities
            for e in self.entities.values():
                e.update()
            
            # Update clients
            # Send entity state to clients
            for e in self.entities.values():
                self.send_global_msg(MESSAGES.UPDATEPOS, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]))
                self.send_global_msg(MESSAGES.UPDATEROT, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ROTATION, e.rotation))

            # Reset ticks counter
            self.last_ticks = current_ticks
        
        else:
            # sleep the thread until it's time for the next update
            # not doing this can cause the main thread to become too busy with processing messages,
            #   preventing pygame from updating/drawing to the screen
            time.sleep(diff/1000.0)

        super().update()

    def create_entity(self, entity_type, pos=(0, 0), rot=0, bounds=pygame.Rect(-0.5, -0.5, 1, 1)):
        try:
            e = self.unused_entities.pop()
            self.log('Reusing entity')
            e.initialize(pos, rot, bounds, self.dispatch.get_id(), entity_type)
        except IndexError:
            self.log('No unused entities free, creating a new one')
            e = Entity(pos, rot, bounds, self.dispatch.get_id(), entity_type)

        if entity_type == GAME.ENTITY_TEST:
            e.add_component(TestComponent())

        e.visible = True
        e.active = True
        self.entities[e.entity_id] = e
        self.send_global_msg(MESSAGES.CREATE_ENTITY, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ENTITY_TYPE, e.entity_type), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]), (MSGCONTENT.ROTATION, e.rotation))
        self.log('Spawned entity %d of type %s' % (e.entity_id, e.entity_type.name))
    
    def destroy_entity(self, entity_id):
        e = self.entities.pop(entity_id, None)
        if e is not None:
            self.send_global_msg(MESSAGES.DESTROY_ENTITY, (MSGCONTENT.ENTITY_ID, e.entity_id))
            self.dispatch.release_id(e.entity_id)
            self.unused_entities.append(e)
