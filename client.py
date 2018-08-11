#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from os import path
import pygame

from gamemodule import GameModule
from constants import GAME, MESSAGES, MSGCONTENT
from entitysprite import EntitySprite, SpriteInfo

# Paths
ASSETSDIR = path.join(path.dirname(__file__), 'assets')

def load_image(name, colorkey=None):
    """Load an image with the specified filename."""
    filename = path.join(ASSETSDIR, name)
    try:
        image = pygame.image.load(filename).convert_alpha()
    except pygame.error as message:
        print('Cannot load image: %s' % name)
        raise SystemExit from message
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image, image.get_rect()

def load_image_all_rotations(name, colorkey=None):
    image, rect = load_image(name, colorkey)
    images = {}
    for angle in range(360):
        rotated_image = pygame.transform.rotozoom(image, angle, 1)
        rotated_rect = rect
        images[angle] = (rotated_image, rotated_rect)
    return images

class GameClient(GameModule):
    """Contains game client and pyGame functionality."""
    def __init__(self, inQueue, outQueue):
        GameModule.__init__(self, inQueue, outQueue)
        self.name = 'Client'
        self.module_id = int(GAME.LOCAL_CLIENT_ID.value)
        self.server_id = int(GAME.INVALID_ID.value)
        self.local_server_id = int(GAME.LOCAL_SERVER_ID.value)

        # Initialize pyGame
        pygame.init()
        self.screen = pygame.display.set_mode((GAME.WIDTH, GAME.HEIGHT))
        pygame.display.set_caption('AstroBlast!')
        self.clock = pygame.time.Clock()

        self.frames = {'ship':[load_image_all_rotations('ship.png'),
                               load_image_all_rotations('ship_thrust.png')],
                       'asteroid_big':[load_image_all_rotations('asteroid_big.png')],
                       'asteroid_med':[load_image_all_rotations('asteroid_med.png')],
                       'asteroid_small':[load_image_all_rotations('asteroid_small.png')],
                       'bullet_g':[load_image_all_rotations('bullet_g.png')],
                       'explosion':[load_image_all_rotations('explosion_1.png'),
                                    load_image_all_rotations('explosion_2.png')]}

        self.entities = {}
        self.unused_entities = []
        # Generate some unused entities
        for x in range(100):
            self.unused_entities.append(EntitySprite(None))
        self.sprites = pygame.sprite.Group()

        self.player_entity_id = -1
        self.player_alive = False
        self.player_lives = 0
        self.player_score = 0

        # self.game_state = GAME.STATE_TITLE
        self.game_state = GAME.STATE_GAME_START

    def quit(self):
        """Sends quit message and halts client"""
        self.send_msg(MESSAGES.TERMINATE, self.local_server_id)
        self.running = False
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""
        # self.log('received %s' % msg_type.name)
        if msg_type == MESSAGES.CONNECT_ACCEPT:
            if self.assert_msg_content(msg_type, msg_content, MSGCONTENT.SET_ID):
                new_id = msg_content[MSGCONTENT.SET_ID]
                self.module_id = new_id
                self.server_id = sender_id
                self.log("Connection to server successful, received client ID %d" % self.module_id)
                self.send_msg(MESSAGES.CONNECT_SUCCESS, sender_id)
        
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

                # Try to get an unused entity, or create one if there are none
                try:
                    e = self.unused_entities.pop()
                except IndexError:
                    e = EntitySprite(None)

                if entity_type == GAME.ENTITY_TEST:
                    info = SpriteInfo(entity_type, self.frames['ship'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

                elif entity_type == GAME.ENTITY_PLAYERSHIP:
                    info = SpriteInfo(entity_type, self.frames['ship'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    pid = msg_content.get(MSGCONTENT.PLAYER_ID, None)
                    if pid is not None and pid == self.module_id:
                        self.player_entity_id = e.entity_id
                        self.player_alive = True
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

                elif entity_type == GAME.ENTITY_ASTEROID_BIG:
                    info = SpriteInfo(entity_type, self.frames['asteroid_big'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

                elif entity_type == GAME.ENTITY_ASTEROID_MED:
                    info = SpriteInfo(entity_type, self.frames['asteroid_med'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

                elif entity_type == GAME.ENTITY_ASTEROID_SMALL:
                    info = SpriteInfo(entity_type, self.frames['asteroid_small'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

                elif entity_type == GAME.ENTITY_BULLET:
                    info = SpriteInfo(entity_type, self.frames['bullet_g'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

                elif entity_type == GAME.ENTITY_EXPLOSION:
                    info = SpriteInfo(entity_type, self.frames['explosion'], 1, 500)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.log('Added sprite for entity %d of type %s' % (e.entity_id, e.entity_type.name))

        elif msg_type == MESSAGES.DESTROY_ENTITY:
            if self.assert_msg_content(msg_type, msg_content, MSGCONTENT.ENTITY_ID):
                entity_id = msg_content[MSGCONTENT.ENTITY_ID]
                e = self.entities.pop(entity_id)
                if e is not None:
                    self.sprites.remove(e)
                    self.unused_entities.append(e)
                    if e.entity_id == self.player_entity_id:
                        self.player_alive = False
                else:
                    self.log('Received message to destroy sprite for entity %d, but sprite did not exist' % entity_id)

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
        
        elif msg_type == MESSAGES.UPDATEPOS:
            expected_content = (MSGCONTENT.X_POS, MSGCONTENT.Y_POS)
            if self.assert_msg_content(msg_type, msg_content, *expected_content):
                entity_id = msg_content[MSGCONTENT.ENTITY_ID]
                pos = (msg_content[MSGCONTENT.X_POS], msg_content[MSGCONTENT.Y_POS])
                e = self.entities.get(entity_id)
                if e is not None:
                    e.position = pos
                else:
                    self.log('Received message to update position for entity %d, but sprite does not exist' % entity_id)
        
        elif msg_type == MESSAGES.UPDATELIVES:
            expected_content = MSGCONTENT.PLAYER_LIVES
            if self.assert_msg_content(msg_type, msg_content, expected_content):
                self.player_lives = msg_content[MSGCONTENT.PLAYER_LIVES]
        
        elif msg_type == MESSAGES.UPDATESCORE:
            expected_content = MSGCONTENT.PLAYER_SCORE
            if self.assert_msg_content(msg_type, msg_content, expected_content):
                self.player_score = msg_content[MSGCONTENT.PLAYER_SCORE]
        
        elif msg_type == MESSAGES.CHANGE_STATE:
            expected_content = MSGCONTENT.GAME_STATE
            if self.assert_msg_content(msg_type, msg_content, expected_content):
                self.game_state = GAME.lookupByValue(str(msg_content[MSGCONTENT.GAME_STATE]))

    def disconnect(self, should_send_signal=True):
        """Disconnect this client from a server"""
        # TODO: Check if connected before proceeding
        if should_send_signal:
            self.send_msg(MESSAGES.SIGNAL_DISCONNECT, self.server_id)

        self.log("Disconnected from server")
        self.module_id = int(GAME.LOCAL_CLIENT_ID.value)

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
                elif event.key == pygame.K_BACKSLASH:
                    # Always use local server here, because this is just for testing purposes
                    self.send_msg(MESSAGES.REQCONNECT, self.local_server_id)
                elif event.key == pygame.K_BACKSPACE:
                    self.disconnect()
                elif event.key == pygame.K_LEFT:
                    self.send_msg(MESSAGES.INPUT_LEFT_DOWN, self.local_server_id)
                elif event.key == pygame.K_RIGHT:
                    self.send_msg(MESSAGES.INPUT_RIGHT_DOWN, self.local_server_id)
                elif event.key == pygame.K_UP:
                    pship = self.entities.get(self.player_entity_id)
                    if pship is not None:
                        pship.current_frame = 1
                    self.send_msg(MESSAGES.INPUT_THRUST_DOWN, self.local_server_id)
                elif event.key == pygame.K_SPACE:
                    self.send_msg(MESSAGES.INPUT_SHOOT_DOWN, self.local_server_id)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.send_msg(MESSAGES.INPUT_LEFT_UP, self.local_server_id)
                elif event.key == pygame.K_RIGHT:
                    self.send_msg(MESSAGES.INPUT_RIGHT_UP, self.local_server_id)
                elif event.key == pygame.K_UP:
                    pship = self.entities.get(self.player_entity_id)
                    if pship is not None:
                        pship.current_frame = 0
                    self.send_msg(MESSAGES.INPUT_THRUST_UP, self.local_server_id)
                elif event.key == pygame.K_SPACE:
                    self.send_msg(MESSAGES.INPUT_SHOOT_UP, self.local_server_id)

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

        # Text
        normal_font = pygame.font.SysFont("Helvetica", 20, 1)
        larger_font = pygame.font.SysFont("Helvetica", 30, 1)
        if self.game_state == GAME.STATE_IN_GAME:
            lives_label = normal_font.render("Lives: %d" % self.player_lives, 1, (255, 255, 0))
            self.screen.blit(lives_label, (50, 20))
            score_label = normal_font.render("Score: %d" % self.player_score, 1, (255, 255, 0))
            self.screen.blit(score_label, (50, 40))
        if self.game_state == GAME.STATE_GAME_START:
            lives_label = normal_font.render("Lives: %d" % self.player_lives, 1, (255, 255, 0))
            self.screen.blit(lives_label, (50, 20))
            score_label = normal_font.render("Score: %d" % self.player_score, 1, (255, 255, 0))
            self.screen.blit(score_label, (50, 40))
            start_label = normal_font.render("Press Fire (Spacebar)", 1, (255, 255, 0))
            self.screen.blit(start_label, (GAME.WIDTH/2 - 50, GAME.HEIGHT/2))
        if self.game_state == GAME.STATE_GAME_OVER:
            game_over_label = larger_font.render("Game Over!", 1, (255, 255, 0))
            press_fire_label = normal_font.render("Press Fire (Spacebar)", 1, (255, 255, 0))
            self.screen.blit(game_over_label, (GAME.WIDTH/2 - 35, GAME.HEIGHT/2 - 30))
            self.screen.blit(press_fire_label, (GAME.WIDTH/2 - 50, GAME.HEIGHT/2))


        # Display surface to the screen
        pygame.display.flip()

        # Handles quitting/etc.
        super().update()
