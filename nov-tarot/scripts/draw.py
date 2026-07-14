#!/usr/bin/env python3
"""塔罗抽牌脚本。

按牌阵结构随机抽取塔罗牌,每张牌带正逆位。用于用户没有实体牌时由 agent 代抽。

用法:
  draw.py --spread time-flow                # 时间流:3 张随机
  draw.py --spread celtic                   # 凯尔特十字:10 张随机
  draw.py --spread four-seasons             # 四季:1 大阿卡纳 + 四花色各一
  draw.py --spread time-flow --no-reversals # 全正位
  draw.py --spread time-flow --seed 42      # 可复现
  draw.py --spread time-flow --format pretty

stdout 只放抽牌结果(json 或 pretty)。错误以结构化 envelope 输出到 stderr。
"""
import argparse
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
        "structure": "fixed-suits",  # 从大阿卡纳抽一张
        "labels": ["大阿卡纳(单牌回答)"],
        "suits_order": ["major"],
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


def draw_for_spread(cards, spread_key, rng):
    """按牌阵结构抽牌。返回有序的牌列表(已含正逆位)。"""
    spread = SPREADS[spread_key]
    structure = spread["structure"]

    if structure == "random":
        # 全随机抽 N 张,不重复
        drawn = rng.sample(cards, spread["count"])
    elif structure == "fixed-suits":
        # 按指定花色顺序,每个花色随机抽一张
        drawn = []
        for suit in spread["suits_order"]:
            pool = [c for c in cards if c["suit"] == suit]
            drawn.append(rng.choice(pool))
    else:
        emit_error("internal_error", "unknown_structure", None,
                   f"未知抽牌结构: {structure}",
                   "这是脚本 bug,请报告")
        return  # 不会到这

    # 给每张牌加正逆位 + 位置标签
    labels = spread["labels"]
    result = []
    for i, card in enumerate(drawn):
        orientation = "逆位" if rng.random() < 0.5 else "正位"
        result.append({
            "position": i + 1,
            "label": labels[i] if i < len(labels) else f"第{i+1}张",
            "ref": card["ref"],
            "en": card["en"],
            "cn": card["cn"],
            "suit": card["suit"],
            "orientation": orientation,
        })
    return result


def apply_no_reversals(drawn):
    """关闭逆位:全部改成正位。"""
    for card in drawn:
        card["orientation"] = "正位"
    return drawn


def format_json(drawn, spread_key):
    return json.dumps({
        "spread": spread_key,
        "structure": SPREADS[spread_key]["structure"],
        "count": len(drawn),
        "cards": drawn,
    }, ensure_ascii=False, indent=2)


def format_pretty(drawn, spread_key):
    spread_name = {
        "time-flow": "时间流牌阵(3 张)",
        "celtic": "凯尔特十字阵(10 张)",
        "four-seasons": "四季牌阵(5 张)",
    }.get(spread_key, spread_key)
    lines = [f"=== {spread_name} ==="]
    for c in drawn:
        lines.append(f"{c['position']:>2}. [{c['label']}] {c['cn']}({c['en']}) — {c['orientation']}")
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
                        help="随机种子,用于复现同一局抽牌")
    parser.add_argument("--deck", default=str(DEFAULT_DECK),
                        help=f"牌池 JSON 路径(默认 {DEFAULT_DECK})")
    parser.add_argument("--format", choices=["json", "pretty"], default=None,
                        help="输出格式。默认:TTY 用 pretty,管道用 json")
    args = parser.parse_args()

    # 确定输出格式:显式指定优先,否则按 TTY 自动选择
    if args.format is None:
        fmt = "pretty" if sys.stdout.isatty() else "json"
    else:
        fmt = args.format

    cards = load_deck(Path(args.deck))
    rng = random.Random(args.seed)  # None → 真随机
    drawn = draw_for_spread(cards, args.spread, rng)

    if args.no_reversals:
        drawn = apply_no_reversals(drawn)

    if fmt == "json":
        sys.stdout.write(format_json(drawn, args.spread) + "\n")
    else:
        sys.stdout.write(format_pretty(drawn, args.spread) + "\n")


if __name__ == "__main__":
    main()
