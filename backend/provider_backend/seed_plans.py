"""
Seed script — InsureFlow Provider Backend
==========================================
Inserts sample health insurance plans into the provider MongoDB database.

Run once from inside the provider_backend directory:
    python seed_plans.py
"""

import asyncio
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

# — Load env ——————————————————————————————————————————————————————————
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("PROVIDER_DB_NAME", "Insurance_aap_provider")

# — Sample plans ——————————————————————————————————————————————————————

PLANS = [
    {
        "company_name": "StarHealth Insurance",
        "logo_url": None,
        "plan_name": "Star Comprehensive Health Plan",
        "plan_code": "STAR-COMP-HEALTH-001",
        "insurance_type": "health",
        "coverage_amount": 500000.0,
        "base_premium": 8500.0,
        "duration_years": 1,
        "benefits": [
            "Hospitalisation cover up to sum insured",
            "Pre and post hospitalisation expenses",
            "Day care treatments",
            "Ambulance charges",
            "No-claim bonus 10% per year",
        ],
        "terms": "Waiting period of 30 days for general illness. 2-year waiting for pre-existing conditions.",
        "available_add_ons": [
            {
                "name": "Critical Illness Rider",
                "description": "Additional lump-sum payout on diagnosis of 32 critical illnesses.",
                "price": 2500.0,
            },
            {
                "name": "Maternity Cover",
                "description": "Covers normal and C-section delivery expenses up to ₹50,000.",
                "price": 3200.0,
            },
        ],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "company_name": "HDFC ERGO",
        "logo_url": None,
        "plan_name": "HDFC ERGO Optima Secure",
        "plan_code": "HDFC-OPTIMA-SEC-001",
        "insurance_type": "health",
        "coverage_amount": 1000000.0,
        "base_premium": 14200.0,
        "duration_years": 1,
        "benefits": [
            "Cashless treatment at 13,000+ hospitals",
            "Restore benefit — sum insured refilled once per year",
            "Day care procedures covered",
            "Pre and post hospitalisation (60/180 days)",
            "Annual health check-up",
        ],
        "terms": "30-day initial waiting period. 4-year wait for specific illnesses.",
        "available_add_ons": [
            {
                "name": "Personal Accident Cover",
                "description": "₹10 lakh accidental death and disability benefit.",
                "price": 1800.0,
            },
            {
                "name": "Super NCB",
                "description": "50% increase in sum insured for every claim-free year.",
                "price": 1200.0,
            },
        ],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "company_name": "StarHealth Insurance",
        "logo_url": None,
        "plan_name": "Star Family Floater Plan",
        "plan_code": "STAR-FAM-FLOAT-001",
        "insurance_type": "health",
        "coverage_amount": 750000.0,
        "base_premium": 11800.0,
        "duration_years": 1,
        "benefits": [
            "Family floater cover for up to 6 members",
            "Hospitalisation up to sum insured",
            "Pre and post hospitalisation expenses",
            "Free health check-up after 2 claim-free years",
        ],
        "terms": "30-day initial waiting period. Pre-existing conditions covered after 3 years.",
        "available_add_ons": [
            {
                "name": "Room Rent Waiver",
                "description": "No sub-limits on room rent category.",
                "price": 1500.0,
            },
        ],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
]


async def seed():
    """Insert sample plans into the provider database."""

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["plans"]

    existing_count = await collection.count_documents({})
    if existing_count > 0:
        print(f"⚠  Plans collection already has {existing_count} document(s). Skipping seed.")
        client.close()
        return

    result = await collection.insert_many(PLANS)
    print(f"✅ Inserted {len(result.inserted_ids)} sample plans into '{DB_NAME}.plans'.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
