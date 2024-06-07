import redis
from dotenv import load_dotenv
load_dotenv()
import os


redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_ENDPOINT'),
    port=int(os.getenv('REDIS_PORT')),
    decode_responses=True
)
