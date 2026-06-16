"""Sync provider-admin identities into the main-backend admin store."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from commons.logger import logger
from core.database.database import MongoDatabase
from core.models.user_model import UserRole


logging = logger(__name__)

PROVIDER_SOURCE_DB_NAME = os.getenv(
    "PROVIDER_SOURCE_DB_NAME",
    "Insurance_aap_provider",
)


async def sync_provider_admins_to_main() -> None:
    """Mirror provider-admin accounts into the main-backend admin collection.

    The customer-app admin flow uses the main backend's ``users`` collection,
    while the provider app stores its admins inside ``provider_users``.
    This synchronisation keeps the same admin email and password usable across
    both backends by copying provider-admin identities into the main backend.
    """

    try:
        logging.info(
            "Starting provider-admin sync into main backend | source_db=%s",
            PROVIDER_SOURCE_DB_NAME,
        )
        main_db = MongoDatabase()
        provider_db = main_db.client[PROVIDER_SOURCE_DB_NAME]

        provider_admin_documents = await provider_db["provider_users"].find(
            {"user_role": "ADMIN"}
        ).to_list(length=None)

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for provider_admin in provider_admin_documents:
            normalized_email = str(provider_admin.get("email", "")).strip().lower()
            password_hash = provider_admin.get("password_hash")
            if not normalized_email or not password_hash:
                skipped_count += 1
                logging.warning(
                    "Skipping provider-admin sync for document %s due to missing email/password hash",
                    str(provider_admin.get("_id")),
                )
                continue

            now = datetime.now(timezone.utc)
            main_admin_payload: dict[str, Any] = {
                "first_name": provider_admin.get("first_name", "Admin"),
                "last_name": provider_admin.get("last_name", "User"),
                "email": normalized_email,
                "mobile_number": provider_admin.get("mobile_number")
                or "9999999999",
                "password": password_hash,
                "user_role": UserRole.ADMIN.value,
                "is_active": provider_admin.get("is_active", True),
                "updated_at": now,
            }

            existing_main_admin = await main_db["users"].find_one(
                {
                    "email": normalized_email,
                    "user_role": UserRole.ADMIN.value,
                }
            )
            if existing_main_admin is None:
                main_admin_payload["created_at"] = now
                main_admin_payload["last_login_at"] = provider_admin.get("last_login_at")
                main_admin_payload["otp"] = None
                await main_db["users"].insert_one(main_admin_payload)
                created_count += 1
                logging.info(
                    "Created missing main-backend admin for email %s",
                    normalized_email,
                )
                continue

            await main_db["users"].update_one(
                {"_id": existing_main_admin["_id"]},
                {
                    "$set": {
                        "first_name": main_admin_payload["first_name"],
                        "last_name": main_admin_payload["last_name"],
                        "mobile_number": main_admin_payload["mobile_number"],
                        "password": main_admin_payload["password"],
                        "is_active": main_admin_payload["is_active"],
                        "updated_at": main_admin_payload["updated_at"],
                    }
                },
            )
            updated_count += 1

        logging.info(
            "Provider-admin sync completed | created=%s updated=%s skipped=%s",
            created_count,
            updated_count,
            skipped_count,
        )
    except Exception as error:
        logging.error("Failed to sync provider admins into main backend: %s", error)
        raise
