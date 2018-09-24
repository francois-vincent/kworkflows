
class MultipleDifferentFirstStates(Exception):
    def __init__(self, cls_name):
        super().__init__("Subclasses of {} must all have same first state".format(cls_name))


class InvalidTransitionName(Exception):
    def __init__(self, cls_name, transition):
        super().__init__("Transition {} not found in Workflow {}".format(transition, cls_name))


class InvalidStateForTransition(Exception):
    def __init__(self, cls_name, transition, state):
        super().__init__("Invalid transition {} for state {} in Workflow {}".format(transition, state, cls_name))


