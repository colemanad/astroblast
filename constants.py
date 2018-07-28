from constantly import ValueConstant, Values

# pyGame-centric constants
class GAME(Values):
    # These should be moved to a global value of some sort later,
    #   since they ostensibly could change during runtime
    WIDTH = 800
    HEIGHT = 600
    FPS = 60

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)

# Message type constants
class MESSAGES(Values):
    NONE = ValueConstant("0")
    TEST = ValueConstant("1")
    TERMINATE = ValueConstant("-1")