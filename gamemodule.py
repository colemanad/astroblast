#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from constants import GAME, MESSAGES, MSGCONTENT
import queue

# Base class for server & client modules
class GameModule():
    """Base class for the client and server modules"""
    def __init__(self, in_queue, out_queue):
        # Name is used for logging
        self.name = "unknown"
        self.running = True

        # Queue of incoming messages
        self.in_queue = in_queue
        # Queue of outgoing messages
        self.out_queue = out_queue

        self.module_id = int(GAME.INVALID_ID.value)

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
        content_list = list(content)
        if self.module_id != int(GAME.DISPATCHER_ID.value):
            content_list.insert(0, (MSGCONTENT.ID, self.module_id))

        # Convert *args to a dictionary
        msg_content = {}
        for pair in content_list:
            msg_content[pair[0]] = pair[1]
        
        return msg_content

    def send_msg(self, msg_type, recipient_id, *content):
        """Send a message to counterpart (i.e., the client or server)"""
        # TODO: Update message format to include recipient ID
        # Message format:
        #   msg = (type, content)
        #   type is a constant from MESSAGES
        #   content is a list of pairs of integers
        #
        # TODO: Entity IDs
        # example: updating entity position client-side
        #   msg = (UPDATEPOS, [(ID, 12345), (X_POS, 14), (Y_POS, 15)])
        #   type = update position
        #   content = ID 12345, X = 14, Y = 15
        # (ID, X_POS, and Y_POS are all symbolic constants in constants.py)

        msg_content = self.prepare_msg(*content)
        msg_content[MSGCONTENT.RECIPIENT_ID] = recipient_id

        msg = (msg_type, msg_content)
        self.out_queue.put(msg, True)
        # self.log('sending %s from %d to %d' % (msg_type.name, msg_content[MSGCONTENT.ID], recipient_id))
    
    def check_msgs(self):
        """Process all incoming messages"""
        # Check queue for new messages & respond to each
        while True:
            try:
                msg_type, msg_content = self.in_queue.get_nowait()
                self.in_queue.task_done()

                sender_id = msg_content.get(MSGCONTENT.ID, None)
                # print("%s: received %s from %d to %d" % (self.name, msg_type.name, sender_id, msg_content[MSGCONTENT.RECIPIENT_ID]))
                if sender_id is not None:
                    self.process_msg(msg_type, sender_id, msg_content)

                if msg_type == MESSAGES.TERMINATE:
                    self.running = False

                elif msg_type == MESSAGES.PING:
                    self.send_msg(MESSAGES.PONG, sender_id)
            except queue.Empty:
                break

    def log(self, msg):
        """Print a log message to stdout, along with the module's ID"""
        print("%s(%d): %s" % (self.name, self.module_id, msg))
        # pass
    
    def assert_msg_content(self, msg_type, msg_content, *expected_content):
        found_all_expected_content = True
        for content_type in expected_content:
            if msg_content.get(content_type, None) is None:
                self.log('Received %s, did not find expected %s' % (msg_type.name, content_type.name))
                found_all_expected_content = False
        return found_all_expected_content
