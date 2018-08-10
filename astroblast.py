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
import cProfile

import pygame

from dispatcher import Dispatcher
from client import GameClient
from server import GameServer


def main():
    """Application entry point"""
    profile = cProfile.Profile()
    try:
        # profile.enable()

        dispatch_queue = Queue()
        remote_queue = Queue()
        # queue of messages for the server
        server_queue = Queue()
        # queue of messages for the client
        local_client_queue = Queue()

        dispatch = Dispatcher(dispatch_queue, server_queue, local_client_queue, remote_queue)

        # Instantiate the server and client modules
        server = GameServer(server_queue, dispatch)
        client = GameClient(local_client_queue, dispatch_queue)

        dispatch.start()
        # Start the server on a separate thread
        server.start()

        ms_per_frame = 1000.0 / 60.0
        last_ticks = 0
        ticks_since_last_update = 17

        running = True
        while running:
            current_ticks = pygame.time.get_ticks()
            diff = current_ticks - last_ticks
            ticks_since_last_update += diff

            if ticks_since_last_update >= ms_per_frame:
                # Check & process incoming messages to the client
                client.check_msgs()
                # Update client-side game state / Process user input
                client.update()

            # Shut down if the client quits
            if not client.running:
                running = False
                # Make sure the server quits too
                if server.running:
                    server.running = False

        # Clean-up pyGame
        print("Exiting...")

        # profile.disable()
    
    finally:
        # profile.print_stats('cumulative')
        pass

if __name__ == '__main__':
    main()
