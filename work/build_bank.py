#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the standard question bank JSON (spec section 6) from extracted text.

Layouts handled
---------------
unnumbered  stem + A/B/C/D options + "答案：X 解析：..." repeating, no question
            numbers  (EPI 综合能力题库 4-1 .. 4-7).  Block boundaries are recovered
            from option runs plus the concluding phrase of each explanation.
numbered    explicit question numbers, with answers either inline or collected in a
            trailing 答案解析 section (真题 / 时政 / 模拟卷).
pair        a numbered question file joined with a numbered 【答案】 file
            (EPI 综合能力500题, 企业文化试题, 笔试模拟卷).

Also expands option lines that PDF extraction merged onto one physical line
("A．实用 欲望 B．生活 情感 C．娱乐 目标 D．交换 生存").

Output: work/bank/questions.json, work/bank/parse_report.json
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter

WORK = r"D:\app project\work"
TEXT = os.path.join(WORK, "text")
TEXT2 = os.path.join(WORK, "text2")
OUT = os.path.join(WORK, "bank")

# ---------------------------------------------------------------- hygiene

BOILERPLATE = [
    r"本资料[属仅].{0,80}(所有|使用)",
    r"不得分享|转赠|转卖",
    r"内部资料\s*免费交流",
    r"报名专线",
    r"天天向上求职工作室",
    r"职场精英工作室",
    r"店址[:：]|唯一旺旺客服",
    r"^\s*\[\[PAGE \d+\]\]\s*$",
    r"祝各位获得心仪",
    r"版权所有|违者必究|盗版可耻",
    r"扫描全能王|CamScanner",
    r"^#\s*(SOURCE|SIZE_MB)",
]
BOILER_RE = [re.compile(p) for p in BOILERPLATE]
PAGE_RE = re.compile(r"^\[\[PAGE (\d+)\]\]\s*$")

OPT_KEY = r"([A-H])\s*[．.、,，:：)）]\s*"
OPT_RE = re.compile(r"^\s*" + OPT_KEY + r"(.+?)\s*$")
OPT_SPLIT_RE = re.compile(OPT_KEY)
# 少数资料把选项写成“字母 + 空格 + 正文”，没有标点分隔（如 `A 30`、`B 32`）。
# 为避免把题干里的“A 地到 B 地”当成选项，限制正文长度并且仅作为最后手段。
OPT_LOOSE_RE = re.compile(r"^\s*([A-H])\s+(\S.{0,26})$")

ANS_ANY_RE = re.compile(
    r"(?:【\s*答\s*案\s*】|参\s*考\s*答\s*案|答\s*[案家])\s*[:：]?\s*"
    r"([A-Ha-h0-9]{1,6}|正确|错误|对|错|√|×|是|否)"
)
EXPL_END_RE = re.compile(
    r"(故本题选|本题选|故答案选|答案选|本题答案为|正确答案为|正确答案是|本题选择|"
    r"故选择|故选|答案为|因此选|正确选项为|故正确答案|本题正确答案|答案为)"
)
QNUM_TITLE_RE = re.compile(r"^\s*(?:[•·●]\s*)?(?:题目|第)\s*(\d{1,4})\s*(?:题)?\s*[．.、:：]\s*(.*)$")
QNUM_PLAIN_RE = re.compile(r"^\s*(\d{1,4})\s*[．.、]\s*(.*)$")


def match_qnum(line: str):
    m = QNUM_TITLE_RE.match(line)
    if m:
        return int(m.group(1)), (m.group(2) or "").strip()
    m = QNUM_PLAIN_RE.match(line)
    if m:
        return int(m.group(1)), (m.group(2) or "").strip()
    return None


QNUM_RE = QNUM_PLAIN_RE
ANSKEY_RE = re.compile(
    r"^\s*(\d{1,4})\s*[．.、,，]?\s*"
    r"(?:【\s*答\s*案\s*】|参\s*考\s*答\s*案|答\s*[案家])\s*[:：]?\s*"
    r"([A-Ha-h0-9]{1,6}|正确|错误|对|错|√|×)"
)
# 只有 `N.【答案】` 而**没有答案字母**的条目（如 `63.【答案】解析：…`）：
# 它是新题边界，必须识别，否则该题正文会并进上一题的解析（解析溢出）。
ANSKEY_NOANS_RE = re.compile(
    r"^\s*(\d{1,4})\s*[．.、,，]?\s*【\s*答\s*案\s*】\s*[:：]?\s*(.*)$"
)
ANSKEY_BARE_RE = re.compile(
    r"^\s*(\d{1,4})\s*[．.、,，]\s*([A-H])\s*(?=【|解\s*析|$|\s)"
)
# 部分真题把答案写在【解析】之后：`1．【解析】A。文段是围绕……`
# 要求字母后紧跟句读，避免把“【解析】第一步……”误当答案。
ANSKEY_JIEXI_RE = re.compile(
    r"^\s*(\d{1,4})\s*[．.、,，]?\s*【\s*解\s*析\s*】\s*"
    r"([A-Ha-h]{1,6}|正确|错误|对|错|√|×)\s*[。.．、]"
)
KEY_HIT_RE = re.compile(
    r"^\s*(?:【\s*答\s*案\s*】|参\s*考\s*答\s*案|答\s*[案家])\s*[:：]?\s*"
    r"([A-Ha-h0-9]{1,6}|正确|错误|对|错|√|×)"
)
STEM_HINT_RE = re.compile(
    r"(？|\?|（\s*）|\(\s*\)|_{2,}|正确的是|错误的是|不属于|包括|依次填入)"
)


def clean_lines(raw: str):
    out = []
    page = 1
    for line in raw.split("\n"):
        m = PAGE_RE.match(line.strip())
        if m:
            page = int(m.group(1))
            continue
        line = unicodedata.normalize("NFKC", line).replace("\u3000", " ").rstrip()
        if any(r.search(line) for r in BOILER_RE):
            continue
        out.append((line, page))
    return out


def _ordered_option_run(keys: str) -> bool:
    """判断这些字母是否构成“从某个字母开始的连续递增序列”。

    原实现要求必须以 A 开头，结果 `C.德国……D.德国……` 这种“一行只排 C、D”的
    排版永远不拆分，D 选项被并进 C 的正文里 —— 大量题目因此只剩 3 个选项。
    """
    if len(keys) < 2:
        return False
    i = "ABCDEFGH".find(keys[0])
    return i >= 0 and keys == "ABCDEFGH"[i:i + len(keys)]


def expand_inline_options(lines):
    """Split lines that carry several options into one line per option."""
    out = []
    for line, page in lines:
        # cut away a trailing answer marker so it cannot end up inside an option
        cut = len(line)
        for am in ANS_ANY_RE.finditer(line):
            if am.start() > 0 and OPT_SPLIT_RE.search(line[:am.start()]):
                cut = am.start()
                break
        body_line = line[:cut]
        ms = list(OPT_SPLIT_RE.finditer(body_line))
        keys = "".join(m.group(1) for m in ms)
        if len(ms) >= 2 and _ordered_option_run(keys):
            prefix = body_line[:ms[0].start()].strip()
            if prefix:
                out.append((prefix, page))
            for k, m in enumerate(ms):
                end = ms[k + 1].start() if k + 1 < len(ms) else len(body_line)
                out.append((f"{m.group(1)}. " + body_line[m.end():end].strip(), page))
            if cut < len(line):
                out.append((line[cut:], page))
        elif len(ms) == 1 and ms[0].group(1) == "A":
            # 题干行末尾直接跟了 A 选项（常见的“题干……（ ）。A.xxx”排版）。
            # 不切开会导致该题只剩 B/C/D 三个选项。
            prefix = body_line[:ms[0].start()].strip()
            if len(prefix) >= 10:
                out.append((prefix, page))
                out.append(("A. " + body_line[ms[0].end():].strip(), page))
                if cut < len(line):
                    out.append((line[cut:], page))
            else:
                out.append((line, page))
        else:
            out.append((line, page))
    return out


def opt_of(line: str):
    m = OPT_RE.match(line)
    if not m:
        m = OPT_LOOSE_RE.match(line)
    if not m:
        return None
    body = m.group(2).strip()
    if not body:
        return None
    return m.group(1), body


def _cont_lookahead(lines, i, expected, window=4):
    """向后看几行：只有出现**下一个应有的选项字母**，才能确认当前行是续行。

    若先遇到答案标记或新的答案键，说明选项组已结束 → 不是续行。
    """
    for k in range(i + 1, min(len(lines), i + 1 + window)):
        t = lines[k][0]
        o = opt_of(t)
        if o and o[0] == expected:
            return True
        if ANS_ANY_RE.match(t) or KEY_HIT_RE.match(t):
            return False
    return False


