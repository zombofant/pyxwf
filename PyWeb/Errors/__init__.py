from HTTP import *

class InternalRedirect(Exception):
    def __init__(self, to):
        self.to = to
