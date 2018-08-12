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
import random, math

import pygame

from gamemodule import GameModule
from constants import MESSAGES, MSGCONTENT, GAME
from entity import Entity
from inputstate import InputState, ClientInputState
import components


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

        self.player_death_delay = 1000
        self.player_death_ticks = {}
        self.player_shoot_delay = 333
        self.player_shoot_ticks = {}

        self.entities = {}
        self.unused_entities = []
        for x in range(100):
            self.unused_entities.append(Entity())
        self.asteroids = []
        self.bullets = {}

        self.player_entities = {}

        # TODO: Asteroids in background on title screen?
        self.game_state = GAME.STATE_IN_GAME
        self.client_states = {}
        self.input_states = {}
        self.client_scores = {}
        self.client_lives = {}

    def run(self):
        """Gets called at thread start"""
        # self.create_entity(GAME.ENTITY_TEST, (400, 300))
        while self.running:
            self.check_msgs()
            self.update()

    def set_client_state(self, client_id, new_state):
        self.client_states[client_id] = new_state
        self.send_msg(MESSAGES.CHANGE_STATE, client_id, (MSGCONTENT.GAME_STATE, int(new_state.value)))
    
    def set_client_lives(self, client_id, new_lives):
        self.client_lives[client_id] = new_lives
        self.send_msg(MESSAGES.UPDATELIVES, client_id, (MSGCONTENT.PLAYER_LIVES, new_lives))

    def set_client_score(self, client_id, new_score):
        self.client_scores[client_id] = new_score
        self.send_msg(MESSAGES.UPDATESCORE, client_id, (MSGCONTENT.PLAYER_SCORE, new_score))
    
    def all_bullets(self):
        bullets = []
        for sb in self.bullets.values():
            for b in sb:
                bullets.append(b)
        return bullets
    
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
            # Create input state for client
            self.input_states[sender_id] = ClientInputState(sender_id)
            self.set_client_state(sender_id, GAME.STATE_GAME_START)
            self.set_client_lives(sender_id, 3)
            self.set_client_score(sender_id, 0)
            self.player_death_ticks[sender_id] = 0
            self.player_shoot_ticks[sender_id] = 0
            self.bullets[sender_id] = []
            # Tell new client about all existing entities
            for e in self.entities.values():
                self.send_msg(MESSAGES.CREATE_ENTITY, sender_id, (MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ENTITY_TYPE, e.entity_type), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]), (MSGCONTENT.ROTATION, e.rotation))

        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            self.log("Received disconnect signal from client %d" % sender_id)
            self.dispatch.clients.discard(sender_id)
        
        elif msg_type == MESSAGES.INPUT_LEFT_DOWN:
            self.input_states[sender_id].left = True
        
        elif msg_type == MESSAGES.INPUT_LEFT_UP:
            self.input_states[sender_id].left = False

        elif msg_type == MESSAGES.INPUT_RIGHT_DOWN:
            self.input_states[sender_id].right = True
        
        elif msg_type == MESSAGES.INPUT_RIGHT_UP:
            self.input_states[sender_id].right = False

        elif msg_type == MESSAGES.INPUT_THRUST_DOWN:
            self.input_states[sender_id].thrust = True

        elif msg_type == MESSAGES.INPUT_THRUST_UP:
            self.input_states[sender_id].thrust = False

        elif msg_type == MESSAGES.INPUT_DOWN_DOWN:
            self.input_states[sender_id].down = True

        elif msg_type == MESSAGES.INPUT_DOWN_UP:
            self.input_states[sender_id].down = False

        elif msg_type == MESSAGES.INPUT_SHOOT_DOWN:
            self.input_states[sender_id].shoot = True

        elif msg_type == MESSAGES.INPUT_SHOOT_UP:
            self.input_states[sender_id].shoot = False
    
    def spawn_player(self, client_id):
        if self.player_entities.get(client_id) is None:
            # Create player entity at random position
            pos = self.random_position_on_screen(100)
            pship = self.create_entity(GAME.ENTITY_PLAYERSHIP, pos, 0, [0, 0], 0, 0, client_id)
            # Temporarily boost radius by 3x to make extra room around newly-spawned player
            pship.radius *= 3
            while (self.collide_group_and_entity(self.asteroids, pship, False) or
                    self.collide_group_and_entity(self.all_bullets(), pship, False)):
                    # Choose a different random spot
                    pship.position = self.random_position_on_screen(100)
            pship.radius /= 3
            self.player_entities[client_id] = pship

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
            self.ticks_since_last_update = 0

            # Process input
            if self.game_state == GAME.STATE_IN_GAME: 
                for input_state in list(self.input_states.values()):
                    client_state = self.client_states[input_state.client_id]
                    # print(client_state.name)
                    if client_state == GAME.STATE_IN_GAME:
                        if input_state.left and not input_state.right:
                            pship = self.player_entities.get(input_state.client_id)
                            if pship is not None:
                                pship.turn_direction = 1
                        elif input_state.right and not input_state.left:
                            pship = self.player_entities.get(input_state.client_id)
                            if pship is not None:
                                pship.turn_direction = -1
                        else:
                            pship = self.player_entities.get(input_state.client_id)
                            if pship is not None:
                                pship.turn_direction = 0

                        if input_state.thrust:
                            pship = self.player_entities.get(input_state.client_id)
                            if pship is not None:
                                pship.thrust = True
                        else:
                            pship = self.player_entities.get(input_state.client_id)
                            if pship is not None:
                                pship.thrust = False

                        if input_state.down:
                            # TODO: Menu stuff here
                            # TODO: actually, menu stuff should probably be client-side only for the most part
                            pass
                        else:
                            pass

                        if input_state.shoot:
                            # input_state.shoot = False
                            if current_ticks - self.player_shoot_ticks[input_state.client_id] >= self.player_shoot_delay:
                                self.player_shoot_ticks[input_state.client_id] = current_ticks
                                pship = self.player_entities.get(input_state.client_id)
                                if pship is not None:
                                    pos = [pship.position[0] + 30*pship.forward[0], pship.position[1] + 30*pship.forward[1]]
                                    vel = [400*pship.forward[0], 400*pship.forward[1]]
                                    self.create_entity(GAME.ENTITY_BULLET, pos, 0, vel, 0, 0, pship.player_id)

                    elif client_state == GAME.STATE_GAME_START:
                        if input_state.shoot:
                            input_state.shoot = False
                            # start game
                            self.set_client_state(input_state.client_id, GAME.STATE_IN_GAME)
                            self.spawn_player(input_state.client_id)

                    elif client_state == GAME.STATE_GAME_OVER:
                        if input_state.shoot:
                            input_state.shoot = False
                            self.set_client_state(input_state.client_id, GAME.STATE_IN_GAME)
                            self.set_client_lives(input_state.client_id, 3)
                            self.set_client_score(input_state.client_id, 0)
                            self.spawn_player(input_state.client_id)
                            self.populate_asteroids(5, True)

            # In Python, an empty sequence type (such as a list) evaluates as False
            if not self.asteroids:
                # TODO: Increase number of big asteroids each round
                self.populate_asteroids(4)

            # Asteroid-bullet collisions
            for client_id, bullets in self.bullets.items():
                collisions = self.collide_groups(self.asteroids, bullets)
                self.set_client_score(client_id, self.client_scores[client_id] + collisions * 10)

            # Player-asteroid and Player-bullet collisions
            self.collide_groups(self.asteroids, list(self.player_entities.values()))
            self.collide_groups(list(self.player_entities.values()), self.all_bullets())

            # Update entities
            to_destroy = []
            for e in list(self.entities.values()):
                e.update(diff/1000)
                if e.should_destroy:
                    to_destroy.append(e)
            
            for e in to_destroy:
                if e.entity_type == GAME.ENTITY_PLAYERSHIP:
                    self.set_client_lives(e.player_id, self.client_lives[e.player_id]-1)
                    self.set_client_state(e.player_id, GAME.STATE_PLAYER_DIED)
                    self.player_death_ticks[e.player_id] = current_ticks
                self.destroy_entity(e.entity_id)
            
            to_destroy.clear()

            # Update clients
            # Change client state after delay
            for client_id, client_state in self.client_states.items():
                if client_state == GAME.STATE_PLAYER_DIED:
                    death_ticks = self.player_death_ticks[client_id]
                    if current_ticks - death_ticks >= self.player_death_delay:
                        self.player_death_ticks[client_id] = 0
                        # Switch to game start or game over state, depending on lives
                        if self.client_lives[client_id] <= 0:
                            self.set_client_state(client_id, GAME.STATE_GAME_OVER)
                        else:
                            self.set_client_state(client_id, GAME.STATE_GAME_START)

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
    
    def random_position_on_screen(self, margin=0):
        return [random.randrange(margin, GAME.WIDTH-margin), random.randrange(margin, GAME.HEIGHT-margin)]

    def populate_asteroids(self, num, clear_existing=False):
        if clear_existing:
            to_remove = []
            for a in self.asteroids:
                to_remove.append(a)
            for a in to_remove:
                self.entities.pop(a.entity_id)
                self.asteroids.remove(a)
                self.send_global_msg(MESSAGES.DESTROY_ENTITY, (MSGCONTENT.ENTITY_ID, a.entity_id))
        for x in range(num):
            # Spawn an asteroid in a random spot
            pos = self.random_position_on_screen()
            asteroid = self.spawn_asteroid(pos, GAME.ENTITY_ASTEROID_BIG)
            # Temporarily boost radius of asteroid by 2x to avoid bad spawning locations
            asteroid.radius *= 2
            while (self.collide_group_and_entity(list(self.player_entities.values()), asteroid, False) or
                    self.collide_group_and_entity(self.all_bullets(), asteroid, False)):
                # Choose a different random spot
                asteroid.position = self.random_position_on_screen()
            asteroid.radius /= 2
    
    def spawn_asteroid(self, pos, kind):
        # Spawn an asteroid in a random spot
        rot = random.randrange(360)
        vel = [random.uniform(25, 75)*random.choice([-1, 1]), random.uniform(25, 75)*random.choice([-1, 1])]
        avel = random.uniform(15, 150)*random.choice([-1, 1])
        return self.create_entity(kind, pos, rot, vel, avel)

    def collide_group_and_entity(self, group, other, destroy=True):
        original_len = len(group)
        group = group.copy()

        for entity in group:
            if entity is not None and entity.collide(other):
                group.remove(entity)
                if destroy:
                    entity.should_destroy = True
                break
        return original_len - len(group)
    
    def collide_groups(self, group1, group2, destroy=True):
        group1 = group1.copy()
        count = 0

        for entity in group1:
            if self.collide_group_and_entity(group2, entity, destroy) > 0:
                count += 1
                group1.remove(entity)
                if destroy:
                    entity.should_destroy = True
        
        return count



    def create_entity(self, entity_type, pos=[0, 0], rot=0, vel=[0, 0], avel=0, radius=0, player_id=-5):
        try:
            e = self.unused_entities.pop()
            self.log('Reusing entity')
            e.initialize(pos, rot, vel, avel, radius, self.dispatch.get_id(), entity_type)
        except IndexError:
            self.log('No unused entities free, creating a new one')
            e = Entity(pos, rot, vel, avel, radius, self.dispatch.get_id(), entity_type)

        msg_content = [(MSGCONTENT.ENTITY_ID, e.entity_id), (MSGCONTENT.ENTITY_TYPE, e.entity_type), (MSGCONTENT.X_POS, e.position[0]), (MSGCONTENT.Y_POS, e.position[1]), (MSGCONTENT.ROTATION, e.rotation)]

        if entity_type == GAME.ENTITY_TEST:
            e.add_component(components.TestComponent())

        elif (entity_type == GAME.ENTITY_ASTEROID_BIG or
              entity_type == GAME.ENTITY_ASTEROID_MED or
              entity_type == GAME.ENTITY_ASTEROID_SMALL):
            if entity_type == GAME.ENTITY_ASTEROID_BIG:
                # TODO: get rid of these magic numbers
                e.radius = 58
                
            elif entity_type == GAME.ENTITY_ASTEROID_MED:
                e.radius = 21
                
            elif entity_type == GAME.ENTITY_ASTEROID_SMALL:
                e.radius = 14
            e.add_component(components.AsteroidComponent())
            self.asteroids.append(e)

        elif entity_type == GAME.ENTITY_BULLET:
            e.add_component(components.BulletComponent())
            e.radius = 5
            e.lifetime = 1
            self.bullets[player_id].append(e)
            
        elif entity_type == GAME.ENTITY_EXPLOSION:
            e.add_component(components.ExplosionComponent(0.5))
            
        elif entity_type == GAME.ENTITY_PLAYERSHIP:
            e.add_component(components.PlayerComponent())
            e.radius = 30
            msg_content.append((MSGCONTENT.PLAYER_ID, player_id))

        e.player_id = player_id
        e.visible = True
        e.active = True
        self.entities[e.entity_id] = e
        self.send_global_msg(MESSAGES.CREATE_ENTITY, *msg_content)
        self.log('Spawned entity %d of type %s' % (e.entity_id, e.entity_type.name))
        return e
    
    def destroy_entity(self, entity_id):
        e = self.entities.pop(entity_id, None)
        if e is not None:
            if e.entity_type == GAME.ENTITY_ASTEROID_BIG:
                for x in range(random.randrange(2, 4)):
                    pos = [e.position[0] + random.randrange(5, 20)*random.choice([-1, 1]), e.position[1] + random.randrange(5, 20)*random.choice([-1, 1])]
                    self.spawn_asteroid(pos, GAME.ENTITY_ASTEROID_MED)
                self.create_entity(GAME.ENTITY_EXPLOSION, e.position.copy())
                self.asteroids.remove(e)

            elif e.entity_type == GAME.ENTITY_ASTEROID_MED:
                for x in range(random.randrange(3, 5)):
                    pos = [e.position[0] + random.randrange(5, 20)*random.choice([-1, 1]), e.position[1] + random.randrange(5, 20)*random.choice([-1, 1])]
                    self.spawn_asteroid(pos, GAME.ENTITY_ASTEROID_SMALL)
                self.create_entity(GAME.ENTITY_EXPLOSION, e.position.copy())
                self.asteroids.remove(e)

            elif e.entity_type == GAME.ENTITY_ASTEROID_SMALL:
                self.create_entity(GAME.ENTITY_EXPLOSION, e.position.copy())
                self.asteroids.remove(e)

            elif e.entity_type == GAME.ENTITY_PLAYERSHIP:
                self.player_entities[e.player_id] = None
                self.create_entity(GAME.ENTITY_EXPLOSION, e.position.copy())
            
            elif e.entity_type == GAME.ENTITY_BULLET:
                self.bullets[e.player_id].remove(e)

            self.send_global_msg(MESSAGES.DESTROY_ENTITY, (MSGCONTENT.ENTITY_ID, e.entity_id))
            self.dispatch.release_id(e.entity_id)
            self.unused_entities.append(e)
