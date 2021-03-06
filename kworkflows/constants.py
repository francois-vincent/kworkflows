
CREATION_STATE = '#created'


class MultipleDifferentFirstStates(Exception):
    def __init__(self, cls_name):
        super().__init__("Subclasses of {} must all have same first state".format(cls_name))


class InconsistentStateList(Exception):
    def __init__(self, cls_name):
        super().__init__("Workflow {}: Some state seem to be declared twice".format(cls_name))


class InconsistentStateInTransition(Exception):
    def __init__(self, cls_name, transition, position):
        super().__init__("Workflow {}: {} state of "
                         "transition {} not found in states list".format(cls_name, position, transition))


class InvalidTransitionName(Exception):
    def __init__(self, cls_name, transition):
        super().__init__("Transition {} not found in Workflow {}".format(transition, cls_name))


class InvalidStateForTransition(Exception):
    def __init__(self, cls_name, transition, state):
        super().__init__("Invalid transition {} for state {} in Workflow {}".format(transition, state, cls_name))


class FailAdvanceState(Exception):
    def __init__(self, cls_name, transition, state):
        super().__init__("Transition {} failed to advance from state {} "
                         "in Workflow {} due to high concurrency".format(transition, state, cls_name))


class InvalidTransitionMethod(Exception):
    def __init__(self, cls_name):
        super().__init__("Invalid transition method in Workflow {}".format(cls_name))
