from conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import get_current_site
from user_profiles.tokens import email_confrimation_token_generator
from utilities.mailer import send_email


def send_confirmation_email(
    user,
    request=None,
    use_https=False,
    subject_template_name='email_confirmation_subject.txt',
    email_template_name='email_confirmation_email.html'
):
    email = getattr(user, get_user_model().get_email_field_name())
    current_site = None if request is None else get_current_site(request)
    site_name = None if current_site is None else current_site.name
    domain = None if current_site is None else current_site.domain
    context = {
        'email': email,
        'domain': domain,
        'frontend_url': settings.FRONTEND_URL,
        'site_name': site_name,
        'user_id': user.id,
        'token': email_confrimation_token_generator.make_token(user),
        'protocol': 'https' if use_https else 'http'
    }
    send_email(
        subject_template_name,
        email_template_name,
        email,
        context
    )
