#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from constants import MESSAGES

# Base class for server & client modules
class GameModule():
    """Base class for the client and server modules"""
    def __init__(self, inQueue, outQueue):
        # Name is used for logging
        self.name = "unknown"
        self.running = True

        # Queue of incoming messages
        self.in_queue = inQueue
        # Queue of outgoing messages
        self.out_queue = outQueue

    def cleanup(self):
        """Stub method for cleanup before termination"""
        pass

    def process_msg(self, msg):
        """Stub method for processing messages"""
        pass

    def update(self):
        """Method for updating module state.
        Overrides of this method should call this version before returning.
        """
        # self.send_msg((MESSAGES.PING, (MESSAGES.NONE, 0)))
        if not self.running:
            self.cleanup()
            print("%s quitting" % (self.name))

    def send_msg(self, msg):
        """Send a message to counterpart (i.e., the client or server)"""
        # TODO: Update message format to include recipient ID
        # Message format:
        #   msg = (type, content)
        #   type is a constant from MESSAGES
        #   content is a tuple of pairs of integers
        #
        # example: updating entity position client-side
        #   msg = (UPDATEPOS, ((ID, 12345), (X, 14), (Y, 15)))
        #   type = update position
        #   content = ID 12345, X = 14, Y = 15
        # (ID, X, and Y are all symbolic constants in constants.py)

        # print("%s: sending %s" % (self.name, msg[0].name))
        self.out_queue.put(msg, True)

    def check_msgs(self):
        """Process all incoming messages"""
        # Check queue for new messages & respond to each
        while not self.in_queue.empty():
            msg_type, msg_content = self.in_queue.get_nowait()
            # print("%s: received %s" % (self.name, msg_type.name))
            self.in_queue.task_done()

            self.process_msg((msg_type, msg_content))

            if msg_type == MESSAGES.TERMINATE:
                self.running = False

            elif msg_type == MESSAGES.PING:
                self.send_msg((MESSAGES.PONG, (MESSAGES.NONE, 0)))
