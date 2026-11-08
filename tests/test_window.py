"""检查窗口的实际按钮、选项和保存过程。"""

from pathlib import Path
import sys
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import linewinnow


class WindowTest(unittest.TestCase):
    def test_scan_change_option_and_save(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "lines.txt"
            source.write_text(" apple \napple\n", encoding="utf-8")
            root = tk.Tk()
            root.withdraw()
            try:
                app = linewinnow.create_app(root)
                app.path.set(str(source))
                for trim, expected in [(False, 0), (True, 1)]:
                    app.trim_edges.set(trim)
                    with patch('tool_window.messagebox.showerror', side_effect=AssertionError):
                        app.run_button.invoke()
                        deadline = time.monotonic() + 5
                        while app.busy and time.monotonic() < deadline:
                            root.update()
                            time.sleep(0.01)
                    self.assertFalse(app.busy)
                    self.assertEqual(app.report['removable_lines'], expected)
                    self.assertIn('LineWinnow', app.output.get('1.0', 'end'))
                target = Path(temp) / "cleaned.txt"
                with patch('tool_window.filedialog.asksaveasfilename', return_value=str(target)):
                    app.clean_button.invoke()
                self.assertEqual(target.read_bytes(), b" apple \n")
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
