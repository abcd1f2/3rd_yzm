# coding: utf-8

import time
import re

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

# 获取结果后1分钟后删除
delay_delete_time_when_success = 60
# 超时10分钟后删除
delay_delete_time_when_timeout = 600


class phone_item(object):
    def __init__(self, d_time=0, get_result=1):
        self.deadline_time = d_time
        self.is_get_result = get_result


def my_post(user_name, pass_wd, business_id, get_numbers, get_interval, max_time):
    """
    @:params
    @user_name 用户名
    @pass_wd 密码
    @business_id 业务ID
    @get_numbers 要取的号码数
    @get_interval 取结果间隔时间 取号间隔
    @max_time 取结果最大时间 超过这个时间丢弃
    """

    # 最大获取结果时间，60秒过后不用获取了
    max_get_results_time = max_time

    try:
        conn = sqlite3.connect('phone_sms.db')
    except Exception as e:
        print u"sqlite3 error {0}".format(e)
        return

    # http://api.jyzszp.com/Api/index/loginIn?uid=用户名&pwd=密码
    login_url = 'http://api.jyzszp.com/Api/index/loginIn?uid={0}&pwd={1}'.format(user_name, pass_wd)
    login_res = None
    try:
        login_res = requests.get(login_url)
    except Exception as e:
        print u"request error {0}".format(e)
        return
    if login_res.status_code != 200:
        print u"requests error {0}".format(login_res.status_code)
        return
    print "login ", login_res.content
    s = login_res.content.split('|')
    if len(s) != 3:
        print u"response error {0}".format(login_res.content)
        return
    user_token = s[2]

    get_numbers_time = int(time.time())
    all_phone_map = {}

    while True:
        if get_numbers_time <= int(time.time()):
            get_numbers_time += get_interval
            # http://api.jyzszp.com/Api/index/getMobilenum?pid=项目 ID&uid=用户名&token=登录时返回的令牌 &mobile=指定手机号码&size=1
            # 手机号码|token注意：多个号码返回值：手机号;手机号;手机号| token
            get_mobile_num_url = 'http://api.jyzszp.com/Api/index/getMobilenum?pid={0}&uid={1}&token={2}&size={3}'.\
                format(business_id, user_name, user_token, get_numbers)
            try:
                requests_response = requests.get(get_mobile_num_url)
            except Exception as e:
                print u"requests error {0}".format(e)
                continue

            print u'requests_response.content {0}'.format(requests_response.content)
            res = requests_response.content
            if not re.match('^[1-9][0-9]{10,}', res):
                print u"response error {0} {1}".format(res, requests_response.status_code)
                continue

            s = res.split('|')
            if len(s) != 2:
                print u"response error {0}".format(res)
                continue

            for mobile_item in s[0].split(';'):
                try:
                    conn.execute("insert into all_phone(phone) values({0})".format(int(mobile_item)))
                    all_phone_map[mobile_item] = phone_item(int(time.time()) + max_get_results_time)
                except Exception as e:
                    print u"execute all_phone error {0}".format(e)
            conn.commit()

        if len(all_phone_map) > 0:
            for mobile_item in all_phone_map.keys():
                if all_phone_map[mobile_item].deadline_time <= int(time.time()) and all_phone_map[mobile_item].is_get_result == 0:
                    try:
                        conn.execute("delete from all_phone where phone = {0}".format(int(mobile_item)))
                        conn.execute("delete from get_phone_sms where phone_times = {0}".format(int(mobile_item)))
                    except Exception as e:
                        print u"execute all_phone error {0}".format(e)
                        continue
                    else:
                        conn.commit()
                    finally:
                        all_phone_map.pop(mobile_item)
                elif all_phone_map[mobile_item].is_get_result == 1:
                    if all_phone_map[mobile_item].deadline_time > int(time.time()):
                        cursor = conn.execute("select phone_times from get_phone_sms where phone_times = {0}".format(int(mobile_item)))
                        for row in cursor:
                            if row[0]:
                                time.sleep(1)
                                # http://api.jyzszp.com/Api/index/getVcodeAndReleaseMobile?uid=用户&token=登录时返回的令牌&mobile=获取到的手机号码&pid=项目ID
                                # 成功返回：手机号码|验证码|短信内容
                                get_vcode_url = 'http://api.jyzszp.com/Api/index/getVcodeAndReleaseMobile?uid={0}&token={1}&mobile={2}&pid={3}'. \
                                    format(user_name, user_token, mobile_item, business_id)
                                try:
                                    requests_response = requests.get(get_vcode_url, timeout=max_time)
                                except requests.Timeout as e:
                                    # http://api.jyzszp.com/Api/index/addIgnoreList?uid=用户名&token=登录时返回的令牌&mobiles=号码1,号码2,号码3&pid=项目ID
                                    try:
                                        back_url = 'http://api.jyzszp.com/Api/index/addIgnoreList?uid={0}&token={1}&mobiles={2}&pid={3}'.format(
                                            user_name, user_token, mobile_item, business_id)
                                        r = requests.get(back_url)
                                        if r.status_code == 200:
                                            print u"set mobile {0} back".format(mobile_item)
                                    except Exception:
                                        continue
                                    finally:
                                        all_phone_map[mobile_item].is_get_result = 0
                                        all_phone_map[mobile_item].deadline_time = int(time.time()) + delay_delete_time_when_timeout
                                except Exception as e:
                                    print u"request error {0}".format(e)
                                    all_phone_map[mobile_item].is_get_result = 0
                                    all_phone_map[mobile_item].deadline_time = int(time.time()) + delay_delete_time_when_timeout
                                    continue

                                res = requests_response.content
                                print u"getVcodeAndReleaseMobile {0} {1}".format(mobile_item, res)
                                if not re.match('^[1-9][0-9]{10,}', res):
                                    print u"response error {0} {1}".format(mobile_item, res)
                                    continue
                                s = res.split('|')
                                if len(s) != 3:
                                    print u"response error {0}".format(mobile_item, res)
                                    continue

                                all_phone_map[mobile_item].is_get_result = 0
                                all_phone_map[mobile_item].deadline_time = int(time.time()) + delay_delete_time_when_success

                                try:
                                    conn.execute("insert into phone_sms(phone, sms) values({0}, '{1}')".format(int(mobile_item), s[2]))
                                except Exception as e:
                                    print u"sql error {0} s2 {1}".format(e, s[2])
                                    continue
                                else:
                                    conn.commit()
                    else:
                        all_phone_map[mobile_item].is_get_result = 0
                        all_phone_map[mobile_item].deadline_time = int(time.time()) + delay_delete_time_when_timeout
                else:
                    time.sleep(1)
        else:
            time.sleep(1)


if __name__ == "__main__":
    user = 'yumi11'
    pass_wd = 'shijian123'
    business_id = 1199
    my_post(user, pass_wd, business_id, 2, 3, 4)



