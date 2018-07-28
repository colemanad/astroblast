from constants import MESSAGES

# Base class for server & client modules
class GameModule():
    name = "unknown"
    running = True

    def __init__(self, inQueue, outQueue):
        self.in_queue = inQueue
        self.out_queue = outQueue

    # Stuf method for cleanup before termination
    def cleanup(self):
        pass

    # Stub method for processing messages
    def process_msg(self, msg):
        pass

    # Update game state
    def update(self):
        if not self.running:
            self.cleanup()
            print("%s quitting" % (self.name))

    # Send a message to counterpart (i.e., the client or server)
    def send_msg(self, msg):
        print("%s: sending %s - %d" % (self.name, msg[0].name, msg[1]))
        self.out_queue.put(msg,True)

    # Process all incoming messages
    def check_msgs(self):
        while not self.in_queue.empty():
            # Check queue for new messages & respond to each
            msg_type = MESSAGES.NONE
            msg_content = 0

            msg_type, msg_content = self.in_queue.get_nowait()
            print("%s: received %s - %d" % (self.name, msg_type.name, msg_content))
            self.in_queue.task_done()

            self.process_msg((msg_type, msg_content))

            if msg_type == MESSAGES.TERMINATE:
                self.running = False
