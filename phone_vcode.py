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


def my_post(user_name, pass_wd, business_id, get_numbers, get_interval, max_time):
    """
    @:params
    @user_name 用户名
    @pass_wd 密码
    @business_id 业务ID
    @get_numbers 要取的号码数
    @get_interval 取结果间隔时间
    @max_time 取结果最大时间
    """

    try:
        conn = sqlite3.connect('phone_sms.db')
    except Exception as e:
        print "sqlite3 error {0}".format(e)
        return

    # http://api.jyzszp.com/Api/index/loginIn?uid=用户名&pwd=密码
    login_url = 'http://api.jyzszp.com/Api/index/loginIn?uid={0}&pwd={1}'.format(user_name, pass_wd)
    login_res = None
    try:
        login_res = requests.get(login_url)
    except Exception as e:
        print "request error {0}".format(e)
        return
    if login_res.status_code != 200:
        print "requests error {0}".format(login_res.status_code)
        return
    print "login ", login_res.content
    s = login_res.content.split('|')
    if len(s) != 3:
        print "response error {0}".format(login_res.content)
        return
    user_token = s[2]

    # http://api.jyzszp.com/Api/index/getMobilenum?pid=项目 ID&uid=用户名&token=登录时返回的令牌 &mobile=指定手机号码&size=1
    get_mobile_num_url = 'http://api.jyzszp.com/Api/index/getMobilenum?pid={0}&uid={1}&token={2}&size={3}'.\
        format(business_id, user_name, user_token, get_numbers)
    try:
        requests_response = requests.get(get_mobile_num_url)
    except Exception as e:
        print "requests error {0}".format(e)
        return
    # 手机号码|token注意：多个号码返回值：手机号;手机号;手机号| token
    print 'requests_response.content ', requests_response.content
    res = requests_response.content
    #res = '13524298699;13524298633|' + user_token
    if not re.match('^[1-9][0-9]{10,}', res):
        print "response error {0}".format(res)
        return

    s = res.split('|')
    if len(s) != 2:
        print "response error {0}".format(res)
        return
    mobiles = s[0].split(';')
    for mobile_item in mobiles:
        try:
            conn.execute("insert into all_phone(phone) values({0})".format(int(mobile_item)))
            conn.commit()
        except Exception as e:
            print "execute all_phone error {0}".format(e)

    while True:
        for mobile_item in mobiles:
            time.sleep(get_interval)
            cursor = conn.execute("select phone_times from get_phone_sms where phone_times = {0}".format(int(mobile_item)))
            print cursor, type(cursor)
            for row in cursor:
                if row[0]:
                    time.sleep(1)
                    # http://api.jyzszp.com/Api/index/getVcodeAndReleaseMobile?uid=用户&token=登录时返回的令牌&mobile=获取到的手机号码&pid=项目ID
                    # 成功返回：手机号码|验证码|短信内容
                    get_vcode_url = 'http://api.jyzszp.com/Api/index/getVcodeAndReleaseMobile?uid={0}&token={1}&mobile={2}&pid={3}'.\
                        format(user_name, user_token, mobile_item, business_id)

                    try:
                        requests_response = requests.get(get_vcode_url, timeout=max_time)
                    except requests.Timeout as e:
                        # http://api.jyzszp.com/Api/index/addIgnoreList?uid=用户名&token=登录时返回的令牌&mobiles=号码1,号码2,号码3&pid=项目ID
                        try:
                            back_url = 'http://api.jyzszp.com/Api/index/addIgnoreList?uid={0}&token={1}&mobiles={2}&pid={3}'.format(user_name, user_token, mobile_item, business_id)
                            r = requests.get(back_url)
                            if r.status_code == 200:
                                print "set mobile {0} back".format(mobile_item)
                        except Exception:
                            pass
                        break
                    except Exception as e:
                        print "request error {0}".format(e)
                        break
                    res = requests_response.content
                    if not re.match('^[1-9][0-9]{10,}', res):
                        print "response error {0}".format(res)
                        break
                    s = res.split('|')
                    if len(s) != 3:
                        print "response error {0}".format(res)
                        break

                    try:
                        conn.execute("delete from get_phone_sms where phone_times = {0}".format(int(mobile_item)))
                        conn.execute("insert into phone_sms(phone, sms) values({0}, {1})".format(int(mobile_item), s[2]))
                        conn.commit()
                    except Exception as e:
                        print "sql error {0}".format(e)
                        break


if __name__ == "__main__":
    user = 'yumi11'
    pass_wd = 'shijian123'
    business_id = 1027
    my_post(user, pass_wd, business_id, 2, 3, 4)
