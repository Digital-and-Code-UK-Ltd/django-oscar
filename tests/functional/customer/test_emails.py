from django.core import mail
from django.test import TestCase

from oscar.core.loading import get_class
from oscar.test.factories import (
    ProductAlertFactory, UserFactory, create_product)
from oscar.test.utils import EmailsMixin

CustomerDispatcher = get_class('customer.utils', 'CustomerDispatcher')
AlertsDispatcher = get_class('customer.alerts.utils', 'AlertsDispatcher')


class TestCustomerConcreteEmailsSending(EmailsMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.dispatcher = CustomerDispatcher()

    def test_send_registration_email_for_user(self):
        extra_context = {'user': self.user}
        self.dispatcher.send_registration_email_for_user(self.user, extra_context)

        self._test_common_part()
        self.assertEqual('Thank you for registering.', mail.outbox[0].subject)
        self.assertIn('Thank you for registering.', mail.outbox[0].body)

    def test_send_password_reset_email_for_user(self):
        extra_context = {
            'user': self.user,
            'reset_url': '/django-oscar/django-oscar',
        }
        self.dispatcher.send_password_reset_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = 'Resetting your password at {}.'.format('example.com')
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('Please go to the following page and choose a new password:', mail.outbox[0].body)
        self.assertIn('http://example.com/django-oscar/django-oscar', mail.outbox[0].body)

    def test_send_password_changed_email_for_user(self):
        extra_context = {
            'user': self.user,
            'reset_url': '/django-oscar/django-oscar',
        }
        self.dispatcher.send_password_changed_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = 'Your password changed at {}.'.format('example.com')
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('your password has been changed', mail.outbox[0].body)
        self.assertIn('http://example.com/django-oscar/django-oscar', mail.outbox[0].body)

    def test_send_email_changed_email_for_user(self):
        extra_context = {
            'user': self.user,
            'reset_url': '/django-oscar/django-oscar',
            'new_email': 'some_new@mail.com',
        }
        self.dispatcher.send_email_changed_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = 'Your email address has changed at {}.'.format('example.com')
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('your email address has been changed', mail.outbox[0].body)
        self.assertIn('http://example.com/django-oscar/django-oscar', mail.outbox[0].body)
        self.assertIn('some_new@mail.com', mail.outbox[0].body)


class TestAlertsConcreteEmailsSending(EmailsMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.dispatcher = AlertsDispatcher()

    def test_send_product_alert_email_for_user(self):
        product = create_product(num_in_stock=5)
        ProductAlertFactory(product=product, user=self.user)

        self.dispatcher.send_product_alert_email_for_user(product)

        self._test_common_part()
        expected_subject = '{} is back in stock'.format(product.title)
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('We are happy to inform you that our product', mail.outbox[0].body)
        # No `hurry_mode`
        self.assertNotIn('Beware that the amount of items in stock is limited.', mail.outbox[0].body)

    def test_send_product_alert_email_for_user_with_hurry_mode(self):
        another_user = UserFactory(email='another_user@mail.com')
        product = create_product(num_in_stock=1)
        ProductAlertFactory(product=product, user=self.user, email=self.user.email)
        ProductAlertFactory(product=product, user=another_user, email=another_user.email)

        self.dispatcher.send_product_alert_email_for_user(product)
        self.assertEqual(len(mail.outbox), 2)  # Separate email for each user
        expected_subject = '{} is back in stock'.format(product.title)
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        for outboxed_email in mail.outbox:
            self.assertEqual(expected_subject, outboxed_email.subject)
            self.assertIn('We are happy to inform you that our product', outboxed_email.body)
            self.assertIn('Beware that the amount of items in stock is limited.', outboxed_email.body)

    def test_send_product_alert_confirmation_email_for_user(self):
        product = create_product(num_in_stock=5)
        alert = ProductAlertFactory(product=product, user=self.user, email=self.user.email, key='key00042')

        self.dispatcher.send_product_alert_confirmation_email_for_user(alert)

        self._test_common_part()
        self.assertEqual('Confirmation required for stock alert', mail.outbox[0].subject)
        self.assertIn('Somebody (hopefully you) has requested an email alert', mail.outbox[0].body)
        self.assertIn(alert.get_confirm_url(), mail.outbox[0].body)
        self.assertIn(alert.get_cancel_url(), mail.outbox[0].body)
