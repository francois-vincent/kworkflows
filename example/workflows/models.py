# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import functools


from django.db import models

from . import constants, utils
from kworkflows.workflow import (KWorkFlow, KWorkFlowEnabled, StateField, transition,
                                 WorkFlowHistory, WorkflowEnabledManager)


class Operator(models.Model):
    uid = utils.UIDField()
    name = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} ({})".format(self.uid, self.name)


# Define workflow mother class
ProviderOrderWorkflow = KWorkFlow.factory('ProviderOrderWorkflow')


# Define workflow specific classes
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


# Define history class (optional)
# with a single field = foreign key to underlying model
class ProviderOrderHistory(WorkFlowHistory):
    underlying = models.ForeignKey('ProviderOrder', related_name='histories')


# Define model with a 'state' field initialised with workflow mother class
class ProviderOrder(KWorkFlowEnabled):
    uid = utils.UIDField()
    type = models.CharField(max_length=16, choices=constants.ORDER_TYPE, default=constants.ORDER_TYPE.ACTIVATE)
    operator = models.ForeignKey(Operator, related_name='provider_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    state = StateField(ProviderOrderWorkflow, choices=True)  # specify workflow mother class here

    objects = WorkflowEnabledManager()  # use this manager
    histo = ProviderOrderHistory

    def __str__(self):
        return "{} on {}, state={}".format(self.uid, self.operator.name, self.state)


# Define proxy classes with specific workflows
class OVHModifyOrder(ProviderOrder):
    specific_fields = {
        'operator': functools.partial(Operator.objects.get, name='OVH'),
        'type': constants.ORDER_TYPE.MODIFY
    }
    workflow = OVHModifyWorkflow   # specify workflow specific class here

    class Meta:
        proxy = True

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


class SFRModifyOrder(ProviderOrder):
    specific_fields = {
        'operator': functools.partial(Operator.objects.get, name='SFR'),
        'type': constants.ORDER_TYPE.MODIFY
    }
    workflow = SFRModifyWorkflow   # specify workflow specific class here

    class Meta:
        proxy = True

    @transition
    def submit(self, advance_state):
        advance_state()

    @transition
    def trans_a(self, advance_state):
        advance_state()

    @transition
    def trans_b(self, advance_state):
        advance_state()

    @transition
    def finalize(self, advance_state):
        advance_state()