def _is_option_continuation(line, cur, lines, i):
    t = line.strip()
    if not t:
        return False
    if not cur[2] or cur[2][0][0] != "A":
        # 只对“从 A 开始的正常选项组”续行。否则会把题干里残留的
        # `C. D 项属于……` 之类解析文字当成选项，造成选项键重复。
        return False
    if len(cur[2]) >= 4:            # 四个选项齐了，不再续接
        return False
    if QNUM_RE.match(line) or ANS_ANY_RE.match(line) or KEY_HIT_RE.match(line):
        return False
    if len(t) > 120:                # 过长的多半是新题干/材料
        return False
    if re.search(r"[：:]\s*$", t):   # 题干常以冒号收尾
        return False
    if re.search(r"[（(]\s*[)）]", t):  # 含“（ ）”空括号的多半是题干
        return False
    return _cont_lookahead(lines, i, "ABCD"[len(cur[2])])


def option_runs(lines):
    runs = []
    cur = None
    for i, (line, _p) in enumerate(lines):
        o = opt_of(line)
        if o:
            if cur is None:
                cur = [i, i, [o]]
            elif o[0] == "ABCDEFGH"["ABCDEFGH".find(cur[2][-1][0]) + 1:][:1]:
                # 必须是紧接上一个选项的字母；否则说明这是新的一组选项
                cur[1] = i
                cur[2].append(o)
            else:
                runs.append(tuple(cur))
                cur = [i, i, [o]]
        elif not line.strip():
            # 空行不切断选项组：PDF 提取经常在 A 与 B/C/D 之间插入空行，
            # 若在此断开就会把 A 误并入题干，使题目只剩 3 个选项。
            continue
        elif cur is not None and _is_option_continuation(line, cur, lines, i):
            # 选项正文换行：并入上一个选项，否则该选项被截断且后续选项丢失
            k, t = cur[2][-1]
            cur[2][-1] = (k, (t + " " + line.strip()).strip())
            cur[1] = i
        else:
            if cur is not None:
                runs.append(tuple(cur))
                cur = None
    if cur is not None:
        runs.append(tuple(cur))
    # 正常选项组都从 A 开始；不是从 A 起头的“组”多半是题干里的字母串（如 “A 地到 B 地”）
    return [r for r in runs if len(r[2]) >= 2 and r[2][0][0] == "A"]


def join_lines(lines, a, b):
    return " ".join(l.strip() for l, _p in lines[a:b] if l.strip())
def clean_text(s: str) -> str:
    return re.sub(r"\s{2,}", " ", s or "").strip()


def strip_expl_prefix(s: str) -> str:
    # 也去掉答案文本留下的前导句读（`1.【答案】C。解析：…` 会剩下 `。解析：…`）
    return re.sub(r"^\s*[。．.、,，;；]?\s*【?\s*解\s*析\s*】?\s*[:：;；]?\s*", "", s or "")


def split_answer(raw: str):
    a = (raw or "").strip()
    if a in ("正确", "对", "√", "是"):
        return ["正确"], "true_false"
    if a in ("错误", "错", "×", "否"):
        return ["错误"], "true_false"
    letters = [c for c in a.upper() if c in "ABCDEFGH"]
    letters = ["D" if c == "0" else c for c in letters]
    if not letters:
        return [], "choice"
    return letters, "choice"


# 无编号资料里，题干常常把“上一题的解析尾巴”一起带进来，例如
#   `……因此，本题选择 B 选项 有一副对联，“白话通神……”  A.戊戌变法 …`
# 题干正文应从上一题解析的结论句之后开始。
CONCL_TRIM_RE = re.compile(
    r"(?:因此[，,、]?\s*)?(?:本题|故)?\s*(?:应?选择|选)\s*[A-H]\s*选项?[。.；;，,]?"
    r"|正确答案\s*(?:为|是)\s*[A-H]\s*[。.；;，,]?"
    r"|故\s*答案\s*选?\s*[A-H]\s*[。.；;，,]?"
    r"|本题答案为\s*[A-H]\s*选项?[。.；;，,]?")


def trim_stem_residue(stem: str) -> str:
    """切掉题干开头残留的“上一题解析结论句”。"""
    if not stem or len(stem) < 80:
        return stem
    last = None
    for m in CONCL_TRIM_RE.finditer(stem):
        last = m
    if last and 8 <= last.end() < len(stem) - 8:
        return stem[last.end():].lstrip("，,。.；;、 ")
    return stem


def make_question(stem, options, answer_raw, expl, page, meta):
    stem = trim_stem_residue(stem or "")
    if not stem or len(stem) < 4:
        return None
    answers, inferred = split_answer(answer_raw)
    qtype = meta.get("force_type")
    if not qtype:
        if inferred == "true_false":
            qtype = "true_false"
        elif len(answers) > 1:
            qtype = "multiple_choice"
        elif not options:
            qtype = "fill_blank"
        else:
            qtype = "single_choice"
    if qtype == "true_false":
        options = []
    status = "verified"
    if not answer_raw:
        status = "missing"
    elif options:
        keys = {o[0] for o in options}
        if any(a not in keys for a in answers):
            status = "needs_review"
    return {
        "type": qtype,
        "stem": stem,
        "options": [{"key": k, "text": clean_text(t)} for k, t in options],
        "answer": answers,
        "explanation": clean_text(expl),
        "answerStatus": status,
        "sourcePage": page,
    }


# --------------------------------- “答案为 X。”分块解析（原卷无题号、无选项字母）
# 这类扫描真题每道题以「答案为 X。」收尾，题干是若干行、选项是紧随其后的短行。
# 但同一批 PDF 常带**斜向水印/广告**（如 103202-511623199、Eun.com、"XX讲义"），
# OCR 会把水印碎片混进选项里。因此本解析器采取**宁缺毋滥**策略：
#   一个块只有在“干净”时才收；一旦发现水印/广告碎片就整块丢弃并计数。
# 这样绝不会把水印当成选项拼出一道题。
ANSBLOCK_ANSWER_RE = re.compile(r"^答案为\s*([A-Ha-h])\s*[。.．]?$")
ANSBLOCK_JUNK_RES = [
    re.compile(r"^\d{6,}\s*[-–—]\s*\d*$"),      # 103202-511623199
    re.compile(r"^\d{4,}$"),                     # 纯长数字
    re.compile(r"^\d{2,}\s*[-–—]\s*\d+$"),       # 202-51
    re.compile(r"^[\d\s\-–—.．]+$"),             # 只有数字/连字符
    re.compile(r"Eun\.com", re.I),
    re.compile(r"^各大"),
    re.compile(r"^经大"),
    re.compile(r"讲义$"),
]
ANSBLOCK_STATS = {"kept": 0, "skippedJunk": 0, "skippedShape": 0}


def parse_answerline_blocks(lines, meta, min_options=2, max_options=4):
    seq = []
    page = None
    for raw, _p in lines:
        m = OCR_PAGE_RE.match(raw.strip())
        if m:
            page = int(m.group(1))
            continue
        if raw.strip():
            seq.append((raw.strip(), page))

    out = []
    start = 0
    for i, (text, pg) in enumerate(seq):
        am = ANSBLOCK_ANSWER_RE.match(text)
        if not am:
            continue
        block = [t for t, _ in seq[start:i]
                 if not t.startswith("#") and not re.match(r"^\[\[PAGE", t)]
        start = i + 1
        if not block:
            continue
        # ① 块内出现水印/广告碎片 → 整块丢弃（不猜哪几行是选项）
        if any(any(rx.search(t) for rx in ANSBLOCK_JUNK_RES) for t in block):
            ANSBLOCK_STATS["skippedJunk"] += 1
            continue
        # ② 选项 = 块尾连续的一段短行
        opts = []
        j = len(block) - 1
        while j >= 0 and 2 <= len(block[j]) <= 30 and len(opts) < max_options:
            opts.append(block[j])
            j -= 1
        opts.reverse()
        if not (min_options <= len(opts) <= max_options):
            ANSBLOCK_STATS["skippedShape"] += 1
            continue
        stem = "".join(block[:j + 1]).strip()
        if len(stem) < 8:
            ANSBLOCK_STATS["skippedShape"] += 1
            continue
        ans = am.group(1).upper()
        if ord(ans) - 65 >= len(opts):      # 答案指向不存在的选项 → 不可信
            ANSBLOCK_STATS["skippedShape"] += 1
            continue
        letters = [chr(65 + k) for k in range(len(opts))]
        q = make_question(stem, list(zip(letters, opts)), ans, "", pg, meta)
        if q:
            out.append(q)
            ANSBLOCK_STATS["kept"] += 1
    return out


# ---------------------------------------------------------------- unnumbered

