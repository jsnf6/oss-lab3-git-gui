"""把抓取到的 CSV 灌入 MySQL（DataEase 数据源），生成 *.sql 并执行。"""
import csv
import os
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "load_mysql.sql")

TABLES = {
    "repos.csv": ("repo_metrics", [
        ("项目名称", "VARCHAR(64)"), ("所属组织", "VARCHAR(64)"), ("主语言", "VARCHAR(32)"),
        ("Star数", "INT"), ("Fork数", "INT"), ("关注数", "INT"), ("开放Issue数", "INT"),
        ("创建日期", "DATE"), ("创建年份", "INT"), ("最近推送日期", "DATE"),
        ("仓库大小MB", "DECIMAL(10,1)"), ("许可证", "VARCHAR(32)"),
    ]),
    "repo_languages.csv": ("repo_languages", [
        ("项目名称", "VARCHAR(64)"), ("编程语言", "VARCHAR(32)"), ("代码字节数", "BIGINT"),
    ]),
    "weekly_commits.csv": ("weekly_commits", [
        ("项目名称", "VARCHAR(64)"), ("周起始日期", "DATE"), ("年周", "VARCHAR(16)"), ("提交数", "INT"),
    ]),
    "language_summary.csv": ("language_summary", [
        ("编程语言", "VARCHAR(32)"), ("项目数", "INT"), ("Star总数", "BIGINT"), ("Fork总数", "BIGINT"),
    ]),
}

lines = [
    "SET NAMES utf8mb4;",
    "DROP DATABASE IF EXISTS oss_ecosystem;",
    "CREATE DATABASE oss_ecosystem DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;",
    "USE oss_ecosystem;",
]


def lit(v):
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


for fn, (table, cols) in TABLES.items():
    path = os.path.join(BASE, fn)
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    names = [c for c, _ in cols]
    lines.append("DROP TABLE IF EXISTS `%s`;" % table)
    lines.append("CREATE TABLE `%s` (%s) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;" % (
        table, ", ".join("`%s` %s" % (c, t) for c, t in cols)))
    numeric = {"INT", "BIGINT"}
    for r in rows:
        vals = []
        for c, t in cols:
            v = r.get(c, "")
            vals.append(v if t in numeric and str(v).strip() != "" else lit(v))
        lines.append("INSERT INTO `%s` (`%s`) VALUES (%s);" % (table, "`, `".join(names), ", ".join(vals)))
    print(table, len(rows))

open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("sql written", OUT, os.path.getsize(OUT))

r = subprocess.run(["docker", "exec", "-i", "de-mysql", "mysql", "-uroot", "-p123456",
                    "--default-character-set=utf8mb4"],
                   stdin=open(OUT, "rb"), capture_output=True)
print("rc", r.returncode, r.stdout.decode("utf-8", "ignore")[-500:], r.stderr.decode("utf-8", "ignore")[-800:])
