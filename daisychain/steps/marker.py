from daisychain.step import Step


class Marker(Step):
    def run(self):
        self.status.set_finished()
