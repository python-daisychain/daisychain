from daisy.steps.compiler import Compiler
from daisy.constants import COMPILERS_KEY
from daisy.instantiator import Instantiator
from daisy.executor import Executor


class Chain(Compiler):
    INPUT_STEP_NAME = '<<INMEMORYCOMPILERSTART>>'
    RUN_FROM_HERE = 'run_from_here'

    def _make_linear_chain(self, compilers, step_config):
        output_config = {}
        previous_input_step = self.INPUT_STEP_NAME
        run_from_step = None
        for compiler in compilers:
            if isinstance(compiler, basestring):
                if self.RUN_FROM_HERE == compiler:
                    assert run_from_step is None, "{!r} can only be specified once in the compilations list and it is specified both after the {!r} compiler and the {!r} compiler".format(self.RUN_FROM_HERE, run_from_step, previous_input_step)
                    run_from_step = previous_input_step
                    continue
                compiler_name = compiler
                next_index = 1
                while compiler_name in output_config:
                    compiler_name = '.'.join((compiler, str(next_index)))
                    next_index += 1
                output_config[compiler_name] = {'class': compiler, 'input_step': previous_input_step}
                previous_input_step = compiler_name
            elif isinstance(compiler, dict):
                base_name = compiler.get('name', compiler['class'])
                compiler_name = base_name
                next_index = 1
                while compiler_name in output_config:
                    compiler_name = '.'.join((base_name, str(next_index)))
                    next_index += 1
                compiler['input_step'] = previous_input_step
                output_config[compiler_name] = compiler
                previous_input_step = compiler_name
            else:
                raise TypeError("When trying to evaluate a list of compilers, all entries must be a dict or basestring.  This entry was {!r}".format(compiler))
        if run_from_step is None:
            run_from_step = previous_input_step
        output_config[run_from_step][self.RUN_FROM_HERE] = True
        return output_config

    def compile(self, config):
        if COMPILERS_KEY in config:
            compilers = config.pop(COMPILERS_KEY)
            if isinstance(compilers, list):
                compilers = self._make_linear_chain(compilers, config)
            elif not isinstance(compilers, dict):
                raise TypeError('{!r} key must specify either a list or a dict of compilers'.format(COMPILERS_KEY))

            compiler_to_run_from = None
            for compiler_name, compiler_config in compilers.iteritems():
                if compiler_config.get(self.RUN_FROM_HERE, False):
                    assert compiler_to_run_from is None, "Only one compiler can specify '{!s}', but both {!r} and {!r} specify it".format(self.RUN_FROM_HERE, compiler_to_run_from, compiler_name)
                    compiler_to_run_from = compiler_name
                compiler_config.setdefault('input_step', self.INPUT_STEP_NAME)

            compilers[self.INPUT_STEP_NAME] = {'class': 'daisy.steps.input.InMemoryInput', 'output': config}

            instantiator = Instantiator(name=self.name, config=compilers)
            instantiator.run()
            executor = Executor(name=self.name, dependencies=instantiator.steps.values())
            executor.execute()

            if compiler_to_run_from:
                return instantiator.steps[compiler_to_run_from].output
        else:
            return config
