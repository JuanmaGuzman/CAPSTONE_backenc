from conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader


def send_email(
    subject_template_name,
    email_template_name,
    to_email,
    context,
    from_email=settings.EMAIL_DEFAULT_FROM,
    html_email_template_name=None,
):
    """
    Based on: django.contrib.auth.forms.PasswordResetForm
    Send a django.core.mail.EmailMultiAlternatives to 'to_email'.
    """
    subject = loader.render_to_string(subject_template_name, context)
    subject = "".join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        message.attach_alternative(html_email, 'text/html')

    message.send()
