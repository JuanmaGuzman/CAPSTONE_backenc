# Django API boilerplate

This project is an opinionated boilerplate intended to be used in projects that
require an API to be built and have the constraint to be a Python/Django
project. This project includes:

- A Django based project
- API built with [django-ninja](https://django-ninja.rest-framework.com/)
- Testing with [pytest](https://docs.pytest.org/en/6.2.x/)
- Linting with [flake8](https://flake8.pycqa.org/en/latest/index.html) and a few
  plugins:
  - [flake8-print](https://github.com/JBKahn/flake8-print)
- Fully dockerized

# Dependencies

We recommend that you locally (as in, not in a virtualenv) install
[taskipy](https://github.com/illBeRoy/taskipy) and
[poetry](https://python-poetry.org/). For that, you can use
[pipx](https://github.com/pypa/pipx).

# Tasks

Having taskipy, installed, there are a couple of tasks defined, of which these are the most important:

- `task dev`: runs the project at localhost:8001
- `task manage`: this runs `manage.py` inside the container
- `task test`: runs tests for this project

You can read other tasks [here](./pyproject.toml)

# AWS ECS Deployment

To deploy to AWS ECS execute the following commands:
1. `aws ecr get-login-password --region us-east-1
		| docker login --username AWS --password-stdin
		431123352116.dkr.ecr.us-east-1.amazonaws.com` 
2. `docker-compose build`
3. With the new image ID: 

		`docker tag {image ID} 431123352116.dkr.ecr.us-east-1.amazonaws.com/captsone_image_repo`

4. `docker push 431123352116.dkr.ecr.us-east-1.amazonaws.com/captsone_image_repo`

After force a new deployment of the ECS Service.

# FINTOC Settings

Fintoc credentials and api keys are stored in AWS secret manager. To update
this credentials edit their value in AWS secret manager and force a new deployment
of the ECS service.
