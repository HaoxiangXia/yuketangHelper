# -*- coding: utf-8 -*-
import os
import re
import json
import requests
import get_info
from videoHelper import videoHelper

try:
    from homeworkHelper import homeworkHelper
except ImportError:
    homeworkHelper = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_CONFIG = {
    "domain": "buu.yuketang.cn",
    "use_cached_cookies": True,
    "cookie_file": "cookie.txt",
    "course_number": None,
    "do_homework": False,
    "learning_rate": 12,
    "base_url": "https://api.openai.com/v1",
    "key": "",
    "model": "gpt-3.5-turbo",
    "system_prompt": "回答下面的问题,如果是填空题则按照下面的json格式返回答案，比如有2个空，则第一个空键为1，值为第一个空的答案，第二个空键为2，值为第二个空的答案。如果是选择题直接返回答案对应选项的字母,不要回复多余内容,如果不知道答案,请直接回答C,多选题回答格式是每个选项之间用一个半角逗号和一个空格分开，判断题只用返回true或false，不用回复标点符号。"
}


def load_config():
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                config.update(user_cfg)
                print(f"[配置] 成功加载配置文件: {CONFIG_FILE}")
        except Exception as e:
            print(f"[警告] 读取 {CONFIG_FILE} 失败，使用默认配置: {e}")
    else:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"[配置] 未找到配置文件，已自动生成默认配置: {CONFIG_FILE}")
        except Exception as e:
            print(f"[警告] 创建默认配置文件失败: {e}")
    return config


def clean_domain(domain_str):
    if not domain_str:
        return ""
    d = str(domain_str).strip()
    if d.startswith("http://"):
        d = d[7:]
    elif d.startswith("https://"):
        d = d[8:]
    return d.rstrip("/")


