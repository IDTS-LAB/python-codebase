from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.user.domain.entities.user import (
    User,
    UserProfile,
    UserSecurity,
    UserSettings,
)
from src.modules.user.domain.repositories.user_repository import UserRepository
from src.modules.user.infrastructure.models.user_model import UserModel
from src.modules.user.infrastructure.models.user_profile_model import UserProfileModel
from src.modules.user.infrastructure.models.user_security_model import UserSecurityModel
from src.modules.user.infrastructure.models.user_settings_model import UserSettingsModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        self._db = db
        self._tenant_id = tenant_id

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email == email)
        if self._tenant_id:
            stmt = stmt.where(UserModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None

        return self._map_to_entity(user_model)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        if self._tenant_id:
            stmt = stmt.where(UserModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        return self._map_to_entity(user_model)

    async def get_by_id_with_relations(self, user_id: int) -> Optional[User]:
        """Get user with profile, settings, and security eagerly loaded."""
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.profile),
                selectinload(UserModel.settings),
                selectinload(UserModel.security),
            )
            .where(UserModel.id == user_id)
        )
        if self._tenant_id:
            stmt = stmt.where(UserModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        return self._map_to_entity_with_relations(user_model)

    async def save(self, user: User) -> User:
        # Check if user exists
        existing = await self.get_by_id(user.id)

        if existing:
            # Update existing user
            user_model = await self._get_user_model(user.id)
            user_model.email = user.email
            user_model.username = user.username
            user_model.password_hash = user.password_hash
            user_model.auth_provider = user.auth_provider
            user_model.status = user.status
            user_model.external_id = user.external_id
        else:
            # Create new user
            model_kwargs = {
                "email": user.email,
                "username": user.username,
                "password_hash": user.password_hash,
                "auth_provider": user.auth_provider,
                "status": user.status,
                "external_id": user.external_id,
                "tenant_id": self._tenant_id or user.tenant_id,
            }
            if user.id is not None:
                model_kwargs["id"] = user.id
            user_model = UserModel(**model_kwargs)
            self._db.add(user_model)
            await self._db.flush()

            # Create default related records
            await self._create_default_related_records(user_model.id)

        await self._db.flush()
        await self._db.refresh(user_model)
        return self._map_to_entity(user_model)

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        existing = await self._db.execute(
            select(UserProfileModel).where(UserProfileModel.user_id == profile.user_id)
        )
        profile_model = existing.scalar_one_or_none()

        if profile_model:
            profile_model.first_name = profile.first_name
            profile_model.last_name = profile.last_name
            profile_model.display_name = profile.display_name
            profile_model.avatar_url = profile.avatar_url
            profile_model.bio = profile.bio
            profile_model.birth_date = profile.birth_date
        else:
            profile_model = UserProfileModel(
                user_id=profile.user_id,
                tenant_id=self._tenant_id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                bio=profile.bio,
                birth_date=profile.birth_date,
            )
            self._db.add(profile_model)

        await self._db.flush()
        await self._db.refresh(profile_model)
        return self._map_profile_to_entity(profile_model)

    async def save_settings(self, settings: UserSettings) -> UserSettings:
        existing = await self._db.execute(
            select(UserSettingsModel).where(
                UserSettingsModel.user_id == settings.user_id
            )
        )
        settings_model = existing.scalar_one_or_none()

        if settings_model:
            settings_model.preferences = settings.preferences
        else:
            settings_model = UserSettingsModel(
                user_id=settings.user_id,
                tenant_id=self._tenant_id,
                preferences=settings.preferences,
            )
            self._db.add(settings_model)

        await self._db.flush()
        await self._db.refresh(settings_model)
        return self._map_settings_to_entity(settings_model)

    async def save_security(self, security: UserSecurity) -> UserSecurity:
        existing = await self._db.execute(
            select(UserSecurityModel).where(
                UserSecurityModel.user_id == security.user_id
            )
        )
        security_model = existing.scalar_one_or_none()

        if security_model:
            security_model.failed_login_attempts = security.failed_login_attempts
            security_model.locked_until = security.locked_until
            security_model.password_changed_at = security.password_changed_at
            security_model.two_factor_enabled = security.two_factor_enabled
            security_model.two_factor_secret = security.two_factor_secret
            security_model.two_factor_backup_codes = security.two_factor_backup_codes
        else:
            security_model = UserSecurityModel(
                user_id=security.user_id,
                tenant_id=self._tenant_id,
                failed_login_attempts=security.failed_login_attempts,
                locked_until=security.locked_until,
                password_changed_at=security.password_changed_at,
                two_factor_enabled=security.two_factor_enabled,
                two_factor_secret=security.two_factor_secret,
                two_factor_backup_codes=security.two_factor_backup_codes,
            )
            self._db.add(security_model)

        await self._db.flush()
        await self._db.refresh(security_model)
        return self._map_security_to_entity(security_model)

    async def _get_user_model(self, user_id: int) -> UserModel:
        stmt = select(UserModel).where(UserModel.id == user_id)
        if self._tenant_id:
            stmt = stmt.where(UserModel.tenant_id == self._tenant_id)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def _create_default_related_records(self, user_id: int) -> None:
        """Create default profile, settings, and security records for a new user."""
        # Default profile
        profile_model = UserProfileModel(user_id=user_id, tenant_id=self._tenant_id)
        self._db.add(profile_model)

        # Default settings
        settings_model = UserSettingsModel(
            user_id=user_id,
            tenant_id=self._tenant_id,
            preferences={
                "language": "en",
                "timezone": "UTC",
                "theme": "light",
                "notifications": {
                    "email": True,
                    "push": False,
                },
            },
        )
        self._db.add(settings_model)

        # Default security
        security_model = UserSecurityModel(
            user_id=user_id,
            tenant_id=self._tenant_id,
            failed_login_attempts=0,
            two_factor_enabled=False,
        )
        self._db.add(security_model)

    def _map_to_entity(self, user_model: UserModel) -> User:
        return User(
            id=user_model.id,
            email=user_model.email,
            password_hash=user_model.password_hash,
            username=user_model.username,
            auth_provider=user_model.auth_provider,
            status=user_model.status,
            external_id=user_model.external_id,
            created_at=user_model.created_at.isoformat(),
            updated_at=user_model.updated_at.isoformat(),
        )

    def _map_to_entity_with_relations(self, user_model: UserModel) -> User:
        user = self._map_to_entity(user_model)

        if user_model.profile:
            user.profile = self._map_profile_to_entity(user_model.profile)

        if user_model.settings:
            user.settings = self._map_settings_to_entity(user_model.settings)

        if user_model.security:
            user.security = self._map_security_to_entity(user_model.security)

        return user

    def _map_profile_to_entity(self, profile_model: UserProfileModel) -> UserProfile:
        return UserProfile(
            user_id=profile_model.user_id,
            first_name=profile_model.first_name,
            last_name=profile_model.last_name,
            display_name=profile_model.display_name,
            avatar_url=profile_model.avatar_url,
            bio=profile_model.bio,
            birth_date=profile_model.birth_date,
            created_at=profile_model.created_at.isoformat(),
            updated_at=profile_model.updated_at.isoformat(),
        )

    def _map_settings_to_entity(
        self, settings_model: UserSettingsModel
    ) -> UserSettings:
        return UserSettings(
            user_id=settings_model.user_id,
            preferences=settings_model.preferences or {},
            created_at=settings_model.created_at.isoformat(),
            updated_at=settings_model.updated_at.isoformat(),
        )

    def _map_security_to_entity(
        self, security_model: UserSecurityModel
    ) -> UserSecurity:
        return UserSecurity(
            user_id=security_model.user_id,
            failed_login_attempts=security_model.failed_login_attempts,
            locked_until=security_model.locked_until,
            password_changed_at=security_model.password_changed_at,
            two_factor_enabled=security_model.two_factor_enabled,
            two_factor_secret=security_model.two_factor_secret,
            two_factor_backup_codes=security_model.two_factor_backup_codes,
            created_at=security_model.created_at.isoformat(),
            updated_at=security_model.updated_at.isoformat(),
        )
