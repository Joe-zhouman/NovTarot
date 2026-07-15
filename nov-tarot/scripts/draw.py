#!/usr/bin/env python3
"""塔罗抽牌脚本。

按牌阵结构随机抽取塔罗牌,每张牌带正逆位。用于用户没有实体牌时由 agent 代抽。

用法:
  draw.py --spread time-flow                # 时间流:3 张随机
  draw.py --spread celtic                   # 凯尔特十字:10 张随机
  draw.py --spread four-seasons             # 四季:1 大阿卡纳 + 四花色各一
  draw.py --spread time-flow --no-reversals # 全正位
  draw.py --spread time-flow --seed 42      # 既定命运:第一轮用 42,之后每轮由上一轮的牌派生(种子链)
  draw.py --spread time-flow --format pretty

stdout 只放抽牌结果(json 或 pretty)。错误以结构化 envelope 输出到 stderr。
"""
import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path

# 牌池:优先 assets/card-data.json(相对脚本位置的 ../assets/)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DECK = SCRIPT_DIR.parent / "assets" / "card-data.json"

# 牌阵结构定义:每种牌阵抽多少张、按什么结构抽
SPREADS = {
    "time-flow": {
        "count": 3,
        "structure": "random",  # 3 张全随机
        "labels": ["过去/根基", "现在/状态", "未来/趋势"],
    },
    "celtic": {
        "count": 10,
        "structure": "random",  # 10 张全随机
        "labels": ["状况", "障碍", "潜意识", "近因", "显意识",
                   "近期未来", "立场", "环境", "希望与恐惧", "结局"],
    },
    "four-seasons": {
        "count": 5,
        "structure": "fixed-suits",  # 1 大阿卡纳 + 四花色各一
        "labels": ["大阿卡纳(整季主题)", "权杖(行动力)", "圣杯(情感)",
                   "宝剑(思维)", "星币(物质)"],
        "suits_order": ["major", "wands", "cups", "swords", "pentacles"],
    },
    "single": {
        "count": 1,
        "structure": "major-from-pile",  # 抽10张沓找第一张大阿卡纳
        "labels": ["大阿卡纳(单牌回答)"],
    },
    "relationship": {
        "count": 7,
        "structure": "random",  # 7 张全随机,分组语义(自己/对方/关系)在 spread 文件
        "labels": ["你自己·现状", "你自己·期待", "你自己·行为",
                   "对方·现状", "对方·期待", "对方·行为",
                   "关系的核心"],
    },
    "zodiac": {
        "count": 12,
        "structure": "random",  # 12 张全随机,逐张揭示,每张对应一个宫位
        "labels": ["1宫·自我形象", "2宫·财富资源", "3宫·沟通近邻",
                   "4宫·家庭根基", "5宫·恋爱创造", "6宫·工作健康",
                   "7宫·伴侣关系", "8宫·蜕变共有", "9宫·哲学远行",
                   "10宫·事业声望", "11宫·朋友理想", "12宫·潜意识隐秘"],
    },
    "mind-body-spirit": {
        "count": 3,
        "structure": "random",  # 3 张全随机,一起揭示
        "labels": ["身·身体与物质层面", "心·思维与情绪", "灵·灵性与潜意识"],
    },
    "choice": {
        "count": 5,
        "structure": "random",  # 5 张全随机,分组语义(A路/B路/建议)在 spread 文件
        "labels": ["A 路·现状", "A 路·结果",
                   "B 路·现状", "B 路·结果",
                   "建议"],
    },
}


def emit_error(err_type, subtype, param, message, hint):
    """结构化错误 envelope 到 stderr。"""
    envelope = {
        "type": err_type,
        "subtype": subtype,
        "param": param,
        "message": message,
        "hint": hint,
    }
    sys.stderr.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    sys.exit(1)


