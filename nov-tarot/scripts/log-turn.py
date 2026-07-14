#!/usr/bin/env python3
"""记录一轮塔罗解牌到会话工作文件。

每轮解牌后由主 agent 调用,把该轮的问题、牌阵、抽到的牌、解读摘要追加到
.nov-tarot/session.json。点开头目录用户不易察觉。收尾时报告 subagent 读这个
文件生成最终报告。

工作文件结构:
{
  "started": "ISO时间(首次创建时写)",
  "turns": [
    {
      "turn": 1,
      "question": "...",
      "spread": "time-flow",
      "reveal_mode": "holistic",
      "cards": [ {position,label,ref,en,cn,orientation}, ... ],
      "summary": "agent 写的该轮解读摘要",
      "logged_at": "ISO时间"
    }, ...
  ]
}

用法:
  log-turn.py --turn 1 --question "..." --spread time-flow \\
              --cards-file /tmp/draw.json --summary "..."
  log-turn.py --turn 2 --question "选A好不好" --spread single \\
              --cards-json '[...]' --summary "..." --reveal-mode grouped

stdout 只放确认信息(json)。错误以结构化 envelope 输出到 stderr。
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_SESSION_DIR = Path(".nov-tarot")
SESSION_FILE = "session.json"


def emit_error(err_type, subtype, param, message, hint):
    envelope = {
        "type": err_type, "subtype": subtype, "param": param,
        "message": message, "hint": hint,
    }
    sys.stderr.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    sys.exit(1)


def load_session(path):
    """加载已有会话文件,不存在则返回空骨架。"""
    if not path.is_file():
        return {"started": None, "turns": []}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        emit_error("io_error", "parse_error", str(path),
                   f"会话文件 JSON 解析失败: {e}",
                   f"检查 {path} 是否合法,或删除它重新开始")


def save_session(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_cards(args):
    """从 --cards-file 或 --cards-json 解析牌列表。"""
    if args.cards_file:
        p = Path(args.cards_file)
        if not p.is_file():
            emit_error("io_error", "file_not_found", "--cards-file",
                       f"牌文件不存在: {p}",
                       "先运行 draw.py 并把输出存到文件,再传进来")
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            emit_error("io_error", "parse_error", "--cards-file",
                       f"牌文件 JSON 解析失败: {e}", "")
        # draw.py 的输出是 {spread, cards:[...]},取 cards
        if isinstance(data, dict) and "cards" in data:
            return data["cards"]
        if isinstance(data, list):
            return data
        emit_error("data_error", "invalid_cards", "--cards-file",
                   "牌文件格式无法识别(需要 draw.py 的输出或牌数组)",
                   "用 draw.py --format json 的输出")
    elif args.cards_json:
        try:
            data = json.loads(args.cards_json)
        except json.JSONDecodeError as e:
            emit_error("data_error", "parse_error", "--cards-json",
                       f"--cards-json 解析失败: {e}",
                       "传合法的 JSON 数组,或改用 --cards-file")
        if isinstance(data, dict) and "cards" in data:
            return data["cards"]
        if isinstance(data, list):
            return data
        emit_error("data_error", "invalid_cards", "--cards-json",
                   "--cards-json 需为牌数组或 draw.py 输出对象", "")
    else:
        emit_error("validation_error", "missing_argument", "--cards-file/--cards-json",
                   "必须提供 --cards-file 或 --cards-json",
                   "把 draw.py 的输出传进来")
    return []  # 不会到这


def main():
    parser = argparse.ArgumentParser(
        description="记录一轮塔罗解牌到会话工作文件(.nov-tarot/session.json)。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--turn", type=int, required=True, help="轮次号(1, 2, 3...)")
    parser.add_argument("--question", required=True, help="用户该轮问的问题")
    parser.add_argument("--spread", required=True, help="该轮用的牌阵")
    parser.add_argument("--reveal-mode", default=None,
                        help="该轮的揭示模式(holistic/sequential/grouped)")
    parser.add_argument("--summary", required=True, help="该轮解读的摘要(agent 写)")
    parser.add_argument("--cards-file", default=None,
                        help="draw.py 输出的 JSON 文件路径")
    parser.add_argument("--cards-json", default=None,
                        help="draw.py 输出的 JSON 字符串(与 --cards-file 二选一)")
    parser.add_argument("--session-dir", default=str(DEFAULT_SESSION_DIR),
                        help=f"会话文件目录(默认 {DEFAULT_SESSION_DIR})")
    args = parser.parse_args()

    session_path = Path(args.session_dir) / SESSION_FILE
    session = load_session(session_path)

    # 首次创建时写 started
    if session.get("started") is None:
        session["started"] = datetime.now().isoformat(timespec="seconds")

    cards = parse_cards(args)

    turn_record = {
        "turn": args.turn,
        "question": args.question,
        "spread": args.spread,
        "reveal_mode": args.reveal_mode,
        "cards": cards,
        "summary": args.summary,
        "logged_at": datetime.now().isoformat(timespec="seconds"),
    }

    # 替换同轮次记录(允许重写某一轮),否则追加
    turns = session["turns"]
    existing_idx = next((i for i, t in enumerate(turns) if t["turn"] == args.turn), None)
    if existing_idx is not None:
        turns[existing_idx] = turn_record
    else:
        turns.append(turn_record)
    turns.sort(key=lambda t: t["turn"])

    save_session(session_path, session)

    sys.stdout.write(json.dumps({
        "ok": True,
        "session_file": str(session_path),
        "turn": args.turn,
        "total_turns": len(turns),
    }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
