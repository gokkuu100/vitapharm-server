import redis
from dotenv import load_dotenv
load_dotenv()
import os

# Correct Redis URL format
redis_url = os.getenv('REDIS_URL')

# Create a Redis client from the URL
r = redis.StrictRedis.from_url(redis_url)

# Test the connection
try:
    print(r.ping())
except redis.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
