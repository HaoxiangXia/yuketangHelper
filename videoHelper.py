# -*- coding: utf-8 -*-
import random
import time
import requests
import re
import json
import string

leaf_type = {"video": 0, "homework": 6, "exam": 5, "recommend": 3, "discussion": 4}


class videoHelper:
    def __init__(self, domain, cookies, user_id, university_id, learning_rate, header):
        self.domain = domain
        self.cookies = cookies
        self.user_id = user_id
        self.learning_rate = learning_rate
        self.university_id = university_id
        self.headers = header
        self.session = requests.Session()
        self.session.headers.update(header)
        # 确保 cookies 注入到 session 中
        if isinstance(cookies, dict):
            self.session.cookies.update(cookies)
        elif isinstance(cookies, str):
            for item in cookies.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    self.session.cookies.set(k.strip(), v.strip())

    def _request_with_retry(self, method, url, max_retries=3, timeout=15, **kwargs):
        for attempt in range(1, max_retries + 1):
            try:
                res = self.session.request(method, url, timeout=timeout, **kwargs)
                if res.status_code == 429 or "Expected available in" in res.text:
                    m = re.search(r"Expected available in\s*([0-9.]+)", res.text)
                    wait_sec = float(m.group(1)) + 2.0 if m else 30.0
                    print(f"    [限流保护] 触发雨课堂限流，等待 {wait_sec:.0f} 秒后重试...")
                    time.sleep(wait_sec)
                    continue
                return res
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    raise e
                time.sleep(2 * attempt)
        raise requests.exceptions.RequestException(f"请求失败（{method} {url}）已重试多次仍失败")

    def one_video_watcher(self, video_id, video_name, cid, user_id, classroomid, skuid):
        video_id = str(video_id)
        classroomid = str(classroomid)
        cid = str(cid)
        post_url = f"https://{self.domain}/video-log/heartbeat/"
        get_url = (
            f"https://{self.domain}/video-log/get_video_watch_progress/?cid={cid}"
            f"&user_id={user_id}&classroom_id={classroomid}&video_type=video&vtype=rate"
            f"&video_id={video_id}&snapshot=1&term=latest&uv_id={self.university_id}"
        )

        # 1. 检查当前进度
        try:
            p_res = self._request_with_retry("GET", get_url)
            vdata = p_res.json().get("data", {}).get(video_id, {})
        except Exception:
            vdata = {}

        completed = vdata.get("completed", 0)
        rate = float(vdata.get("rate", 0) or 0)
        if completed == 1 or rate >= 0.95:
            print(f"  [跳过] 《{video_name}》 已经学习完毕 (100.0%)")
            return 1

        # 2. 查询 leaf_info 获取真实 ccid 与 duration
        url_leaf = (
            f"https://{self.domain}/mooc-api/v1/lms/learn/leaf_info/{classroomid}/{video_id}/"
            f"?term=latest&uv_id={self.university_id}"
        )
        ccid = ""
        duration = float(vdata.get("video_length", 0) or 0)
        leaf_sku_id = skuid
        try:
            leaf_res = self._request_with_retry("GET", url_leaf).json()
            leaf_data = leaf_res.get("data", {})
            leaf_sku_id = leaf_data.get("sku_id") or skuid
            media = leaf_data.get("content_info", {}).get("media", {})
            ccid = media.get("ccid", "")
            if not duration:
                duration = float(media.get("duration", 0) or 0)
        except Exception:
            pass

        if not duration:
            duration = 1200.0

        print(f"  [开始] 《{video_name}》 (当前进度: {rate*100:.1f}%, 预计时长: {duration:.0f}s)...")

        # 3. 循环推进进度直到 >= 95% 或 completed
        max_rounds = 4
        for round_idx in range(max_rounds):
            start_cp = float(vdata.get("watch_length", 0) or 0)
            real_len = float(vdata.get("video_length", 0) or duration)
            rate = float(vdata.get("rate", 0) or 0)
            completed = vdata.get("completed", 0)

            if completed == 1 or rate >= 0.95:
                print(f"  [完成] 《{video_name}》 学习完成！进度: {rate*100:.1f}%")
                return 1

            chars = string.digits + string.ascii_lowercase
            pg = f"{video_id}_" + "".join(random.sample(chars, 4))
            now_ms = int(time.time() * 1000)
            logs = []
            sq = 1

            if round_idx == 0:
                for et in ["loadstart", "loadeddata", "play", "playing"]:
                    logs.append({
                        "i": 5, "et": et, "p": "web", "n": "ali-cdn.xuetangx.com", "lob": "ykt",
                        "cp": 0, "fp": 0, "tp": 0, "sp": 1, "ts": str(now_ms), "u": int(user_id), "uip": "",
                        "c": int(cid), "v": int(video_id), "skuid": leaf_sku_id, "classroomid": str(classroomid),
                        "cc": ccid, "d": real_len, "pg": pg, "sq": sq, "t": "video", "cards_id": 0, "slide": 0, "v_url": ""
                    })
                    sq += 1
                    now_ms += 100

            cp = 0.0
            step = 5.0
            while cp <= real_len:
                logs.append({
                    "i": 5, "et": "heartbeat", "p": "web", "n": "ali-cdn.xuetangx.com", "lob": "ykt",
                    "cp": round(cp, 1), "fp": 0, "tp": 0, "sp": 1, "ts": str(now_ms), "u": int(user_id), "uip": "",
                    "c": int(cid), "v": int(video_id), "skuid": leaf_sku_id, "classroomid": str(classroomid),
                    "cc": ccid, "d": real_len, "pg": pg, "sq": sq, "t": "video", "cards_id": 0, "slide": 0, "v_url": ""
                })
                sq += 1
                cp += step
                now_ms += int(step * 1000)

            logs.append({
                "i": 5, "et": "videoend", "p": "web", "n": "ali-cdn.xuetangx.com", "lob": "ykt",
                "cp": real_len, "fp": 0, "tp": 0, "sp": 1, "ts": str(now_ms), "u": int(user_id), "uip": "",
                "c": int(cid), "v": int(video_id), "skuid": leaf_sku_id, "classroomid": str(classroomid),
                "cc": ccid, "d": real_len, "pg": pg, "sq": sq, "t": "video", "cards_id": 0, "slide": 0, "v_url": ""
            })

            # 发送心跳数据
            r = self._request_with_retry("POST", post_url, json={"heart_data": logs})
            time.sleep(2)

            # 查询更新后的进度
            try:
                p_res = self._request_with_retry("GET", get_url)
                vdata = p_res.json().get("data", {}).get(video_id, {})
                rate = float(vdata.get("rate", 0) or 0)
                completed = vdata.get("completed", 0)
                print(f"    -> 《{video_name}》 进度更新为: {rate*100:.1f}%")
            except Exception:
                pass

        print(f"  [完成] 《{video_name}》 学习完成！")
        return 1

    def get_videos_ids(self, course_name, classroom_id, course_sign):
        get_homework_ids = (
            f"https://{self.domain}/mooc-api/v1/lms/learn/course/chapter?cid={classroom_id}"
            f"&term=latest&uv_id={self.university_id}&sign={course_sign}"
        )
        try:
            r = self._request_with_retry("GET", get_homework_ids)
            homework_json = r.json()
        except Exception as e:
            print(f"获取章节列表失败: {e}")
            return {}

        homework_dic = {}
        course_chapters = homework_json.get("data", {}).get("course_chapter", [])
        for i in course_chapters:
            for j in i.get("section_leaf_list", []):
                if "leaf_list" in j:
                    for z in j.get("leaf_list", []):
                        if z.get("leaf_type") == leaf_type["video"]:
                            homework_dic[z["id"]] = z["name"]
                else:
                    if j.get("leaf_type") == leaf_type["video"]:
                        homework_dic[j["id"]] = j["name"]

        if len(homework_dic) > 0:
            print(f"{course_name} 共有 {len(homework_dic)} 个视频需要学习！")
        else:
            print(f"{course_name} 没有检测到线上视频，跳过。")
        return homework_dic

    def watch_videos(self, videos_id_name_dic, course_id, user_id, classroom_id, sku_id):
        total = len(videos_id_name_dic)
        for idx, (vid, vname) in enumerate(videos_id_name_dic.items(), 1):
            print(f"\n[{idx}/{total}] ----------------------------------------")
            self.one_video_watcher(vid, vname, course_id, user_id, classroom_id, sku_id)
            time.sleep(1.5)

    def multiple_watch_video(self, videos_id_name_dic, course_id, user_id, classroom_id, sku_id, num_workers=1):
        # 顺序执行，防止并发冲突及 429 限速
        self.watch_videos(videos_id_name_dic, course_id, user_id, classroom_id, sku_id)
