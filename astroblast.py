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

from gamemodule import MESSAGES
from client import GameClient
from server import GameServer

def main():
    # queue of server->main process messages
    mainQueue = Queue()
    # queue of messages for the server
    serverQueue = Queue()
    # queue of messages for the client
    clientQueue = Queue()
    # put a message in the client queue to get execution started
    clientQueue.put((MESSAGES.TEST, -1),True)

    server = GameServer(serverQueue, clientQueue, mainQueue)
    client = GameClient(clientQueue, serverQueue)

    server.start()
    client.start()

    # Just infinitely loop for now
    while True:
        msgType, msgContent = mainQueue.get()
        if msgType == MESSAGES.TERMINATE:
            print("Exiting...")
            break

if __name__ == '__main__':
    main()