from contextlib import contextmanager
from unittest import mock

from django.test import TestCase
from moneyed import Money

from datatrans.models import AliasRegistration, Payment
from datatrans.signals import alias_registration_done, payment_done


class EventProcessingTest(TestCase):
    def test_payment_error(self):
        payment_error = Payment(
            is_success=False,
            transaction_id='170720154219033737',
            merchant_id='1111111111',
            request_type='CAA',
            expiry_month=12,
            expiry_year=19,
            client_ref='1234',
            value=Money(1.0, 'CHF'),
            payment_method='VIS',
            credit_card_country='CHE',

            error_code='1403',
            error_message='declined',
            error_detail='Declined',
            acquirer_error_code='50',
        )
        with catch_signal(payment_done) as signal_handler:
            payment_error.send_signal()
            signal_handler.assert_called_once_with(
                sender=None,
                signal=payment_done,
                instance=payment_error,
                is_success=False,
                client_ref=payment_error.client_ref,
            )

    def test_payment_success(self):
        payment = Payment(
            is_success=True,
            transaction_id='170717104749732144',
            merchant_id='2222222222',
            request_type='CAA',
            masked_card_number='424242xxxxxx4242',
            card_alias='70119122433810042',
            expiry_month=12,
            expiry_year=18,
            client_ref='1234',
            value=Money(10, 'CHF'),
            credit_card_country='CHE',

            response_code='01',
            response_message='Authorized',
            authorization_code='749762145',
            acquirer_authorization_code='104749',
        )
        with catch_signal(payment_done) as signal_handler:
            payment.send_signal()
            signal_handler.assert_called_once_with(
                sender=None,
                instance=payment,
                signal=payment_done,
                is_success=True,
                client_ref=payment.client_ref,
            )

    def test_register_alias_success(self):
        alias_registration = AliasRegistration(
            is_success=True,
            transaction_id='170710155947695609',
            merchant_id='1111111111',
            request_type='CAA',
            masked_card_number='424242xxxxxx4242',
            card_alias='70119122433810042',
            expiry_month=11,
            expiry_year=18,
            client_ref='1234',
            value=Money(0, 'CHF'),
            payment_method='VIS',
            credit_card_country='CHE',

            error_code='1403',
            acquirer_error_code='50',
            error_message='declined',
            error_detail='Declined',
        )
        with catch_signal(alias_registration_done) as signal_handler:
            alias_registration.send_signal()
            signal_handler.assert_called_once_with(
                sender=None,
                signal=alias_registration_done,
                instance=alias_registration,
                is_success=True,
                client_ref=alias_registration.client_ref,
            )


# From https://medium.freecodecamp.org/how-to-testing-django-signals-like-a-pro-c7ed74279311
@contextmanager
def catch_signal(signal):
    """Catch django signal and return the mocked call."""
    handler = mock.Mock()
    signal.connect(handler)
    yield handler
    signal.disconnect(handler)