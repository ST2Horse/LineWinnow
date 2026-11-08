# LineWinnow

检查文本文件中的重复行，显示次数与行号，并可另存按首次出现顺序去重的文本。适合整理网址清单、文献编号、文件名列表或逐行笔记。

版本：0.1.1。需要 Python 3.10 或以上；仅使用标准库，窗口需要 Tkinter。程序在本地运行，不访问网络。

## 双击使用

Windows 下双击 `打开工具.cmd`，选择 `demo/lines.txt`，点击“开始检查”。本机已有运行环境。其他电脑需要先安装包含 Tkinter 的 Python，并使 `python` 命令可用。

- 默认：8 行，2 组重复，去重后保留 6 行。
- 勾选“忽略行首尾空白”：3 组重复，保留 5 行。
- 再勾选“忽略大小写”：3 组重复，保留 4 行。

“另存报告”保存 JSON，包括行号与重复内容。“另存去重文本”输出新的文本文件。必须使用尚不存在的新文件名，不会覆盖输入文件或已有输出。

## 命令行

在本工具目录中运行；路径含空格时加双引号。

```powershell
python linewinnow.py demo/lines.txt
python linewinnow.py demo/lines.txt --linewinnow-trim-edges
python linewinnow.py demo/lines.txt --linewinnow-trim-edges --ignore-case --output cleaned.txt
python linewinnow.py demo/lines.txt --json
python linewinnow.py --gui
```

第三条命令生成 `cleaned.txt`；已有同名文件时会拒绝覆盖，需要换一个新名字。

| 参数 | 作用 |
| --- | --- |
| `file` | 输入文本文件 |
| `--linewinnow-trim-edges` | 比较时忽略每行开头和末尾的空白，默认关闭；保留下来的原文不变 |
| `--ignore-case` | 比较时使用 Unicode casefold 忽略大小写，默认关闭 |
| `--encoding 编码` | 输入编码，默认 `utf-8-sig`，可读取有或没有 BOM 的 UTF-8；其他编码需明确指定 |
| `--output 新路径` | 另存去重文本，保留第一次出现的原文和顺序，拒绝覆盖已有文件 |
| `--json` | 输出 JSON 报告 |
| `--gui` | 打开窗口 |
| `--version` | 显示版本 |

`--linewinnow-trim-edges` 的真实作用：把 `apple` 与 ` apple ` 判为同组，但不会把 `a b` 和 `a  b` 判为同组。忽略的是 Python `str.strip()` 定义的首尾空白，包括空格和制表符。若首次出现的是带空格的那一行，导出的文本仍保留该行的空格。

## 输入输出规则

- 按 CRLF、CR 或 LF 划分行；空行也是一行，会按当前规则参与去重。空文件为 0 行，文件末尾换行不会额外制造一行。
- 默认严格区分大小写和首尾空白，不猜测文本的意思，也不合并近义句。
- 导出的文本使用 UTF-8、无 BOM、LF 换行；是否保留末尾换行取决于输入文件。
- 输入文件不会被修改。导出的去重文本采用本次检查时读取的内容；随后修改输入文件，应重新检查。
- 默认不自动猜测编码。乱码或解码失败时选择正确编码；窗口支持 UTF-8、GB18030、UTF-16，命令行可指定 Python 支持的文本编码。
- 适合普通文本列表。CSV 的引号内换行、Word/PDF、压缩文件不按这些格式解析。
- 全文读入内存，报告也可能包含原文；大文件会占用较多内存。分享报告前检查是否含私人内容。
- 成功退出码为 0；输入、编码、参数或保存失败时为 2。

## 检查程序

```powershell
python -m unittest discover -s tests -v
```

测试使用临时文件，覆盖中文、编码、空行、换行、选项效果、原文保留和拒绝覆盖。
