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

from gamemodule import GameModule
from constants import GAME, MESSAGES, MSGCONTENT
from entitysprite import EntitySprite

class GameClient(GameModule):
    """Contains game client and pyGame functionality."""
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = 'Client'

        # Initialize pyGame
        pygame.init()
        self.screen = pygame.display.set_mode((GAME.WIDTH, GAME.HEIGHT))
        pygame.display.set_caption('AstroBlast!')
        self.clock = pygame.time.Clock()

        # Create a sprite to draw on the screen
        self.entities = {}
        self.sprites = pygame.sprite.Group()
        # ship = EntitySprite('ship.png', (400, 300))
        # self.ship_sprite = ship
        # self.sprites = pygame.sprite.Group(self.ship_sprite)

    def quit(self):
        """Sends quit message and halts client"""
        self.send_msg(MESSAGES.TERMINATE)
        self.running = False
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""
        # self.log('received %s' % msg_type.name)
        if msg_type == MESSAGES.CONNECT_ACCEPT:
            if self.assert_msg_content(msg_type, msg_content, MSGCONTENT.SET_ID):
                new_id = msg_content[MSGCONTENT.SET_ID]
                self.module_id = new_id
                self.log("Connection to server successful, received client ID %d" % self.module_id)
                self.send_msg(MESSAGES.CONNECT_SUCCESS)
        
        elif msg_type == MESSAGES.CONNECT_REJECT:
            self.log("Connection to server unsuccessful; connection rejected")
        
        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.disconnect(False)
        
        elif msg_type == MESSAGES.CREATE_ENTITY:
            expected_content = (MSGCONTENT.ENTITY_ID, MSGCONTENT.ENTITY_TYPE, MSGCONTENT.X_POS, MSGCONTENT.Y_POS, MSGCONTENT.ROTATION)
            if self.assert_msg_content(msg_type, msg_content, *expected_content):
                entity_id = msg_content[MSGCONTENT.ENTITY_ID]
                entity_type = msg_content[MSGCONTENT.ENTITY_TYPE]
                pos = (msg_content[MSGCONTENT.X_POS], msg_content[MSGCONTENT.Y_POS])
                rot = msg_content[MSGCONTENT.ROTATION]

                if entity_type == GAME.ENTITY_TEST:
                    e = EntitySprite('ship.png', pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

        elif msg_type == MESSAGES.DESTROY_ENTITY:
            entity_id_content = msg_content[0]
            e = self.entities.pop(entity_id_content[1], None)
            if e is not None:
                self.sprites.remove(e)
            else:
                self.log('Received message to destroy sprite for entity %d, but sprite did not exist' % (entity_id_content[1]))

        elif msg_type == MESSAGES.UPDATEROT:
            expected_content = (MSGCONTENT.ENTITY_ID, MSGCONTENT.ROTATION)
            if self.assert_msg_content(msg_type, msg_content, *expected_content):
                entity_id = msg_content[MSGCONTENT.ENTITY_ID]
                rot = msg_content[MSGCONTENT.ROTATION]
                e = self.entities.get(entity_id)
                if e is not None:
                    e.rotation = rot
                else:
                    self.log('Received message to update rotation for entity %d, but sprite does not exist' % entity_id)

    def disconnect(self, should_send_signal=True):
        """Disconnect this client from a server"""
        # TODO: Check if connected before proceeding
        if should_send_signal:
            self.send_msg(MESSAGES.SIGNAL_DISCONNECT)

        self.log("Disconnected from server")
        self.module_id = int(GAME.INVALID_ID.value)

        # Delete sprites
        self.sprites.empty()
        self.entities.clear()

    def update(self):
        """Update game state/input state"""
        self.clock.tick(GAME.FPS)

        # Handle pyGame events
        events_found = False
        event_str = 'pyGame events: '
        for event in pygame.event.get():
            # Cache the event name for logging
            events_found = True
            event_str += pygame.event.event_name(event.type) + ', '

            # Handle keyboard events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_SPACE:
                    self.send_msg(MESSAGES.REQCONNECT)
                elif event.key == pygame.K_BACKSPACE:
                    self.disconnect()
            elif event.type == pygame.QUIT:
                self.quit()
        
        # Print the event name to stdout
        if events_found and GAME.PRINTEVENTS:
            print(event_str)
        
        # Clear surface
        self.screen.fill(GAME.BLACK)

        # Draw sprites on the surface
        # self.ship_sprite.rotation += 10
        self.sprites.update()
        self.sprites.draw(self.screen)

        # Display surface to the screen
        pygame.display.flip()

        # Handles quitting/etc.
        super().update()
