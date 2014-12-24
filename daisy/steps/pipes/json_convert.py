from daisy.steps.pipe import Pipe
import json


class JsonLoad(Pipe):
    def run(self):
        self.output = json.loads(self.input_step.output)
        self.status.set_finished()


class JsonDump(Pipe):
    def __init__(self, **kwargs):
        fields, json_args = self.__class__._split_fields(**kwargs)
        super(Pipe, self).__init__(**fields)
        self.json_args = json_args

    def run(self):
        self.output = json.dumps(self.input_step.output, **self.json_args)
        self.status.set_finished()
