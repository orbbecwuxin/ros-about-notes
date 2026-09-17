# About ROS — 中文翻译学习笔记

本仓库是 [ROS 2 官方文档：About ROS](https://docs.ros.org/en/jazzy/About-ROS.html) 的镜像，
用于在原文基础上添加中文翻译笔记。页面外观与官方文档保持一致。

## 许可与署名

- 原文来自 [ROS 2 Documentation](https://docs.ros.org/en/jazzy/About-ROS.html)，© Open Robotics。
- 原文内容遵循 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。
- 本站为转载 + 中文翻译，已在页面顶部注明来源与修改说明。

## 怎么填翻译

1. 打开 `index.html`。
2. 每个蓝色 **「📝 译文：」** 框对应上方一段英文。
3. 把占位文字 `（在此填写中文翻译）` 替换成你的中文翻译即可。
4. 不需要翻译的框，整段删掉即可（从 `<div class="my-translation">` 到 `</div>`）。

## 发布到 GitHub Pages

### 方法一：网页操作（最简单）
1. 在 GitHub 新建仓库（Public），例如 `ros-notes`。
2. 在仓库页点击 **Add file → Upload files**，把本文件夹里所有文件（`index.html`、`_static`、`_images`、`.nojekyll`、`README.md`）上传。
3. 进入 **Settings → Pages → Source**，选择 `main` 分支，点 Save。
4. 稍等 1~2 分钟，访问 `https://<你的用户名>.github.io/ros-notes/`。

### 方法二：命令行
```bash
git init
git add -A
git commit -m "About ROS 中文翻译学习页（转载自 ROS 2 文档，CC BY 4.0）"
git branch -M main
git remote add origin https://github.com/<你的用户名>/ros-notes.git
git push -u origin main
```
然后按“方法一”第 3、4 步开启 Pages。

## 目录结构
```
index.html           主页面（含 22 个译文框）
_static/             页面样式与脚本（勿删）
_images/             页面图片
README.md            本说明
.nojekyll            让 GitHub Pages 按纯 HTML 发布
```

## 自动化技能（Skill）

本仓库附带一个**自动推进翻译的技能** `sop_skill.py`：
检查当前页翻译/理解是否完成 → 未完成继续填 → 完成自动拉取下一页并发布。

```bash
python3 sop_skill.py status   # 查看当前页完成情况
python3 sop_skill.py run      # 自动：未完成就填，完成就拉下一页
```

详见 `SKILL.md`。
