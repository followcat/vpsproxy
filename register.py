# coding=utf-8
import re
import time
import requests
import subprocess
from requests.exceptions import ConnectionError, ReadTimeout
from redis import StrictRedis

from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, PROXY_KEY, GET_BAN_URL

# 拨号间隔
ADSL_CYCLE = 2
# 拨号出错重试间隔
ADSL_ERROR_CYCLE = 3

# ADSL命令
ADSL_BASH = 'pppoe-stop ; pppoe-start'
TINYPROXY_BASH = 'systemctl restart tinyproxy.service'
# 代理运行端口
PROXY_PORT = 8888

# 拨号网卡
ADSL_IFNAME = 'ppp0'

# 测试URL
TEST_URL = 'http://www.baidu.com'

# 测试超时时间
TEST_TIMEOUT = 5


class Sender():
    def get_ip(self, ifname=ADSL_IFNAME):
        """
        获取本机IP
        :param ifname: 网卡名称
        :return:
        """
        ip = None
        (status, output) = subprocess.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + r'.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
            result = re.search(pattern, output)
        if result:
            ip = result.group(1)
        return ip

    def test_proxy(self, proxy):
        """
        测试代理
        :param proxy: 代理
        :return: 测试结果
        """
        try:
            response = requests.get(TEST_URL, proxies={
                'http': 'http://' + proxy,
                'https': 'https://' + proxy
            }, timeout=TEST_TIMEOUT)
            if response.status_code == 200:
                return True
        except (ConnectionError, ReadTimeout):
            return False

    def remove_proxy(self):
        """
        移除代理
        :return: None
        """
        redis = StrictRedis(
            host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)
        redis.hdel('proxy', PROXY_KEY)
        print('Successfully Removed Proxy')

    def set_proxy(self, proxy):
        """
        设置代理
        :param proxy: 代理
        :return: None
        """
        rediscli = StrictRedis(
            host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)
        if rediscli.hset('proxy', PROXY_KEY, proxy):
            print('Successfully Set Proxy', proxy)

    def get_bans(self):
        try:
            bans = requests.get(GET_BAN_URL)
            return bans.json()['data']
        except Exception as e:
            return list()

    def change_ip(self):
        result = False
        print('ADSL Start, Remove Proxy, Please wait')
        try:
            self.remove_proxy()
        except Exception as e:
            print("Redis", e)
            return False
        (status, output) = subprocess.getstatusoutput(ADSL_BASH)
        ip = self.get_ip()
        if status == 0 and ip:
            print('ADSL Successfully')
            print('Now IP', ip)
            print('Testing Proxy, Please Wait')
            proxy = '{ip}:{port}'.format(ip=ip, port=PROXY_PORT)
            if self.test_proxy('{ip}:{port}'.format(ip='127.0.0.1', port=PROXY_PORT)):
                print('Valid Proxy')
                try:
                    self.set_proxy(proxy)
                except Exception:
                    print("Redis", e)
                    return False
                result = True
            else:
                (status, output) = subprocess.getstatusoutput(TINYPROXY_BASH)
                result = False
        else:
            print('ADSL Failed, Please Check')
            time.sleep(ADSL_ERROR_CYCLE)
            result = False
        return result

    def adsl(self):
        """
        拨号主进程
        :return: None
        """
        self.change_ip()
        while(True):
            changed = False
            ip = self.get_ip()
            bans = self.get_bans()
            print(ip, bans)
            if ip is None or ip in bans:
                changed = self.change_ip()
                ip = self.get_ip()
            if ip is not None:
                proxy = '{ip}:{port}'.format(ip=ip, port=PROXY_PORT)
                if not self.test_proxy('{ip}:{port}'.format(ip='127.0.0.1', port=PROXY_PORT)):
                    self.change_ip()
            time.sleep(ADSL_CYCLE)

if __name__ == '__main__':
    sender = Sender()
    sender.adsl()
