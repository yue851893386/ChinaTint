# -*- coding: utf-8 -*-
"""
下载全部地图数据到本地 geo/ 目录（部署前跑一次即可，之后网站零外部依赖）

用法：
    python download_geo.py

成功后会生成 geo/ 文件夹（约 60+ 个 json，共 10-20MB），
把这个文件夹连同代码一起上传部署即可。
"""
import json
import os
import time
import urllib.request

MUNICIPALITIES = [110000, 120000, 310000, 500000, 810000, 820000]
PROVINCES = [
    130000,140000,150000,210000,220000,230000,320000,330000,340000,350000,
    360000,370000,410000,420000,430000,440000,450000,460000,510000,520000,
    530000,540000,610000,620000,630000,640000,650000,710000
]
BASE = "https://geo.datav.aliyun.com/areas_v3/bound/{}.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo")
os.makedirs(OUT, exist_ok=True)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    jobs = []
    # 地级市：直辖市/港澳用自身，普通省用 _full
    for c in MUNICIPALITIES:
        jobs.append((str(c), BASE.format(c)))
    for c in PROVINCES:
        jobs.append((str(c) + "_full", BASE.format(str(c) + "_full")))
    # 省份轮廓（淡蓝省界用）：每个省自身面，文件名加 p 前缀
    for c in MUNICIPALITIES + PROVINCES:
        jobs.append(("p" + str(c), BASE.format(c)))

    ok, fail, skip = 0, [], 0
    for name, url in jobs:
        path = os.path.join(OUT, name + ".json")
        if os.path.exists(path):
            skip += 1
            continue
        try:
            data = fetch(url)
            if not isinstance(data, dict) or not data.get("features"):
                raise ValueError("接口返回空数据")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            ok += 1
            print(f"  OK   {name}")
        except Exception as e:
            fail.append(name)
            print(f"  FAIL {name}: {e}")
        time.sleep(0.25)   # 限速，防止被接口封禁

    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f"\n完成：新增 {ok} 个，已存在跳过 {skip} 个，失败 {len(fail)} 个")
    if fail:
        print("失败的文件：" + ", ".join(fail) + "（可重新运行本脚本补下载）")
    print(f"geo/ 目录共 {len(os.listdir(OUT))} 个文件，合计 {total/1024/1024:.1f} MB")
    print("\n下一步：把 geo/ 文件夹和代码一起上传部署。")


if __name__ == "__main__":
    main()
