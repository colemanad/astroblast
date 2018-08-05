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

class MESSAGES(Values):
    """Message type constants"""
    NONE = ValueConstant("0")
    TEST = ValueConstant("1")
    TERMINATE = ValueConstant("-1")

    PING = ValueConstant("100")
    PONG = ValueConstant("101")

    # Server->Client messages
    UPDATEPOS = ValueConstant("200")    # Update client-side entity position
    UPDATEROT = ValueConstant("201")    # Update client-side entity rotation

    # Client->Server messages
    REQCONNECT = ValueConstant("300")   # Request connection to server
    REQUPDATE = ValueConstant("301")    # Request updated game state

class MSGCONTENT(Values):
    """Message content constants"""
    NONE = ValueConstant("0")
    TEST = ValueConstant("1")

    X_POS = ValueConstant("100")
    Y_POS = ValueConstant("101")
    ROTATION = ValueConstant("102")