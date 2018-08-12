#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

import socket
from threading import Thread, Event
import queue
from queue import Queue
from itertools import chain

from Crypto.PublicKey import RSA

from constants import MESSAGES, MSGCONTENT, NETWORK, GAME

BUFF_SIZE = 1024

# Networking model:

# Networking management thread
#   server mode
#       loops, listening for new connections
#       when new connection comes in, launches new receiving/sending thread
#       then goes back to listening
#   client mode
#       establishes connection with remote server
#       loops, waiting for new messages and sending out pending ones

# Server send/recv thread
#   loops, grabbing incoming messages and sending outgoing ones

class NetworkManager(Thread):
    def __init__(self, in_queue, dispatch, dispatch_queue, mode, port=50000, remote_server_addr='127.0.0.1', num_unaccepted=5):
        Thread.__init__(self)
        # Queue of messages coming from dispatch
        self.in_queue = in_queue
        # Reference to message dispatcher
        self.dispatch = dispatch
        # Queue of translated messages going to dispatch
        self.dispatch_queue = dispatch_queue
        # Queue of csvized messages going out to remote
        self.remote_queue = Queue()

        self.mode = mode
        self.port = port
        self.num_unaccepted = num_unaccepted

        self.kill_all_threads = Event()

        self.RSA_key = RSA.generate(1024)

        self.name = 'Network'
        self.running = True

        self.remote_server_addr = remote_server_addr

        # Associates remote addresses with threads
        self.connections = {}

    def run(self):
        """Gets called at thread start"""
        s = socket.socket()
        s.settimeout(10)
        host = socket.gethostname()

        if self.mode == NETWORK.MODE_SERVER:
            s.bind((host, self.port))
            s.listen(self.num_unaccepted)
            
            running_threads = []

            while self.running:
                c, addr = s.accept()
                t = Thread(target=on_new_client, args=(c, self.dispatch, self.dispatch_queue, self.kill_all_threads, self.RSA_key))
                running_threads.append(t)
                t.start()
            
            self.kill_all_threads.set()
            s.close()
            for t in running_threads:
                t.join()
        
        else:
            # Client mode
            conn = s
            conn.connect((self.remote_server_addr))
            self.dispatch.lock.acquire()
            local_to_remote_queue = self.dispatch.out_queues[GAME.LOCAL_CLIENT_ID]
            self.dispatch.lock.release()
            remote_to_local_queue = self.dispatch_queue
            remote_pub_key = RSA.importKey(conn.recv(BUFF_SIZE))
            print('Received public key: ' + remote_pub_key.exportKey().decode('UTF-8'))
            local_pub_key = self.RSA_key.publickey().exportKey()
            conn.send(local_pub_key)
            print('Sent public key: ' + local_pub_key.exportKey().decode('UTF-8'))
            while self.running:
                handle_messages(conn, self.RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue)
            
            conn.close()

def on_new_client(conn, dispatch, remote_to_local_queue, kill_flag, RSA_key):
    local_to_remote_queue, client_id = dispatch.add_new_remote_client()
    local_pub_key = RSA_key.publickey().exportKey()
    conn.send(local_pub_key)
    print('Sent public key: ' + local_pub_key.exportKey().decode('UTF-8'))
    remote_pub_key = RSA.importKey(conn.recv(BUFF_SIZE))
    print('Received public key: ' + remote_pub_key.exportKey().decode('UTF-8'))
    while not kill_flag.is_set():
        handle_messages(conn, RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue)
    
    # Clean up
    dispatch.remove_remote_client(client_id)
    conn.close()

def handle_messages(conn, RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue):
    # Check for incoming messages
    msg = conn.recv(BUFF_SIZE)
    if msg:
        plaintext_msg = RSA_key.decrypt(msg)
        print("Got message: " + str(plaintext_msg))
        # Convert message to internal format and then dispatch
        converted_msg = deserialize_msg(msg)
        # TODO: Close thread on disconnect signal
        remote_to_local_queue.put(converted_msg)

    # Process outgoing messages
    while True:
        try:
            msg = local_to_remote_queue.get_nowait()
            local_to_remote_queue.task_done()
            # Convert message to CSV
            converted_msg = serialize_msg(msg)
            # Encrypt message
            encrypted_msg = remote_pub_key.encrypt(converted_msg)
            # Send to remote client
            conn.send(str(encrypted_msg).encode())

        except queue.Empty:
            break

def serialize_msg(msg):
    """Converts a message from our internal format into a comma-delimited string."""
    # The message comes in as a tuple of (ValueConstant, Dictionary)
    # The dictionary has ValueConstant keys and integer values
    msg_type, msg_content = msg
    # Convert the keys into a list of strings
    msgc_keys = [k.value for k in list(msg_content.keys())]
    # Get a list of the values as strings, too
    msgc_values = [int(v) for v in list(msg_content.values())]
    # Convert the entire message into a list of interleaved values
    msg_list = list(chain([msg_type.value,], list(chain.from_iterable(zip(msgc_keys, msgc_values)))))
    # Finally, convert the list into a CSV string
    converted_msg = ','.join(str(x) for x in msg_list)
    return converted_msg

def deserialize_msg(msg):
    """Converts a message from a comma-delimited string into our internal format."""
    # The message comes in as a comma-delimited string of numbers
    # First, split the message into a list
    msg = msg.split(',')
    # Next, pop off the first element, which is the msg_type, and convert it into a ValueConstant
    msg_type = MESSAGES.lookupByValue(msg.pop(0))
    # msg now consists of interleaved string representations of the keys and values of the msg_content dicitonary,
    #   so next we'll slice it into two separate lists consisting of the even elements (the keys)
    #   and the odd elements (the values)
    msg_keys = msg[::2]
    msg_values = msg[1::2]
    # Both the keys and values are still strings, so we need to convert the keys back into ValueConstants
    #   and the values back into integers
    msg_keys = [MSGCONTENT.lookupByValue(k) for k in msg_keys]
    msg_values = [int(v) for v in msg_values]
    # Now just zip them together and convert the result to a dictionary
    msg_content = dict(zip(msg_keys, msg_values))
    # Finally, combine msg_type and msg_content into a tuple to complete the internal message format.
    converted_msg = (msg_type, msg_content)
    return converted_msg