def parse_unnumbered(lines, meta):
    runs = option_runs(lines)
    questions = []
    prev_end = 0
    for idx, (rs, re_, opts) in enumerate(runs):
        next_rs = runs[idx + 1][0] if idx + 1 < len(runs) else len(lines)
        ai = None
        for j in range(re_ + 1, min(re_ + 5, next_rs)):
            if ANS_ANY_RE.search(lines[j][0]):
                ai = j
                break
        if ai is None:
            q = make_question(clean_text(join_lines(lines, prev_end, rs)), opts,
                              "", "", lines[rs][1], meta)
            if q:
                questions.append(q)
            prev_end = next_rs
            continue
        stem = clean_text(join_lines(lines, prev_end, rs))
        m = ANS_ANY_RE.search(lines[ai][0])
        tail = lines[ai][0][m.end():]
        e_idx = None
        for j in range(ai, next_rs):
            probe = tail if j == ai else lines[j][0]
            if EXPL_END_RE.search(probe):
                e_idx = j
        if e_idx is None:
            e_idx = ai
            k = next_rs - 1
            taken = 0
            while k > ai and taken < 2 and STEM_HINT_RE.search(lines[k][0]) and len(lines[k][0]) < 120:
                e_idx = k - 1
                k -= 1
                taken += 1
        expl = strip_expl_prefix(clean_text(tail + " " + join_lines(lines, ai + 1, e_idx + 1)))
        q = make_question(stem, opts, m.group(1), expl, lines[rs][1], meta)
        if q:
            questions.append(q)
        prev_end = e_idx + 1
    return questions


# ---------------------------------------------------------------- numbered

def question_starts(lines):
    starts = []
    for i, (line, _p) in enumerate(lines):
        if opt_of(line):
            continue
        if ANSKEY_RE.match(line) or ANS_ANY_RE.search(line):
            # a line that already carries the answer is not a question heading
            if ANS_ANY_RE.search(line) and len(line) < 200:
                continue
        m = match_qnum(line)
        if not m:
            continue
        no, head = m
        if no < 1 or no > 500:
            continue
        if starts and no <= starts[-1][1]:
            continue
        starts.append((i, no, head))
    return starts


def parse_question_blocks(lines, meta, min_stem=1):
    """Parse numbered blocks; attach an answer found inside the block when present.

    min_stem=1 keeps even very short blocks so that positional alignment against a
    trailing answer section stays exact; the length filter is re-applied at emit time
    by make_question.
    """
    starts = question_starts(lines)
    blocks = []
    for k, (si, no, head) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        stem_parts = [head] if head else []
        opts = []
        stop = si + 1
        state = "stem"
        for j in range(si + 1, end):
            line = lines[j][0]
            if state != "stem" and ANS_ANY_RE.search(line):
                break
            o = opt_of(line)
            if o:
                opts.append(o)
                state = "opt"
            elif state == "opt":
                if line.strip():
                    opts[-1] = (opts[-1][0], opts[-1][1] + " " + line.strip())
            elif line.strip():
                stem_parts.append(line.strip())
            stop = j + 1
        # answer + explanation living inside this block (un-numbered 答案:D style)
        inline = None
        inline_idx = None
        for j in range(stop, end):
            m = ANS_ANY_RE.search(lines[j][0])
            if m:
                tail = lines[j][0][m.end():]
                expl = strip_expl_prefix(clean_text(
                    tail + " " + join_lines(lines, j + 1, end)))
                inline = (m.group(1), expl)
                inline_idx = j
                break
        stem = clean_text(" ".join(stem_parts))
        if len(stem) >= min_stem:
            blocks.append({
                "no": no, "stem": stem, "options": opts, "page": lines[si][1],
                "inline": inline, "inlineIdx": inline_idx,
            })
    return blocks


def parse_answer_keys(lines):
    """Ordered answer keys + {no: entry}. Tolerant of OCR noise."""
    ordered = []
    by_no = {}
    for i, (line, page) in enumerate(lines):
        m = ANSKEY_RE.match(line)
        if m:
            token = m.group(2)
            expl = line[m.end():]
        else:
            jm = ANSKEY_JIEXI_RE.match(line)
            if jm:
                token = jm.group(2)
                expl = line[jm.end():]
            else:
                bm = ANSKEY_BARE_RE.match(line)
                if not bm:
                    continue
                tail = line[bm.end():]
                if len(line) > 40 and not re.search(r"【|解\s*析", line):
                    continue
                token = bm.group(2)
                expl = tail
        no = int(re.match(r"\s*(\d{1,4})", line).group(1))
        entry = [token, strip_expl_prefix(clean_text(expl)), page]
        ordered.append((no, entry))
        by_no.setdefault(no, entry)
    return ordered, by_no


def parse_numbered(lines, meta):
    blocks = parse_question_blocks(lines, meta, min_stem=1)
    ordered, by_no = parse_answer_keys(lines)

    # answer-key lines only (a marker at line start, or a numbered answer key)
    all_hits = []
    for j, (line, _page) in enumerate(lines):
        m = ANSKEY_RE.match(line) or KEY_HIT_RE.match(line)
        if m:
            expl = strip_expl_prefix(clean_text(
                line[m.end():] + " " + join_lines(lines, j + 1, j + 2)))
            all_hits.append((m.group(m.lastindex), expl))
            continue
        jm = ANSKEY_JIEXI_RE.match(line)
        if jm:
            expl = strip_expl_prefix(clean_text(
                line[jm.end():] + " " + join_lines(lines, j + 1, j + 2)))
            all_hits.append((jm.group(2), expl))

    un = [b for b in blocks if not b["inline"]]
    L = len(all_hits)
    un_nos = sorted({b["no"] for b in un if b["no"] <= L})
    seq = None
    by_num = None
    dense = (un_nos and un_nos[0] == 1 and len(un_nos) >= L * 0.9)
    if un and 0 < L <= 500 and dense:
        # a trailing 答案解析 section listed in question order: the n-th entry
        # belongs to question number n
        by_num = {n: all_hits[n - 1] for n in range(1, L + 1)}
    elif un and len(un) == len(ordered) and len(ordered) > 0 and not by_no:
        seq = [e for _no, e in ordered]
    elif un and len(un) == len(all_hits):
        seq = all_hits

    out = []
    ui = 0
    for b in blocks:
        if b["inline"]:
            answer_raw, expl = b["inline"]
        elif by_num is not None and b["no"] in by_num:
            answer_raw, expl = by_num[b["no"]]
        elif seq is not None and ui < len(seq):
            answer_raw, expl = seq[ui]
            ui += 1
        else:
            entry = by_no.get(b["no"])
            answer_raw = entry[0] if entry else ""
            expl = entry[1] if entry else ""
        q = make_question(b["stem"], b["options"], answer_raw, expl, b["page"], meta)
        if q:
            out.append(q)
    return out


# ---------------------------------------------------------------- pair

def parse_numbered_qfile(lines):
    items = {}
    for si, no, head in question_starts(lines):
        pass
    starts = question_starts(lines)
    for k, (si, no, head) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        stem_parts = [head] if head else []
        opts = []
        for line, _p in lines[si + 1:end]:
            o = opt_of(line)
            if o:
                opts.append(o)
            elif opts:
                if line.strip():
                    opts[-1] = (opts[-1][0], opts[-1][1] + " " + line.strip())
            elif line.strip():
                stem_parts.append(line.strip())
        items[no] = {"stem": clean_text(" ".join(stem_parts)), "options": opts,
                     "page": lines[si][1]}
    return items


def parse_numbered_afile(lines):
    ans = {}
    cur = None
    for line, page in lines:
        m = ANSKEY_RE.match(line)
        if m:
            cur = int(re.match(r"\s*(\d{1,4})", line).group(1))
            ans[cur] = [m.group(2), strip_expl_prefix(line[m.end():]), page]
            continue
        # `63.【答案】解析：…` 这类**漏了答案字母**的条目也是新题的边界；
        # 不识别它，该题正文就会被并进上一题的解析（实测 11 题出现解析溢出）。
        m2 = ANSKEY_NOANS_RE.match(line)
        if m2 and not re.match(r"^[A-Ha-h0-9]|^正确|^错误|^对|^错", (m2.group(2) or "").strip()):
            cur = int(m2.group(1))
            if cur not in ans:
                ans[cur] = ["", strip_expl_prefix(m2.group(2)), page]
            continue
        if cur is None:
            continue
        if line.strip():
            if not ans[cur][0]:
                mk = ANS_ANY_RE.search(line)
                if mk:
                    ans[cur][0] = mk.group(1)
                    ans[cur][1] += " " + strip_expl_prefix(line[mk.end():])
                    continue
            ans[cur][1] += " " + line.strip()
    return ans


