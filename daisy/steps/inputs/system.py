from daisy.steps.input import Input
import sys

class StdIn(Input):
    def run(self):
        self.output = sys.stdin.read()
        self.status.set_finished()
