# -*- coding: utf-8 -*-
# version 1
# developed by MuWinds
import os
import requests
import time
import get_websockets
import json


def getUniversityId(domain):
    url = (
        "https://"
        + domain
        + "/edu_admin/get_custom_university_info/?current=1&_="
        + str((round(time.time() * 1000)))
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
        "Content-Type": "application/json",
    }
    response = requests.get(url=url, headers=headers).json()
    data = response["data"]
    print(data["university_id"])
    return data["university_id"]


def getWebSocketInfo(domain):
    ws = None
    try:
        ws = get_websockets.WebSocketQrcode()
        message = ws.run(domain)
        return message
    except KeyboardInterrupt:
        print("\n检测到用户中断，正在关闭WebSocket连接...")
        if ws:
            ws.close()  # 确保 WebSocket 连接被关闭
        raise  # 重新抛出异常让外层处理
    except Exception as e:
        print(f"WebSocket连接发生错误: {e}")
        if ws:
            ws.close()
        return None


def getCookies(domain, use_cached=None, cookie_file="cookie.txt"):
    if not cookie_file.endswith(".txt"):
        cookie_file += ".txt"
    if not os.path.isabs(cookie_file):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_file = os.path.join(base_dir, cookie_file)
    if use_cached is True:
        if os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 0:
            print(f"正在读取已有 cookies 文件: {cookie_file}")
            with open(cookie_file, "r", encoding="utf-8") as ck_file:
                return ck_file.read().strip()
        else:
            print(f"未找到有效 cookie 文件（{cookie_file}），准备扫码登录...")
    elif use_cached is False:
        print("根据配置，准备重新扫码登录并覆盖 cookies...")
    else:
        is_cached = input(
            "是否用已有cookies?是输入1(否则会将原来的cookies以新获得cookies覆盖)"
        ).strip()
        if is_cached == "1":
            filename = input("请输入cookies文件名:").strip()
            if not filename.endswith(".txt"):
                filename += ".txt"
            with open(filename, "r", encoding="utf-8") as ck_file:
                return ck_file.read().strip()
        else:
            filename = input("请输入保存新cookies的文件名(默认cookie.txt): ").strip()
            if filename:
                cookie_file = filename if filename.endswith(".txt") else filename + ".txt"

    university_id = getUniversityId(domain)
    login_message = getWebSocketInfo(domain)
    if not login_message:
        raise Exception("登录失败，未收到登录消息！")
    # message转json
    message = json.loads(login_message)
    auth_info = message["Auth"]
    user_id = message["UserID"]
    verify_url = (
        "https://"
        + domain
        + "/edu_admin/account/login/verify-origin-system-bind?term=latest&uv_id="
        + str(university_id)
    )
    verify_header = {
        "referer": "https://" + domain + "/pro/portal/home/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Cookie": f"university_id={university_id};platform_id=3;xtbz=cloud;platform_type=1;",
        "Origin": "https://" + domain,
        "Platform-Id": "3",
        "University-Id": str(university_id),
        "Terminal-Type": "web",
        "X-Client": "web",
        "X-Csrftoken": "undefined",
        "Xtbz": "cloud",
    }
    verify_form = {"auth": auth_info, "origin_user_id": str(user_id)}
    response = requests.post(verify_url, json=verify_form, headers=verify_header)
    cookie = response.headers.get("Set-Cookie")
    if not cookie:
        try:
            res_data = response.json()
            if res_data.get("data", {}).get("bind_status") is False:
                err_msg = (
                    f"\n【微信身份未绑定或学校域名不匹配】\n"
                    f"服务器返回 bind_status: false。\n"
                    f"可能原因：\n"
                    f"1. 当前域名配置为 {domain}，如果你不是该校学生，请在 config.json 中修改为自己学校的雨课堂域名。\n"
                    f"2. 扫码的微信号尚未在雨课堂绑定学号身份（请在微信公众号【雨课堂】-> 我的 -> 身份绑定中绑定）。\n"
                    f"3. 推荐最快方式：直接在浏览器登录雨课堂，F12复制 Cookie 中的 csrftoken 和 sessionid 保存到 {cookie_file}。"
                )
                raise Exception(err_msg)
        except Exception as e:
            if "bind_status" in str(e):
                raise
        raise Exception(f"登录验证失败，未获取到 Set-Cookie！响应: {response.text}")
    with open(cookie_file, "w", encoding="utf-8") as ck_write:
        ck_write.write(cookie)
    print(f"登录成功，cookies 已保存至 {cookie_file}")
    return cookie


def extract_specific_cookies(cookie_string):
    cookies = {}
    if not cookie_string:
        return None, None
    # 尝试逗号分割
    for cookie in cookie_string.split(","):
        key_value = cookie.split(";")[0].strip()
        if "=" in key_value:
            key, value = key_value.split("=", 1)
            cookies[key.strip()] = value.strip()
    # 如果未获取到，再尝试分号分割
    if not cookies.get("csrftoken") or not cookies.get("sessionid"):
        for item in cookie_string.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                key = key.strip()
                if key.lower() not in ("path", "domain", "expires", "max-age", "secure", "httponly", "samesite"):
                    cookies[key] = value.strip()
    csrf = cookies.get("csrftoken")
    sess = cookies.get("sessionid")
    print("csrftoken:", csrf)
    print("sessionid:", sess)
    return csrf, sess
