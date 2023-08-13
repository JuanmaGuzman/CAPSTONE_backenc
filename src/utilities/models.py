from django.core.validators import RegexValidator


phone_regex = RegexValidator(
    regex=r'^\+?1?\d{8,15}$',
    message="Invalid phone number"
)


def get_latest_id(model) -> int:
    model_query = model.objects.last()
    if model_query is not None:
        return model_query.id + 1
    return 1
