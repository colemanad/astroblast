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

from Crypto.PublicKey import RSA

from constants import NETWORK, GAME

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
    def __init__(self, in_queue, dispatch, dispatch_queue, mode, port=50000, remote_server_addr='127.0.0.1' num_unaccepted=5):
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
            dispatch.lock.acquire()
            local_to_remote_queue = dispatch.out_queues[GAME.LOCAL_CLIENT_ID]
            dispatch.lock.release()
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
        handle_messages(conn, self.RSA_key, remote_pub_key, remote_to_local_queue, local_to_remote_queue)
    
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
        converted_msg = csv_to_internal(msg)
        # TODO: Close thread on disconnect signal
        remote_to_local_queue.put(converted_msg)

    # Process outgoing messages
    while True:
        try:
            msg = local_to_remote_queue.get_nowait()
            local_to_remote_queue.task_done()
            # Convert message to CSV
            converted_msg = internal_to_csv(msg)
            # Encrypt message
            encrypted_msg = remote_pub_key.encrypt(converted_msg)
            # Send to remote client
            conn.send(str(encrypted_msg).encode())

        except queue.Empty:
            break

def internal_to_csv(msg):
    converted_msg = msg
    return converted_msg

def csv_to_internal(msg):
    converted_msg = msg
    return converted_msg
