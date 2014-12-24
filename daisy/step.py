from daisy.step_status import StepStatus, CheckStatusException
from daisy.reference import ReferencingObject, ReferenceList, MAXIMUM_REFERENCE_DEPTH, ExceedsMaximumDepthError, CircularReferenceError
from abc import abstractmethod


class Step(ReferencingObject):
    """
    Superclass for defining a step.

    All subclasses must implement the 'run' method.  The check_status method is optional and used to detect the current
    status of the step.  The step's 'status' attribute is what governs the stage the step is in:

    StepStatus.pending

        method run(self): The work for the step itself. Is responsible for making the step 'status' match its current
                          state.  For long running steps, you may want to have it spawn a thread and specify a callback
                          for the 'status' attribute that points to an instance method for updating the status
    """
    STATUS_PROMPT = "What would you like to do? (a)bort the plan, mark the step as (f)inished (any step that requires output from this step may have issues), or (r)etry?"

    def __init__(self, status=None, **fields):
        if status is None:
            status = StepStatus()
        self.status = status
        self.status.step = self
        self.status.callback = self.check_status
        self.executor = None

        super(Step, self).__init__(**fields)
        self.dependencies = set(self.dependencies)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.name)

    @property
    def finished(self):
        return self.status.finished

    @property
    def running(self):
        return self.status.running

    @property
    def pending(self):
        return self.status.pending

    @property
    def failed(self):
        return self.status.failed

    @property
    def validated(self):
        return self.status.validated

    def prune(self, previously_seen_cache=None, parent_nodes=None):
        """
        Does the bulk of the work for walking the reference tree for all of the references and references for the node
        Does this recursively doing a depth-first search
        """
        if previously_seen_cache is None:
            parent_nodes = set()
            previously_seen_cache = dict()

        if self in previously_seen_cache:
            return previously_seen_cache[self]

        if len(self.dependencies) == 0:
            previously_seen_cache[self] = set()
        else:
            if len(parent_nodes) > MAXIMUM_REFERENCE_DEPTH:
                raise ExceedsMaximumDepthError()

        parent_nodes.add(self)
        sub_dependencies = set()

        for reference in self.dependencies:
            if reference in parent_nodes:
                error = CircularReferenceError(reference)
                error.add_reference(self, self._find_attributes_for_reference(reference, for_execution=True))
                raise error

            try:
                sub_dependencies.update(reference.prune(previously_seen_cache=previously_seen_cache, parent_nodes=parent_nodes))
            except CircularReferenceError as e:
                e.add_reference(self, self._find_attributes_for_reference(reference, for_execution=True))
                raise e

        parent_nodes.remove(self)
        self.dependencies -= sub_dependencies
        previously_seen_cache[self] = self.dependencies | sub_dependencies
        return previously_seen_cache[self]

    def check_status(self):
        """
        Check and set the status of the step.
        Useful if you want to skip a step that you can detect it has already been done
        """
        pass

    def validate(self):
        """
        This should be overloaded and is used to verify the step can be run, raising an error if something wrong occurs.
        For authentication steps, this should likely simply run the authentication getting mechanism and actually retrieve the credentials.
        For all other steps, this verification happens at run-time and should validate that any services they consume are accessible and
            any consumed credentials are valid.  Otherwise, this method does not need to be overloaded.
        """
        self.status.set_validated()

    @abstractmethod
    def run(self):
        """
        This should throw an exception if it cannot run or fails
        """

    def prompt_user(self, prompt, valid_choices=None, default=None, exception=None):
        if self.executor is None:
            raise RuntimeError("Cannot prompt the user for input if not run through an executor")
        return self.executor.prompt_user_for_step(self, prompt=prompt, exception=exception, valid_choices=valid_choices, default=default)

    def prompt_user_for_status(self, message=None, exception=None):
        try:
            if self.executor is None:
                raise RuntimeError("Cannot prompt the user for input if not run through an executor")

            if message is None:
                prompt = Step.STATUS_PROMPT
            else:
                prompt = '{}\n{}'.format(message, Step.STATUS_PROMPT)
            choice = self.prompt_user(prompt=prompt, exception=exception)
            if choice == 'r':
                if isinstance(self.status.stage, CheckStatusException):
                    self.status.stage.revert()
                else:
                    self.status.set_pending()
            elif choice == 'f':
                self.status.set_finished()
            else:
                if not self.status.failed:
                    self.status.set_failed(RuntimeError("Execution aborted due to step choice"))
                self.executor.execution.aborted = True
                self.executor.execution.working_set.discard(self)
                self.executor.execution.failed_steps.add(self)

        except Exception as e:
            self.log().exception("Could not get user input.  Aborting plan")
            self.status.set_failed(e)
            if self.executor is not None:
                self.executor.execution.aborted = True
                self.executor.execution.working_set.discard(self)
                self.executor.execution.failed_steps.add(self)

Step.dependencies = ReferenceList(elements_of=Step, optional=True)
