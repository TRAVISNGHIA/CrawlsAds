from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB: {settings.MONGO_URI}")
        # Create indexes
        await db.crawl_runs.create_index("run_id", unique=True)
        await db.ad_results.create_index("run_id")
        await db.ad_results.create_index("keyword")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


async def disconnect_db():
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


def get_db():
    return db
