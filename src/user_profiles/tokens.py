from django.contrib.auth.tokens import PasswordResetTokenGenerator


# Equivalent to the default token but without adding the {last login timestamp}
# to the hash input so users can login before confirming their email.
class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk}{user.password}{timestamp}{email}"


email_confrimation_token_generator = EmailConfirmationTokenGenerator()
