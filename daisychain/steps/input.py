from daisychain.step import Step
import re
import getpass
import py3compat

if py3compat.PY2:
    input = raw_input

class Input(Step):
    """
    Generic input_step step that should present an 'output' attribute that represents the configuration dictionary-tree for
    consumption.  It may get it from a JSON or YAML file, an HTTP Post, from an in-memory variable at instantiation like this,
    or otherwise
    """
    def __init__(self, **fields):
        super(Input, self).__init__(**fields)
        self.output = None


class InMemoryInput(Input):
    """
    Takes in the output as an argument to present as output for other tasks to ingest
    """
    def __init__(self, output, **fields):
        super(InMemoryInput, self).__init__(**fields)
        self.output = output

    def run(self):
        self.status.set_finished()


class UserInput(Input):
    """
    A special type of Input class for a prompted input from a user.
    In general use, an Executor requires a UserInput class in order
    to make requests when its failure mode is set to 'PROMPT'.
    """
    VALID_CHOICE_FINDER_REGEX = re.compile('\((\w)\)')

    @classmethod
    def find_valid_choices_from_prompt(cls, prompt):
        return [v.lower() for v in cls.VALID_CHOICE_FINDER_REGEX.findall(prompt)]

    def __init__(self, prompt, valid_choices=None, default=None, **fields):
        super(UserInput, self).__init__(**fields)
        self.prompt = prompt
        if valid_choices is None:
            valid_choices = self.find_valid_choices_from_prompt(prompt)
            if len(valid_choices) == 0:
                raise ValueError("Could not find any default choices looking for '(\w)' in the prompt: {}".format(prompt))
        self.valid_choices = valid_choices
        self.default = default
        self.user = None

    def prompt_user(self):
        self.log('input_step').info("Prompting user for: {}".format(self.prompt))
        while self.output is None:
            self.run()

            if len(self.output) == 0:
                self.output = self.default

            if self.output not in self.valid_choices:
                self.log('input_step').info("{0.user!r} input_step invalid option {0.output!r}".format(self))
                self.output = None


class ConsoleInput(UserInput):
    """
    Default user input class for prompting on the console where the executor is being run
    """

    SEPARATOR = "----------------------------------------------------------------------"

    def run(self):
        full_prompt = "{0.SEPARATOR}\n{0.prompt}\n{0.SEPARATOR}\n>".format(self)
        self.user = getpass.getuser()
        self.output = input(full_prompt).lower().strip()
        self.status.set_finished()
