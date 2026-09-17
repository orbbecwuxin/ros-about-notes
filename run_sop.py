#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP 运行脚本 —— 中文翻译标准作业流程
用法:
    python3 run_sop.py            # 交互式逐段翻译（默认）
    python3 run_sop.py --list     # 只列出每段翻译进度，不修改
    python3 run_sop.py --from 3   # 从第 3 段开始
说明:
    读取 index.html 中所有「译文框」，显示对应的英文原文，
    提示输入「译文」和「理解」，写回 index.html。
"""
import sys
from bs4 import BeautifulSoup

HTML = 'index.html'

def get_section_title(box):
    sec = box.find_parent('section')
    if sec:
        h = sec.find(['h1', 'h2', 'h3'])
        if h:
            return ' '.join(h.get_text(' ', strip=True).split())
    return ''

def get_orig_text(box):
    p = box.find_previous_sibling('p')
    if p:
        return ' '.join(p.get_text(' ', strip=True).split())
    return ''

def get_field(box, label_class, placeholder_class, text_class):
    """取某字段当前文本；若未填返回 None。"""
    ph = box.find('span', class_=placeholder_class)
    if ph is not None:
        return None
    sp = box.find('span', class_=text_class)
    if sp is not None:
        t = ' '.join(sp.get_text(' ', strip=True).split())
        return t if t else None
    # 兜底：取 label 后面的文本
    lab = box.find('span', class_=label_class)
    if lab:
        nxt = lab.find_next_sibling()
        if nxt and nxt.name == 'span':
            t = ' '.join(nxt.get_text(' ', strip=True).split())
            return t if t else None
    return None

def set_field(box, label_class, placeholder_class, text_class, value):
    """把字段设为 value；value 为空则恢复为占位符。"""
    ph = box.find('span', class_=placeholder_class)
    sp = box.find('span', class_=text_class)
    if value:
        # 写入真实内容
        if sp is None:
            if ph is not None:
                ph['class'] = [text_class]
                ph.string = value
            else:
                lab = box.find('span', class_=label_class)
                n = box.new_tag('span')
                n['class'] = [text_class]
                n.string = value
                if lab:
                    lab.insert_after(n)
        else:
            sp.string = value
    else:
        # 恢复占位符
        if sp is not None:
            sp['class'] = [placeholder_class]
            sp.string = '（在此填写中文翻译）' if 'tr' in text_class else '（用一句话写下你对这段的理解，可选填）'

def main():
    args = [a for a in sys.argv[1:]]
    list_only = '--list' in args
    from_idx = 1
    if '--from' in args:
        i = args.index('--from')
        from_idx = int(args[i + 1])

    soup = BeautifulSoup(open(HTML, encoding='utf-8').read(), 'html.parser')
    boxes = soup.select('.my-translation')
    total = len(boxes)
    print(f'共找到 {total} 个译文框\n')

    done_tr = done_un = 0
    for idx, box in enumerate(boxes, start=1):
        if idx < from_idx:
            continue
        title = get_section_title(box)
        orig = get_orig_text(box)
        cur_tr = get_field(box, 'my-tr-label', 'my-tr-placeholder', 'my-tr-text')
        cur_un = get_field(box, 'my-un-label', 'my-un-placeholder', 'my-un-text')

        print('=' * 70)
        print(f'【第 {idx}/{total} 段】 章节: {title}')
        print('-' * 70)
        print('【英文原文】')
        print(orig)
        print('-' * 70)
        print(f'【现有译文】{cur_tr if cur_tr else "（未填）"}')
        print(f'【现有理解】{cur_un if cur_un else "（未填）"}')
        print('-' * 70)
        print('👉 请把这一段的中文翻译 + 理解发给我')

        if list_only:
            print()
            continue

        print()
        tr = input('📝 请输入译文（直接回车=跳过/不改）：').strip()
        if tr:
            set_field(box, 'my-tr-label', 'my-tr-placeholder', 'my-tr-text', tr)
            done_tr += 1
        un = input('💡 请输入理解（直接回车=跳过/不改）：').strip()
        if un:
            set_field(box, 'my-un-label', 'my-un-placeholder', 'my-un-text', un)
            done_un += 1
        print()

    if list_only:
        print('=' * 70)
        print('进度清单输出完毕。')
        return

    open(HTML, 'w', encoding='utf-8').write(str(soup))
    print('=' * 70)
    print(f'✅ 已保存到 {HTML}')
    print(f'   本次新填译文 {done_tr} 条，新填理解 {done_un} 条。')
    print('   下一步: 本地预览 index.html → git add -A && git commit && git push')

if __name__ == '__main__':
    main()
