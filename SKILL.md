# ROS 翻译推进技能（Skill）

> 一个带**人工勘误门禁**的逐页翻译流程技能。
> 核心逻辑：**用户提交翻译 → AI 勘误并指出问题 → 勘误通过后 commit+push+刷新 → 再拉取下一页。**
> **翻译绝不自动提交/推送。**

## 硬性规则（不要违反）

1. **翻译内容只能由用户填写，AI 不得代填。** AI 的角色是勘误、指出问题、在用户批准后发布。
2. **AI 绝不自动提交/推送翻译。** 用户填写只保存到本地；只有用户明确批准后，AI 才 `publish`。
3. **展示新章节/新页时，必须同时给出网址**：该页的官方网址（`docs.ros.org/...`）和本站网址（`orbbecwuxin.github.io/ros-about-notes/...`）。
4. **勘误时把有价值的英文短语写进该段「💡 理解」框**：将勘误中纠正/涉及的有用短语连同中文含义记入理解，作为短语笔记。例如 `are for general use and provide...`（用于常规使用并提供…）、`dive in and start using`（立即上手使用）、`is great for...`（非常适合…）。
5. **每次展示段落都要显示本段的所有链接**（fill/review 都要列出：链接文字 → 网址），并且有链接时要提示用户先去点开学习相关内容，再填写翻译/理解；翻译/勘误完成后也要提醒用户记得去学习这些链接指向的内容。
6. **学习堆栈（后进先出）**：当段落里有链接、需要深入学习时，用 `stack push <url> [标题]` 把链接压栈并自动生成一份学习文档（`learn/<slug>.md`，记录链接、来源页），同时记下返回位置（当前页）；学习完成后用 `stack pop` 出栈并返回原页。堆栈用 `stack show` 查看。

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

# ⑧ 学习堆栈（后进先出）：把要学的链接压栈并生成学习文档
python3 sop_skill.py stack push "https://docs.ros.org/en/jazzy/..." "标题"
# ⑨ 查看学习堆栈
python3 sop_skill.py stack show
# ⑩ 学习完成，出栈返回原页
python3 sop_skill.py stack pop
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
