"""检查重复文本行，另存按首次出现顺序去重的文本。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

TOOL_NAME = "LineWinnow"
VERSION = "0.1.1"


def analyze_file(filename, trim_edges=False, ignore_case=False, encoding="utf-8-sig"):
    source = Path(filename).expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("请选择文本文件。")
    # 只把 CRLF、CR、LF 视为换行；不把其他 Unicode 字符拆成新行。
    with source.open("r", encoding=encoding, errors="strict", newline=None) as stream:
        text = stream.read()
    if "\x00" in text:
        raise ValueError("文件含有空字符，请选择普通文本文件并检查编码。")
    lines = text.split("\n") if text else []
    final_newline = text.endswith("\n")
    if final_newline:
        lines.pop()
    groups = {}
    kept = []
    for number, line in enumerate(lines, 1):
        key = line.strip() if trim_edges else line
        if ignore_case:
            key = key.casefold()
        if key not in groups:
            groups[key] = {"comparison_text": key, "first_text": line, "line_numbers": []}
            kept.append(line)
        groups[key]["line_numbers"].append(number)
    duplicates = [dict(row, count=len(row["line_numbers"]))
                  for row in groups.values() if len(row["line_numbers"]) > 1]
    report = {
        "tool": TOOL_NAME, "version": VERSION, "source": str(source),
        "encoding": encoding, "trim_edges": trim_edges, "ignore_case": ignore_case,
        "total_lines": len(lines), "unique_lines": len(kept),
        "duplicate_groups": len(duplicates), "removable_lines": len(lines) - len(kept),
        "groups": duplicates,
    }
    # 比较时的选项不改变保留下来的原文，只统一导出的换行格式。
    cleaned = "\n".join(kept) + ("\n" if final_newline and kept else "")
    return report, cleaned


def save_new_file(filename, content):
    """仅创建新文件，拒绝覆盖原文件或已有报告。"""
    with Path(filename).expanduser().open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def format_report(report):
    lines = [f"{TOOL_NAME} {VERSION}", f"文件：{report['source']}",
             f"总行数：{report['total_lines']}；保留行数：{report['unique_lines']}",
             f"重复组：{report['duplicate_groups']}；可去除重复行：{report['removable_lines']}",
             f"忽略行首尾空白：{'是' if report['trim_edges'] else '否'}；忽略大小写：{'是' if report['ignore_case'] else '否'}", ""]
    for row in report["groups"]:
        # 引号显示空行、制表符和首尾空格，避免误读。
        lines += [f"出现 {row['count']} 次，行号：{', '.join(map(str, row['line_numbers']))}",
                  f"比较内容：{json.dumps(row['comparison_text'], ensure_ascii=False)}", ""]
    if not report["groups"]:
        lines.append("按当前规则没有重复行。")
    return "\n".join(lines)


def create_app(root):
    import tkinter as tk
    from tkinter import ttk
    from tool_window import ToolWindow

    app = ToolWindow(root, TOOL_NAME, "检查重复行，另存去重后的文本", directory=False,
                     description="保留每组第一次出现的原文和顺序；保存时需选择一个尚不存在的新文件。")
    trim = tk.BooleanVar(value=False)
    fold = tk.BooleanVar(value=False)
    encoding = tk.StringVar(value="utf-8-sig")
    ttk.Checkbutton(app.options, text="忽略行首尾空白", variable=trim).pack(side="left", padx=(0, 14))
    ttk.Checkbutton(app.options, text="忽略大小写", variable=fold).pack(side="left", padx=(0, 14))
    ttk.Label(app.options, text="编码：").pack(side="left")
    ttk.Combobox(app.options, textvariable=encoding, values=("utf-8-sig", "gb18030", "utf-16"),
                 state="readonly", width=13).pack(side="left")
    app.prepare = lambda: (app.path.get(), trim.get(), fold.get(), encoding.get())
    app.analyze = analyze_file
    app.render = format_report
    app.save_new = save_new_file
    app.enable_cleaned()
    app.trim_edges = trim
    app.ignore_case = fold
    app.encoding = encoding
    return app


def launch_gui():
    import tkinter as tk
    root = tk.Tk()
    create_app(root)
    root.mainloop()


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME}：检查重复行，按首次出现顺序另存去重文本。")
    parser.add_argument("file", nargs="?", help="要检查的文本文件")
    parser.add_argument("--linewinnow-trim-edges", action="store_true", help="比较时忽略行首尾空白，保留的原文不变")
    parser.add_argument("--ignore-case", action="store_true", help="比较时忽略大小写（Unicode casefold）")
    parser.add_argument("--encoding", default="utf-8-sig", help="输入编码，默认 utf-8-sig；可用 gb18030 或 utf-16")
    parser.add_argument("--output", help="将去重文本另存到尚不存在的新文件，UTF-8 编码")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    parser.add_argument("--gui", action="store_true", help="打开窗口")
    parser.add_argument("--version", action="version", version=f"{TOOL_NAME} {VERSION}")
    args = parser.parse_args(argv)
    if args.gui:
        launch_gui()
        return 0
    if not args.file:
        parser.error("请提供文本路径，或使用 --gui。")
    try:
        report, cleaned = analyze_file(args.file, args.linewinnow_trim_edges, args.ignore_case, args.encoding)
        if args.output:
            save_new_file(args.output, cleaned)
            report["output"] = str(Path(args.output).expanduser().resolve())
    except (OSError, ValueError, LookupError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and not stream.isatty():
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
