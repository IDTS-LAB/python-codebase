from typing import Optional

from pydantic import BaseModel, EmailStr


class EmailMessage(BaseModel):
    """Standard email message format"""

    to: EmailStr
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None
