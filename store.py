import redis


class Store(object):
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = str(host)
        self.port = int(port)
        self.db = int(db)

    def get(self, key, attempts=5):
        value = None
        r = redis.StrictRedis(host=self.host, port=self.port, db=self.db, socket_timeout=5)
        while attempts > 0:
            try:
                value = r.get(key)
                return value
            except TimeoutError:
                attempts -= 1
                continue
        if value is None:
            raise ConnectionError("Can't connect to storage")

    def set(self, key, value, attempts=5):
        r = redis.StrictRedis(host=self.host, port=self.port, db=self.db, socket_timeout=5)
        while attempts > 0:
            try:
                r.set(key, value)
                return True
            except TimeoutError:
                attempts -= 1
                continue
        return False

    def cache_get(self, key, attempts=1):
        r = redis.StrictRedis(host=self.host, port=self.port, db=self.db, socket_timeout=5)
        while attempts > 0:
            try:
                value = r.get(key)
                return value
            except TimeoutError:
                attempts -= 1
                continue
        return None

    def cache_set(self, key, value, time, attempts=5):
        while attempts > 0:
            try:
                r = redis.StrictRedis(host=self.host, port=self.port, db=self.db, socket_timeout=5)
                r.setex(key, time, value)
                return
            except TimeoutError:
                attempts -= 1
                continue
        return


if __name__ == '__main__':
    store = Store()
    store.set('key1', ['val1', 'val2'])
    lst = store.get('key1')
    print(lst)
    lst = store.get('key2')
    print(lst)




