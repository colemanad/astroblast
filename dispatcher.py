#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from threading import Thread, Lock
import queue
from queue import Queue
import time

import pygame

from gamemodule import GameModule
from constants import MSGCONTENT, GAME, NETWORK

class Dispatcher(Thread, GameModule):
    """Message dispatch module.  Facilitates communication between threads."""

    def __init__(self, in_queue, server_queue, client_queue, remote_queue):
        Thread.__init__(self)
        out_queue = Queue()
        self.global_msg_queue = Queue()
        GameModule.__init__(self, in_queue, out_queue)

        self.name = "Dispatch"
        self.server_queue = server_queue
        self.client_queue = client_queue
        self.remote_queue = remote_queue
        self.clients = set()

        # Determines how message routing should behave in certain situations
        self.mode = NETWORK.MODE_SERVER

        self.running = True

        self.module_id = GAME.DISPATCHER_ID
        self.next_id = GAME.LOCAL_SERVER_ID + 1
        self.ids = [self.module_id, GAME.LOCAL_SERVER_ID]

        # Timing
        self.ms_per_frame = 1.0 / (GAME.FPS / 1.0) * 1000.0
        self.last_ticks = 0
        self.ticks_since_last_update = 0

        self.lock = Lock()

    def run(self):
        """Gets called at thread start"""
        while self.running:
            self.route_global_msgs()
            self.check_msgs()
            self.route_msgs()
            self.update()

    def route_global_msgs(self):
        """Route messages intended for all clients"""

        while True:
            try:
                msg_type, msg_content = self.global_msg_queue.get_nowait()
                self.global_msg_queue.task_done()
                for an_id in self.clients:
                    new_content = msg_content.copy()
                    new_content[MSGCONTENT.RECIPIENT_ID] = an_id
                    msg = (msg_type, new_content)
                    self.in_queue.put(msg, True)
            except queue.Empty:
                break

    def process_msg(self, msg_type, sender_id, msg_content):
        """Checks whether incoming messages have recipient IDs"""
        recipient_id = msg_content.pop(MSGCONTENT.RECIPIENT_ID)
        # Pass message on for routing
        if recipient_id is not None:
            self.send_msg(msg_type, recipient_id, *[(k, v) for k, v in msg_content.items()])
        else:
            self.log('Received %s message but recipient ID is missing' % msg_type.name)

    def route_msgs(self):
        """Redirect incoming messages to specific queues"""
        while not self.out_queue.empty():
            msg_type, msg_content = self.out_queue.get_nowait()
            # print(msg_type)
            self.out_queue.task_done()

            recipient_id = int(msg_content.get(MSGCONTENT.RECIPIENT_ID))
            if recipient_id is not None:
                msg = (msg_type, msg_content)
                if recipient_id == GAME.LOCAL_SERVER_ID:
                    # In server mode, messages for the server should go to the server component
                    if self.mode == NETWORK.MODE_SERVER:
                        self.server_queue.put(msg, True)
                    # In client mode, the server is remote, so direct its messages to the network outbox
                    else:
                        self.remote_queue.put(msg, True)
                elif recipient_id == GAME.LOCAL_CLIENT_ID:
                    # "Local" is relative to the server, so if we're on a remote client, then local client messages
                    #   should go to the remote client
                    if self.mode == NETWORK.MODE_SERVER:
                        self.client_queue.put(msg, True)
                    else:
                        self.remote_queue.put(msg, True)
                elif recipient_id == GAME.REMOTE_CLIENT_ID:
                    # Similarly, "Remote" is also relative
                    if self.mode == NETWORK.MODE_SERVER:
                        self.remote_queue.put(msg, True)
                    else:
                        self.client_queue.put(msg, True)
                else:
                    self.log('Recipient ID %d is not registered.' % (recipient_id))
            else:
                self.log('No recipient ID specified.  Message type: %s' % msg_type)
    
    def get_id(self):
        "Get either a discarded ID or hand out a new one"
        self.lock.acquire()
        for an_id in range(GAME.LOCAL_SERVER_ID+1, self.next_id):
            if an_id not in self.ids:
                # Found an unused id less than next_id
                self.log('Reusing id %d' % an_id)
                self.ids.append(an_id)
                self.lock.release()
                return an_id
        # didn't find any unused ids below next_id
        an_id = self.next_id
        self.ids.append(an_id)
        self.next_id += 1
        self.log('Generated id %d' % an_id)
        self.lock.release()
        return an_id

    def release_id(self, an_id):
        """ Mark an id as unused"""
        self.lock.acquire()
        if an_id in self.ids:
            self.ids.remove(an_id)
            self.log('Released id %d' % an_id)
        else:
            self.log('Tried to release id %d, but it was not taken' % an_id)
        self.lock.release()
