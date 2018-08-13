#!/usr/bin/env python3

# AstroBlast!
# Copyright Andrew Coleman and Zachary Conlyn
# CMSC 495-7380, Group 4
#
# Art assets Copyright 2018 Blindman67
#   Licensed under the Creative Commons CC-BY 3.0 license: https://creativecommons.org/licenses/by/3.0/
#   The assets have been modified.
#   https://opengameart.org/content/rocks-ships-stars-gold-and-more

from constantly import NamedConstant, Names

class GAME():
    """pyGame-centric constants"""

    # These should be moved to a global value of some sort later,
    #   since they ostensibly could change during runtime
    WIDTH = 1024
    HEIGHT = 1024
    FPS = 60

    BLACK = (0, 0, 0)

    # Print pygame events to stdout?
    PRINTEVENTS = False

    # Default ID values
    INVALID_ID = -1
    DISPATCHER_ID = 0
    LOCAL_SERVER_ID = 1
    LOCAL_CLIENT_ID = 2
    REMOTE_CLIENT_ID = 3

    # Entity types
    ENTITY_NONE = 100
    ENTITY_TEST = 101
    ENTITY_PLAYERSHIP = 102
    ENTITY_BULLET = 103
    ENTITY_ASTEROID_BIG = 104
    ENTITY_ASTEROID_MED = 105
    ENTITY_ASTEROID_SMALL = 106
    ENTITY_EXPLOSION = 107

    # Game states
    STATE_TITLE = 200
    STATE_MULTIPLAYER_MENU = 201
    STATE_GAME_LOADING = 202
    STATE_GAME_START = 203
    STATE_IN_GAME = 204
    STATE_GAME_OVER = 205
    STATE_PLAYER_DIED = 206

    # GUI
    GUI_BUTTON_SP = 300
    GUI_BUTTON_MP = 301
    GUI_BUTTON_BACK = 302
    GUI_BUTTON_HOST = 303
    GUI_BUTTON_JOIN = 304


class MESSAGES():
    """Message type constants"""

    NONE = 0
    TEST = 1
    TERMINATE = -1

    PING = 100
    PONG = 101

    # Messages used Client->Server and Server->Client
    SIGNAL_DISCONNECT = 200    # Tell server client is disconnecting now/tell client to disconnect

    CREATE_ENTITY = 250
    DESTROY_ENTITY = 251

    UPDATEPOS = 252    # Update client-side entity position
    UPDATEROT = 253    # Update client-side entity rotation

    UPDATELIVES = 260
    UPDATESCORE = 261

    # Client->Server messages
    REQCONNECT = 300   # Request connection to server
    REQUPDATE = 301    # Request updated game state

    SIGNAL_PLAYER_READY = 310

    INPUT_RIGHT_DOWN = 350
    INPUT_RIGHT_UP = 351
    INPUT_LEFT_DOWN = 352
    INPUT_LEFT_UP = 353
    INPUT_THRUST_DOWN = 354
    INPUT_THRUST_UP = 355
    INPUT_DOWN_DOWN = 356
    INPUT_DOWN_UP = 357
    INPUT_SHOOT_DOWN = 358
    INPUT_SHOOT_UP = 359

    # Server->Client messages
    CONNECT_ACCEPT = 400
    CONNECT_REJECT = 401
    CONNECT_SUCCESS = 402
    CHANGE_STATE = 450

class MSGCONTENT():
    """Message content constants"""

    NONE = 0
    TEST = 1

    GAME_STATE = 5

    RECIPIENT_ID = 9
    ID = 10
    SET_ID = 11
    ENTITY_ID = 13
    ENTITY_TYPE = 14
    PLAYER_ID = 15
    PLAYER_LIVES = 16
    PLAYER_SCORE = 17

    GAME_STATE = 50

    # Game state
    X_POS = 100
    Y_POS = 101
    ROTATION = 102

class NETWORK(Names):
    """Modes for network behavior"""

    MODE_SERVER = NamedConstant()
    MODE_CLIENT = NamedConstant()