def parse_pair(qfile, afile, meta):
    qlines = expand_inline_options(clean_lines(open(qfile, encoding="utf-8", errors="replace").read()))
    alines = clean_lines(open(afile, encoding="utf-8", errors="replace").read())
    qs = parse_numbered_qfile(qlines)
    ans = parse_numbered_afile(alines)
    if len(ans) and len(qs) and (not set(qs) & set(ans)):
        # answer file numbering does not line up: fall back to positional
        keys = [ans[k] for k in sorted(ans)]
        out = []
        for idx, no in enumerate(sorted(qs)):
            item = qs[no]
            a = keys[idx] if idx < len(keys) else ["", "", item["page"]]
            q = make_question(item["stem"], item["options"], a[0], a[1], item["page"], meta)
            if q:
                out.append(q)
        return out
    out = []
    for no in sorted(qs):
        item = qs[no]
        a = ans.get(no, ["", "", item["page"]])
        q = make_question(item["stem"], item["options"], a[0], a[1], item["page"], meta)
        if q:
            out.append(q)
    return out


# --------------------------------------------------- 分段重排题号的配对来源
# 资料分析这类「材料 + 若干小题」的资料，**每组小题的题号都从 1 重新开始**；
# 而 `question_starts` 要求题号严格递增（`no <= starts[-1][1]` 就丢弃），
# 于是只吃下第一组：实测资料分析学生版有 ~250 道小题，却只解析出 56 题，
# 而且「按题号取答案」会把不同组的题与答案错配（答案版是**全局连续**编号）。
# 对策：以「一、根据以下资料…」这类分组标题切段，段内递增即可，段间允许重排，
# 再把各段按**文档顺序**串起来，最后与答案文件的全局序列**逐位对齐**。
# 安全性：位数不一致就**拒绝产出**（宁可不出题，也不出错配的题）。
SECTION_RE = re.compile(
    r"^\s*[一二三四五六七八九十]+\s*[、.．]\s*(?:根据以下|阅读以下|以下资料|根据材料|请根据)")
PAIR_POSITIONAL_TOLERANCE = 0.05     # 数量偏差上限：超过即判定为不可靠


def split_sections(lines):
    """按‘材料分组’标题切分；没有分组标题时整份作为一段。"""
    bounds = [i for i, (t, _p) in enumerate(lines) if SECTION_RE.match(t)]
    if not bounds:
        return [lines]
    out = []
    if bounds[0] > 0:
        out.append(lines[:bounds[0]])
    for k, s in enumerate(bounds):
        e = bounds[k + 1] if k + 1 < len(bounds) else len(lines)
        out.append(lines[s:e])
    return out


def parse_pair_sectioned(qfile, afile, meta, label=""):
    """分段配对解析（备用口径）：段内题号递增、段间重排时使用。

    返回题列表；数量与答案文件相差超过容差则**拒绝产出**（宁可不出题，也不错配答案）。
    """
    qlines = expand_inline_options(
        clean_lines(open(qfile, encoding="utf-8", errors="replace").read()))
    alines = clean_lines(open(afile, encoding="utf-8", errors="replace").read())
    items = []
    for seg in split_sections(qlines):
        d = parse_numbered_qfile(seg)
        for no in sorted(d):
            items.append(d[no])
    ans = parse_numbered_afile(alines)
    order = [ans[k] for k in sorted(ans)]
    n_q, n_a = len(items), len(order)
    if not n_q or not n_a:
        print(f"   ⚠️ 分段配对不可用：题目 {n_q} / 答案 {n_a}（{label}）")
        return []
    tol = max(2, int(n_a * PAIR_POSITIONAL_TOLERANCE))
    if abs(n_q - n_a) > tol:
        print(f"   ❌ 分段配对**拒绝产出**：题目 {n_q} 与答案 {n_a} 数量相差超过容差 {tol}"
              f"（{label}）—— 逐位对齐不可靠，故不出题，以免错配答案。")
        return []
    out = []
    for i, it in enumerate(items):
        a = order[i] if i < len(order) else ["", "", it["page"]]
        q = make_question(it["stem"], it["options"], a[0], a[1], it["page"], meta)
        if q:
            out.append(q)
    return out


# ------------------------------------------- 表格残留行污染递增序列的修复
# 资料分析这类题的**材料里有大量表格**，表格单元格被抽成独立行后会出现
# `52 1.49 1.28 1.24 1.15` 这种「数字.数字」的行。`match_qnum` 会把它当作题号行
# （题号 52），而 `question_starts` 之后只接受**严格递增**的题号 —— 于是这个 52
# 直接把后面所有真题（题号 5、6、7…）判成“题号回退”而丢弃：
# 实测学生版实有 250 道小题、题号 1~250 连续，却只解析出 **56** 题。
# 修复：加一个**严格题号行判据**——题号行后面必须紧跟选项（或有问句标记），
# 表格残留行不满足，被提前滤掉，递增序列就不会被污染。
STRICT_LOOKAHEAD = 5


def question_starts_strict(lines):
    """只接受『后随选项或有问句标记』的题号行，滤掉表格/统计残留行。"""
    starts = []
    for i, (line, _p) in enumerate(lines):
        if opt_of(line):
            continue
        if ANSKEY_RE.match(line) or ANS_ANY_RE.search(line):
            if ANS_ANY_RE.search(line) and len(line) < 200:
                continue
        m = match_qnum(line)
        if not m:
            continue
        no, head = m
        if no < 1 or no > 500:
            continue
        if starts and no <= starts[-1][1]:
            continue
        # 严格判据：紧邻后续行里出现选项，或题干自带问句标记
        near_opt = False
        for j in range(i + 1, min(len(lines), i + 1 + STRICT_LOOKAHEAD)):
            if opt_of(lines[j][0]):
                near_opt = True
                break
            if lines[j][0].strip() and match_qnum(lines[j][0]):
                break
        if not near_opt and not re.search(r"[：:？?]|（\s*）|\(\s*\)|____", head):
            continue
        starts.append((i, no, head))
    return starts


def parse_pair_strict(qfile, afile, meta, label=""):
    """配对解析：用严格题号行判据解析学生版，再**按题号**与答案文件对齐。

    适用于「题号全局连续、但材料表格会污染题号行」的配对来源（资料分析）。
    安全性：题目与答案的题号交集过少则**拒绝产出**，不靠位置猜测。
    """
    qlines = expand_inline_options(
        clean_lines(open(qfile, encoding="utf-8", errors="replace").read()))
    alines = clean_lines(open(afile, encoding="utf-8", errors="replace").read())
    starts = question_starts_strict(qlines)
    items = {}
    for k, (si, no, head) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(qlines)
        stem_parts = [head] if head else []
        opts = []
        for line, _p in qlines[si + 1:end]:
            o = opt_of(line)
            if o:
                opts.append(o)
            elif opts:
                if line.strip():
                    opts[-1] = (opts[-1][0], opts[-1][1] + " " + line.strip())
            elif line.strip():
                stem_parts.append(line.strip())
        items[no] = {"stem": clean_text(" ".join(stem_parts)), "options": opts,
                     "page": qlines[si][1]}
    ans = parse_numbered_afile(alines)
    inter = set(items) & set(ans)
    if not items or not ans or len(inter) < 0.6 * min(len(items), len(ans)):
        print(f"   ❌ 严格配对**拒绝产出**：题目 {len(items)} / 答案 {len(ans)} / 题号交集 "
              f"{len(inter)} —— 对齐不可靠，故不出题（{label}）。")
        return []
    out = []
    for no in sorted(items):
        if no not in ans:
            continue
        it = items[no]
        a = ans[no]
        q = make_question(it["stem"], it["options"], a[0], a[1], it["page"], meta)
        if q:
            out.append(q)
    return out


# ------------------------------------------------------------------ OCR 题库
# 扫描件经 RapidOCR 识别后，文本形如：
#     1，1，5，13，41，（)
#     A. 53
#     B. 79
#     C. 95
#     D. 121
#     答案：D解析：解法一：第一步，本题考查多级数列……
# 据此按“题干 → 选项组 → 答案行”切块。识别讹字无法避免，因此凡答案无法
# 对应到选项的题目一律标为 needs_review，由 APP 排除出正确率统计。

OCR_ANS_RE = re.compile(
    r"^\s*(?:【\s*答\s*案\s*】\s*[:：]?|(?:参\s*考\s*答\s*案|答\s*案)\s*[:：])\s*"
    r"([A-Ha-h]{0,4})")# 双栏 PDF 经 OCR 后，答案字母有时独占下一行
