from ninja import Schema
from ninja.orm import create_schema
from example_app.models import ExampleModel
from typing import Optional


class HelloWorldSchema(Schema):
    hello: str
    param: Optional[int]


class HelloWorldIn(Schema):
    name: str


class HelloWorldOut(Schema):
    hello: str


ExampleModelSchema = create_schema(
    ExampleModel,
    name='ExampleModel',
    exclude=['example_self_relations'],
    custom_fields=[('greetins', str, None)]
)
