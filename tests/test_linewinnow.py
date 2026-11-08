"""用临时文件检查真实去重行为和原文件保护。"""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import linewinnow


class LineWinnowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "中文 空格.txt"

    def test_exact_and_trim_preserve_first_text_and_original(self):
        raw = "  苹果  \r\n苹果\r\n  苹果  \r\n香蕉\r\n".encode("utf-8-sig")
        self.source.write_bytes(raw)
        before = self.source.stat().st_mtime_ns
        report, cleaned = linewinnow.analyze_file(self.source)
        self.assertEqual((report["total_lines"], report["unique_lines"], report["removable_lines"]), (4, 3, 1))
        self.assertEqual(report["groups"][0]["line_numbers"], [1, 3])
        report, cleaned = linewinnow.analyze_file(self.source, trim_edges=True)
        self.assertEqual(report["groups"][0]["line_numbers"], [1, 2, 3])
        self.assertEqual(cleaned, "  苹果  \n香蕉\n")
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertEqual(self.source.stat().st_mtime_ns, before)

    def test_casefold_and_internal_spaces(self):
        self.source.write_text("Straße\nSTRASSE\nA B\nA  B", encoding="utf-8")
        report, cleaned = linewinnow.analyze_file(self.source, trim_edges=True, ignore_case=True)
        self.assertEqual(report["removable_lines"], 1)
        self.assertEqual(cleaned, "Straße\nA B\nA  B")

    def test_empty_and_blank_and_newlines(self):
        cases = [(b"", 0, ""), (b"\n", 1, "\n"), (b"\n\n", 2, "\n"),
                 (b"a\ra\r", 2, "a\n"), (b"a\r\nb", 2, "a\nb")]
        for raw, count, expected in cases:
            with self.subTest(raw=raw):
                self.source.write_bytes(raw)
                report, cleaned = linewinnow.analyze_file(self.source)
                self.assertEqual(report["total_lines"], count)
                self.assertEqual(cleaned, expected)
        self.source.write_text("a\u2028b\na\u2028b", encoding="utf-8")
        report, _ = linewinnow.analyze_file(self.source)
        self.assertEqual(report["total_lines"], 2)

    def test_encoding_and_invalid_inputs(self):
        self.source.write_bytes("中文\n中文".encode("gb18030"))
        with self.assertRaises(UnicodeDecodeError):
            linewinnow.analyze_file(self.source)
        report, _ = linewinnow.analyze_file(self.source, encoding="gb18030")
        self.assertEqual(report["removable_lines"], 1)
        self.source.write_bytes(b"a\x00b")
        with self.assertRaises(ValueError):
            linewinnow.analyze_file(self.source)
        with self.assertRaises(FileNotFoundError):
            linewinnow.analyze_file(self.root / "missing.txt")
        with self.assertRaises(ValueError):
            linewinnow.analyze_file(self.root)

    def test_export_never_overwrites_existing_files(self):
        self.source.write_text("a\na\n", encoding="utf-8")
        _, cleaned = linewinnow.analyze_file(self.source)
        with self.assertRaises(FileExistsError):
            linewinnow.save_new_file(self.source, cleaned)
        target = self.root / "新结果.txt"
        linewinnow.save_new_file(target, cleaned)
        self.assertEqual(target.read_bytes(), b"a\n")
        with self.assertRaises(FileExistsError):
            linewinnow.save_new_file(target, "other")
        self.assertEqual(self.source.read_text(encoding="utf-8"), "a\na\n")

    def test_real_cli_custom_parameter_and_output(self):
        self.source.write_text("a\n a \nb\n", encoding="utf-8")
        target = self.root / "output.txt"
        result = subprocess.run([sys.executable, str(Path(linewinnow.__file__)), str(self.source),
                                 "--linewinnow-trim-edges", "--output", str(target), "--json"],
                                capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["removable_lines"], 1)
        self.assertEqual(target.read_bytes(), b"a\nb\n")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            linewinnow.main([str(self.source), "--output", str(self.source)])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
