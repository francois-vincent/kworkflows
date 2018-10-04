from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from mixer.backend.django import mixer

from kworkflows.constants import *

from . import constants, models


class TestModels(TestCase):

    def test_order_generic(self):
        t = timezone.now()
        order = mixer.blend('workflows.providerorder')
        self.assertTrue(order)
        self.assertEqual(order.type, constants.ORDER_TYPE.ACTIVATE)
        self.assertEqual(order.state, 'start')
        self.assertEqual(order._meta.get_field('state').choices, models.ProviderOrderWorkflow.get_aggregated_states())
        d = timedelta(microseconds=10000)  # 10 ms
        self.assertTrue(t-d < order.created_at < t+d)
        self.assertTrue(t-d < order.modified_at < t+d)

    def test_order_specific(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHModifyOrder.objects.create()
        self.assertTrue(order)
        self.assertEqual(order.operator.name, 'OVH')
        self.assertEqual(order.type, constants.ORDER_TYPE.MODIFY)
        self.assertEqual(order.state, 'start')
        self.assertDictEqual(dict(order._meta.get_field('state').choices),
                             dict(start='Start', state_1='State 1', state_2='State 2',
                                  state_a='State A', state_b='State B', end='End'))
        self.assertEqual(set(order.get_transitions_methods()), {'submit', 'trans_1', 'trans_2', 'finalize'})
        self.assertTrue(order.workflow.check_transitions(order.get_transitions_methods()))

    def test_order_advance_state(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHModifyOrder.objects.create()
        self.assertEqual(order.state, 'start')
        order.advance_state('submit')
        self.assertEqual(order.state, 'state_1')
        # state is not saved to db
        order.refresh_from_db()
        self.assertEqual(order.state, 'start')

    def test_order_safe_advance_state(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHModifyOrder.objects.create()
        self.assertEqual(order.state, 'start')
        t = order.modified_at
        order.safe_advance_state('submit')
        self.assertEqual(order.state, 'state_1')
        # state is saved to db
        order.refresh_from_db()
        self.assertEqual(order.state, 'state_1')
        self.assertGreater(order.modified_at, t)

    def test_order_invalid_transition(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHModifyOrder.objects.create()
        self.assertRaises(InvalidTransitionName, order.advance_state, 'toto')

    def test_order_invalid_state_for_transition(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHModifyOrder.objects.create()
        order.advance_state('submit')
        self.assertRaises(InvalidStateForTransition, order.advance_state, 'submit')


class TestTransition(TestCase):

    def test_transitions_OVH(self):
        models.Operator.objects.create(name='OVH')
        order = models.OVHModifyOrder.objects.create()
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
        order = models.SFRModifyOrder.objects.create()
        order.submit()
        self.assertEqual(order.state, 'state_a')
        order.trans_a()
        self.assertEqual(order.state, 'state_b')
        order.trans_b()
        self.assertEqual(order.state, 'state_a')
        self.assertRaises(InvalidStateForTransition, order.finalize)

    def test_transitions_together(self):
        # ensure that 2 proxy models can live together independently
        models.Operator.objects.create(name='OVH')
        models.Operator.objects.create(name='SFR')
        order_ovh = models.OVHModifyOrder.objects.create()
        order_ovh.submit()
        self.assertEqual(order_ovh.state, 'state_1')
        order_sfr = models.SFRModifyOrder.objects.create()
        order_sfr.submit()
        self.assertEqual(order_sfr.state, 'state_a')

    def test_transition_history(self):
        models.Operator.objects.create(name='OVH')
        o1 = models.OVHModifyOrder.objects.create()
        models.Operator.objects.create(name='SFR')
        o2 = models.SFRModifyOrder.objects.create()
        self.assertEqual(o1.histories.count(), 1)
        self.assertEqual(o2.histories.count(), 1)
        o1_first = o1.histories.first()
        self.assertEqual(o1_first.from_state, '#created')
        self.assertEqual(o1_first.to_state, 'start')
        o1.submit()
        self.assertEqual(o1.histories.count(), 2)
        o2.submit()
        o1.trans_1()
        o2.trans_a()
        self.assertEqual(o1.histories.count(), 3)
        self.assertEqual(o2.histories.count(), 3)
        o2_last = o2.histories.latest()
        self.assertEqual(o2_last.from_state, 'state_a')
        self.assertEqual(o2_last.to_state, 'state_b')
        self.assertEqual(o2_last.underlying, o2)
