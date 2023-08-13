from ninja import Router
from example_app.schema import HelloWorldSchema, HelloWorldIn, HelloWorldOut
from typing import Optional

router = Router()


@router.get('/', response=HelloWorldSchema)
def hello_world(request, param: Optional[int] = None):
    return {
        'hello': 'world',
        'param': param,
        'otra': 'cosa'
    }


@router.post('/', response=HelloWorldOut)
def post_hello_world(request, body: HelloWorldIn):
    return {
        'hello': f'greetings, {body.name}'
    }
