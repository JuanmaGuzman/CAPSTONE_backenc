import unicodedata
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model


UserModel = get_user_model()


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return (
        unicodedata.normalize("NFKC", s1).casefold()
        == unicodedata.normalize("NFKC", s2).casefold()
    )


class VerifiedEmailPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel.objects.filter(
            **{
                "%s__iexact" % email_field_name: email,
                "is_active": True,
                "email_verified": True
            }
        )
        return (
            u
            for u in active_users
            if u.has_usable_password()
            and _unicode_ci_compare(email, getattr(u, email_field_name))
        )
