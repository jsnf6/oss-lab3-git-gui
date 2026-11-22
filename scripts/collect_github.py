"""抓取 GitHub 开源项目生态数据（真实接口数据），生成 DataEase 大屏所需的 CSV 数据集。

数据来源：GitHub REST API v3
  - GET /repos/{owner}/{repo}                 项目基础信息
  - GET /repos/{owner}/{repo}/languages       语言构成（字节数）
  - GET /repos/{owner}/{repo}/stats/participation  近 52 周提交数
"""
import csv
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))

REPOS = [
    "dataease/dataease",
    "jumpserver/jumpserver",
    "apache/dubbo",
    "apache/dolphinscheduler",
    "vuejs/vue",
    "microsoft/vscode",
    "kubernetes/kubernetes",
    "redis/redis",
    "grafana/grafana",
    "prometheus/prometheus",
    "tensorflow/tensorflow",
    "pytorch/pytorch",
    "langchain-ai/langchain",
    "golang/go",
    "torvalds/linux",
    "spring-projects/spring-boot",
]


def token():
    t = os.environ.get("GITHUB_TOKEN", "")
    if t:
        return t
    import subprocess
    inp = "protocol=https\nhost=github.com\n\n"
    out = subprocess.run(["git", "credential", "fill"], input=inp, capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    return ""


TOKEN = token()
HDR = {
    "User-Agent": "dsh-lab3-datacollect",
    "Accept": "application/vnd.github+json",
}
if TOKEN:
    HDR["Authorization"] = "token " + TOKEN


def get(url, tries=4):
    for i in range(tries):
        req = urllib.request.Request(url, headers=HDR)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read().decode("utf-8")
                return json.loads(body) if body.strip() else None
        except urllib.error.HTTPError as e:
            if e.code == 202:          # 统计接口首次请求返回 202，稍后重试
                time.sleep(4)
                continue
            if e.code in (403, 429):
                print("rate limited, sleep 30s", e.code)
                time.sleep(30)
                continue
            print("HTTP", e.code, url)
            return None
        except Exception as e:         # noqa: BLE001
            print("ERR", e, url)
            time.sleep(3)
    return None


today = dt.date.today()
repos_rows, lang_rows, week_rows = [], [], []

for full in REPOS:
    info = get(f"https://api.github.com/repos/{full}")
    if not info:
        print("SKIP", full)
        continue
    owner, name = full.split("/")
    created = (info.get("created_at") or "")[:10]
    print("OK", full, info.get("stargazers_count"), info.get("language"))
    repos_rows.append({
        "项目名称": info["name"],
        "所属组织": owner,
        "主语言": info.get("language") or "未标注",
        "Star数": info.get("stargazers_count", 0),
        "Fork数": info.get("forks_count", 0),
        "关注数": info.get("subscribers_count", 0),
        "开放Issue数": info.get("open_issues_count", 0),
        "创建日期": created,
        "创建年份": created[:4],
        "最近推送日期": (info.get("pushed_at") or "")[:10],
        "仓库大小MB": round(info.get("size", 0) / 1024, 1),
        "许可证": (info.get("license") or {}).get("spdx_id") or "NOASSERTION",
    })

    langs = get(f"https://api.github.com/repos/{full}/languages") or {}
    for lang, size in sorted(langs.items(), key=lambda kv: -kv[1])[:4]:
        lang_rows.append({"项目名称": info["name"], "编程语言": lang, "代码字节数": size})

    part = get(f"https://api.github.com/repos/{full}/stats/participation")
    weeks = (part or {}).get("all") or []
    n = len(weeks)
    for i, cnt in enumerate(weeks):
        start = today - dt.timedelta(days=(n - i) * 7)
        week_rows.append({
            "项目名称": info["name"],
            "周起始日期": start.isoformat(),
            "年周": "%d-W%02d" % (start.isocalendar()[0], start.isocalendar()[1]),
            "提交数": cnt,
        })
    time.sleep(0.4)


def dump(fn, rows, cols):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(fn, len(rows))


dump("repos.csv", repos_rows,
     ["项目名称", "所属组织", "主语言", "Star数", "Fork数", "关注数", "开放Issue数",
      "创建日期", "创建年份", "最近推送日期", "仓库大小MB", "许可证"])
dump("repo_languages.csv", lang_rows, ["项目名称", "编程语言", "代码字节数"])
dump("weekly_commits.csv", week_rows, ["项目名称", "周起始日期", "年周", "提交数"])

# 语言汇总（按主语言聚合，用于占比类图表）
summary = {}
for r in repos_rows:
    k = r["主语言"]
    s = summary.setdefault(k, {"编程语言": k, "项目数": 0, "Star总数": 0, "Fork总数": 0})
    s["项目数"] += 1
    s["Star总数"] += r["Star数"]
    s["Fork总数"] += r["Fork数"]
dump("language_summary.csv", sorted(summary.values(), key=lambda x: -x["Star总数"]),
     ["编程语言", "项目数", "Star总数", "Fork总数"])
