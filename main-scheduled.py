# -*- coding:utf-8 -*-
import time
from functools import wraps
from types import MethodType
import json
import os
import re
from typing import Dict, Optional

import requests
import toml
from datetime import datetime, timedelta

# 图片下载路径
save_img_path = "./end/"

verbose = True

urls = None
wxAppId = None
headers = None


def load_config():
    global urls, wxAppId, headers  # 声明变量为全局变量
    profile = toml.load(
        os.path.dirname(os.path.realpath(__file__)) + "/profile.toml"
    )
    urls = profile["profile"]["url"]
    wxAppId = profile["profile"]["other"]["wxAppId"]
    headers = {
        "User-Agent": profile["profile"]["other"]["UA"],
    }


class TimeoutRetry:
    max_retry = 3

    def __init__(self, func):
        wraps(func)(self)

    def __call__(self, *args, **kwargs):
        retry_count = 0
        while retry_count < self.max_retry:
            try:
                return self.__wrapped__(*args, **kwargs)
            except requests.RequestException:
                print("请求超时，等待 5 秒后重试")
                time.sleep(5)
                retry_count += 1
        raise TimeoutError("重试三次，连接无效，请检查网络")

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            return MethodType(self, instance)


@TimeoutRetry
def getToken(openId: str) -> Optional[str]:
    response = requests.get(
        url=urls["accessToken"],
        params={"appid": wxAppId, "openid": openId},
        headers={},
    )
    accessTokenMatch = re.compile(
        r"(['\"])(?P<accessToken>([A-Z0-9]|-)+)(\1)"
    ).search(response.text)
    if accessTokenMatch is not None:
        accessToken = accessTokenMatch.groupdict()["accessToken"]
        return accessToken


@TimeoutRetry
def getInfo(
        accessToken: str, nid: Optional[str], cardNo: Optional[str]
) -> Optional[Dict[str, str]]:
    infoResponse = requests.get(
        urls["lastInfo"], params={"accessToken": accessToken}, headers=headers
    )
    userInfo = infoResponse.json()["result"]
    if userInfo is None:
        return

    # if this cannot get nid or cardNo, then get it using config
    _nid = userInfo["nid"]
    if _nid is None:
        _nid = nid
    _cardNo = userInfo["cardNo"]
    if _cardNo is None:
        _cardNo = cardNo

    # still None, config is not set
    if _nid is None or _cardNo is None:
        return None

    courseResponse = requests.get(
        urls["currentCourse"],
        params={"accessToken": accessToken},
        headers=headers,
    )
    classInfo = courseResponse.json()["result"]
    if classInfo is None:
        return
    classId = classInfo["id"]
    faculty = [item["title"] for item in userInfo["nodes"]]

    if verbose:
        print(
            "[**] Course title: " + classInfo["title"],
            "[**] Group info: " + str(faculty) + ", nid: " + _nid,
            "[**] cardNo: " + _cardNo,
            sep="\n",
        )
    return {"course": classId, "nid": _nid, "cardNo": _cardNo}


@TimeoutRetry
def getUserScore(accessToken: str) -> str:
    return requests.get(
        url=urls["userInfo"],
        params={"accessToken": accessToken},
        headers=headers,
    ).json()["result"]["score"]


@TimeoutRetry
def join(accessToken: str, joinData: Dict[str, str]) -> bool:
    response = requests.post(
        urls["join"],
        params={"accessToken": accessToken},
        data=json.dumps(joinData),
        headers=headers,
    )
    content = response.json()

    if content["status"] == 200:
        print("[*] Check in success")
        return True
    else:
        print("[!] Error:", content["message"])
        return False


@TimeoutRetry
def download_end_img(access_token: str, name: str) -> bool:
    # 获取当前时间
    now = datetime.now()
    # 将时间转换为指定格式
    formatted_date = now.strftime("%Y-%m-%d")
    folder_name = formatted_date.replace("-", "_")
    # 按照日期生成路径
    path = save_img_path + folder_name + "/" + name + ".jpg"
    # 判断路径是否存在，不存在则创建
    if not os.path.exists(save_img_path + folder_name):
        os.makedirs(save_img_path + folder_name)

    course_url = urls["image"] + access_token
    print("Downloading end of image...")
    response = requests.get(course_url)
    path_list = response.json().get("result").get("uri").split("/")
    path_list[-1] = "images"
    path_list.append("end.jpg")
    img_url = "/".join(path_list)  # 拼接图片url
    end_img = requests.get(img_url)
    with open(path, "wb") as f:
        f.write(end_img.content)
        print("Image saved")


def runCheckIn(
        openid: str,
        nid: Optional[str] = None,
        cardNo: Optional[str] = None,
        name: Optional[str] = None
) -> None:
    accessToken = getToken(openid)
    if accessToken is None:
        print("[!] Error getting accessToken, maybe your openid is invalid")
        exit(-1)

    joinData = getInfo(accessToken, nid=nid, cardNo=cardNo)
    if joinData is None:
        print(
            "[!] Error getting join data, maybe your openid is invalid or given nid/cardNo is invalid"
        )
        exit(-1)

    print("[*] Score before checkin:", getUserScore(accessToken))

    if not join(accessToken, joinData):
        exit(-1)

    print("[*] Score after checkin:", getUserScore(accessToken))

    print("[*] Start Download end image for name:", name)
    download_end_img(accessToken, name)
    print("[*] End Download end image for name:", name)
    print("=============================================done=============================================")


def Tests():
    if "OPENID" in os.environ:
        print("[*] Reading openid from environ", end="\n\n")
        verbose = False
        for openid in os.environ["OPENID"].split(","):
            runCheckIn(openid)
    else:
        print("[*] Reading openid from config.toml", end="\n\n")

        config = toml.load(
            os.path.dirname(os.path.realpath(__file__)) + "/config.toml"
        )
        for name, user in config["user"].items():
            print("[*] Checking in for openid", name)
            runCheckIn(user["openid"], user["nid"], user["cardNo"], name)


def main():
    print("[*] Reading openid from config.toml", end="\n\n")

    config = toml.load(
        os.path.dirname(os.path.realpath(__file__)) + "/config.toml"
    )
    for name, user in config["user"].items():
        print("[*] Checking in for openid", name)
        runCheckIn(user["openid"], user["nid"], user["cardNo"], name)


if __name__ == "__main__":
    while True:
        try:
            # 加载配置文件
            load_config()
            # 计算现在到下周一早上八点钟的时间
            now = datetime.now()
            next_monday = now + timedelta(days=-now.weekday(), weeks=1)
            next_monday_morning = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)
            delta = next_monday_morning - now
            print("Next check in will be executed at", delta)
            # 如果距离下次签到时间小于1小时，则开始签到
            if delta < timedelta(hours=1):
                main()
            else:
                print("Waiting for next check in...")
            # 每隔1小时检查一次
            time.sleep(3600)
        except Exception as e:
            print(e)
            print("Error occurred, retrying...")
