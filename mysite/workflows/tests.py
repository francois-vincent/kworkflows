from django.test import TestCase
from mixer.backend.django import mixer

from kworkflows.constants import *

from . import constants, models


class TestModels(TestCase):

    def test_order_generic(self):
        order = mixer.blend('workflows.providerorder')
        self.assertTrue(order)
        self.assertEqual(order.type, constants.ORDER_TYPE.ACTIVATE)
        self.assertEqual(order.state, 'start')
        self.assertEqual(order._meta.get_field('state').choices, models.ProviderOrderWorkflow.get_states())

    def test_order_specific(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        self.assertTrue(order)
        self.assertEqual(order.operator.name, 'OVH')
        self.assertEqual(order.type, constants.ORDER_TYPE.ACTIVATE)
        self.assertEqual(order.state, 'start')
        self.assertEqual(order._meta.get_field('state').choices, models.ProviderOrderWorkflow.get_states())

    def test_order_advance_state(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        self.assertEqual(order.state, 'start')
        order.advance_state('submit')
        self.assertEqual(order.state, 'state_1')
        order.refresh_from_db()
        self.assertEqual(order.state, 'state_1')

    def test_order_invalid_transition(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        self.assertRaises(InvalidTransitionName, order.advance_state, 'toto')

    def test_order_invalid_state_for_transition(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        order.advance_state('submit')
        self.assertRaises(InvalidStateForTransition, order.advance_state, 'submit')
