from daisychain.steps.compilers.namespace_compiler import NamespaceCompiler
from daisychain.steps.input import InMemoryInput

from .util import compare_trees

def run_compiler(input_config, expected_output):
    compiler_input = InMemoryInput(output=input_config)
    compiler = NamespaceCompiler(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)


def test_no_op():
    input_configs = [ {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}},
                      {'steps': {'step1': {'class': 'nonamespace'}, 'step2': {'param2': 'value2'}}}]
    for input_config in input_configs:
        run_compiler(input_config, input_config)

def test_passthrough():
    input_config = {'__namespaces__': 'daisychain.steps', 'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}}
    run_compiler(input_config, expected_output)


    input_config = {'__namespaces__': 'daisychain.steps', 'steps': {'step1': {'class': 'value1'}, 'step2': {'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'class': 'value1'}, 'step2': {'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

def test_single_find():
    input_config = {'__namespaces__': ['daisychain.steps'], 'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'class': 'daisychain.steps.input.InMemoryInput'}, 'step2': {'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

def test_multiple_find():
    input_config = {'__namespaces__': ['daisychain.steps'], 'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'daisychain.executor.Executor', 'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'class': 'daisychain.steps.input.InMemoryInput'}, 'step2': {'class': 'daisychain.executor.Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain.steps.input'], 'steps': {'step1': {'class': 'InMemoryInput'}, 'step2': {'class': 'daisychain.executor.Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain.steps.input','daisychain.executor'], 'steps': {'step1': {'class': 'InMemoryInput'}, 'step2': {'class': 'Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain'], 'steps': {'step1': {'class': 'steps.input.InMemoryInput'}, 'step2': {'class': 'executor.Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain.*'], 'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain.**'], 'steps': {'step1': {'class': 'InMemoryInput'}, 'step2': {'class': 'Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain.steps.*'], 'steps': {'step1': {'class': 'InMemoryInput'}, 'step2': {'__namespaces__': ['daisychain.executor'], 'class': 'Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__namespaces__': ['daisychain.steps.output'], 'steps': {'__namespaces__': ['daisychain.steps.input', 'daisychain.executor'], 'step1': {'class': 'InMemoryInput'}, 'step2': {'__namespaces__': ['daisychain.executor'], 'class': 'Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)
