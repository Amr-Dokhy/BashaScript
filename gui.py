import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os

class YallaCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BashaScript Language Compiler")
        self.root.geometry("1200x800")

        # Editor
        self.editor = scrolledtext.ScrolledText(root, height=15, font=("Consolas", 12))
        self.editor.pack(fill="x", padx=10, pady=10)

        # Default Code
        self.editor.insert("1.0", """yalla {
    daraga = 75
    lw daraga >= 50 {
        ekteb("ناجح")
    } nafez {
        ekteb("راسب")
    }
}""")

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack()

        tk.Button(btn_frame, text="▶ Run", command=self.run_code, bg="green", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear", command=self.clear_editor, width=15).pack(side="left", padx=5)

        # Tabs
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.outputs = {}
        for tab_name in ["Tokens", "AST", "Semantic", "Python", "Output"]:
            frame = tk.Frame(self.tabs)
            self.tabs.add(frame, text=tab_name)

            text_area = scrolledtext.ScrolledText(frame, font=("Consolas", 11))
            text_area.pack(fill="both", expand=True)

            self.outputs[tab_name] = text_area

    def clear_editor(self):
        self.editor.delete("1.0", tk.END)

    def run_code(self):
        code = self.editor.get("1.0", tk.END)

        with open("code.txt", "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
    ["python", "main.py"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore"
)

        output = result.stdout + result.stderr

        sections = {
            "Tokens": "",
            "AST": "",
            "Semantic": "",
            "Python": "",
            "Output": ""
        }

        current = None

        for line in output.splitlines():
            if "===== TOKENS =====" in line:
                current = "Tokens"
                continue
            elif "===== AST" in line:
                current = "AST"
                continue
            elif "===== SEMANTIC CHECK =====" in line:
                current = "Semantic"
                continue
            elif "===== CODE GENERATION =====" in line:
                current = "Python"
                continue
            elif "===== EXECUTION OUTPUT =====" in line:
                current = "Output"
                continue

            if current:
                sections[current] += line + "\n"

        for tab in sections:
            self.outputs[tab].delete("1.0", tk.END)
            self.outputs[tab].insert("1.0", sections[tab])

root = tk.Tk()
app = YallaCompilerGUI(root)
root.mainloop()