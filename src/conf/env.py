from typing import List

from pydantic import BaseSettings


class EnvSettings(BaseSettings):
    # class Config:
    #     secrets_dir = '/run/secrets'

    # Specify directly. We don't want to leak anything
    django_secret_key: str = ""
    prod: bool = False
    debug: bool = False
    allowed_hosts: List[str] = [
        'capstonebackendlb-9055839.us-east-1.elb.amazonaws.com',
        'backend.nudoseline.com',
        'd36qgxdzumrtgg.cloudfront.net',
        'neline.cl',
        'www.neline.cl'
    ]
    csrf_trusted_origins: List[str] = [
        'https://d36qgxdzumrtgg.cloudfront.net/',
        'https://www.neline.cl/',
        'https://neline.cl'
    ]

    # Database settings
    database_engine: str = ""
    database_name: str = ""
    database_user: str = ""
    database_password: str = ""
    database_host: str = ""
    database_port: int = 0

    # Mailer settings
    email_use_tls: bool = True

    # Fintoc settings
    fintoc_holder_id: str = ""
    fintoc_institution_id: str = ""
    fintoc_number: str = ""
    fintoc_type: str = ""
    fintoc_key: str = ""
    fintoc_payment_uri: str = ""
    fintoc_webhook_secret: str = ""

    # AWS secrets
    secrets: dict[str, str] = {}

    max_file_size = 10485760  # 10MB
    max_file_number = 5


env = EnvSettings()
