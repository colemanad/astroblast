#!/usr/bin/env Python
# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from queue import Queue
from threading import Thread
from constantly import ValueConstant, Values
from os import path

import pygame

from gamemodule import MESSAGES
from client import GameClient
from server import GameServer

# Constants
# Will use fixed screen dimensions for now
WIDTH = 800
HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Initialize pyGame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AstroBlast!")

# Paths
assets_dir = path.join(path.dirname(__file__), 'assets')

def main():
    # queue of server->main process messages
    mainQueue = Queue()
    # queue of messages for the server
    serverQueue = Queue()
    # queue of messages for the client
    clientQueue = Queue()

    server = GameServer(serverQueue, clientQueue, mainQueue)
    client = GameClient(clientQueue, serverQueue)

    server.start()
    # client.start()

    # Just infinitely loop for now
    running = True
    while running:
        # print("before checkMsgs")
        client.checkMsgs()
        client.update()
        # print("after checkMsgs")
        msgType = MESSAGES.NONE
        msgContent = 0
        if not mainQueue.empty():
            msgType, msgContent = mainQueue.get_nowait()
        # print("after mq.get")
        if msgType == MESSAGES.TERMINATE:
            print("Exiting...")
            running = False
        # print("after terminate check")

    pygame.quit()

if __name__ == '__main__':
    main()