OCR_ANS_LONE_RE = re.compile(r"^\s*([A-Ha-h]{1,6}|正确|错误|对|错|√|×)\s*$")
OCR_EXPL_RE = re.compile(r"[解详]\s*析\s*[:：]")
OCR_PAGE_RE = re.compile(r"^\[\[PAGE (\d+)\]\]$")
OCR_OPT_RE = re.compile(r"^\s*([A-Ha-h])\s*[.、．，,:：]\s*(.+)$")
OCR_NOISE_RE = re.compile(
    r"(第[一二三四五六七八九十]步|因此|本题考查|规律为|解法|做一次和|和数列|等比数列|等差数列|"
    r"^\s*[\(\（]?\s*\d+\s*[\)\）]?\s*$)")
# OCR 讹字的典型痕迹：方括号、连续等号/减号、连续引号
OCR_GARBLE_RE = re.compile(r"[\[\]{}<>|~^\\]|[-=－＝]{2,}|[“”]{2,}")
OCR_EXPL_UNRELIABLE = "（OCR 识别不可靠，本段解析未采用；请查阅原资料对应页）"

# 解析中自带的结论句（独立于答案行的第二处答案信息，亦可用于回填）
OCR_CONCL_RES = [
    re.compile(r"选择\s*([A-Ha-h])\s*选项"),
    re.compile(r"故选\s*([A-Ha-h])"),
    re.compile(r"故本题\s*选\s*([A-Ha-h])"),
    re.compile(r"本题\s*选\s*([A-Ha-h])"),
    re.compile(r"应选\s*([A-Ha-h])"),
    re.compile(r"正确答案\s*(?:为|是)?\s*([A-Ha-h])"),
    re.compile(r"选\s*([A-Ha-h])\s*项"),
    re.compile(r"答案\s*(?:为|是)\s*([A-Ha-h])\b"),
]


# 部分扫描时政题库把答案压成一行紧凑串排在卷末，例如 `1B2A3D4ABCD5C`
OCR_KEYLINE_RE = re.compile(r"^\s*(?:\d{1,3}\s*[.、．]?\s*[A-Ha-h]{1,6}\s*)+$")


def compact_answer_map(lines):
    """从卷末紧凑答案串提取 {题号: 答案}。"""
    m = {}
    for line, _p in lines:
        t = line.strip()
        if len(t) < 6 or not OCR_KEYLINE_RE.match(t):
            continue
        pairs = re.findall(r"(\d{1,3})\s*[.、．]?\s*([A-Ha-h]{1,6})", t)
        if len(pairs) < 2:
            continue
        for no, ans in pairs:
            m[int(no)] = ans.upper()
    return m


def inject_compact_answer_keys(lines):
    """把紧凑答案串展开成 numbered 解析器认识的答案行。"""
    m = compact_answer_map(lines)
    if not m:
        return lines
    page = lines[-1][1] if lines else 1
    extra = [(f"{no}．【答案】{ans}", page) for no, ans in sorted(m.items())]
    return lines + extra


# 扫描件 OCR 常把选项写成“字母紧跟正文”而没有分隔符，例如
#   `A山水相连的好邻居B.信义相交的好朋友C守望相助的好伙伴D.患难与共的好兄弟`
# 若不补分隔符，整行会被并入题干，该题一个选项都不剩。
BARE_LETTER_RE = re.compile(r"(?<![A-Za-z0-9])([A-H])(?=[\u4e00-\u9fff“”《〈（(])")


def normalize_bare_option_letters(line):
    hits = list(BARE_LETTER_RE.finditer(line))
    if len(hits) < 2:
        return line
    keys = "".join(m.group(1) for m in hits)
    if len(set(keys)) != len(keys) or keys != "".join(sorted(keys)):
        return line          # 不是递增且不重复的选项序列，不动它
    out, prev = [], 0
    for m in hits:
        out.append(line[prev:m.start(1)])
        out.append(m.group(1) + ". ")
        prev = m.start(1) + 1
    out.append(line[prev:])
    return "".join(out)


# 扫描件里的水印/推广文字会混进题干与选项，必须在解析前剥掉。
# 注意「…输部微信公众号发布…」是正文，所以只匹配带号/链接的推广形态。
OCR_WM_RES = [
    re.compile(r"微信\s*[:：]?\s*[A-Za-z0-9_\-]{3,24}"),
    re.compile(r"\bQQ\s*[:：]?\s*\d{4,12}"),
    re.compile(r"https?://\S+"),
    re.compile(r"www\.[A-Za-z0-9.\-]+"),
    re.compile(r"(?:家?有小宁)(?:唯一总信)?"),
    re.compile(r"[^\s]{0,8}关注公众号获取售后服务"),
    re.compile(r"\bjyxn\d+\b"),
    re.compile(r"\b[A-Za-z]{2,6}\d{4,8}\b(?=\s|$)"),
]


def strip_ocr_watermarks(text: str) -> str:
    for rx in OCR_WM_RES:
        text = rx.sub("", text or "")
    return re.sub(r"\s{2,}", " ", text).strip()


def ocr_lines(raw: str):
    """OCR 文本 → 清洗后的行（去页码、去水印）。"""
    return [(strip_ocr_watermarks(t), p) for t, p in clean_lines(raw)]


def parse_ocr_sectioned(lines, meta):
    """按“卷末答案串”分段解析。

    某些扫描时政试题把整份资料切成很多**小题组**，每组 4~7 题，题号从 1 重新
    开始，答案紧跟在组末（如 `1B2A3D4ABCD5C`）。若把整份文件当一套题，
    题号会互相覆盖，只能得到最后一组的几道题。故以答案串为界逐段解析。
    """
    bounds = [i for i, (t, _p) in enumerate(lines) if OCR_KEYLINE_RE.match(t.strip())]
    if not bounds:
        return []
    out = []
    prev = 0
    for b in bounds:
        seg = lines[prev:b + 1]
        prev = b + 1
        if not any(QNUM_RE.match(t) for t, _p in seg):
            continue
        amap = compact_answer_map(seg)
        if not amap:
            continue
        out += parse_numbered(inject_compact_answer_keys(seg), meta)
    return out


def parse_ocr_choice(lines, meta):
    """解析 OCR 后的“题干 + A-D 选项 + 答案：X解析：…”结构。"""
    # 去掉页码标记但记录当前页
    seq = []
    page = None
    for raw, _p in lines:
        m = OCR_PAGE_RE.match(raw.strip())
        if m:
            page = int(m.group(1))
            continue
        if not raw.strip():
            continue
        seq.append((raw.strip(), page))

    out = []
    i = 0
    n = len(seq)
    while i < n:
        text, pg = seq[i]
        # 找选项组起点：从 i+1 开始连续出现 A/B/C/D
        j = i + 1
        opts = []
        while j < n and len(opts) < 8:
            m = OCR_OPT_RE.match(seq[j][0])
            if m:
                opts.append((m.group(1).upper(), m.group(2)))
                j += 1
            else:
                break
        if len(opts) < 2:
            i += 1
            continue
        # 选项之后必须紧跟答案行（允许少量噪声行）
        k = j
        ans_raw, expl = None, ""
        while k < n and k <= j + 3:
            am = OCR_ANS_RE.match(seq[k][0])
            if am:
                ans_raw = am.group(1)
                rest = OCR_ANS_RE.sub("", seq[k][0], count=1)
                em = OCR_EXPL_RE.search(rest)
                expl = rest[em.end():] if em else rest
                # 后续行并入解析，直到下一个题块的题干
                k += 1
                if not ans_raw.strip() and k < n:
                    lm = OCR_ANS_LONE_RE.match(seq[k][0])
                    if lm:
                        ans_raw = lm.group(1)
                        k += 1
                buf = [expl] if expl else []
                while k < n:
                    nxt = seq[k][0]
                    if OCR_PAGE_RE.match(nxt):
                        k += 1
                        continue
                    # 若当前行之后紧跟选项组，说明它是新题干
                    if k + 1 < n and OCR_OPT_RE.match(seq[k + 1][0]) and not OCR_OPT_RE.match(nxt):
                        break
                    if OCR_ANS_RE.match(nxt):
                        break
                    buf.append(nxt)
                    k += 1
                    if len(" ".join(buf)) > 1200:
                        break
                expl = "\n".join(buf)
                break
            k += 1
        if ans_raw is None:
            i += 1
            continue
        # 答案行没识别出字母时，尝试从解析自带的结论句回填（同一份资料的独立答案信息）
        recovered = False
        if not ans_raw.strip():
            cand = []
            for rx in OCR_CONCL_RES:
                cand += [m.group(1).upper() for m in rx.finditer(expl or "")]
            if len(set(cand)) == 1:
                ans_raw = cand[0]
                recovered = True
            else:
                i += 1
                continue
        # 题干：第 i 行（若过短则向前并入一行）
        stem = text
        if len(stem) < 6 and i > 0:
            stem = seq[i - 1][0] + " " + stem
        if OCR_NOISE_RE.search(stem):
            i += 1
            continue
        q = make_question(stem, opts, ans_raw, expl, pg, meta)
        if q:
            q["tags"] = list(q.get("tags") or []) + ["OCR"]
            if recovered:
                q["tags"] = list(q["tags"]) + ["答案由解析回填"]
            # 解析若被 OCR 讹字污染，则替换为如实说明，不展示乱码、也不编造解析
            if len(OCR_GARBLE_RE.findall(q.get("explanation") or "")) >= 3:
                q["explanation"] = OCR_EXPL_UNRELIABLE
                q["tags"] = list(q["tags"]) + ["解析待核"]
            out.append(q)
        i = k if k > i else i + 1
    return out


