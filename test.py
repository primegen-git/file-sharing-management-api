import os
import redis
from dotenv import load_dotenv


load_dotenv()


REDIS_HOST_NAME = os.getenv("REDIS_HOST_NAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def get_from_redis():

    logger = __import__('logger').get_logger(__name__)
    if REDIS_HOST_NAME is None:
        logger.error("HOST_NAME is not set in environment variables")
        raise RuntimeError("HOST_NAME is not set in environment variables")
    if REDIS_PORT is None:
        logger.error("PORT_NUMBER is not set in environment variables")
        raise RuntimeError("PORT_NUMBER is not set in environment variables")
    if REDIS_PASSWORD is None:
        logger.error("REDIS_PASSWORD is not set in environment variables")
        raise RuntimeError("REDIS_PASSWORD is not set in environment variables")

    logger = __import__('logger').get_logger(__name__)
    logger.info(f"REDIS_HOST_NAME: {REDIS_HOST_NAME}")
    logger.info(f"REDIS_PORT: {REDIS_PORT}")
    logger.info(f"REDIS_PORT Type: {type(int(REDIS_PORT))}")
    logger.info(f"REDIS_PASSWORD: {REDIS_PASSWORD}")
    try:
        r = redis.Redis(
            host=REDIS_HOST_NAME,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD,
            ssl=True,
        )
        r.set("name", "uk")
        # r.set("name", "ujjawal")
        if r.exists("name"):
            logger.info(r.get("name"))
        else:
            logger.info("no name exist")
    except Exception as e:
        logger = __import__('logger').get_logger(__name__)
        logger.error(f"error in login redis instance {str(e)}")

    #


get_from_redis()
