import boto3
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.email.providers.base import EmailMessage, EmailProvider


class SESProvider(EmailProvider):
    def __init__(self):
        self.client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    async def send(self, message: EmailMessage) -> bool:
        try:
            source = (
                f"{message.from_name} <{message.from_email}>"
                if message.from_name
                else message.from_email
            )

            response = self.client.send_email(
                Source=source or settings.SES_FROM_EMAIL,
                Destination={"ToAddresses": [message.to]},
                Message={
                    "Subject": {"Data": message.subject},
                    "Body": {
                        "Html": {"Data": message.html_body},
                        "Text": {"Data": message.text_body or ""},
                    },
                },
            )
            return response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            print(f"SES error: {e}")
            return False

    def is_configured(self) -> bool:
        return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
