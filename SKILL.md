# ROS 翻译推进技能（Skill）

> 一个自动逐页推进“ROS 2 文档中文翻译”的流程技能。
> 核心逻辑：**检查当前页翻译/理解是否完成 → 未完成就继续填写 → 完成就自动拉取下一页并发布。**

## 用途 / 何时使用

- 想按顺序把 ROS 2 文档一页页翻译成中文并发布到 GitHub Pages。
- 每次只关注“当前这一页”，完成后自动进入下一页，不用手动搬运。

## 输入

- 官方文档：https://docs.ros.org/en/jazzy/ （以 `sitemap.xml` 为页面顺序）
- 本地翻译页：`<slug>.html`（每个页面独立文件，带「📝 译文」「💡 理解」框）
- 进度清单：`state.json`（记录 298 个页面的完成状态）

## 流程（每次运行只做一步，可反复调用）

```
┌──────────────────────────────────────────────┐
│  ① 读取 state.json，定位“当前页”（第一个未完成） │
└──────────────────────────────────────────────┘
              │
              ▼
      ┌─ 当前页有本地文件吗？ ─┐
      │ 没有                  │ 有
      ▼                       ▼
  拉取该页(镜像+加译文框)   检查完成度
  提交并发布               ┌────┴────┐
              │          未完成      完成
              │           ▼           ▼
              │        继续填写     标记完成→拉取下一页
              │        (fill)      提交并发布
              └──────────┴───────────┘
```

## 调用命令

在仓库目录 `~/ros-notes-site` 下：

```bash
# ① 查看当前页完成情况（不修改）
python3 sop_skill.py status

# ② 未完成则继续填写当前页（交互式）
python3 sop_skill.py fill

# ③ 当前页完成后，拉取下一页并自动 git 提交+推送发布
python3 sop_skill.py next

# ④ 主流程：自动判断 —— 未完成就填，完成就拉下一页
python3 sop_skill.py run

# ⑤ 从官方 sitemap 重建进度清单
python3 sop_skill.py sync
```

可选参数：`--ignore-understanding`（判定“完成”时只看译文、不要求理解）。

## “完成”的判定标准

- 默认：当前页**所有**「📝 译文」和「💡 理解」都填了才算完成；
- 加 `--ignore-understanding` 后：只要求**所有**译文填完。

## 输出 / 产物

| 产物 | 说明 |
|------|------|
| `<slug>.html` | 每一页的翻译页（原排版 + 译文框） |
| `index.html` | 导航首页，列出所有页面与状态 |
| `state.json` | 进度清单，自动更新 |
| GitHub Pages | 每次 `next`/`run` 自动 `git push`，1~2 分钟后线上更新 |

## 依赖

```bash
pip install requests beautifulsoup4
```

## 许可

- 原文：ROS 2 官方文档，© Open Robotics，遵循 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。
- 每页顶部已自动加入署名与修改说明。