# ---------------------------------------------------------------- 行内答案式
# 时政题库的常见版式：
#     1.2025 年 8 月 1 日，习近平同尼泊尔总统鲍德尔互致贺电……
#     A.60 周年
#     B.70 周年
#     参考答案：B
#     【解析】：……
# 且常有“同行排四个选项”“A 与 ．之间有空格”等情况。numbered 解析器依赖
# 题号块与尾部答案区的对齐，遇到这种版式会大量漏答；此处改为**就地配对**：
# 逐个找“题干 → 选项 → 答案标记”，答案字段紧随选项，天然对齐。
INL_QSTART_RE = re.compile(r"^\s*(\d{1,4})\s*[．.、]\s*(\S.*)$")
INL_ANS_RE = re.compile(
    r"^\s*(?:【\s*答\s*案\s*】|参\s*考\s*答\s*案|答\s*[案家])\s*[:：]?\s*"
    r"([A-Ha-h]{1,6}|正确|错误|对|错|√|×)")
# 选项行允许字母与分隔符之间有空格（OCR/排版常见）
INL_OPT_RE = re.compile(r"^\s*([A-Ha-h])\s*[．.、，,:：]\s*(\S.*)$")


def looks_like_question(lines, i, window=20):
    """向后看若干行，确认这行确实是一道题的题干（紧随选项或答案标记）。"""
    n = len(lines)
    for k in range(i + 1, min(n, i + 1 + window)):
        t = lines[k][0]
        if INL_ANS_RE.match(t):
            return True
        if INL_OPT_RE.match(t):
            return True
        if INL_QSTART_RE.match(t):
            return False
    return False


def parse_inline_answer(lines, meta):
    """就地把“题干 + 选项 + 参考答案/答案”配对成题。"""
    out = []
    n = len(lines)
    i = 0
    while i < n:
        m = INL_QSTART_RE.match(lines[i][0])
        if not m or not looks_like_question(lines, i):
            i += 1
            continue
        page = lines[i][1]
        stem_parts = [m.group(2)]
        opts = []
        ans_raw = None
        expl_parts = []
        j = i + 1
        while j < n:
            t = lines[j][0]
            if (opts or ans_raw is not None) and INL_QSTART_RE.match(t) \
                    and looks_like_question(lines, j):
                break
            am = INL_ANS_RE.match(t)
            if am:
                ans_raw = am.group(1)
                rest = INL_ANS_RE.sub("", t, count=1)
                rest = re.sub(r"^[\s。．.：:，,、；;]*", "", rest)
                if rest.strip():
                    expl_parts.append(rest)
                j += 1
                while j < n:
                    nt = lines[j][0]
                    if INL_QSTART_RE.match(nt) and looks_like_question(lines, j):
                        break
                    if INL_ANS_RE.match(nt):
                        break
                    expl_parts.append(nt)
                    j += 1
                break
            o = INL_OPT_RE.match(t)
            if o:
                opts.append((o.group(1).upper(), o.group(2)))
            elif opts:
                expl_parts.append(t)
            else:
                stem_parts.append(t)
            j += 1
            if j - i > 240:
                break
        stem = clean_text(" ".join(x for x in stem_parts if x and x.strip()))
        q = make_question(stem, opts, ans_raw or "", clean_text("\n".join(expl_parts)), page, meta)
        if q:
            out.append(q)
        i = j if j > i else i + 1
    return out


# ---------------------------------------------------------------- source map

OCR_DIR = os.path.join(WORK, "ocr")

# OCR 文本 → (类别, 章节) 归类规则；按关键词匹配相对路径。
# 未匹配到的 OCR 文本仅作为文字资料保留，不进题库（如面试资料）。
OCR_RULES = [
    ("数字推理350", "EPI通用能力", "数字推理（350题·OCR）", ["行测", "OCR"]),
    # 说明：“图形推理”OCR 后四个选项均为“如上图所示”，图形本身无法提取，
    #       题目不含可作答信息，故**不入题库**，仅保留文本供查阅。
    ("资料分析图表", "EPI通用能力", "资料分析（图表·OCR）", ["行测", "OCR", "缺图表", "材料需回原文"]),
    ("逻辑推理精选400", "EPI通用能力", "逻辑推理（400题·OCR）", ["行测", "OCR"]),
    ("言语理解400", "EPI通用能力", "言语理解与表达（400题·OCR）", ["行测", "OCR"]),
    ("数学运算", "EPI通用能力", "数学运算（400题·OCR）", ["行测", "OCR"]),
    ("2014国电", "历年真题", "2014国电集团笔试真题（OCR）", ["真题", "OCR"]),
    ("2015国电", "历年真题", "2015国电集团笔试真题（OCR）", ["真题", "OCR"]),
    ("2016年国电", "历年真题", "2016国电集团笔试真题（OCR）", ["真题", "OCR"]),
    ("2017国电", "历年真题", "2017国电集团笔试真题（OCR）", ["真题", "OCR"]),
    ("2022国家能源集团招聘在线笔试", "历年真题", "2022国家能源集团笔试真题（OCR）", ["真题", "OCR"]),
    # 补救 OCR：文本层残缺（选项正文丢失）的讲话考点 400 题
    # 注意：OCR 输出文件名已把 .pdf 换成 .txt，规则关键词**不能带扩展名**
    ("重要讲话考点预测400题（更新至25年7月底）", "时政",
     "24—25年重要讲话考点预测400题（OCR）", ["时政", "OCR", "重要讲话"]),
    # 2026-10-18 审计补入：`audit_ingest_gap.py` 发现该文件试解析可得 293 题、
    # 其中 264 题已验证（采纳率 90.1%），却因时政月份兜底规则里的「考点」二字被排除
    # —— 属**规则漏掉的真内容**，故显式接入。其 `-纯题本` 同伴仍由 OCR_EXCLUDE 挡掉。
    ("重要讲话考点预测300题（更新至26年3月底）", "时政",
     "25—26年重要讲话考点预测300题（OCR）", ["时政", "OCR", "重要讲话"]),
    ("考点速记  2025.9.29中共中央政治局会议", "时政",
     "2025年9月29日中央政治局会议（OCR）", ["时政", "OCR", "政治局会议"]),
    ("考点速记  2024.12中央经济工作会议", "时政",
     "2024年12月中央经济工作会议（OCR）", ["时政", "OCR", "中央经济工作会议"]),
    ("考点速记  2025.12中央经济工作会议", "时政",
     "2025年12月中央经济工作会议（OCR）", ["时政", "OCR", "中央经济工作会议"]),
]

# 匹配到这些子串的 OCR 文本只作文字资料保留，不入题库
# （如“-纯题本”是同一套题的题干版，答案版已入库，避免产生大量无答案重复题）
OCR_EXCLUDE = ["-纯题本"]

# 少数真题扫描件的答案集中在文末（题号 + 【解析】X。），应走 numbered 而非 ocr
OCR_MODE_OVERRIDE = {
    "2014国电": "numbered",
    "2015国电": "numbered",
}

