import redis


class RedisClient:
    def __init__(self, host='redis', port=6379):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.client.flushall()

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

    def delete(self, key):
        self.client.delete(key)

    def set_hash(self, name, key, value):
        self.client.hset(name, key, value)

    def get_hash(self, name, key):
        return self.client.hget(name, key)

    def get_all_hash(self, name):
        return self.client.hgetall(name)

    def delete_hash_key(self, name, key):
        self.client.hdel(name, key)

    def delete_hash(self, name):
        self.client.delete(name)
