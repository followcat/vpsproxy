from flask import Flask, request
from redis import StrictRedis

from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, PROXY_KEY


app = Flask(__name__)

@app.route("/get/all")
def get_all():
    rediscli = StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    results = rediscli.hgetall('proxy')
    return {'data': [r.decode("utf-8") for r in results.values()]}


@app.route("/ban", methods=['GET'])
def get_ban():
    rediscli = StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    results = rediscli.smembers('ban')
    exists = set([r for r in rediscli.hgetall('proxy')])
    bans = set([r for r in results])
    unexists = bans - exists
    for v in results:
        if v in unexists:
            rediscli.srem('ban', v)
    return {'data': list([r.decode("utf-8") for r in rediscli.smembers('ban')])}


@app.route("/ban", methods=['POST'])
def post_ban():
    data = request.json
    rediscli = StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    for proxy in data:
        rediscli.sadd('ban', proxy)
        rediscli.expire('ban', 180)
    return 'True'


if __name__ == "__main__":
    app.run(host='0.0.0.0')