def load_deck(deck_path):
    """加载牌池。"""
    if not deck_path.is_file():
        emit_error("io_error", "file_not_found", "--deck",
                   f"牌池文件不存在: {deck_path}",
                   f"确认 assets/card-data.json 存在;或用 --deck 指定其他路径")
    try:
        with open(deck_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        emit_error("io_error", "parse_error", "--deck",
                   f"牌池 JSON 解析失败: {e}",
                   f"检查 {deck_path} 是否为合法 JSON")
    cards = data.get("cards", [])
    if len(cards) != 78:
        emit_error("data_error", "invalid_deck", "--deck",
                   f"牌池应有 78 张,实际 {len(cards)} 张",
                   "重新生成 assets/card-data.json")
    return cards


def derive_next_seed(prev_seed, prev_card_refs):
    """种子链:由上一轮的种子 + 上一轮抽到的牌,派生这一轮的种子。

    命运是一条因果链——前一轮翻出的牌,种下下一轮的因。初始种子(用户给的命运之种)
    锁定整局基调;每一轮的牌把命运往前推一步。同初始种子 + 同流程 → 同一条链,整局可复现;
    而每轮牌不同 → 每轮种子自然不同(修复"全程同种子多轮复现同一组牌"的 bug)。

    prev_seed: 上一轮的有效种子(第一轮传用户给的 base_seed)。
    prev_card_refs: 上一轮抽到的牌的 ref 列表(第一轮传空列表)。
    返回 32 位无符号整数。
    """
    material = f"{prev_seed}|{' '.join(prev_card_refs)}"
    h = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big")


def prev_turn_from_file(prev_path):
    """从 --prev 指向的文件读"上一轮"的牌 ref + 有效种子,用于推进种子链。

    调用链强制落盘:从第二轮起,agent 必须把上一轮的落盘文件传进 --prev,
    draw.py 才能派生这一轮的种子。不落盘就没法抽下一轮——物理上消灭"攒到收尾才写"。

    接受三种文件形态(都从中取出"最后一轮的牌"):
      - session.json(log-turn 落盘的会话文件):取 turns 里 max-turn 的 cards + effective_seed
      - 单轮 draw 输出({spread, cards, effective_seed}):取 cards + effective_seed
      - 牌数组([{ref,...}]):直接用

    返回 (prev_card_refs, prev_seed)。prev_seed 为 None 时,调用方回退用 base_seed。
    """
    p = Path(prev_path)
    if not p.is_file():
        emit_error("io_error", "file_not_found", "--prev",
                   f"上一轮落盘文件不存在: {p}",
                   "先把上一轮抽到的牌用 log-turn.py 落盘,再把落盘文件路径传给 --prev")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        emit_error("io_error", "parse_error", "--prev",
                   f"上一轮落盘文件 JSON 解析失败: {e}",
                   f"检查 {p} 是否合法(应是 log-turn 的 session.json 或 draw 的输出)")
    # 形态1:session.json(有 turns 数组)→ 取最后一轮
    if isinstance(data, dict) and isinstance(data.get("turns"), list) and data["turns"]:
        nums = [t for t in data["turns"]
                if isinstance(t, dict) and isinstance(t.get("turn"), int)]
        if not nums:
            emit_error("data_error", "invalid_prev", "--prev",
                       f"{p} 的 turns 里没有有效的轮次记录",
                       "确认 session.json 是 log-turn.py 正确落盘的")
        last = max(nums, key=lambda t: t["turn"])
        cards = last.get("cards") or []
        refs = [c.get("ref") for c in cards if isinstance(c, dict) and c.get("ref")]
        return refs, last.get("effective_seed")
    # 形态2:单轮 draw 输出({cards: [...]})
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        refs = [c.get("ref") for c in data["cards"] if isinstance(c, dict) and c.get("ref")]
        return refs, data.get("effective_seed")
    # 形态3:牌数组
    if isinstance(data, list):
        refs = [c.get("ref") for c in data if isinstance(c, dict) and c.get("ref")]
        return refs, None
    emit_error("data_error", "invalid_prev", "--prev",
               f"{p} 无法识别(应是 session.json / draw 输出 / 牌数组)",
               "传 log-turn.py 的 session.json 或 draw.py 的输出")
    return [], None  # 不会到这


def draw_major_from_pile(cards, rng, pile_size=10):
    """大阿卡纳抽取的传统沓法:从整副牌抽 pile_size 张,依次揭示,
    第一张大阿卡纳为答案。若无大阿卡纳,返回 None(留空,agent 裁决命运之轮/世界)。
    返回 (命中牌或None, 10张沓过程)。
    """
    pile = rng.sample(cards, pile_size)
    for c in pile:
        if c["suit"] == "major":
            return c, pile
    return None, pile


def draw_for_spread(cards, spread_key, rng):
    """按牌阵结构抽牌。返回有序的牌列表(已含正逆位)。
    大阿卡纳位用沓法(major-from-pile):抽10张找第一张大阿卡纳,无则留空。
    """
    spread = SPREADS[spread_key]
    structure = spread["structure"]

    # 记录沓法过程(若有),供输出展示
    pile_info = []  # 每个用沓法的位置的 (位置标签, 沓, 命中)

    if structure == "random":
        drawn = rng.sample(cards, spread["count"])
    elif structure == "fixed-suits":
        drawn = []
        for suit in spread["suits_order"]:
            if suit == "major":
                # 大阿卡纳用沓法
                hit, pile = draw_major_from_pile(cards, rng)
                drawn.append(hit)  # 可能 None(留空)
                pile_info.append((suit, pile, hit))
            else:
                pool = [c for c in cards if c["suit"] == suit]
                drawn.append(rng.choice(pool))
    elif structure == "major-from-pile":
        # 整个牌阵就是抽一张大阿卡纳(single)
        hit, pile = draw_major_from_pile(cards, rng)
        drawn = [hit]
        pile_info.append(("major", pile, hit))
    else:
        emit_error("internal_error", "unknown_structure", None,
                   f"未知抽牌结构: {structure}", "这是脚本 bug,请报告")
        return

    # 给每张牌加正逆位 + 位置标签(留空的位特殊处理)
    labels = spread["labels"]
    result = []
    for i, card in enumerate(drawn):
        orientation = "逆位" if rng.random() < 0.5 else "正位"
        if card is None:
            # 大阿卡纳留空:命运未给出明确回应,agent 裁决逆位命运之轮/世界
            result.append({
                "position": i + 1,
                "label": labels[i] if i < len(labels) else f"第{i+1}张",
                "ref": None,
                "en": None,
                "cn": "（留空·命运未明示）",
                "suit": "major",
                "orientation": None,
                "empty_major": True,
                "hint": "10 张沓中无大阿卡纳。视为逆位命运之轮(命运转动受阻)或逆位世界(未圆满),由 agent 判断哪个更像这次命运主题。",
            })
        else:
            result.append({
                "position": i + 1,
                "label": labels[i] if i < len(labels) else f"第{i+1}张",
                "ref": card["ref"],
                "en": card["en"],
                "cn": card["cn"],
                "suit": card["suit"],
                "orientation": orientation,
            })
    return result, pile_info


def apply_no_reversals(drawn):
    """关闭逆位:全部改成正位。"""
    for card in drawn:
        card["orientation"] = "正位"
    return drawn


def attach_meanings(drawn, deck):
    """给每张牌附带牌意 md(读 references/cards/<deck>/<ref>.md)。缺文件的牌 meaning 留 None。"""
    cards_root = SCRIPT_DIR.parent / "references" / "cards" / deck
    for c in drawn:
        md_path = cards_root / f"{c['ref']}.md"
        c["meaning"] = md_path.read_text(encoding="utf-8") if md_path.is_file() else None
    return drawn


def format_json(drawn, spread_key, pile_info=None, effective_seed=None):
    out = {
        "spread": spread_key,
        "structure": SPREADS[spread_key]["structure"],
        "count": len(drawn),
        "effective_seed": effective_seed,  # 本轮有效种子(种子链);落盘进 session 供复现
        "cards": drawn,
    }
    if pile_info:
        out["major_piles"] = [
            {
                "position_label": "大阿卡纳位" if s == "major" else s,
                "pile": [{"cn": c["cn"], "en": c["en"], "suit": c["suit"]} for c in pile],
                "hit": ({"cn": hit["cn"], "en": hit["en"]} if hit else None),
            }
            for s, pile, hit in pile_info
        ]
    return json.dumps(out, ensure_ascii=False, indent=2)


def format_pretty(drawn, spread_key, pile_info=None, effective_seed=None):
    spread_name = {
        "time-flow": "时间流牌阵(3 张)",
        "celtic": "凯尔特十字阵(10 张)",
        "four-seasons": "四季牌阵(5 张)",
        "single": "单张大阿卡纳(沓法:抽10张找首张大阿卡纳)",
        "relationship": "关系牌阵(7 张)",
        "zodiac": "黄道十二宫(12 张)",
        "mind-body-spirit": "身心灵(3 张)",
        "choice": "选择牌阵(5 张)",
    }.get(spread_key, spread_key)
    has_meaning = any(c.get("meaning") for c in drawn)
    lines = [f"=== {spread_name} ==="]
    if effective_seed is not None:
        # 内部信息:供落盘/复现用,不要念给用户
        lines.append(f"[internal · 本轮种子 {effective_seed},落盘进 session 供复现]")

    # 展示大阿卡纳沓法过程(若有)
    if pile_info:
        for _suit, pile, hit in pile_info:
            lines.append("")
            lines.append("〔大阿卡纳·沓法揭示〕依次翻开 10 张,第一张大阿卡纳为答案:")
            seq = []
            for c in pile:
                mark = " ◀ 命中" if (hit and c["ref"] == hit["ref"]) else ""
                seq.append(f"{c['cn']}({c['suit'][:3]}){mark}")
                if hit and c["ref"] == hit["ref"]:
                    break
            lines.append("  " + " → ".join(seq))
            if not hit:
                lines.append("  ⚠ 10 张中无大阿卡纳 → 留空,视为逆位命运之轮或逆位世界(agent 裁决)")

    lines.append("")
    for c in drawn:
        orient = c.get("orientation") or "—"
        en = c.get("en") or ""
        lines.append(f"{c['position']:>2}. [{c['label']}] {c['cn']}({en}) — {orient}")
        if c.get("empty_major"):
            lines.append(f"    {c.get('hint','')}")
        if has_meaning and c.get("meaning"):
            lines.append("")
            lines.append(c["meaning"])
            lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="塔罗抽牌脚本。按牌阵结构随机抽牌,带正逆位。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--spread", required=True,
                        choices=list(SPREADS.keys()),
                        help="牌阵类型:time-flow(3张)/celtic(10张)/four-seasons(5张固定结构)")
    parser.add_argument("--no-reversals", action="store_true",
                        help="关闭逆位,全部正位")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子(既定命运 / 命运之种)。第一轮用本值;之后每轮的有效种子由上一轮的牌派生(种子链),整局可复现、每轮自然不同")
    parser.add_argument("--turn", type=int, default=None,
                        help="当前轮次号(1=首轮)。≥2 时强制要求 --prev,强制每轮抽完即落盘;不传则按 --prev 有无判定轮次")
    parser.add_argument("--prev", default=None,
                        help="上一轮的落盘文件(session.json 或 draw 输出)。第二轮起必传——draw.py 从中读上一轮的牌派生种子,也借此强制落盘")
    parser.add_argument("--deck", default=str(DEFAULT_DECK),
                        help=f"牌池 JSON 路径(默认 {DEFAULT_DECK})")
    parser.add_argument("--system", default="waite",
                        help="塔罗体系(牌意目录名,当前 waite)。带牌意时用")
    parser.add_argument("--no-meanings", action="store_true",
                        help="不带牌意(默认带,方便直接解读)。关掉后只输出抽到的牌")
    parser.add_argument("--format", choices=["json", "pretty"], default=None,
                        help="输出格式。默认:TTY 用 pretty,管道用 json")
    args = parser.parse_args()

    # 确定输出格式:显式指定优先,否则按 TTY 自动选择
    if args.format is None:
        fmt = "pretty" if sys.stdout.isatty() else "json"
    else:
        fmt = args.format

    cards = load_deck(Path(args.deck))

    # 种子链:既定命运(args.seed)是整局的命运之种。
    # 第一轮(--prev 缺失 / --turn 1)直接用 base_seed;之后每轮的种子由
    # 「上一轮的种子 + 上一轮抽到的牌」派生——前一轮的牌种下下一轮的因,命运成因果链。
    # 调用链强制落盘:--turn ≥2 时 --prev 必传,不落盘就没法抽下一轮——物理上消灭"攒到收尾才写"。
    # 完全混沌(不传 seed):真随机,不进链。
    if args.turn is not None and args.turn >= 2 and args.prev is None:
        emit_error("validation_error", "missing_prev", "--prev",
                   f"第 {args.turn} 轮抽牌必须带 --prev(上一轮的落盘文件)",
                   "先把上一轮抽到的牌用 log-turn.py 落盘,再把 session.json 路径传给 --prev")

    if args.seed is None:
        effective_seed = None  # 完全混沌
    elif args.prev is None:
        effective_seed = args.seed  # 第一轮:命运之种本身
    else:
        prev_refs, prev_seed = prev_turn_from_file(args.prev)
        if not prev_refs:
            # --prev 给了但取不到牌:文件异常,报错(不要静默退回第一轮)
            emit_error("data_error", "empty_prev", "--prev",
                       f"{args.prev} 里读不到上一轮的牌",
                       "确认传的是上一轮真正落盘的文件;若这是第一轮,不要传 --prev")
        base = prev_seed if prev_seed is not None else args.seed
        effective_seed = derive_next_seed(base, prev_refs)

    rng = random.Random(effective_seed)
    drawn, pile_info = draw_for_spread(cards, args.spread, rng)

    if args.no_reversals:
        drawn = apply_no_reversals(drawn)

    if not args.no_meanings:
        drawn = attach_meanings(drawn, args.system)

    if fmt == "json":
        sys.stdout.write(format_json(drawn, args.spread, pile_info, effective_seed) + "\n")
    else:
        sys.stdout.write(format_pretty(drawn, args.spread, pile_info, effective_seed) + "\n")


if __name__ == "__main__":
    main()
