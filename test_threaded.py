#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

# This is the network code from before it was integrated with the main codebase.
# It is preserved here for historical purposes.

import socket
from threading import Thread, Event
from sys import argv, stdin
from queue import Queue
from Crypto.PublicKey import RSA
from Crypto import Random
from time import sleep


BUFF_SIZE = 1024


# define networking functions

def recv_conn(port):
    """Server module receives connection"""
    s = socket.socket()
    s.settimeout(10)
    s.bind(("127.0.0.1", port))
    s.listen(1)
    return s

def make_conn(ip, port):
    """client module connects"""
    s = socket.socket()
    s.settimeout(10) 
    s.connect((ip, port))
    return s

def get_messages(conn, kill_flag, our_key):
    """Gets a message from the network connection and puts it in the in_q"""
    # receive public key
    global their_public_key
    their_public_key = RSA.importKey(conn.recv(BUFF_SIZE))
    print("Received public key: " + their_public_key.exportKey().decode("UTF-8"))
    while not kill_flag.is_set():
        msg = conn.recv(BUFF_SIZE)
        if not msg:
            print("No more messages. Breaking")
            break
        # decrypt message with our private key
        msg = eval(msg)
        plaintext_msg = our_key.decrypt(msg)
        print("Got message: " + str(plaintext_msg))
        plaintext_int = int(plaintext_msg)
        in_q.put(plaintext_int)
    if kill_flag.is_set():
        print("get_messages: Kill message recieved")

def send_message(conn, kill_flag, our_key):
    """Sends messages over the network from the out_q"""
    # send public key
    global their_public_key
    our_pub_key = RSA_key.publickey().exportKey()
    conn.send(RSA_key.publickey().exportKey())
    print("Sent our public key: " + our_pub_key.decode("UTF-8"))
    while not kill_flag.is_set():
        while their_public_key is None:
            print("Waiting to get public key")
        raw_msg = out_q.get()
        print("Sending message: " + str(raw_msg))
        print(raw_msg)
        msg_to_send = their_public_key.encrypt(raw_msg, 32)
        conn.send(str(msg_to_send).encode())
    if kill_flag.is_set():
        print("send_message: kill message recieved")

# get port

port = int(argv[2])

# generate RSA key

RSA_key = RSA.generate(1024)

# create a variable for their public key

their_public_key = None

# create queues
in_q = Queue() # holds all messages received
out_q = Queue() # holds all messages to send
kill_thread = Event()

# make connection (as client), or receive connection (as server)
# also, start threaded network senders and getters
if argv[1] == "client":
    s = make_conn("127.0.0.1", port)
    print("Connected to localhost")
    listener = Thread(target=get_messages, args=(s,kill_thread,RSA_key,))
    sender = Thread(target=send_message, args=(s,kill_thread, RSA_key,))
    listener.start()
    sender.start()
else:
    s = recv_conn(port)
    conn, addr = s.accept()
    listener = Thread(target=get_messages, args=(conn,kill_thread, RSA_key))
    sender = Thread(target=send_message, args=(conn,kill_thread, RSA_key))
    listener.start()
    sender.start()

# test sending and recieving messages
for line in stdin:
    out_q.put(int(line))

print("EOF reached, here are the messages recieved in the queue:")
for item in list(in_q.queue):
    print(item.decode("utf-8"))

# clean up threads
print("Killing threads")
kill_thread.set()
s.close()
listener.join()
sender.join()