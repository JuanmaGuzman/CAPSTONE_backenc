from django.db import models


class ExampleModel(models.Model):
    name = models.CharField(max_length=100)
    example_self_relations = models.ManyToManyField(
        "self",
        symmetrical=True
    )

    @property
    def greetings(self):
        return 'hello there'


class OtherModel(models.Model):
    name = models.CharField(max_length=100)
    enemy = models.ForeignKey(
        ExampleModel,
        on_delete=models.PROTECT,
        related_name="enemies"
    )

    @property
    def greetings(self):
        return 'general kenobi'
