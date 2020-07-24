from redis import Redis

r = Redis()

with r.pipeline() as p:
    watch
    result = p.lpop('key1')
    p.zadd('key2', result)