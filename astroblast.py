#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from queue import Queue

from client import GameClient
from server import GameServer

def main():
    # queue of messages for the server
    server_queue = Queue()
    # queue of messages for the client
    client_queue = Queue()

    server = GameServer(server_queue, client_queue)
    client = GameClient(client_queue, server_queue)

    # Server runs on a separate thread
    server.start()

    running = True
    while running:
        # Check & process incoming messages to the client
        client.check_msgs()
        # Update client-side game state / Process user input
        client.update()

        if not client.running:
            running = False
            if server.running:
                server.running = False

    # Clean-up pyGame
    print("Exiting...")

if __name__ == '__main__':
    main()
