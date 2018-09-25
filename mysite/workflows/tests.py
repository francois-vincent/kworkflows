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
        self.assertDictEqual(dict(order._meta.get_field('state').choices),
                             dict(start='Start', state_1='State 1', state_2='State 2',
                                  state_a='State A', state_b='State B', end='End'))

    def test_order_advance_state(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        self.assertEqual(order.state, 'start')
        order.advance_state('submit')
        self.assertEqual(order.state, 'state_1')
        order.refresh_from_db()
        self.assertEqual(order.state, 'start')

    def test_order_safe_advance_state(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        self.assertEqual(order.state, 'start')
        order.safe_advance_state('submit')
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


class TestTransition(TestCase):

    def test_transitions_OVH(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHActivateOrder.objects.create()
        order.submit()
        self.assertEqual(order.state, 'state_1')
        order.trans_1()
        self.assertEqual(order.state, 'state_2')
        order.trans_2()
        self.assertEqual(order.state, 'state_1')
        order.finalize()
        self.assertEqual(order.state, 'end')

    def test_transitions_SFR(self):
        models.Operator.objects.create(name='SFR')
        order = models.SFRActivateOrder.objects.create()
        order.submit()
        self.assertEqual(order.state, 'state_a')
        order.trans_a()
        self.assertEqual(order.state, 'state_b')
        order.trans_b()
        self.assertEqual(order.state, 'state_a')
        self.assertRaises(InvalidStateForTransition, order.finalize)

    def test_transition_history(self):
        models.Operator.objects.create(name='OVH')
        o1 = models.OVHActivateOrder.objects.create()
        models.Operator.objects.create(name='SFR')
        o2 = models.SFRActivateOrder.objects.create()
        o1.submit()
        self.assertEqual(o1.histories.count(), 1)
        self.assertEqual(o2.histories.count(), 0)
        o2.submit()
        o1.trans_1()
        o2.trans_a()
        self.assertEqual(o1.histories.count(), 2)
        self.assertEqual(o2.histories.count(), 2)
        o1_first = o1.histories.first()
        self.assertEqual(o1_first.from_state, 'start')
        self.assertEqual(o1_first.to_state, 'state_1')
        o2_last = o2.histories.latest()
        self.assertEqual(o2_last.from_state, 'state_a')
        self.assertEqual(o2_last.to_state, 'state_b')
        self.assertEqual(o2_last.underlying, o2)