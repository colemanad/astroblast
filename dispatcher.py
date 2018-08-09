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
from queue import Queue

from gamemodule import GameModule
from constants import MESSAGES, MSGCONTENT, GAME

class Dispatcher(Thread, GameModule):
    def __init__(self, in_queue, server_queue, local_client_queue, remote_queue):
        Thread.__init__(self)
        out_queue = Queue()
        GameModule.__init__(self, in_queue, out_queue)

        self.name = "Dispatch"
        self.remote_queue = remote_queue
        # Dictionary of module IDs : outgoing queues
        self.out_queues = {int(GAME.LOCAL_SERVER_ID.value):server_queue,
                            int(GAME.LOCAL_CLIENT_ID.value):local_client_queue} 
        self.addresses = {}     # Dictionary of module IDs : remote IP addresses
        self.running = True

        self.module_id = int(GAME.DISPATCHER_ID.value)
        self.next_id = int(GAME.LOCAL_CLIENT_ID.value) + 1
        self.ids = [self.module_id]

        self.id_lock = Lock()

    def run(self):
        """Gets called at thread start"""
        while self.running:
            self.check_msgs()
            self.route_msgs()
            self.update()

    def process_msg(self, msg_type, sender_id, msg_content):
        should_send = True
        if msg_type == MESSAGES.REQCONNECT:
            # Check if sender id is already registered
            if sender_id in self.addresses:
                # sender ID is already registered, send CONNECT_REJECT and scrap REQCONNECT msg
                self.log('Received %s from %d, but sender ID %d is already registered' % (msg_type.name, sender_id, sender_id))
                self.send_msg(MESSAGES.CONNECT_REJECT, sender_id)
                should_send = False
            elif sender_id not in self.out_queues:
                # sender ID is remote and not yet registered
                # generate ID for sender and register it
                # TODO: Registration
                sender_id = self.get_id()
                msg_content[MSGCONTENT.ID] = sender_id

        elif msg_type == MESSAGES.CONNECT_REJECT:
            # Connection rejected, deregister ID if recipient is remote
            # TODO: Registration
            pass
        elif msg_type == MESSAGES.SIGNAL_DISCONNECT:
            # Connection rejected, deregister ID if sender is remote
            # TODO: Registration
            pass
        
        recipient_id = msg_content.pop(MSGCONTENT.RECIPIENT_ID, None)
        # Pass message on for routing
        if should_send:
            if recipient_id is not None:
                # self.log('passing %s from %d to %d' % (msg_type.name, sender_id, recipient_id))
                self.send_msg(msg_type, recipient_id, *[(k, v) for k, v in msg_content.items()])
            else:
                self.log('Received %s message but recipient ID is missing' % msg_type.name)


    def route_msgs(self):
        while not self.out_queue.empty():
            msg_type, msg_content = self.out_queue.get_nowait()
            self.out_queue.task_done()

            recipient_id = msg_content.get(MSGCONTENT.RECIPIENT_ID)
            if recipient_id is not None:
                if recipient_id in self.addresses:
                    # Recipient is on a remote client, get IP address
                    remote_address = self.addresses[recipient_id]
                    # TODO: Implement sending message via network module
                elif recipient_id in self.out_queues:
                    # Recipient is local
                    msg = (msg_type, msg_content)
                    self.out_queues[recipient_id].put(msg, True)
                
                else:
                    self.log('Recipient ID %d is not registered.  Message type: %s' % (recipient_id, msg_type.name))
            else:
                self.log('No recipient ID specified.  Message type: %s' % msg_type)
    
    def get_id(self):
        self.id_lock.acquire()
        for an_id in range(int(GAME.LOCAL_CLIENT_ID.value)+1, self.next_id):
            if an_id not in self.ids:
                # Found an unused id less than next_id
                self.log('Reusing id %d' % an_id)
                self.id_lock.release()
                return an_id
        # didn't find any unused ids below next_id
        an_id = self.next_id
        self.ids.append(an_id)
        self.next_id += 1
        self.log('Generated id %d' % an_id)
        self.id_lock.release()
        return an_id

    def release_id(self, an_id):
        self.id_lock.acquire()
        if an_id in self.ids:
            self.ids.remove(an_id)
            self.log('Released id %d' % an_id)
        else:
            self.log('Tried to release id %d, but it was not taken' % an_id)
        self.id_lock.release()
