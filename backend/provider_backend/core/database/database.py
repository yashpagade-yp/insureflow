"""
database.py — MongoDB connection management for the Provider Backend.

Connects to the "insureflow_provider" database on the same Atlas cluster
as the main backend. Manages InsurancePlan, Quote, and Payment collections.

Pattern: identical to main_backend's database.py — only the DB name differs.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from motor import motor_asyncio, core
from odmantic import AIOEngine
from pymongo.driver_info import DriverInfo

# Load variables from this backend's own .env file.
ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH)

# Set up logging so connection events are visible in the console.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Identifies this application to MongoDB Atlas in connection logs.
DRIVER_INFO = DriverInfo(name="insureflow-provider", version="0.1.0")

# Read connection settings from environment — same cluster, different DB.
MONGODB_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017")   # same Atlas cluster URI
DATABASE_NAME = os.getenv("PROVIDER_DB_NAME", "insureflow_provider") # provider DB name


class _MongoClientSingleton:
    """
    Singleton holding the Motor client and ODMantic engine for the provider DB.
    Created once at startup and reused across all requests.
    """

    mongo_client: Optional[motor_asyncio.AsyncIOMotorClient] = None
    engine: Optional[AIOEngine] = None

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(_MongoClientSingleton, cls).__new__(cls)

            # Create the async Motor client (manages connection pool internally)
            cls.instance.mongo_client = motor_asyncio.AsyncIOMotorClient(
                MONGODB_URL, driver=DRIVER_INFO
            )

            # Wrap with ODMantic engine pointed at the provider database
            cls.instance.engine = AIOEngine(
                client=cls.instance.mongo_client, database=DATABASE_NAME
            )

            logger.info(f"Provider MongoDB singleton initialised | DB: {DATABASE_NAME}")

        return cls.instance


def MongoDatabase() -> core.AgnosticDatabase:
    """Return the raw Motor database — for aggregations or raw queries."""
    return _MongoClientSingleton().mongo_client[DATABASE_NAME]


def get_engine() -> AIOEngine:
    """
    Return the ODMantic AIOEngine for the provider database.
    Imported directly in CRUD classes — no FastAPI dependency injection needed.
    """
    return _MongoClientSingleton().engine


async def ping():
    """Verify the provider MongoDB connection is alive."""
    await MongoDatabase().command("ping")
    logger.info("Provider MongoDB ping successful")


async def connect_to_mongo():
    """
    Called at provider backend startup (lifespan).
    Initialises the singleton and verifies connectivity to insureflow_provider.
    """
    logger.info("Connecting to Provider MongoDB...")
    _MongoClientSingleton()
    await ping()
    logger.info("Provider MongoDB connection established")


async def close_mongo_connection():
    """
    Called at provider backend shutdown (lifespan).
    Closes the Motor client and releases all connection pool resources.
    """
    singleton = _MongoClientSingleton()
    if singleton.mongo_client:
        singleton.mongo_client.close()
        singleton.mongo_client = None
        singleton.engine = None
        if hasattr(_MongoClientSingleton, "instance"):
            delattr(_MongoClientSingleton, "instance")
        logger.info("Provider MongoDB connection closed")
