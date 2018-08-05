#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from constantly import ValueConstant, Values

class GAME(Values):
    """pyGame-centric constants"""
    # These should be moved to a global value of some sort later,
    #   since they ostensibly could change during runtime
    WIDTH = 800
    HEIGHT = 600
    FPS = 60

    WHITE = (255, 255, 255, 255)
    BLACK = (0, 0, 0, 255)
    RED = (255, 0, 0, 255)
    GREEN = (0, 255, 0, 255)
    BLUE = (0, 0, 255, 255)
    YELLOW = (255, 255, 0, 255)

    # Print pygame events to stdout?
    PRINTEVENTS = False

    INVALID_ID = ValueConstant("-1")
    SERVER_ID = ValueConstant("0")

class MESSAGES(Values):
    """Message type constants"""
    NONE = ValueConstant("0")
    TEST = ValueConstant("1")
    TERMINATE = ValueConstant("-1")

    PING = ValueConstant("100")
    PONG = ValueConstant("101")

    # Messages used Client->Server and Server->Client
    SIGNAL_DISCONNECT = ValueConstant("200")    # Tell server client is disconnecting now/tell client to disconnect

    UPDATEPOS = ValueConstant("250")    # Update client-side entity position
    UPDATEROT = ValueConstant("251")    # Update client-side entity rotation

    # Client->Server messages
    REQCONNECT = ValueConstant("300")   # Request connection to server
    REQUPDATE = ValueConstant("301")    # Request updated game state

    # Server->Client messages
    CONNECT_ACCEPT = ValueConstant("400")
    CONNECT_REJECT = ValueConstant("401")

class MSGCONTENT(Values):
    """Message content constants"""
    NONE = ValueConstant("0")
    TEST = ValueConstant("1")

    ID = ValueConstant("10")
    SET_ID = ValueConstant("11")

    # Game state
    X_POS = ValueConstant("100")
    Y_POS = ValueConstant("101")
    ROTATION = ValueConstant("102")