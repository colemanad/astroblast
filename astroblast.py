#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

import time

import pygame

from client import GameClient


def main():
    """Application entry point"""
    # Instantiate client module
    client = GameClient()

    # Timing variables
    ms_per_frame = 1000.0 / 60.0
    last_ticks = 0
    ticks_since_last_update = 0

    running = True
    while running:
        # Timing logic
        current_ticks = pygame.time.get_ticks()
        diff = current_ticks - last_ticks
        ticks_since_last_update += diff

        if ticks_since_last_update >= ms_per_frame:
            ticks_since_last_update = 0
            # Check & process incoming messages to the client
            client.check_msgs()
            # Update client-side game state / Process user input
            client.update()

            last_ticks = current_ticks
        else:
            time.sleep(diff/1000.0)

        # Shut down if the client quits
        if not client.running:
            running = False

    # Clean-up pyGame
    print("Exiting...")

if __name__ == '__main__':
    main()