def main():
    config = load_config()

    domain = clean_domain(config.get("domain", ""))
    if not domain:
        domain = clean_domain(input("输入雨课堂域名：(BUU输入buu.yuketang.cn)\n").strip())

    use_cached = config.get("use_cached_cookies", True)
    cookie_file = config.get("cookie_file", "cookie.txt")
    if not os.path.isabs(cookie_file):
        cookie_file = os.path.join(BASE_DIR, cookie_file)

    print(f"[配置] 雨课堂域名: {domain}")
    print(f"[配置] Cookie 文件路径: {cookie_file}")
    cookies = get_info.getCookies(domain, use_cached=use_cached, cookie_file=cookie_file)
    csrftoken, sessionid = get_info.extract_specific_cookies(cookies)

    if not csrftoken or not sessionid:
        raise Exception(f"未能获取到 csrftoken 或 sessionid！如使用缓存 cookies，请尝试删除 {cookie_file} 或将 use_cached_cookies 设为 false 重新扫码登录。")

    university_id = "0"
    try:
        university_id = str(get_info.getUniversityId(domain))
    except Exception:
        pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Cookie": f"csrftoken={csrftoken}; sessionid={sessionid}; university_id={university_id}; platform_id=3",
        "x-csrftoken": csrftoken,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "university-id": university_id,
        "xtbz": "ykt",
    }

    # 获取用户的个人ID（user_id）及基本信息
    user_id = None
    user_realname = "同学"
    school_name = ""

    # 1. 优先尝试通用的 /api/v3/user/basic-info (适用于 www.yuketang.cn 及各区)
    try:
        basic_info_url = f"https://{domain}/api/v3/user/basic-info"
        res = requests.get(basic_info_url, headers=headers).json()
        if res.get("code") == 0 and res.get("data"):
            user_id = str(res["data"].get("id"))
            user_realname = res["data"].get("name", "同学")
            school_name = res["data"].get("school", "")
            print(f"欢迎您，{user_realname}{f'（{school_name}）' if school_name else ''}！")
    except Exception:
        pass

    # 2. 尝试 /v2/api/web/userinfo
    if not user_id:
        try:
            uinfo_url = f"https://{domain}/v2/api/web/userinfo"
            res = requests.get(uinfo_url, headers=headers).json()
            if res.get("errcode") == 0 and res.get("data"):
                user_id = str(res["data"][0].get("user_id"))
                user_realname = res["data"][0].get("name", "同学")
                print(f"欢迎您，{user_realname}！")
        except Exception:
            pass

    # 3. 尝试高校专属后台的 /edu_admin/check_user_session/
    if not user_id:
        try:
            user_id_url = f"https://{domain}/edu_admin/check_user_session/"
            id_response = requests.get(url=user_id_url, headers=headers)
            user_id = re.search(r'"user_id":(.+?)}', id_response.text).group(1).strip()
            user_info_url = f"https://{domain}/edu_admin/get_user_basic_info/"
            user_info_r = requests.get(url=user_info_url, headers=headers)
            user_info = json.loads(user_info_r.text)["data"]["user_info"]
            user_realname = user_info.get("name", "同学")
            print(f"欢迎您，{user_realname}！")
        except Exception:
            pass

    if not user_id:
        print(f"获取 user_id 失败！请检查 cookies 是否有效或已过期。")
        raise Exception("无法获取 user_id，程序退出。")

    # 获取课程列表
    courses = []

    # 1. 优先尝试通用接口 /v2/api/web/courses/list?identity=2 (适用于 www.yuketang.cn)
    try:
        c_url = f"https://{domain}/v2/api/web/courses/list?identity=2"
        c_res = requests.get(c_url, headers=headers).json()
        if c_res.get("errcode") == 0 and c_res.get("data", {}).get("list"):
            for item in c_res["data"]["list"]:
                raw_class_name = item.get("name", "")
                raw_course_name = item.get("course", {}).get("name", "")
                if raw_course_name and raw_course_name not in raw_class_name:
                    display_name = f"{raw_course_name} ({raw_class_name})"
                else:
                    display_name = raw_class_name or raw_course_name

                courses.append({
                    "course_name": display_name,
                    "classroom_id": item["classroom_id"],
                    "course_sign": item.get("course_sign", ""),
                    "sku_id": item.get("sku_id", 0),
                    "course_id": item.get("course", {}).get("id") or item.get("course_id", 0),
                    "university_id": str(item.get("course", {}).get("university_id") or university_id),
                    "teacher_name": item.get("teacher", {}).get("name", ""),
                })
    except Exception:
        pass

    # 2. 若未获取到，尝试高校专属接口 /mooc-api/v1/lms/user/user-courses/
    if not courses:
        try:
            get_classroom_id = (
                f"https://{domain}/mooc-api/v1/lms/user/user-courses/?status=1&page=1&no_page=1&term=latest&uv_id={university_id}"
            )
            classroom_id_response = requests.get(url=get_classroom_id, headers=headers)
            for ins in json.loads(classroom_id_response.text)["data"]["product_list"]:
                courses.append(
                    {
                        "course_name": ins["course_name"],
                        "classroom_id": ins["classroom_id"],
                        "course_sign": ins.get("course_sign", ""),
                        "sku_id": ins.get("sku_id", 0),
                        "course_id": ins["course_id"],
                        "university_id": university_id,
                    }
                )
        except Exception as e:
            raise Exception(f"获取课程列表失败: {e}")

    if not courses:
        print("未获取到任何课程！")
        return

    print("\n" + "=" * 60)
    print("                        课程列表")
    print("=" * 60)
    for index, value in enumerate(courses):
        teacher_str = f" (教师: {value['teacher_name']})" if value.get("teacher_name") else ""
        print(f"[{index + 1:2d}] {value['course_name']}{teacher_str}")
    print("=" * 60 + "\n")

    # 确定刷课编号（支持配置与交互式选择）
    configured_course = config.get("course_number")
    target_courses = []

    if configured_course is not None and str(configured_course).strip() != "":
        candidate = str(configured_course).strip()
        if candidate.isdigit() and int(candidate) <= len(courses):
            if int(candidate) == 0:
                target_courses = courses
                print(f"[配置] 自动选择: 全部课程（共 {len(courses)} 门）")
            else:
                target_courses = [courses[int(candidate) - 1]]
                print(f"[配置] 自动选择: {target_courses[0]['course_name']}")
        else:
            print(f"[警告] 配置中的 course_number ({configured_course}) 不合法，转为手动输入。")

    if not target_courses:
        while True:
            print("你想刷哪门课的视频呢？")
            print("  - 输入 0：刷全部课程")
            print("  - 输入课程序号（如 6）：刷该单门课程")
            print("  - 支持多选（如 6 8 10 或 6, 8）：刷多门指定课程")
            raw_inp = input("请输入课程编号: ").strip()
            if not raw_inp:
                continue
            raw_tokens = [t.strip() for t in raw_inp.replace("，", ",").replace(" ", ",").split(",") if t.strip()]
            valid = True
            parsed_nums = []
            for tok in raw_tokens:
                if tok.isdigit():
                    val = int(tok)
                    if 0 <= val <= len(courses):
                        parsed_nums.append(val)
                    else:
                        valid = False
                        break
                else:
                    valid = False
                    break
            if not valid or not parsed_nums:
                print(f"输入无效！请输入 0~{len(courses)} 之间的数字。")
                continue

            if 0 in parsed_nums:
                target_courses = courses
                print(f"\n已选定: 全部课程（共 {len(courses)} 门）")
                break
            else:
                seen = set()
                target_courses = []
                for n in parsed_nums:
                    if n not in seen:
                        seen.add(n)
                        target_courses.append(courses[n - 1])
                selected_names = "、".join([c["course_name"] for c in target_courses])
                print(f"\n已选定课程: {selected_names}（共 {len(target_courses)} 门）")
                break

    # 确定是否做作业
    configured_hw = config.get("do_homework")
    choice_hw = None
    if configured_hw is not None:
        choice_hw = bool(configured_hw)
        print(f"[配置] 是否做作业: {'开启（AI答题）' if choice_hw else '关闭（只刷课，跳过答题）'}")
    else:
        while True:
            inp = input("需不需要AI做作业（Y/N）：").strip()
            if inp in ("Y", "y"):
                choice_hw = True
                break
            elif inp in ("N", "n"):
                choice_hw = False
                break
            else:
                print("输入无效，请输入 Y 或 N。")

    learning_rate = config.get("learning_rate", 12)
    video_helper = videoHelper(domain, cookies, user_id, university_id, learning_rate, headers)

    if choice_hw:
        if homeworkHelper is None:
            print("[警告] 缺少 homeworkHelper 依赖，无法执行做作业，将仅刷课。")
            homework_helper = None
            choice_hw = False
        else:
            homework_helper = homeworkHelper(domain, cookies, user_id, university_id, headers)
    else:
        homework_helper = None

    # 多门课时询问是否每门课单独挑视频
    pick_video_per_course = True
    if len(target_courses) > 1:
        choice_pick = input("\n检测到选择了多门课程，是否需要为每门课单独选择要刷的视频？(Y: 单独挑选 / 回车或N: 自动刷所有视频) [默认N]: ").strip().lower()
        pick_video_per_course = (choice_pick == "y")

    print(f"\n开始刷课任务，共需处理 {len(target_courses)} 门课程...")
    for ins in target_courses:
        print(f"\n==================================================")
        print(f">>> 正在读取课程: {ins['course_name']}")
        print(f"==================================================")
        course_uv_id = str(ins.get("university_id") or university_id)
        video_helper.university_id = course_uv_id
        video_helper.headers["university-id"] = course_uv_id
        videos_id_name_dic = video_helper.get_videos_ids(
            ins["course_name"], ins["classroom_id"], ins.get("course_sign", "")
        )
        if not videos_id_name_dic:
            continue

        target_video_dic = videos_id_name_dic
        video_items = list(videos_id_name_dic.items())

        if pick_video_per_course:
            print(f"\n《{ins['course_name']}》共有 {len(video_items)} 个视频：")
            for v_idx, (v_id, v_name) in enumerate(video_items):
                print(f"  [{v_idx + 1:2d}] {v_name}")

            print("\n请选择要刷的视频：")
            print("  - 直接按回车 或 输入 0：刷本门课的全部视频")
            print("  - 输入视频序号（如 1）：只刷第 1 个视频")
            print("  - 输入多个序号（如 1 3 5 或 1,3,5）：只刷指定视频")
            v_input = input("请输入视频编号 [默认全部]: ").strip()

            if v_input and v_input != "0":
                v_tokens = [t.strip() for t in v_input.replace("，", ",").replace(" ", ",").split(",") if t.strip()]
                chosen_indices = []
                for tok in v_tokens:
                    if tok.isdigit():
                        val = int(tok)
                        if 1 <= val <= len(video_items):
                            chosen_indices.append(val - 1)
                if chosen_indices:
                    seen_v = set()
                    filtered_dic = {}
                    for idx in chosen_indices:
                        if idx not in seen_v:
                            seen_v.add(idx)
                            v_id, v_name = video_items[idx]
                            filtered_dic[v_id] = v_name
                    target_video_dic = filtered_dic
                    print(f"已选定 {len(target_video_dic)} 个视频进行学习！")
                else:
                    print("输入无效或超出范围，将默认刷全部视频。")
            else:
                print("已选择刷本课程全部视频。")

        course_id = ins["course_id"]
        classroom_id = ins["classroom_id"]
        sku_id = ins.get("sku_id", 0)
        video_helper.multiple_watch_video(
            target_video_dic, course_id, user_id, classroom_id, sku_id
        )

    if choice_hw and homework_helper:
        print("\n开始执行作业任务...")
        for ins in target_courses:
            print(f"\n>>> 正在完成作业: {ins['course_name']}")
            homework_helper.do_homework(
                ins["classroom_id"],
                ins["course_sign"],
                ins["course_name"],
            )

    print("\n搞定啦！")

if __name__ == "__main__":
    main()
