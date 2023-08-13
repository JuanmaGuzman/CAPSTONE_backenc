from collections.abc import Callable
from conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import get_current_site
from transactions.models import Transaction, AcountlessTransaction
from utilities.mailer import send_email
from typing import Union


def get_email_and_send(
    request,
    transaction: Union[Transaction, AcountlessTransaction],
    function: Callable,
):
    if isinstance(transaction, Transaction):
        user = transaction.buyer
        email = getattr(user, get_user_model().get_email_field_name())
    else:
        email = transaction.email
        if email is None:
            return
    function(email, request)


def proto_send_email(
    email,
    request=None,
    use_https=False,
    subject_template_name='purchase_in_process_subject.txt',
    email_template_name='purchase_in_process_email.html'
):
    current_site = None if request is None else get_current_site(request)
    site_name = None if current_site is None else current_site.name
    domain = None if current_site is None else current_site.domain
    context = {
        'email': email,
        'domain': domain,
        'frontend_url': settings.FRONTEND_URL,
        'site_name': site_name,
        'protocol': 'https' if use_https else 'http'
    }
    send_email(
        subject_template_name,
        email_template_name,
        email,
        context
    )


def send_purchase_in_process_email(
    email,
    request=None,
    use_https=False,
):
    proto_send_email(
        email,
        request,
        use_https,
        subject_template_name='purchase_in_process_subject.txt',
        email_template_name='purchase_in_process_email.html'
    )


def send_purchase_succeded_email(
    email,
    request=None,
    use_https=False,
):
    proto_send_email(
        email,
        request,
        use_https,
        subject_template_name='purchase_confirmed_subject.txt',
        email_template_name='purchase_confirmed_email.html'
    )


def send_purchase_failed_email(
    email,
    request=None,
    use_https=False
):
    proto_send_email(
        email,
        request,
        use_https,
        subject_template_name='purchase_failed_subject.txt',
        email_template_name='purchase_failed_email.html'
    )
