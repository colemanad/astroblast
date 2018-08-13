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
import ast

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from constants import MESSAGES, MSGCONTENT, NETWORK, GAME
from helperfuncs import get_lan_ip

# Buffer size: This should be a small power of 2.
BUFF_SIZE = 1024

class NetworkManager(Thread):
    """Handles and routes all internat traffic to and from remote clients/servers"""

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

        # Number of unaccepted connections to tolerate before rejecting connections
        self.num_unaccepted = num_unaccepted

        self.kill_all_threads = Event()

        # Generate a private RSA key
        self.RSA_key = RSA.generate(1024)

        self.name = 'Network'
        self.running = True

        self.remote_server_addr = remote_server_addr
        self.addr = '127.0.0.1'

    def run(self):
        """Gets called at thread start"""

        # Open a socket and give it a half-second timeout
        s = socket.socket()
        s.settimeout(0.5)

        # Get the LAN IP address for this machine
        self.addr = get_lan_ip()

        # Logic for listening for messages as a server
        if self.mode == NETWORK.MODE_SERVER:
            s.bind((self.addr, self.port))
            s.listen(self.num_unaccepted)

            running_threads = []

            while self.running:
                try:
                    # Accept incoming connections
                    c, addr = s.accept()
                    c.settimeout(0.5)

                    # We found a connection, so launch a new thread to listen/send to it
                    t = Thread(target=on_new_client, args=(c, self.dispatch, self.dispatch_queue, self.in_queue, self.kill_all_threads, self.RSA_key))
                    running_threads.append(t)
                    t.start()
                except socket.timeout:
                    pass
            
            self.kill_all_threads.set()
            s.close()
            for t in running_threads:
                t.join()
        
        else:
            # Running as a remote client
            conn = s

            # Connect to the remote server
            conn.connect((self.remote_server_addr, self.port))

            # Assign more idiomatic names to the queues, in this context
            local_to_remote_queue = self.in_queue
            remote_to_local_queue = self.dispatch_queue

            # Listen for the server's public key
            remote_pub_key = RSA.importKey(conn.recv(BUFF_SIZE))
            # Generate our public key and send it to the server
            local_pub_key = self.RSA_key.publickey().exportKey()
            conn.send(local_pub_key)
            while self.running:
                # Handle any incoming or outgoing messages until it's time to go
                handle_messages(conn, self.RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue)
            
            conn.close()

def on_new_client(conn, dispatch, remote_to_local_queue, local_to_remote_queue, kill_flag, RSA_key):
    """Launches whenever a new client connects to the server"""

    # Generate the public key and send it (server always sends first)
    local_pub_key = RSA_key.publickey().exportKey()
    conn.send(local_pub_key)

    # Wait for the client's public key in response
    remote_pub_key = RSA.importKey(conn.recv(BUFF_SIZE))

    while not kill_flag.is_set():
        # Handle any incoming and outgoing messages
        handle_messages(conn, RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue)
    
    conn.close()

def handle_messages(conn, RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue):
    """Shared code between the server & client implementations"""

    # Check for incoming messages
    try:
        msg = conn.recv(BUFF_SIZE)

        # Decrypt an incoming message
        # plaintext_msg = RSA_key.decrypt(msg)
        decryptor = PKCS1_OAEP.new(RSA_key)
        plaintext_msg = decryptor.decrypt(ast.literal_eval(str(msg)))

        # Now deserialize it from CSV format
        converted_msg = deserialize_msg(msg.decode())

        # And send it to the dispatcher
        remote_to_local_queue.put(converted_msg)
    except socket.timeout:
        pass

    # Process outgoing messages
    while True:
        try:
            msg = local_to_remote_queue.get_nowait()
            local_to_remote_queue.task_done()
            # Convert message to CSV
            converted_msg = serialize_msg(msg)
            # Encrypt message
            # encrypted_msg = remote_pub_key.encrypt(converted_msg, 32)
            encryptor = PKCS1_OAEP.new(remote_pub_key)
            encrypted_msg = encryptor.encrypt(converted_msg.encode('UTF-8'))
            # Send to remote client
            conn.send(converted_msg.encode('UTF-8'))

        except queue.Empty:
            break

def serialize_msg(msg):
    """Converts a message from our internal format into a comma-delimited string."""

    # The message comes in as a tuple of (integer, Dictionary)
    # The dictionary has integer keys and integer values
    # print(msg)
    msg_type, msg_content = msg
    # Convert the keys into a list of strings
    msgc_keys = [int(k) for k in list(msg_content.keys())]
    # Get a list of the values as strings, too
    msgc_values = [int(v) for v in list(msg_content.values())]
    # Convert the entire message into a list of interleaved values
    msg_list = list(chain([msg_type,], list(chain.from_iterable(zip(msgc_keys, msgc_values)))))
    # Finally, convert the list into a CSV string
    converted_msg = ','.join(str(x) for x in msg_list)
    return converted_msg

def deserialize_msg(msg):
    """Converts a message from a comma-delimited string into our internal format."""

    # The message comes in as a comma-delimited string of numbers
    # First, split the message into a list
    msg = msg.split(',')
    # Next, pop off the first element, which is the msg_type
    msg_type = int(msg.pop(0))
    # msg now consists of interleaved string representations of the keys and values of the msg_content dicitonary,
    #   so next we'll slice it into two separate lists consisting of the even elements (the keys)
    #   and the odd elements (the values)
    msg_keys = msg[::2]
    msg_values = msg[1::2]
    # Both the keys and values are still strings, so we need to convert the keys back into integers
    #   and the values back into integers
    msg_keys = [int(k) for k in msg_keys]
    msg_values = [int(v) for v in msg_values]
    # Now just zip them together and convert the result to a dictionary
    msg_content = dict(zip(msg_keys, msg_values))
    # Finally, combine msg_type and msg_content into a tuple to complete the internal message format.
    converted_msg = (msg_type, msg_content)
    return converted_msg
