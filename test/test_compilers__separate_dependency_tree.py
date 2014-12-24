from daisy.steps.compilers.separate_dependency_tree import SeparateDependencyTree
from daisy.steps.input import InMemoryInput

from .util import compare_trees

def run_compiler(input_config, expected_output):
    compiler_input = InMemoryInput(output=input_config)
    compiler = SeparateDependencyTree(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)


def test_no_op():
    input_configs = [ {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}},
            {'steps': {'step1': {'param1': 'value1', 'dependencies': []}, 'step2': {'param2': 'value2', 'dependencies': ['step1']}}}]
    for input_config in input_configs:
        run_compiler(input_config, input_config)

def test_successes():
    input_config = {'__dependencies__': {},'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'daisy.executor.Executor', 'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'daisy.executor.Executor', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

    input_config = {'__dependencies__': {'step2': ['step1']},'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'daisy.executor.Executor', 'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'daisy.executor.Executor', 'param2': 'value2', 'dependencies': ['step1']}}}
    run_compiler(input_config, expected_output)

def test_failure():
    input_config = {'__dependencies__': {},'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'class': 'daisy.executor.Executor', 'param2': 'value2', 'dependencies': ['step1']}}}
    compiler_input = InMemoryInput(output=input_config)
    compiler = SeparateDependencyTree(input_step=compiler_input)
    try:
        compiler.run()
    except ValueError:
        pass
    else:
        assert False, "Should have raised a ValueError"
        

