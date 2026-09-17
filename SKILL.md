# ROS 翻译推进技能（Skill）

> 一个带**人工勘误门禁**的逐页翻译流程技能。
> 核心逻辑：**用户提交翻译 → AI 勘误并指出问题 → 勘误通过后 commit+push+刷新 → 再拉取下一页。**
> **翻译绝不自动提交/推送。**

## 硬性规则（不要违反）

1. **翻译内容只能由用户填写，AI 不得代填。** AI 的角色是勘误、指出问题、在用户批准后发布。
2. **AI 绝不自动提交/推送翻译。** 用户填写只保存到本地；只有用户明确批准后，AI 才 `publish`。

## 用途 / 何时使用

- 想按顺序把 ROS 2 文档一页页翻译成中文并发布到 GitHub Pages。
- 每页翻译都要经过 AI 勘误把关，确认无误后才发布。

## 输入

- 官方文档：https://docs.ros.org/en/jazzy/ （以 `sitemap.xml` 为页面顺序）
- 本地翻译页：`<slug>.html`（每个页面独立文件，带「📝 译文」「💡 理解」框）
- 进度清单：`state.json`（记录各页面完成/勘误状态）

## 流程（每页四步，翻译不自动提交）

```
用户提交翻译（fill，只存本地，不提交）
        │
        ▼
AI 勘误（review：输出译文/理解，AI 指出问题）
        │
        ▼
勘误通过 → publish（commit + push）→ 刷新网页
        │
        ▼
next（拉取下一页，仅拉新页，不涉及翻译提交）
```

## 调用命令

在仓库目录 `~/ros-notes-site` 下：

```bash
# ① 查看当前页完成情况（不修改）
python3 sop_skill.py status

# ② 用户填写当前页 —— 逐段打印【英文原文】后提示“请把这一段的中文翻译 + 理解发给我”，只保存本地，绝不自动提交
python3 sop_skill.py fill

# ③ 逐段输出【英文原文 + 译文 + 理解】，供 AI 勘误
python3 sop_skill.py review

# ④ AI 勘误通过后：commit + push（发布翻译）
python3 sop_skill.py publish

# ⑤ 当前页已发布后：拉取下一页（仅拉新页并推送）
python3 sop_skill.py next

# ⑥ 主流程：自动判断当前该 填/勘误/发布/拉页
python3 sop_skill.py run

# ⑦ 从官方 sitemap 重建进度清单
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
