from daisy.steps.compilers.chain import Chain, COMPILERS_KEY
from daisy.steps.input import InMemoryInput

from .util import compare_trees

def run_compiler(input_config, expected_output):
    compiler_input = InMemoryInput(output=input_config)
    compiler = Chain(input_step=compiler_input)
    compiler.run()
    compare_trees(compiler.output, expected_output)

def test_no_op():
    input_configs = [ {'steps': {'step1': {'param1': 'value1'}, 'step2': {'param2': 'value2'}}},
                      {'steps': {'step1': {'class': 'nonamespace'}, 'step2': {'param2': 'value2'}}}]
    for input_config in input_configs:
        run_compiler(input_config, input_config)

def test_simple_single_compiler():
    input_config = {COMPILERS_KEY: ['daisy.steps.compilers.namespace_compiler.NamespaceCompiler'],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {'step1': {'class': 'input.InMemoryInput'}, 'step2': {'param2': 'value2'}}}
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'param2': 'value2'}}}
    run_compiler(input_config, expected_output)


def test_compiler_list():
    input_config = {COMPILERS_KEY: [
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                'daisy.**.StepConfigInheritance'],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'class': 'daisy.steps.input.InMemoryInput', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

def test_compiler_list_with_repeat():
    input_config = {COMPILERS_KEY: [
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                'daisy.**.StepConfigInheritance',
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                ],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'class': 'daisy.steps.input.InMemoryInput', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

def test_compiler_list_with_run_from_here():
    # Will Fail if it doesn't use 'run_from_here' because StdOut is an output and doesn't specify any output for a next compiler
    input_config = {COMPILERS_KEY: [
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                'daisy.**.StepConfigInheritance',
                'run_from_here',
                'daisy.steps.pipes.json_convert.JsonDump',
                'daisy.steps.outputs.system.StdOut'
                ],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'class': 'daisy.steps.input.InMemoryInput', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

def test_compiler_list_with_multiple_run_from_here():
    input_config = {COMPILERS_KEY: [
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                'run_from_here',
                'daisy.**.StepConfigInheritance',
                'run_from_here',
                ],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'class': 'daisy.steps.input.InMemoryInput', 'param2': 'value2'}}}
    try:
        run_compiler(input_config, expected_output)
    except AssertionError:
        pass
    else:
        assert False, "Should have thrown an assertion error for only specifying run_from_here once"



def test_compiler_list_with_repeat_and_dictionary_based():
    input_config = {COMPILERS_KEY: [
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                'daisy.**.StepConfigInheritance',
                {'class': 'daisy.steps.compilers.namespace_compiler.NamespaceCompiler'},
                ],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'class': 'daisy.steps.input.InMemoryInput', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)

def test_compiler_list_with_bad_type():
    input_config = {COMPILERS_KEY: [
                'daisy.steps.compilers.namespace_compiler.NamespaceCompiler',
                'daisy.**.StepConfigInheritance',
                3
                ],
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = None
    try:
        run_compiler(input_config, expected_output)
    except TypeError:
        pass
    else:
        assert False, "Should have thrown a type-error for a compiler that wasn't a string or dict"

def test_compiler_with_tree():
    input_config = {COMPILERS_KEY: {
                'namespace_compiler': {'class': 'daisy.steps.compilers.namespace_compiler.NamespaceCompiler'},
                'stepconfig_compiler': {'class': 'daisy.**.StepConfigInheritance', 'input_step': 'namespace_compiler', 'run_from_here': True}
                },
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    expected_output = {'steps': {'step1': {'class': 'daisy.steps.input.InMemoryInput'}, 'step2': {'class': 'daisy.steps.input.InMemoryInput', 'param2': 'value2'}}}
    run_compiler(input_config, expected_output)


def test_compiler_with_tree():
    input_config = {COMPILERS_KEY: {
                'namespace_compiler': {'class': 'daisy.steps.compilers.namespace_compiler.NamespaceCompiler', 'run_from_here': True},
                'stepconfig_compiler': {'class': 'daisy.**.StepConfigInheritance', 'input_step': 'namespace_compiler', 'run_from_here': True}
                },
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    try:
        compiler_input = InMemoryInput(output=input_config)
        compiler = Chain(input_step=compiler_input)
        compiler.run()
    except AssertionError:
        pass
    else:
        assert False, "Should have thrown an assertion when more than one compiler sets itself to 'run_from_here'"

def test_compiler_with_bad_compilers_key():
    input_config = {COMPILERS_KEY: 3,
                    '__namespaces__': ['daisy.steps'],
                    'steps': {
                        'step1': {'class': 'input.InMemoryInput'},
                        'step2': {'__super__': 'step1', 'param2': 'value2'}
                    }
                }
    try:
        compiler_input = InMemoryInput(output=input_config)
        compiler = Chain(input_step=compiler_input)
        compiler.run()
    except TypeError:
        pass
    else:
        assert False, "Should have thrown TypeError when the compilers key is set to an unrecognizable value"

