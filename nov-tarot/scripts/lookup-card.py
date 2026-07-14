#!/usr/bin/env python3
"""塔罗牌牌意查询。输入体系 + 牌名(支持多张、模糊匹配),直接把对应牌的牌意
markdown 内容输出到 stdout,进入 agent 上下文。替代"读 card-index 表 + Read 单牌 ref"
的两步流程。

数据源:assets/card-data.json(78 张牌的 ref/en/cn/suit/rank/element/planet/sign)。
牌意文件:references/cards/<deck>/<ref>.md。

用法:
  lookup-card.py --deck waite --card "愚者"                # 单张
  lookup-card.py --deck waite --card "愚者" --card "女皇"   # 多张(重复 --card)
  lookup-card.py --deck waite --cards "愚者,女皇,宝剑七"    # 多张(逗号分隔)
  lookup-card.py --deck waite --card "The Fool"             # 英文各种写法
  lookup-card.py --deck waite --card "fool" --card "wands ace"

匹配:归一化(转小写、去空格/连字符/标点、去 the/王牌 后缀)后比对
en(英文驼峰)/ cn(中文)/ ref(小写连字符)。覆盖各种写法变体。

输出:命中的牌的牌意 md 拼接到 stdout。未命中的在末尾以 hint 说明。
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_DECK_DATA = SKILL_ROOT / "assets" / "card-data.json"
CARDS_DIR = SKILL_ROOT / "references" / "cards"


def emit_error(err_type, message, hint):
    sys.stderr.write(json.dumps({"type": err_type, "message": message, "hint": hint}, ensure_ascii=False) + "\n")
    sys.exit(1)


def normalize(s):
    """归一化牌名用于匹配:转小写、去空格/连字符/标点、去常见冠词和后缀。"""
    s = s.lower().strip()
    # 去标点和分隔符(保留中文字符和字母数字)
    s = re.sub(r'[\s\-_·,\.;:!?\'\"/\\]+', '', s)
    # 去英文冠词 the
    s = re.sub(r'^the', '', s)
    # 去中文常见后缀变体
    s = re.sub(r'(王牌|首牌)$', '', s)
    # 数字牌: ace/1 都归一
    s = re.sub(r'^ace$', '1', s)
    return s


def load_deck(deck_data_path):
    if not deck_data_path.is_file():
        emit_error("io_error", f"牌池文件不存在: {deck_data_path}", "确认 assets/card-data.json 存在")
    try:
        with open(deck_data_path, encoding="utf-8") as f:
            return json.load(f)["cards"]
    except (json.JSONDecodeError, KeyError) as e:
        emit_error("data_error", f"牌池解析失败: {e}", f"检查 {deck_data_path}")


def find_card(query, cards):
    """在 cards 里找归一化匹配 query 的牌。返回 (card, is_exact) 或 None。"""
    q = normalize(query)
    # 建归一化索引:每个候选键都指向同一张牌
    for c in cards:
        keys = [c["ref"], c["en"], c["cn"]]
        # 加变体:中文花色+数字、英文花色大写等
        for k in keys:
            if normalize(k) == q:
                return c, True
    # 模糊:query 是某牌归一化名的子串,或反之(处理 "fool" 匹配 "thefool" 已被 the 去除覆盖)
    candidates = []
    for c in cards:
        for k in [c["ref"], c["en"], c["cn"]]:
            nk = normalize(k)
            if q and (q in nk or nk in q) and len(q) >= 2:
                candidates.append(c)
                break
    # 去重保序
    seen = set()
    uniq = []
    for c in candidates:
        if c["ref"] not in seen:
            seen.add(c["ref"])
            uniq.append(c)
    if len(uniq) == 1:
        return uniq[0], False
    if len(uniq) > 1:
        return {"_ambiguous": True, "candidates": uniq}, False
    return None


def read_card_md(deck, ref):
    md_path = CARDS_DIR / deck / f"{ref}.md"
    if not md_path.is_file():
        return None, md_path
    return md_path.read_text(encoding="utf-8"), md_path


def main():
    ap = argparse.ArgumentParser(description="查询塔罗牌牌意,直接输出牌意 markdown 到 stdout。",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", default="waite", help="塔罗体系(当前支持 waite)")
    ap.add_argument("--card", action="append", default=[], help="牌名(可多次用,中文/英文/ref都行)")
    ap.add_argument("--cards", default=None, help="多张牌名,逗号分隔(替代多次 --card)")
    ap.add_argument("--deck-data", default=str(DEFAULT_DECK_DATA), help=f"牌池 JSON 路径(默认 {DEFAULT_DECK_DATA})")
    args = ap.parse_args()

    # 合并 --card 和 --cards
    queries = list(args.card)
    if args.cards:
        queries.extend([q.strip() for q in args.cards.split(",") if q.strip()])
    if not queries:
        emit_error("usage_error", "未提供牌名", "用 --card \"愚者\" 或 --cards \"愚者,女皇\" 指定要查的牌")

    cards = load_deck(Path(args.deck_data))

    # 检查 deck 目录存在
    deck_dir = CARDS_DIR / args.deck
    if not deck_dir.is_dir():
        emit_error("env_error", f"体系目录不存在: {deck_dir}", f"当前仅支持 waite;{args.deck} 暂未实现")

    out_parts = []
    misses = []
    ambiguous = []
    for q in queries:
        result = find_card(q, cards)
        if result is None:
            misses.append(q)
            continue
        card, exact = result
        if isinstance(card, dict) and card.get("_ambiguous"):
            ambiguous.append((q, card["candidates"]))
            continue
        md, md_path = read_card_md(args.deck, card["ref"])
        if md is None:
            misses.append(f"{q}(牌意文件缺失: {card['ref']}.md)")
            continue
        out_parts.append(f"## {card['cn']}({card['en']}) — {args.deck}\n> 来源: {md_path.relative_to(SKILL_ROOT)}  | 元素:{card['element']} 守护星:{card['planet']} 星座:{card['sign']}\n\n{md}")

    # 输出命中的牌意
    if out_parts:
        sys.stdout.write("\n\n---\n\n".join(out_parts) + "\n")

    # 末尾 hint:未命中或歧义
    hints = []
    for q, cands in ambiguous:
        names = " / ".join(f"{c['cn']}({c['en']},ref={c['ref']})" for c in cands)
        hints.append(f"「{q}」匹配到多张牌,请用更精确的名字: {names}")
    for q in misses:
        # 给近似候选
        near = []
        qn = normalize(q)
        for c in cards:
            for k in [c["ref"], c["en"], c["cn"]]:
                if qn and len(qn) >= 2 and (qn in normalize(k) or normalize(k) in qn):
                    near.append(f"{c['cn']}({c['en']})")
                    break
        near_str = f"。你可能想找: {', '.join(near[:8])}" if near else ""
        hints.append(f"「{q}」未找到对应牌意{near_str}。检查牌名拼写,或用中文牌名(如「愚者」「权杖王牌」「圣杯皇后」)、英文驼峰(如 TheFool)、ref(如 the-fool、wands-ace)")
    if hints:
        hint_block = "\n\n## ⚠ 未匹配 / 歧义\n\n" + "\n\n".join(hints) + "\n"
        sys.stdout.write(hint_block)
        # 同时给 stderr 一个结构化 hint,方便 agent 看到非零时的指导
        sys.stderr.write(json.dumps({
            "type": "partial_miss",
            "matched": len(out_parts),
            "missed": len(misses) + len(ambiguous),
            "hint": "部分牌未匹配,见 stdout 末尾的 ⚠ 段落;调整牌名后重新查询未匹配的那些"
        }, ensure_ascii=False) + "\n")
        if not out_parts:
            sys.exit(1)


if __name__ == "__main__":
    main()