# 题目与答案解析分列两个文件的题库（补救提取所得）
# 2026-10-18：`【模拟试题】2025年中央一号文件` 的题目/答案文件**题号错位**
# （答案文件第 1 题答案 D 与解析均对应题干 1，但解析器按位置配对得到 A），
# 经自洽复核判定不可靠，故**不接入题库**；该主题改由
# `2025年中央一号文件（全文+划重点+58题）.txt` 提供。原文仍保留在 text2。
#
# 2026-10-19：使用者新加入 `D:\DOWNLOADS\F` 的 14 份（3 套校招真题 + 4 个模块易错 1000 题），
#   均为「学生版（题干）」＋「答案版（答案+解析）」两份一对，文本层完好、题号一一对应，
#   故接入题库。因它们位于 work/text7（而非既有的 text2），元组改为带**基目录**：
#       (base, 题目文件, 答案文件, 类别, 章节, 标签, 解析口径)
#   解析口径：pair=按题号配对（题号全局连续、无表格污染）；
#             pair_strict=严格题号行判据再按题号配对（材料含表格时必需）。
SOURCES_PAIR = [
    # ---- 校招真题（学生版 + 答案版）----
    ("text7", "2021年国家能源集团春季校园招聘笔试题-学生.txt",
     "2021年国家能源集团春季校园招聘笔试题-答案.txt",
     "历年真题", "2021年春季校招笔试真题", ["真题", "校招"], "pair"),
    ("text7", "2022年国家能源集团秋季校园招聘笔试题-学生.txt",
     "2022年国家能源集团秋季校园招聘笔试题-答案.txt",
     "历年真题", "2022年秋季校招笔试真题", ["真题", "校招"], "pair"),
    ("text7", "2023年国家能源集团秋季校园招聘笔试题-学生.txt",
     "2023年国家能源集团秋季校园招聘笔试题-答案.txt",
     "历年真题", "2023年秋季校招笔试真题", ["真题", "校招"], "pair"),
    # ---- 秋招常考易错 1000 题（学生版 + 答案版，按行测模块分册）----
    ("text7", "国家能源秋招常考易错1000题-判断推理-学生版.txt",
     "国家能源秋招常考易错1000题-判断推理-答案版.txt",
     "EPI通用能力", "判断推理（易错1000题）", ["行测", "易错题"], "pair"),
    ("text7", "国家能源秋招常考易错1000题-数量关系-学生版.txt",
     "国家能源秋招常考易错1000题-数量关系-答案版.txt",
     "EPI通用能力", "数量关系（易错1000题）", ["行测", "易错题"], "pair"),
    ("text7", "国家能源秋招常考易错1000题-言语理解-学生版.txt",
     "国家能源秋招常考易错1000题-言语理解-答案版.txt",
     "EPI通用能力", "言语理解（易错1000题）", ["行测", "易错题"], "pair"),
    ("text7", "国家能源秋招常考易错1000题-资料分析-学生版.txt",
     "国家能源秋招常考易错1000题-资料分析-答案版.txt",
     "EPI通用能力", "资料分析（易错1000题）", ["行测", "易错题", "材料需回原文"],
     "pair_strict"),
]


def discover_ocr_sources():
    """扫描 work/ocr 下已完成的 OCR 文本，按 OCR_RULES 归类。"""
    found = []
    if not os.path.isdir(OCR_DIR):
        return found
    for dp, _d, fs in os.walk(OCR_DIR):
        for fn in sorted(fs):
            if not fn.lower().endswith(".txt"):
                continue
            rel = os.path.relpath(os.path.join(dp, fn), OCR_DIR)
            if fn.startswith("_"):
                continue
            if any(x in rel for x in OCR_EXCLUDE):
                continue
            hit = None
            for key, cat, ch, tags in OCR_RULES:
                if key in rel:
                    hit = (cat, ch, tags)
                    break
            if hit is None:
                # 时政月份类：2024年X月 / 2025年X月（含 2024.12 式写法）
                m = re.search(r"((?:2024|2025|2026)\s*[年.]\s*\d{1,2}\s*月?)", rel)
                if m and "时政" in rel and "考点" not in rel:
                    ym = m.group(1).replace(".", "年").replace(" ", "")
                    if not ym.endswith("月"):
                        ym += "月"
                    ym = re.sub(r"年(\d{1,2})月", lambda x: f"年{int(x.group(1))}月", ym)
                    hit = ("时政", f"{ym}时政（OCR）", ["时政", "OCR"])
            if hit is None:
                continue
            found.append((rel, hit[0], hit[1], hit[2]))
    return found


SOURCES = [
    # (base, file, mode, category, chapter, tags, answer file)
    ("text", "4-1-EPI综合能力题库----常识题精选600道_.txt", "unnumbered", "EPI通用能力", "常识判断（600题）", ["重点", "高频"], ""),
    ("text", "4-2-EPI综合能力题库----数字推理题精选300道详解_.txt", "unnumbered", "EPI通用能力", "数字推理（300题）", [], ""),
    ("text", "4-3-EPI综合能力题库----数学运算、应用题精选400道详解_.txt", "unnumbered", "EPI通用能力", "数学运算（400题）", [], ""),
    ("text", "4-4-EPI综合能力题库----言语理解与表达试题精选350道详解_.txt", "unnumbered", "EPI通用能力", "言语理解与表达（350题）", [], ""),
    ("text", "4-5-EPI综合能力题库----图形推理习题精选300道详解_.txt", "unnumbered", "EPI通用能力", "图形推理（300题）", ["图形"], ""),
    ("text", "4-6-EPI综合能力题库----逻辑推理题精选300道详解_.txt", "unnumbered", "EPI通用能力", "逻辑推理（300题）", [], ""),
    ("text", "4-7-EPI综合能力题库----资料分析题库+解析_.txt", "unnumbered", "EPI通用能力", "资料分析", ["图表"], ""),

    ("text", "EPI综合能力500题\\EPI综合能力测试-判断推理-试题.txt", "pair", "EPI通用能力", "判断推理（100题）", ["真题风格"], "EPI综合能力500题\\EPI综合能力测试-判断推理-试题答案.txt"),
    ("text", "EPI综合能力500题\\EPI综合能力测试-思维策略-试题.txt", "pair", "EPI通用能力", "思维策略（100题）", [], "EPI综合能力500题\\EPI综合能力测试-思维策略-试题答案.txt"),
    ("text", "EPI综合能力500题\\EPI综合能力测试-数量关系-试题.txt", "pair", "EPI通用能力", "数量关系（100题）", [], "EPI综合能力500题\\EPI综合能力测试-数量关系-试题答案.txt"),
    ("text", "EPI综合能力500题\\EPI综合能力测试-言语理解-试题.txt", "pair", "EPI通用能力", "言语理解（100题）", [], "EPI综合能力500题\\EPI综合能力测试-言语理解-试题答案.txt"),
    ("text", "EPI综合能力500题\\EPI综合能力测试-资料分析-试题.txt", "pair", "EPI通用能力", "资料分析（100题）", ["图表"], "EPI综合能力500题\\EPI综合能力测试-资料分析-试题答案.txt"),
    ("text", "EPI综合能力500题\\常识200道试题.txt", "pair", "EPI通用能力", "常识判断（200题）", ["重点"], "EPI综合能力500题\\常识200道试题答案.txt"),

    ("text", "国家能源集团企业文化试题.txt", "pair", "企业文化", "企业文化专项", ["必背", "重点"], "国家能源集团企业文化试题答案.txt"),
    ("text", "国家能源集团笔试模拟卷（一）.txt", "pair", "模拟笔试", "模拟卷（一）", ["模拟考"], "国家能源集团笔试模拟卷（一）解析.txt"),
    ("text", "国家能源集团笔试模拟卷（二）.txt", "pair", "模拟笔试", "模拟卷（二）", ["模拟考"], "国家能源集团笔试模拟卷（二）解析.txt"),

    ("text", "2025国家能源校招笔试真题（不含英语）完整版答案及解释.txt", "numbered", "历年真题", "2025校招真题", ["真题", "优先"], ""),
    ("text", "2025国家能源校招笔试真题（含英语）完整版答案及解释.txt", "numbered", "历年真题", "2025校招真题（含英语）", ["真题"], ""),
    ("text", "2024国家能源校招笔试真题及参考答案1.txt", "numbered", "历年真题", "2024校招真题（一）", ["真题"], ""),
    ("text", "2024国家能源校招笔试真题及参考答案2.txt", "numbered", "历年真题", "2024校招真题（二）", ["真题"], ""),
    ("text", "2023国家能源集团夏招招聘在线笔试真题及答案解析.txt", "numbered", "历年真题", "2023夏招真题", ["真题"], ""),
    ("text", "2023国家能源集团秋李招聘在线笔试完整真题及答系.txt", "numbered", "历年真题", "2023秋招真题", ["真题"], ""),
    ("text", "2012年国电集团招聘笔试试题及答案.txt", "numbered", "历年真题", "2012国电集团真题", ["真题"], ""),
    ("text", "2025国家能源集团模拟笔试试题和答案解析（一）.txt", "numbered", "模拟笔试", "2025模拟卷（一）", ["模拟考"], ""),
    ("text", "2025国家能源集团模拟笔试试题和答案解析（二）.txt", "numbered", "模拟笔试", "2025模拟卷（二）", ["模拟考"], ""),
    ("text", "2025国家能源集团模拟笔试试题和答案解析（三）.txt", "numbered", "模拟笔试", "2025模拟卷（三）", ["模拟考"], ""),
]

T2 = "【全国时政】全国时政热点（已更4月）"

