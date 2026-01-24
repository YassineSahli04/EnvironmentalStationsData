import os
from redis import Redis
from rq import Worker, Queue

def worker():
    redisUrl = os.environ.get("REDIS_URL")
    if redisUrl is None:
        raise ValueError("Redis Url is not defined")
    redis_connection = Redis.from_url(redisUrl)

    workerQueue = Queue(name="SemanticSearchQueue", connection=redis_connection)
    worker = Worker([workerQueue], connection=redis_connection, name = "SemanticSearchWorker")
    worker.work(with_scheduler=False)

if __name__ == "__main__":
    worker()