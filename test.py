import os
import redis
from dotenv import load_dotenv


load_dotenv()


REDIS_HOST_NAME = os.getenv("REDIS_HOST_NAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def get_from_redis():

    if REDIS_HOST_NAME is None:
        raise RuntimeError("HOST_NAME is not set in environment variables")
    if REDIS_PORT is None:
        raise RuntimeError("PORT_NUMBER is not set in environment variables")
    if REDIS_PASSWORD is None:
        raise RuntimeError("REDIS_PASSWORD is not set in environment variables")

    print(REDIS_HOST_NAME)
    print(REDIS_PORT)
    print(type(int(REDIS_PORT)))
    print(REDIS_PASSWORD)
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
            print(r.get("name"))
        else:
            print("no name exist")
    except Exception as e:
        print(f"error in login redis instance {str(e)}")

    #


get_from_redis()
