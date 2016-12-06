# coding: utf-8

import time
import json

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    import sqlite3
except ImportError:
    sys.exit("Error: you need to install sqlite3")
try:
    import requests
except ImportError:
    sys.exit("Error: you need to install requests")

"""
@:params
@user_name 用户名
@pass_wd 密码
@business_id 业务ID
@get_numbers 要取的号码数
@get_interval 取结果间隔时间
@max_time 取结果最大时间
"""
def my_post(user_name, pass_wd, business_id, get_numbers, get_interval, max_time):
    """
    url = 'https://api.github.com/some/endpoint'
    payload = {'some': 'data'}
    headers = {'content-type': 'application/json'}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    """
    conn = None
    try:
        conn = sqlite3.connect('phone_sms.db')
    except Exception as e:
        print "sqlite3 error {0}".format(e)
        return
    cursor = conn.execute("select rowid, phone_times from get_phone_sms")
    for row in cursor:
        print row[0], row[1]
        if row[1] >= int(time.time()):
            payload = {'a': '杨', 'b': 'hello'}
            r = requests.post("http://www.jyzszp.com/index.php/index/api", data=payload)
            print r.content
            if r.status_code == 200:
                conn.execute("replace into phone_sms(phone,sms) values(%d, %s)", 100, 'hello')
                conn.execute("delete from all_phone where phone=%d", 100)
                conn.commit()

    conn.close()


if __name__ == "__main__":
    user = 'yumi11'
    pass_wd = 'shijian123'
    my_post(user, pass_wd, 1, 2, 3, 4)
