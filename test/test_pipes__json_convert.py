from daisychain.steps.input import InMemoryInput
from daisychain.steps.pipes.json_convert import JsonLoad, JsonDump
import json

from .util import compare_trees

def test_load():
    input_config = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}}
    pipe_input = InMemoryInput(output=json.dumps(input_config))
    pipe = JsonLoad(input_step=pipe_input)
    pipe.run()
    compare_trees(pipe.output, input_config)

def test_dump_no_args():
    input_config = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'__super__': 'step1', 'param2': 'value2'}}}
    pipe_input = InMemoryInput(output=input_config)
    pipe = JsonDump(input_step=pipe_input)
    pipe.run()
    compare_trees(json.loads(pipe.output), input_config)
    assert '\n' not in pipe.output and '\r' not in pipe.output

def test_dump_with_args():
    input_config = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'__super__': 'step1', 'param2': 'value2'}}}
    pipe_input = InMemoryInput(output=input_config)
    pipe = JsonDump(indent=2, input_step=pipe_input)
    pipe.run()
    compare_trees(json.loads(pipe.output), input_config)
    assert '\n' in pipe.output or '\r' in pipe.output
