# 开源软件社区生态数据可视化（实验三）

本仓库是《开源软件设计与分析》课程实验三的配套工程，内容为 **DataEase 数据大屏** 与 **Git 图形化工具（TortoiseGit）** 实践，分支 feature/dashboard-doc 用于补充大屏文档。

## 数据来源

数据通过 GitHub REST API v3 实时采集，包含 16 个国内外主流开源项目，共 4 张数据表：

| 数据表 | 含义 | 记录数 |
| --- | --- | --- |
| `repo_metrics` | 项目维度指标（Star/Fork/Issue/语言/创建时间等） | 16 |
| `weekly_commits` | 各项目近 52 周每周提交数 | 832 |
| `repo_languages` | 各项目代码语言构成（字节数） | 64 |
| `language_summary` | 按主语言聚合的 Star/Fork 汇总 | 6 |

## 目录结构

```text
oss-lab3-git-gui/
├─ data/                 采集到的 CSV 数据集
├─ docs/                 数据字典与指标口径说明
├─ scripts/
│  ├─ collect_github.py  调用 GitHub API 采集数据
│  └─ load_to_mysql.py   建库建表并导入 MySQL
└─ README.md
```

## 使用方式

1. `python scripts/collect_github.py` 采集数据到 `data/`；
2. `python scripts/load_to_mysql.py` 创建 `oss_ecosystem` 库并导入；
3. 在 DataEase 中添加 MySQL 数据源 → 创建数据集 → 搭建 16:9 数据大屏。

## 大屏结构

- 顶部 4 个指标卡：全项目 Star 总数、Fork 总数、收录项目数、近一年提交总数；
- 中部左侧折线图：近一年各周提交总数趋势；右侧环形图：主语言 Star 数分布；
- 底部左侧柱状图：各项目 Star 数对比；右侧明细表：开源项目指标明细。

## 大屏指标口径

1. 全项目 Star 总数 = SUM(repo_metrics.Star数)；
2. 近一年提交总数 = SUM(weekly_commits.提交数)，统计窗口为最近 52 周；
3. 主语言占比按 language_summary.Star总数 求和后计算各扇区百分比；
4. 明细表展示项目名称、主语言、Star数、开放Issue数、Fork数五列。

## 版本记录

- v1.0.0 完成数据采集脚本、数据集与大屏初版
