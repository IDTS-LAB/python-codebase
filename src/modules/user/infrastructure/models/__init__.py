"""Normalized user domain models following DDD principles.

This module contains all SQLAlchemy models for the normalized user domain:
- users: Core identity and authentication
- user_profiles: Personal information
- user_contacts: Multiple contact methods
- user_addresses: Multiple addresses
- user_settings: User preferences (JSONB)
- user_security: Security configuration
- user_verifications: Verification status
- user_sessions: Session management
"""

from .user_model import UserModel, UserStatus, AuthProvider
from .user_profile_model import UserProfileModel
from .user_contact_model import UserContactModel
from .user_address_model import UserAddressModel
from .user_settings_model import UserSettingsModel
from .user_security_model import UserSecurityModel
from .user_verification_model import UserVerificationModel
from .refresh_token_model import UserSessionModel

__all__ = [
    "UserModel",
    "UserStatus",
    "AuthProvider",
    "UserProfileModel",
    "UserContactModel",
    "UserAddressModel",
    "UserSettingsModel",
    "UserSecurityModel",
    "UserVerificationModel",
    "UserSessionModel",
]
