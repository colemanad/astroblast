#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

import queue

from constants import GAME, MESSAGES, MSGCONTENT
from helperfuncs import split_ip, rejoin_ip

# Base class for server & client modules
class GameModule():
    """Base class for the dispatch, client, and server modules"""
    def __init__(self, in_queue, out_queue):
        # Name is used for logging
        self.name = "unknown"
        self.running = True

        # Queue of incoming messages
        self.in_queue = in_queue
        # Queue of outgoing messages
        self.out_queue = out_queue

        self.module_id = GAME.INVALID_ID
        self.addr = '127.0.0.1'     # Default to localhost

    def cleanup(self):
        """Stub method for cleanup before termination"""
        pass

    def process_msg(self, msg_type, sender_id, msg_content):
        """Stub method for processing messages"""
        pass

    def update(self):
        """Method for updating module state.
        Overrides of this method should call this version before returning.
        """
        # self.send_msg((MESSAGES.PING, (MESSAGES.NONE, 0)))
        if not self.running:
            self.cleanup()
            self.log("quitting")
    
    def prepare_msg(self, *content):
        """Prepare an outgoing message by adding the sender ID to it"""
        content_list = list(content)
        if self.module_id != GAME.DISPATCHER_ID:
            content_list.insert(0, (MSGCONTENT.ID, self.module_id))

        # Convert *args to a dictionary
        msg_content = {}
        for pair in content_list:
            msg_content[pair[0]] = pair[1]
        
        return msg_content

    def send_msg(self, msg_type, recipient_id, *content):
        """Send a message to another module (e.g. server, client, dispatch)"""

        msg_content = self.prepare_msg(*content)
        msg_content[MSGCONTENT.RECIPIENT_ID] = recipient_id

        msg = (msg_type, msg_content)
        self.out_queue.put(msg, True)
    
    def check_msgs(self):
        """Process all incoming messages"""

        # Check queue for new messages & respond to each
        while True:
            try:
                msg_type, msg_content = self.in_queue.get_nowait()
                self.in_queue.task_done()

                sender_id = msg_content.get(MSGCONTENT.ID, None)
                if sender_id is not None:
                    self.process_msg(msg_type, sender_id, msg_content)

                if msg_type == MESSAGES.TERMINATE:
                    self.running = False

                elif msg_type == MESSAGES.PING:
                    self.send_msg(MESSAGES.PONG, sender_id)
            except queue.Empty:
                break

    # Sometimes useful, but slows the game down very badly
    def log(self, msg):
        """Print a log message to stdout, along with the module's ID"""

        # print("%s(%d): %s" % (self.name, self.module_id, msg))
        pass
    
    def assert_msg_content(self, msg_type, msg_content, *expected_content):
        """Make sure that a given msg_content has all of the sections you're looking for"""

        found_all_expected_content = True
        for content_type in expected_content:
            if msg_content.get(content_type, None) is None:
                self.log('Received %s, did not find expected %s' % (msg_type.name, content_type.name))
                found_all_expected_content = False
        return found_all_expected_content
