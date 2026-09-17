#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS 翻译技能 (Skill) —— 带人工勘误门禁的逐页翻译流程

流程（翻译绝不自动提交）:
    用户填翻译 → AI 勘误 → 通过后 publish (commit+push) → next (拉下一页)

用法:
    python3 sop_skill.py status             # 检查当前页翻译/理解完成情况
    python3 sop_skill.py fill               # 填写当前页（只存本地，不提交）
    python3 sop_skill.py review             # 输出当前页译文/理解，供 AI 勘误
    python3 sop_skill.py publish            # 勘误通过后 commit + push 发布
    python3 sop_skill.py next               # 当前页已发布则拉取下一页（仅拉页）
    python3 sop_skill.py run                # 主流程：自动判断当前应填写/勘误/发布/拉页
    python3 sop_skill.py sync               # 从官方 sitemap 重建 state.json

选项:
    --ignore-understanding   判定“完成”时只要求译文，不要求理解
"""
import os, re, json, sys, subprocess
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, Comment

ROOT = os.environ.get('ROS_NOTES_REPO') or os.path.dirname(os.path.abspath(__file__))
SITEMAP_URL = 'https://docs.ros.org/en/jazzy/sitemap.xml'
TOC_URL = 'https://docs.ros.org/en/jazzy/index.html'
BASE_URL = 'https://docs.ros.org/en/jazzy/'
GIT_NAME, GIT_EMAIL = 'ros-skill', 'ros-skill@local'

# ---------------------------------------------------------------- 工具 -----
def state_path():
    return os.path.join(ROOT, 'state.json')

def load_state():
    p = state_path()
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    return {'pages': []}

def save_state(state):
    json.dump(state, open(state_path(), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def git(*args):
    subprocess.run(['git', '-C', ROOT] + list(args), check=False,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def git_commit_push(msg):
    git('add', '-A')
    git('-c', f'user.name={GIT_NAME}', '-c', f'user.email={GIT_EMAIL}',
        'commit', '-m', msg)
    r = subprocess.run(['git', '-C', ROOT, 'push'], capture_output=True, text=True)
    return r.returncode == 0

# ------------------------------------------------------------ 完成度检查 ----
def check_page(local_file, require_understanding=True):
    """返回 (total, tr_done, un_done, 未完成列表)"""
    path = os.path.join(ROOT, local_file)
    if not os.path.exists(path):
        return 0, 0, 0, []
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    boxes = soup.select('.my-translation')
    total = len(boxes)
    tr_done = un_done = 0
    undone = []
    for i, box in enumerate(boxes, 1):
        tr = box.find('span', class_='my-tr-text')
        un = box.find('span', class_='my-un-text')
        tr_ok = bool(tr and tr.get_text(strip=True))
        un_ok = bool(un and un.get_text(strip=True))
        tr_done += tr_ok
        un_done += un_ok
        if not tr_ok or (require_understanding and not un_ok):
            p = box.find_previous_sibling('p')
            snippet = ' '.join(p.get_text(' ', strip=True).split())[:50] if p else ''
            undone.append((i, tr_ok, un_ok, snippet))
    return total, tr_done, un_done, undone

def is_done(total, tr_done, un_done, require_understanding=True):
    if total == 0:
        return False
    if tr_done != total:
        return False
    if require_understanding and un_done != total:
        return False
    return True

# ------------------------------------------------------------ 交互填写 ----
def page_urls(pg, state=None):
    """返回 (官方网址, 本站网址)"""
    official = pg.get('url', '')
    site = ''
    if state and pg.get('local'):
        site = state.get('site_url', '') + pg['local']
    return official, site

def local_target(rel):
    """若 rel 对应的文档页已有本地镜像，返回本地文件名；否则返回 None"""
    slug = re.sub(r'\.html$', '', rel)
    slug = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')
    local = f'{slug}.html'
    if os.path.exists(os.path.join(ROOT, local)):
        return local
    return None

def fill_page(pg, state):
    local = pg['local']
    path = os.path.join(ROOT, local)
    official, site = page_urls(pg, state)
    print('=' * 70)
    print(f'📄 官方网址: {official}')
    if site:
        print(f'🌐 本站网址: {site}')
    print('=' * 70)
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    boxes = soup.select('.my-translation')
    for i, box in enumerate(boxes, 1):
        title = ''
        sec = box.find_parent('section')
        if sec:
            h = sec.find(['h1', 'h2', 'h3'])
            if h:
                title = ' '.join(h.get_text(' ', strip=True).split())
        p = box.find_previous_sibling('p')
        orig = ' '.join(p.get_text(' ', strip=True).split()) if p else ''
        tr_span = box.find('span', class_='my-tr-placeholder')
        un_span = box.find('span', class_='my-un-placeholder')
        cur_tr = box.find('span', class_='my-tr-text')
        cur_un = box.find('span', class_='my-un-text')
        print('=' * 70)
        print(f'【第 {i}/{len(boxes)} 段】 章节: {title}')
        print('-' * 70)
        print('【英文原文】')
        print(orig)
        print('-' * 70)
        print(f'【现有译文】{cur_tr.get_text(strip=True) if cur_tr else "（未填）"}')
        print(f'【现有理解】{cur_un.get_text(strip=True) if cur_un else "（未填）"}')
        print('-' * 70)
        print('👉 请把这一段的中文翻译 + 理解发给我')
        print()
        tr = input('📝 译文（回车=跳过）：').strip()
        if tr:
            if tr_span is not None:
                tr_span['class'] = ['my-tr-text']; tr_span.string = tr
            elif cur_tr is not None:
                cur_tr.string = tr
        un = input('💡 理解（回车=跳过）：').strip()
        if un:
            if un_span is not None:
                un_span['class'] = ['my-un-text']; un_span.string = un
            elif cur_un is not None:
                cur_un.string = un
        print()
    open(path, 'w', encoding='utf-8').write(str(soup))
    print(f'✅ 已保存 {local_file}')

# ------------------------------------------------------------ 拉取新页 ----
def mirror_page(url, local_file):
    """拉取官方页面 + 资源，扁平化保存到本地并做翻译装饰"""
    r = requests.get(url, timeout=40)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    base = BASE_URL

    def abs_of(v):
        return urljoin(url, v)

    # 1) 处理所有本地资源/链接：下载资源并扁平化，文档链接改写为官方绝对地址
    for tag, attr in [('img', 'src'), ('script', 'src'), ('link', 'href'), ('a', 'href')]:
        for el in soup.find_all(tag):
            v = el.get(attr)
            if not v:
                continue
            if v.startswith(('http://', 'https://', '//', '#', 'javascript:', 'mailto:')):
                continue
            absu = abs_of(v)
            path = urlparse(absu).path          # /en/jazzy/...
            if not path.startswith('/en/jazzy/'):
                continue
            rel = path[len('/en/jazzy/'):]
            if rel.startswith(('_static', '_images', '_downloads', 'icons', '_sources')):
                # 资源：下载并改写为本地相对路径
                try:
                    rr = requests.get(absu, timeout=40)
                    rr.raise_for_status()
                    dest = os.path.join(ROOT, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, 'wb') as f:
                        f.write(rr.content)
                except Exception as e:
                    print('  跳过资源下载失败:', rel, e)
                el[attr] = rel
            elif rel.endswith('.html') or '/' in rel:
                # 文档链接：已本地镜像 → 本地翻译页；否则 → 官方绝对地址
                lt = local_target(rel)
                if lt:
                    el[attr] = lt
                else:
                    el[attr] = base + rel

    # 2) 移除 Google 统计
    for c in soup.find_all(string=lambda t: isinstance(t, Comment) and 'Google tag' in t):
        c.extract()
    for s in soup.find_all('script'):
        if 'googletagmanager' in s.get('src', '') or 'gtag' in s.get_text():
            s.decompose()

    # 3) canonical 指回官方
    can = soup.find('link', rel='canonical')
    if can:
        can['href'] = url

    # 4) 加入样式 + 署名 + 译文框
    style = soup.new_tag('style')
    style.string = CSS
    if soup.head and style not in soup.head:
        soup.head.append(style)

    body = soup.find('div', itemprop='articleBody')
    if body is not None:
        banner = BeautifulSoup(ATTRIBUTION, 'html.parser').div
        body.insert(0, banner)

    n = 0
    for section in soup.find_all('section'):
        for p in section.find_all('p', recursive=False):
            txt = ' '.join(p.get_text(' ', strip=True).split())
            if re.match(r'^Area:.*Content-type:.*Experience:', txt):
                continue
            box = BeautifulSoup(BOX_HTML, 'html.parser').div
            p.insert_after(box)
            n += 1

    open(os.path.join(ROOT, local_file), 'w', encoding='utf-8').write(str(soup))
    return n

# ------------------------------------------------------------ 常量模板 ----
CSS = '''
.my-attribution { background:#fff8e6; border:1px solid #f0d27a; border-left:4px solid #e0a800;
  border-radius:4px; padding:10px 14px; margin:0 0 18px 0; font-size:0.92em; line-height:1.7; color:#5c4a00; }
.my-attribution a { color:#8a6d00; text-decoration:underline; }
.my-translation { background:#f0f6ff; border-left:4px solid #2c7be5; border-radius:4px;
  padding:10px 14px; margin:14px 0; font-size:0.95em; line-height:1.75; color:#17324d; }
.my-translation .my-tr-label { font-weight:700; color:#2c7be5; margin-right:6px; }
.my-translation .my-tr-placeholder { color:#93a5bb; font-style:italic; }
.my-translation .my-tr-text { color:#17324d; font-style:normal; }
.my-translation .my-understanding { margin-top:8px; padding-top:8px; border-top:1px dashed #c8ddf5; }
.my-translation .my-un-label { font-weight:700; color:#0b8a5a; margin-right:6px; }
.my-translation .my-un-placeholder { color:#8fa8b8; font-style:italic; }
.my-translation .my-un-text { color:#2f5d50; font-style:normal; }
'''

ATTRIBUTION = '''
<div class="my-attribution">
  📄 本文转载自 <a href="https://docs.ros.org/en/jazzy/About-ROS.html">ROS 2 官方文档</a>
  （© Open Robotics），内容遵循 <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> 许可，
  本页在原文基础上加入了中文翻译，翻译部分及说明为本站所加。
  <br/><b>翻译 SOP：</b>① 读英文 → ② 填「📝 译文」→ ③ 填「💡 理解」（可选）→ ④ 保存并推送发布。
</div>
'''

BOX_HTML = '''
<div class="my-translation">
  <span class="my-tr-label">📝 译文：</span>
  <span class="my-tr-placeholder">（在此填写中文翻译）</span>
  <div class="my-understanding">
    <span class="my-un-label">💡 理解：</span>
    <span class="my-un-placeholder">（用一句话写下你对这段的理解，可选填）</span>
  </div>
</div>
'''

# ------------------------------------------------------------ 主流程 ----
def current_page(state):
    """当前页 = 按 TOC 顺序第一个未完成 (done=false) 且未跳过 (skipped) 的页面"""
    for pg in state['pages']:
        if pg.get('skipped'):
            continue
        if not pg.get('done'):
            return pg
    return None

def cmd_status(state, require_un):
    pg = current_page(state)
    if not pg:
        print('🎉 所有页面都已完成！')
        return
    local = pg.get('local')
    total, tr, un, undone = check_page(local, require_un)
    print(f'当前页: {pg["title"]}  ({local})')
    print(f'  段落总数: {total}')
    print(f'  已填译文: {tr}/{total}')
    print(f'  已填理解: {un}/{total}')
    done = is_done(total, tr, un, require_un)
    print(f'  页面完成: {"✅ 是" if done else "❌ 否"}')
    if undone:
        print(f'  未完成 {len(undone)} 段：')
        for i, tr_ok, un_ok, snip in undone[:10]:
            print(f'    - 第{i}段 译文{"✔" if tr_ok else "✘"} 理解{"✔" if un_ok else "✘"} | {snip}…')
        if len(undone) > 10:
            print(f'    … 其余 {len(undone)-10} 段')
    return done

def cmd_fill(state, require_un):
    """只填写并保存到本地，绝不自动提交。"""
    pg = current_page(state)
    if not pg:
        print('所有页面已完成。'); return
    fill_page(pg, state)
    print('💾 已保存到本地，但【不会自动提交/推送】。')
    print('   请把翻译交给 AI 勘误： python3 sop_skill.py review')
    print('   勘误通过后再发布：   python3 sop_skill.py publish')

def cmd_review(state, require_un):
    """输出当前页所有已填译文/理解，供 AI 逐段勘误。"""
    pg = current_page(state)
    if not pg:
        print('所有页面已完成。'); return
    local = pg['local']
    path = os.path.join(ROOT, local)
    if not os.path.exists(path):
        print('当前页还没有本地文件，先运行 fill 或 run 拉取。'); return
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    boxes = soup.select('.my-translation')
    official, site = page_urls(pg, state)
    print(f'📖 当前页：{pg["title"]}（{local}）共 {len(boxes)} 段，供 AI 勘误：')
    print(f'   📄 官方网址: {official}')
    if site:
        print(f'   🌐 本站网址: {site}')
    print()
    issues = []
    for i, box in enumerate(boxes, 1):
        # 章节 + 原始英文段落
        sec = box.find_parent('section')
        h = sec.find(['h1', 'h2', 'h3']) if sec else None
        title = ' '.join(h.get_text(' ', strip=True).split()) if h else ''
        p = box.find_previous_sibling('p')
        orig = ' '.join(p.get_text(' ', strip=True).split()) if p else ''

        tr = box.find('span', class_='my-tr-text')
        un = box.find('span', class_='my-un-text')
        tr_t = tr.get_text(strip=True) if tr else ''
        un_t = un.get_text(strip=True) if un else ''
        flag = []
        if not tr_t:
            flag.append('缺译文')
        elif len(tr_t) < 4:
            flag.append('译文过短')
        if not un_t:
            flag.append('缺理解')
        if box.find('span', class_='my-tr-placeholder') or box.find('span', class_='my-un-placeholder'):
            flag.append('仍有占位符')
        print(f'\n--- 第{i}段（{title}）---')
        print('【英文原文】', orig if orig else '（无）')
        print('【译   文】', tr_t if tr_t else '（未填）')
        print('【理   解】', un_t if un_t else '（未填）')
        if flag:
            print('⚠️ 提示:', '、'.join(flag))
            issues.append((i, flag))
    if issues:
        print(f'\n共发现 {len(issues)} 段需要关注，请 AI 结合语义给出勘误意见。')
    else:
        print('\n✅ 无明显缺漏，可进行语义/术语勘误。')

def cmd_publish(state, require_un):
    """勘误通过后：commit + push（发布翻译），绝不自动触发。"""
    pg = current_page(state)
    if not pg:
        print('所有页面已完成。'); return
    local = pg['local']
    total, tr, un, undone = check_page(local, require_un)
    print(f'当前页: {pg["title"]}  译文 {tr}/{total}  理解 {un}/{total}')
    if total and not is_done(total, tr, un, require_un):
        print('⚠️ 还有段落未完成，仍要发布吗？（y/N）')
        if input().strip().lower() not in ('y', 'yes'):
            print('已取消发布。'); return
    ok = git_commit_push(f'✍️ 发布翻译：{pg["title"]}（勘误通过）')
    if ok:
        pg['reviewed'] = True
        save_state(state)
        print('✅ 已 commit + push，网页 1~2 分钟后刷新可见。')
    else:
        print('❌ push 失败或没有可提交内容，请检查 git 状态。')

def cmd_next(state, require_un):
    """当前页完成并已发布后，拉取下一页（仅拉页，不涉及翻译提交）。"""
    pg = current_page(state)
    if pg is None:
        print('所有页面已完成。'); return
    local = pg['local']
    total, tr, un, undone = check_page(local, require_un)
    if not is_done(total, tr, un, require_un):
        print(f'❌ 当前页“{pg["title"]}”还没完成（译文 {tr}/{total}，理解 {un}/{total}）。')
        print('   请先运行: python3 sop_skill.py fill')
        return
    if not pg.get('reviewed'):
        print(f'❌ 当前页“{pg["title"]}”已填完，但还未经过勘误发布。')
        print('   流程: python3 sop_skill.py review  →  publish  →  next')
        return
    # 完成且已发布 → 标记 done，找下一页（跳过 skipped）
    pg['done'] = True
    nxt = None
    for cand in state['pages']:
        if cand.get('skipped'):
            continue
        if not cand.get('done'):
            nxt = cand; break
    if nxt is None:
        save_state(state)
        print('🎉 全部页面已完成！')
        return
    print(f'✅ 当前页“{pg["title"]}”已发布，拉取下一页：{nxt["title"]}')
    off, site = page_urls(nxt, state)
    print(f'   📄 官方网址: {off}')
    if site:
        print(f'   🌐 本站网址: {site}')
    n = mirror_page(nxt['url'], nxt['local'])
    print(f'   已生成 {nxt["local"]}，插入 {n} 个译文框')
    save_state(state)
    ok = git_commit_push(f'📥 拉取新页 {nxt["title"]}（待翻译）')
    print(f'   推送: {"成功 ✔" if ok else "失败（请手动 git push）"}')
    print(f'   新页: {nxt["local"]}   线上: {state.get("site_url","")}')

def cmd_sync():
    """按官方左侧目录（TOC）顺序重建 state.json（不是字母序 sitemap）"""
    r = requests.get(TOC_URL, timeout=40); r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    nav = soup.find('nav', class_='wy-nav-side') or soup.find('div', class_='wy-menu')
    order = []
    for a in nav.find_all('a', href=True):
        h = a['href']
        if h.endswith('.html') and not h.startswith(('http', '#')) and not h.startswith('index.html'):
            order.append((h, ' '.join(a.get_text(' ', strip=True).split())))
    state = load_state()
    existing = {p['url']: p for p in state.get('pages', [])}
    new_pages = []
    for path, title in order:
        u = BASE_URL + path
        slug = re.sub(r'\.html$', '', path)
        slug = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')
        if u in existing:
            p = existing[u]
        else:
            p = {'slug': slug, 'title': title or slug.replace('-', ' ').title(),
                 'url': u, 'local': f'{slug}.html', 'done': False}
        p.setdefault('skipped', False)
        new_pages.append(p)
    state['pages'] = new_pages
    state['toc_url'] = TOC_URL
    save_state(state)
    print(f'已按官方目录顺序同步，共 {len(new_pages)} 页')

def main():
    global ROOT
    args = sys.argv[1:]
    if '--repo' in args:
        i = args.index('--repo')
        ROOT = os.path.abspath(args[i + 1])
    cmd = 'run'
    if args and args[0] in ('status', 'fill', 'review', 'publish', 'next', 'run', 'sync'):
        cmd = args[0]
    require_un = '--ignore-understanding' not in args
    state = load_state()
    if cmd == 'sync':
        cmd_sync(); return
    if not state.get('pages'):
        print('state.json 为空，先运行: python3 sop_skill.py sync'); return
    if cmd == 'status':
        cmd_status(state, require_un)
    elif cmd == 'fill':
        cmd_fill(state, require_un)
    elif cmd == 'review':
        cmd_review(state, require_un)
    elif cmd == 'publish':
        cmd_publish(state, require_un)
    elif cmd == 'next':
        cmd_next(state, require_un)
    else:  # run
        pg = current_page(state)
        if pg is None:
            print('🎉 所有页面已完成！'); return
        local = pg['local']
        if not os.path.exists(os.path.join(ROOT, local)):
            print(f'📥 当前页无本地文件，拉取新页：{pg["title"]}')
            off, site = page_urls(pg, state)
            print(f'   📄 官方网址: {off}')
            if site:
                print(f'   🌐 本站网址: {site}')
            n = mirror_page(pg['url'], local)
            print(f'   已生成 {local}，插入 {n} 个译文框')
            save_state(state)
            git_commit_push(f'📥 拉取新页 {pg["title"]}（待翻译）')
            return
        total, tr, un, undone = check_page(local, require_un)
        if not is_done(total, tr, un, require_un):
            print(f'⏳ 当前页“{pg["title"]}”未完成（译文 {tr}/{total}，理解 {un}/{total}），继续填写…')
            cmd_fill(state, require_un)
        elif not pg.get('reviewed'):
            print(f'✅ 当前页“{pg["title"]}”已填完，进入勘误发布环节（不会自动提交）：')
            print('   python3 sop_skill.py review   →  AI 勘误')
            print('   python3 sop_skill.py publish  →  通过后 commit+push')
        else:
            print(f'✅ 当前页“{pg["title"]}”已完成并已发布，自动拉取下一页')
            cmd_next(state, require_un)

if __name__ == '__main__':
    main()
