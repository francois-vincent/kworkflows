# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db import models

from . import constants
from kworkflows.workflow import KWorkFlow, KWorkFlowEnabled, StateField, UIDField


class Operator(models.Model):
    uid = UIDField()
    name = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} ({})".format(self.uid, self.name)


ProviderOrderWorkflow = KWorkFlow.factory('ProviderOrderWorkflow')


class OVHActivateWorkflow(ProviderOrderWorkflow):
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
        ('finalize', 'state_2', 'end'),
    )


class SFRActivateWorkflow(ProviderOrderWorkflow):
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


class ProviderObjectManager(models.Manager):

    def create(self, **kwargs):
        if getattr(self.model._meta, 'proxy', None):
            kwargs['operator'] = Operator.objects.get(name=self.model.operator_name)
            kwargs['type'] = self.model.type_value
        return super().create(**kwargs)


class ProviderOrder(KWorkFlowEnabled, models.Model):
    uid = UIDField()
    type = models.CharField(max_length=16, choices=constants.ORDER_TYPE, default=constants.ORDER_TYPE.ACTIVATE)
    operator = models.ForeignKey(Operator, related_name='provider_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    state = StateField(ProviderOrderWorkflow)

    objects = ProviderObjectManager()

    def __str__(self):
        return "{} on {}, state={}".format(self.uid, self.operator.name, self.state)


class OVHActivateOrder(ProviderOrder):
    operator_name = 'OVH'
    type_value = constants.ORDER_TYPE.ACTIVATE
    workflow = OVHActivateWorkflow

    class Meta:
        proxy = True


class SFRActivateOrder(ProviderOrder):
    operator_name = 'SFR'
    type_value = constants.ORDER_TYPE.ACTIVATE
    workflow = SFRActivateWorkflow

    class Meta:
        proxy = True

