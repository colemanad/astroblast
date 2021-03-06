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
from queue import Queue

import pygame
from pgu import gui

from dispatcher import Dispatcher
from server import GameServer
from networking import NetworkManager
from gamemodule import GameModule
from constants import GAME, MESSAGES, MSGCONTENT, NETWORK
from entitysprite import EntitySprite, SpriteInfo
from helperfuncs import get_lan_ip

# Path to assets directory
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
    """Load an image and pre-generate it rotated for 0 - 359 degrees"""

    image, rect = load_image(name, colorkey)
    images = {}
    for angle in range(360):
        rotated_image = pygame.transform.rotozoom(image, angle, 1)
        rotated_rect = rect
        images[angle] = (rotated_image, rotated_rect)
    return images

class GameClient(GameModule):
    """Contains game client and pyGame functionality."""

    def __init__(self):
        self.in_queue = Queue()
        self.dispatch_queue = Queue()
        GameModule.__init__(self, self.in_queue, self.dispatch_queue)

        self.name = 'Client'
        self.module_id = GAME.INVALID_ID
        self.server_id = GAME.LOCAL_SERVER_ID
        self.server_addr = '127.0.0.1'

        self.local_server_instance = None
        self.dispatch = None
        self.network_mgr = None

        self.connected = False

        # Initialize pyGame
        pygame.mixer.pre_init()
        pygame.init()
        self.screen = pygame.display.set_mode((GAME.WIDTH, GAME.HEIGHT))
        pygame.display.set_caption('AstroBlast!')
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)

        # Initialize pgu.gui
        # Title screen GUI
        self.title_app = gui.App()
        self.title_container = gui.Container(width=GAME.WIDTH, height=GAME.HEIGHT, x=0, y=0)
        self.title_sp_button = gui.Button("Single Player", width=150, height=100)
        self.title_sp_button.connect(gui.CLICK, self.gui_button_clicked, GAME.GUI_BUTTON_SP)
        self.title_container.add(self.title_sp_button, GAME.WIDTH/2 - 75, GAME.HEIGHT/2)
        self.title_mp_button = gui.Button("Multiplayer", width=150, height=100)
        self.title_mp_button.connect(gui.CLICK, self.gui_button_clicked, GAME.GUI_BUTTON_MP)
        self.title_container.add(self.title_mp_button, GAME.WIDTH/2 - 75, 2*GAME.HEIGHT/3)
        self.title_sp_button.connect(gui.CLICK, self.gui_button_clicked, GAME.GUI_BUTTON_MP)
        self.title_app.init(self.title_container, self.screen, pygame.rect.Rect(0, 0, GAME.WIDTH, GAME.HEIGHT))

        # Multiplayer Menu GUI
        self.multi_app = gui.App()
        self.multi_container = gui.Container(width=GAME.WIDTH, height=GAME.HEIGHT, x=0, y=0)
        self.multi_host_button = gui.Button("Host Game", width=100, height=100)
        self.multi_host_button.connect(gui.CLICK, self.gui_button_clicked, GAME.GUI_BUTTON_HOST)
        self.multi_container.add(self.multi_host_button, GAME.WIDTH/3, GAME.HEIGHT/3)
        self.multi_join_button = gui.Button("Join Game", width=100, height=100)
        self.multi_join_button.connect(gui.CLICK, self.gui_button_clicked, GAME.GUI_BUTTON_JOIN)
        self.multi_container.add(self.multi_join_button, GAME.WIDTH/3+150, GAME.HEIGHT/3)
        self.multi_back_button = gui.Button("Back", width=50, height=50)
        self.multi_back_button.connect(gui.CLICK, self.gui_button_clicked, GAME.GUI_BUTTON_BACK)
        self.multi_container.add(self.multi_back_button, 30, GAME.HEIGHT - 80)
        self.multi_ip_input = gui.Input("IP address")
        self.multi_container.add(self.multi_ip_input, 2*GAME.WIDTH/3, GAME.HEIGHT/3)
        self.multi_port_input = gui.Input("Port")
        self.multi_container.add(self.multi_port_input, 2*GAME.WIDTH/3, GAME.HEIGHT/3+50)
        self.multi_app.init(self.multi_container, self.screen, pygame.rect.Rect(0, 0, GAME.WIDTH, GAME.HEIGHT))

        # Mouse cursor
        cursor, rect = load_image('cursor.png')
        self.cursor = cursor

        # Images for sprites
        self.frames = {'ship':[load_image_all_rotations('ship.png'),
                               load_image_all_rotations('ship_thrust.png')],
                       'asteroid_big':[load_image_all_rotations('asteroid_big.png')],
                       'asteroid_med':[load_image_all_rotations('asteroid_med.png')],
                       'asteroid_small':[load_image_all_rotations('asteroid_small.png')],
                       'bullet_g':[load_image_all_rotations('bullet_g.png')],
                       'explosion':[load_image_all_rotations('explosion_1.png'),
                                    load_image_all_rotations('explosion_2.png')]}

        self.background = load_image('bg5.jpg')[0]

        # Sounds
        self.thrust_sound = pygame.mixer.Sound(path.join(ASSETSDIR, 'thrust.ogg'))
        self.thrust_sound.set_volume(1)
        self.shot_sound = pygame.mixer.Sound(path.join(ASSETSDIR, 'shot.wav'))
        self.shot_sound.set_volume(0.75)
        self.explode_sound = pygame.mixer.Sound(path.join(ASSETSDIR, 'explode.wav'))
        self.explode_sound.set_volume(1)

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

        self.game_state = GAME.STATE_TITLE

    def quit(self):
        """Sends quit message and halts client"""

        # Make sure Server and Dispatcher quit too
        if self.local_server_instance is not None:
            self.local_server_instance.running = False
        if self.dispatch is not None:
            self.dispatch.running = False
        if self.network_mgr is not None:
            self.network_mgr.running = False
        # self.send_msg(MESSAGES.TERMINATE, self.local_server_id)
        self.running = False
    
    def process_msg(self, msg_type, sender_id, msg_content):
        """Process an incoming message"""

        # Server accepted connection request
        if msg_type == MESSAGES.CONNECT_ACCEPT:
            self.connected = True
            self.send_msg(MESSAGES.CONNECT_SUCCESS, sender_id)
        
        # Server rejected connection request
        elif msg_type == MESSAGES.CONNECT_REJECT:
            self.log("Connection to server unsuccessful; connection rejected")
        
        # Server is disconnecting
        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.disconnect(False)
        
        # Server created an entity
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

                elif entity_type == GAME.ENTITY_PLAYERSHIP:
                    info = SpriteInfo(entity_type, self.frames['ship'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    pid = msg_content.get(MSGCONTENT.PLAYER_ID, None)
                    if pid is not None and pid == self.module_id:
                        self.player_entity_id = e.entity_id
                        self.player_alive = True

                elif entity_type == GAME.ENTITY_ASTEROID_BIG:
                    info = SpriteInfo(entity_type, self.frames['asteroid_big'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)

                elif entity_type == GAME.ENTITY_ASTEROID_MED:
                    info = SpriteInfo(entity_type, self.frames['asteroid_med'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)

                elif entity_type == GAME.ENTITY_ASTEROID_SMALL:
                    info = SpriteInfo(entity_type, self.frames['asteroid_small'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)

                elif entity_type == GAME.ENTITY_BULLET:
                    info = SpriteInfo(entity_type, self.frames['bullet_g'], 0, 0)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.shot_sound.play()

                elif entity_type == GAME.ENTITY_EXPLOSION:
                    info = SpriteInfo(entity_type, self.frames['explosion'], 1, 500)
                    e.initialize(info, pos, rot, entity_id, entity_type)
                    self.entities[e.entity_id] = e
                    self.sprites.add(e)
                    self.explode_sound.play()

        # Server destroyed an entity
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

        # An entity rotated by some amount
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
        
        # An entity moved
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
        
        # Player life count changed
        elif msg_type == MESSAGES.UPDATELIVES:
            expected_content = MSGCONTENT.PLAYER_LIVES
            if self.assert_msg_content(msg_type, msg_content, expected_content):
                self.player_lives = msg_content[MSGCONTENT.PLAYER_LIVES]
        
        # Player score changed
        elif msg_type == MESSAGES.UPDATESCORE:
            expected_content = MSGCONTENT.PLAYER_SCORE
            if self.assert_msg_content(msg_type, msg_content, expected_content):
                self.player_score = msg_content[MSGCONTENT.PLAYER_SCORE]
        
        # Server wants to change the client state to some other setting
        elif msg_type == MESSAGES.CHANGE_STATE:
            expected_content = MSGCONTENT.GAME_STATE
            if self.assert_msg_content(msg_type, msg_content, expected_content):
                self.game_state = msg_content[MSGCONTENT.GAME_STATE]

    def disconnect(self, should_send_signal=True):
        """Disconnect this client from a server"""

        if should_send_signal:
            self.send_msg(MESSAGES.SIGNAL_DISCONNECT, self.server_id, self.server_addr)
        
        self.connected = False

        self.log("Disconnected from server")
        self.module_id = GAME.INVALID_ID

        # Delete sprites
        self.sprites.empty()
        self.entities.clear()

    def gui_button_clicked(self, button_type):
        """Called when one of the buttons in the UI is clicked"""

        # Singleplayer button
        if button_type == GAME.GUI_BUTTON_SP:
            server_queue = Queue()
            remote_queue = Queue()
            # Create server and dispatcher
            self.dispatch = Dispatcher(self.dispatch_queue, server_queue, self.in_queue, remote_queue)
            self.dispatch.start()
            self.out_queue = self.dispatch_queue
            self.module_id = GAME.LOCAL_CLIENT_ID
            self.local_server_instance = GameServer(self.dispatch, server_queue)
            self.local_server_instance.start()
            self.server_id = self.local_server_instance.module_id
            self.server_addr = self.local_server_instance.addr
            # Start singleplayer by connecting to server
            self.send_msg(MESSAGES.REQCONNECT, self.server_id)

        # Switch to multiplayer menu
        elif button_type == GAME.GUI_BUTTON_MP:
            self.game_state = GAME.STATE_MULTIPLAYER_MENU

        # Host Multiplayer Session
        elif button_type == GAME.GUI_BUTTON_HOST:
            port = int(self.multi_port_input.value)
            server_queue = Queue()
            remote_queue = Queue()
            # Create server and dispatcher
            self.dispatch = Dispatcher(self.dispatch_queue, server_queue, self.in_queue, remote_queue)
            self.network_mgr = NetworkManager(remote_queue, self.dispatch, self.dispatch_queue, NETWORK.MODE_SERVER, port)
            self.dispatch.start()
            self.network_mgr.start()
            self.addr = self.network_mgr.addr
            self.server_addr = self.network_mgr.addr
            self.out_queue = self.dispatch_queue
            self.module_id = GAME.LOCAL_CLIENT_ID
            self.local_server_instance = GameServer(self.dispatch, server_queue)
            self.local_server_instance.start()
            self.server_id = GAME.LOCAL_SERVER_ID
            self.send_msg(MESSAGES.REQCONNECT, self.server_id)

        # Join a Multiplayer session
        elif button_type == GAME.GUI_BUTTON_JOIN:
            server_queue = Queue()
            remote_queue = Queue()
            self.server_addr = self.multi_ip_input.value
            port = int(self.multi_port_input.value)
            self.dispatch = Dispatcher(self.dispatch_queue, server_queue, self.in_queue, remote_queue)
            self.dispatch.mode = NETWORK.MODE_CLIENT
            self.network_mgr = NetworkManager(remote_queue, self.dispatch, self.dispatch_queue, NETWORK.MODE_CLIENT, port, self.server_addr)
            self.dispatch.start()
            self.network_mgr.start()
            self.out_queue = self.dispatch_queue
            self.addr = get_lan_ip()
            self.module_id = GAME.REMOTE_CLIENT_ID
            self.send_msg(MESSAGES.REQCONNECT, self.server_id)

        elif button_type == GAME.GUI_BUTTON_BACK:
            self.game_state = GAME.STATE_TITLE

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

            if self.game_state == GAME.STATE_TITLE:
                # Pass events to gui
                self.title_app.event(event)

            elif self.game_state == GAME.STATE_MULTIPLAYER_MENU:
                # Pass events to gui
                self.multi_app.event(event)

            else:
                # Handle keyboard events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_BACKSLASH:
                        pass
                    elif event.key == pygame.K_BACKSPACE:
                        self.disconnect()
                    elif event.key == pygame.K_LEFT:
                        self.send_msg(MESSAGES.INPUT_LEFT_DOWN, self.server_id)
                    elif event.key == pygame.K_RIGHT:
                        self.send_msg(MESSAGES.INPUT_RIGHT_DOWN, self.server_id)
                    elif event.key == pygame.K_UP:
                        pship = self.entities.get(self.player_entity_id)
                        if pship is not None:
                            pship.current_frame = 1
                            self.thrust_sound.play()
                        else:
                            self.thrust_sound.stop()
                        self.send_msg(MESSAGES.INPUT_THRUST_DOWN, self.server_id)
                    elif event.key == pygame.K_SPACE:
                        self.send_msg(MESSAGES.INPUT_SHOOT_DOWN, self.server_id)

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.send_msg(MESSAGES.INPUT_LEFT_UP, self.server_id)
                    elif event.key == pygame.K_RIGHT:
                        self.send_msg(MESSAGES.INPUT_RIGHT_UP, self.server_id)
                    elif event.key == pygame.K_UP:
                        pship = self.entities.get(self.player_entity_id)
                        if pship is not None:
                            pship.current_frame = 0
                        self.thrust_sound.stop()
                        self.send_msg(MESSAGES.INPUT_THRUST_UP, self.server_id)
                    elif event.key == pygame.K_SPACE:
                        self.send_msg(MESSAGES.INPUT_SHOOT_UP, self.server_id)

            if event.type == pygame.QUIT:
                self.quit()
        
        # Print the event name to stdout
        if events_found and GAME.PRINTEVENTS:
            print(event_str)
        
        # Clear surface
        self.screen.fill(GAME.BLACK)

        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw sprites on the surface
        # self.ship_sprite.rotation += 10
        self.sprites.update()
        self.sprites.draw(self.screen)

        # Text/GUI
        if (self.game_state == GAME.STATE_TITLE):
            # Draw GUI
            self.title_app.paint(self.screen)
            # Draw cursor when appropriate
            if pygame.mouse.get_focused():
                self.screen.blit(self.cursor, pygame.mouse.get_pos())
        elif (self.game_state == GAME.STATE_MULTIPLAYER_MENU):
            # Draw GUI
            self.multi_app.paint(self.screen)
            # Draw cursor when appropriate
            if pygame.mouse.get_focused():
                self.screen.blit(self.cursor, pygame.mouse.get_pos())

        # Draw labels
        normal_font = pygame.font.SysFont('Helvetica, Arial', 20, 1)
        larger_font = pygame.font.SysFont('Helvetica, Arial', 30, 1)
        huge_font = pygame.font.SysFont('Helvetica, Arial,', 150, 1)
        if (self.game_state == GAME.STATE_TITLE):
            width, height = huge_font.size('AstroBlast!')
            title_label = huge_font.render('AstroBlast!', 1, (0, 255, 0))
            self.screen.blit(title_label, (GAME.WIDTH/2 - width/2, height))
        if (self.game_state == GAME.STATE_IN_GAME or self.game_state == GAME.STATE_GAME_START or
            self.game_state == GAME.STATE_PLAYER_DIED):
            width, height = normal_font.size('Lives:')
            lives_label = normal_font.render('Lives: %d' % self.player_lives, 1, (255, 255, 0))
            self.screen.blit(lives_label, (20, 20))
            score_label = normal_font.render('Score: %d' % self.player_score, 1, (255, 255, 0))
            self.screen.blit(score_label, (20, height + 20))

        if self.game_state == GAME.STATE_GAME_START or self.game_state == GAME.STATE_GAME_OVER:
            width, height = normal_font.size('Press Fire (Spacebar)')
            start_label = normal_font.render('Press Fire (Spacebar)', 1, (255, 255, 0))
            self.screen.blit(start_label, (GAME.WIDTH/2 - width/2, GAME.HEIGHT/2))

        if self.game_state == GAME.STATE_GAME_OVER:
            width, height = larger_font.size('Game Over!')
            game_over_label = larger_font.render('Game Over!', 1, (255, 255, 0))
            self.screen.blit(game_over_label, (GAME.WIDTH/2 - width/2, GAME.HEIGHT/2 - 40))

        # Display surface to the screen
        pygame.display.flip()

        # Handles quitting/etc.
        super().update()
