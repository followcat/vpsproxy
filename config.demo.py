import subprocess


_, PROXY_KEY = subprocess.getstatusoutput('hostname')

REDIS_HOST = '1.15.85.134'
REDIS_PORT = 6379
REDIS_PASSWORD = ''
GET_BAN_URL = 'http://1.15.85.134:5000/ban'
