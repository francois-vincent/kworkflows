# kworkflows

A small module adding versatile state/transition workflows to Django applications.

kworkflows is inspired from xworkflows and its buddy django-xworkflows, two modules offering a good state/transition workflow framework for general Python and Django applications.

Our goal in this work is to offer some flexibility, especially regarding flow inheritance, i.e. the possibility to have "typed" workflows, i.e. dynamically attach a workflow to an object according to the value of one or more fields of the underlying object.


## Quickstart

The main use case is to have a family of workflows attached to a single model but depending on the value of one or more fields.
i.e. when an object is instanciated, it is attached one of the available workflows according to the values of the relevant fields.
There is a single constraint to respect: all the sub worflows must have the same first state (=initial state).

In the short example below, we show all the steps that make a working polymorphic workflow:
 - Create the workflows from a mother class (constraint: same first state)
 - Add a `state` field to the underlying model
 - Create as many proxies as there are workflows, add relevant attributes and transition methods
 - Add a manager to the underlying model with at least a `create` method for creating derived objects
 - Optionally add an history class to the underlying model

First of all, create the mother class for your workflows family :

```
from kworkflows import KWorkFlow

ProviderOrderWorkflow = KWorkFlow.factory('ProviderOrderWorkflow')
```

Then describe your workflows states and transitions as subclasses of this mother class:
```
class OVHModifyWorkflow(ProviderOrderWorkflow):
    states = (
        ('start', 'Start'),
        ('state_1', 'State 1'),
        ('state_2', 'State 2'),
        ('end', 'End'),
    )
    transitions = (
        ('submit', 'start', 'state_1'),
        ('trans_1', 'state_1', 'state_2'),
        ('trans_2', 'state_2', 'state_1'),
        ('finalize', ('state_1', 'state_2'), 'end'),
    )


class SFRModifyWorkflow(ProviderOrderWorkflow):
    states = (
        ('start', 'Start'),
        ('state_a', 'State A'),
        ('state_b', 'State B'),
        ('end', 'End'),
    )
    transitions = (
        ('submit', 'start', 'state_a'),
        ('trans_a', 'state_a', 'state_b'),
        ('trans_b', 'state_b', 'state_a'),
        ('finalize', 'state_b', 'end'),
    )
```

Then, add this (quasi) mixin and your `state` field to the underlying model:

```
from kworkflows import KWorkFlowEnabled, StateField

class ProviderOrder(KWorkFlowEnabled, models.Model):
    ...
    state = StateField(ProviderOrderWorkflow)
```

Then write each workflow derived subclass of the underlying model as a proxy,
with transitions written this way at least:
```
from kworkflows import transition

class OVHModifyOrder(ProviderOrder):
    specific_fields = {
        'operator': functools.partial(Operator.objects.get, name='OVH'),
        'type': constants.ORDER_TYPE.MODIFY
    }
    workflow = OVHModifyWorkflow

    @transition
    def submit(self, advance_state):
        advance_state()

    @transition
    def trans_1(self, advance_state):
        advance_state()

    @transition
    def trans_2(self, advance_state):
        advance_state()

    @transition
    def finalize(self, advance_state):
        advance_state()

    class Meta:
        proxy = True
```
You can enrich transitions code as you wish, you only need to call
the `advance_state` method at one point when you want the state transition
and its optional history record to be performed.

Then add the `WorkflowProxyManager` manager to the underlying model:
```
class ProviderOrder(KWorkFlowEnabled, models.Model):
    ...
    objects = WorkflowProxyManager()
```
This manager has a `create` method which reponsibility is to auto fill fields that need to be,
according to the `specific_fields` in the worflow subclasses.

Then optionally add an history class:
```
from kworkflows import WorkFlowHistory

class ProviderOrderHistory(WorkFlowHistory):
    underlying = models.ForeignKey('ProviderOrder', related_name='histories')

class ProviderOrder(KWorkFlowEnabled, models.Model):
    ...
    histo = ProviderOrderHistory
```