# 答案集中在文末的文件：numbered（题号块 + 尾部答案区对齐）比 inline 更准
T2_NUMBERED = {
    "各考试中党的二十大相关试题汇总（一）（50题）.txt",
    "各考试中党的二十大相关试题汇总（二）（66题）.txt",
    "各考试中党的二十大相关试题汇总（三）（130题）.txt",
}
SOURCES_T2 = [
    (f"{T2}\\24-26年时政\\2026年时政+试题\\2026年1月时政试题179道.txt", "2026年1月时政（179题）"),
    (f"{T2}\\24-26年时政\\2026年时政+试题\\2026年2月时政试题汇总.txt", "2026年2月时政"),
    (f"{T2}\\24-26年时政\\2026年时政+试题\\2026年3月时政试题汇总.txt", "2026年3月时政"),
    (f"{T2}\\24-26年时政\\2026年时政+试题\\2026年4月时政试题165道.txt", "2026年4月时政（165题）"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\2025年9月时政试题190道.txt", "2025年9月时政（190题）"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\2025年10月时政试题汇总.txt", "2025年10月时政"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\2025年11月时政试题186道汇总.txt", "2025年11月时政（186题）"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\2025年12月时政试题汇总.txt", "2025年12月时政"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\二十大相关资料\\二十大试题（240题）.txt", "党的二十大（240题）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\二十大相关资料\\各考试中党的二十大相关试题汇总（一）（50题）.txt", "党的二十大试题汇总（一）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\二十大相关资料\\各考试中党的二十大相关试题汇总（二）（66题）.txt", "党的二十大试题汇总（二）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\二十大相关资料\\各考试中党的二十大相关试题汇总（三）（130题）.txt", "党的二十大试题汇总（三）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\十五五规划建议考点速记\\（试题）关于《中共中央关于制定国民经济和社会发展第十五个五年规划的建议》的说明（70题）-.txt", "十五五规划建议（70题）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\二十届3中全会\\二十届三中全会（考点+40题）.txt", "二十届三中全会（40题）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\2025年上合组织峰会考点速记\\上合组织试题\\试题44道  习近平在上海合作组织成员国元首理事会第二十五次会议上的讲话.txt", "上合组织峰会（44题）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\2025年上合组织峰会考点速记\\上合组织试题\\试题53道  习近平在“上海合作组织+”会议上的讲话.txt", "上合组织+会议（53题）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\中央经济工作会议时政\\中央经济工作会议（考点+划重点+32题）.txt", "中央经济工作会议（32题）"),
    # ---- 2024 年各月时政（逐月题库；1、2 月原文件无任何答案标记，
    #      11 月为双栏 PDF 错行文本，均已剔除，见下方说明） ----
    (f"{T2}\\24-26年时政\\2024年时政热点+试题\\24年12月\\24年1月-24年12月时政要问及1950题及答案（24年12月更新完）.txt", "2024年全年时政（1950题）"),
    # ---- 2025 年各月押题（只取“带答案”版本，避免与不带答案版重复） ----
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\1月押题\\2025年1月时事政治模拟题(带答案).txt", "2025年1月时政"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\2月押题\\2025年2月时事政治模拟题(带答案).txt", "2025年2月时政"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\3月押题\\2025年3月时事政治模拟题(带答案).txt", "2025年3月时政"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\4月押题\\2025年4月时事政治模拟题(带答案).txt", "2025年4月时政"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\5月押题\\2025年5月时事政治模拟题(带答案).txt", "2025年5月时政"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\7月押题\\2025年7月时政183题.txt", "2025年7月时政（183题）"),
    (f"{T2}\\24-26年时政\\2025年每月时政热点配套押题\\8月押题\\2025年8月时政试题173道.txt", "2025年8月时政（173题）"),
    # ---- 重要文件与会议（此前完全未接入） ----
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\2025年中央一号文件\\2025年中央一号文件（全文+划重点+58题）.txt", "2025年中央一号文件（58题）"),
    (f"{T2}\\【重要会议】2025重要时政+文章考点\\2026年\\试题21道  2026.2.27中央政治局会议.txt", "2026年2月27日中央政治局会议（21题）"),
]


def build():
    os.makedirs(OUT, exist_ok=True)
    all_q = []
    report = []
    seq = 0
    jobs = [(os.path.join(WORK, base), f, mode, cat, ch, tags, af)
            for base, f, mode, cat, ch, tags, af in SOURCES]
    for f, ch in SOURCES_T2:
        # 时政题库普遍为“题干/选项/参考答案”就近排版，inline 解析器对齐更可靠；
        # 但少数文件的答案集中排在文末，用 numbered 的题号块+答案区对齐更准。
        mode = "numbered" if os.path.basename(f) in T2_NUMBERED else "inline"
        jobs.append((TEXT2, f, mode, "时政", ch, ["时政"], ""))
    for base_name, qf, af, cat, ch, tags, pmode in SOURCES_PAIR:
        # 配对来源自带基目录与解析口径：2026-10-19 新增的 F 目录 14 份放在 work/text7
        jobs.append((os.path.join(WORK, base_name), qf, pmode, cat, ch, tags, af))
    for f, cat, ch, tags in discover_ocr_sources():
        mode = "ocr"
        for key, m in OCR_MODE_OVERRIDE.items():
            if key in f:
                mode = m
                break
        jobs.append((OCR_DIR, f, mode, cat, ch, tags, ""))

    for base, fname, mode, category, chapter, tags, ansfile in jobs:
        p = os.path.join(base, fname)
        if not os.path.exists(p):
            report.append({"source": fname, "status": "missing-file"})
            continue
        try:
            raw = open(p, encoding="utf-8", errors="replace").read()
            lines = expand_inline_options(clean_lines(raw))
            if mode == "pair":
                qs = parse_pair(p, os.path.join(base, ansfile), {})
            elif mode == "pair_strict":
                # 材料表格会污染题号行，须用严格判据（见 question_starts_strict）
                qs = parse_pair_strict(p, os.path.join(base, ansfile), {},
                                       label=os.path.basename(p))
            elif mode == "ocr":
                qs = parse_ocr_choice(ocr_lines(raw), {})
                if not qs:
                    # 备用路径：选项同行排列 + 卷末（分段）紧凑答案串
                    exp = expand_inline_options(
                        [(normalize_bare_option_letters(t), p) for t, p in ocr_lines(raw)])
                    qs = parse_ocr_sectioned(exp, {})
                    if qs:
                        mode = "ocr_sect"
                    else:
                        inj = inject_compact_answer_keys(exp)
                        if len(inj) != len(exp):
                            qs = parse_numbered(inj, {})
                            if qs:
                                mode = "ocr_keyed"
            elif mode == "inline":
                qs = parse_inline_answer(lines, {})
            elif mode == "unnumbered":
                qs = parse_unnumbered(lines, {})
            else:
                qs = parse_numbered(lines, {})
        except Exception as exc:
            import traceback
            report.append({"source": fname, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
            print(f"ERROR {fname}: {exc}")
            traceback.print_exc()
            continue
        kept = 0
        for q in qs:
            seq += 1
            q.update({
                "id": f"q{seq:05d}",
                "sourceFile": fname,
                "category": category,
                "chapter": chapter,
                "knowledgePoints": [chapter],
                "difficulty": "medium",
                "tags": tags,
                "passageId": None,
                "assets": [],
                "enabled": True,
            })
            all_q.append(q)
            kept += 1
        tc = Counter(q["answerStatus"] for q in qs)
        report.append({
            "source": fname, "mode": mode, "parsed": len(qs), "kept": kept,
            "verified": tc.get("verified", 0), "needs_review": tc.get("needs_review", 0),
            "missing": tc.get("missing", 0), "status": "ok",
        })
        print(f"{os.path.basename(fname)[:52]:54s} {mode:10s} n={len(qs):5d} "
              f"ok={tc.get('verified',0):5d} review={tc.get('needs_review',0):4d} "
              f"missing={tc.get('missing',0):4d}")

    with open(os.path.join(OUT, "questions.json"), "w", encoding="utf-8") as fh:
        json.dump({"schemaVersion": 1, "generatedAt": "2026-10-18",
                   "questions": all_q}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "parse_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    tc = Counter(q["answerStatus"] for q in all_q)
    print(f"\nTOTAL = {len(all_q)}  {dict(tc)}")

    # 失败/缺文件的来源必须在最后**醒目列出**，否则很容易被“TOTAL 看着还行”掩盖
    bad = [r for r in report if r.get("status") != "ok"]
    if bad:
        print(f"\n!!! 有 {len(bad)} 个来源未能解析（这些资料的内容没有进入题库）：")
        for r in bad:
            print(f"    [{r.get('status')}] {r.get('source')}  {r.get('error', '')}")
        print("!!! 请修正后重新构建；构建脚本以非零退出码结束。")
    return len(bad)


if __name__ == "__main__":
    sys.exit(build())
