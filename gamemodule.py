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
        if not self.running:
            self.cleanup()
            print("%s quitting" % (self.name))

    def send_msg(self, msg):
        """Send a message to counterpart (i.e., the client or server)"""
        print("%s: sending %s - %d" % (self.name, msg[0].name, msg[1]))
        self.out_queue.put(msg,True)

    def check_msgs(self):
        """Process all incoming messages"""
        # Check queue for new messages & respond to each
        while not self.in_queue.empty():
            msg_type, msg_content = self.in_queue.get_nowait()
            print("%s: received %s - %d" % (self.name, msg_type.name, msg_content))
            self.in_queue.task_done()

            self.process_msg((msg_type, msg_content))

            if msg_type == MESSAGES.TERMINATE:
                self.running = False
