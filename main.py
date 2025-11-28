import tkinter as tk
from tkinter import filedialog
from lexicalAnalyzer import analizar_lexico
from syntaxAnalyzer import analizar_sintactico
from semanticAnalyzer import analizar_semantico

# ================== Editor con numeración ==================
class LineNumberedText(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.text = tk.Text(self, **kwargs, bg="black", fg="white", insertbackground="white")
        self.text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.linenumbers = tk.Canvas(self, width=40, bg="#222222")
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)

        self.text.bind("<KeyRelease>", self.update_numbers)
        self.text.bind("<MouseWheel>", self.update_numbers)
        self.text.bind("<ButtonRelease>", self.update_numbers)
        self.text.bind("<Configure>", self.update_numbers)

        self.update_numbers()

    def update_numbers(self, event=None):
        self.linenumbers.delete("all")
        i = self.text.index("@0,0")
        while True:
            info = self.text.dlineinfo(i)
            if info is None:
                break
            y = info[1]
            linenum = i.split(".")[0]
            self.linenumbers.create_text(2, y, anchor="nw", text=linenum, fill="white")
            i = self.text.index(f"{i}+1line")

    def get(self, *args):
        return self.text.get(*args)

    def delete(self, *args):
        return self.text.delete(*args)

    def insert(self, *args):
        return self.text.insert(*args)


# ================== Interfaz principal ==================
class RustAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rust Analyzer")
        self.root.geometry("1100x650")
        self.root.configure(bg="#1e1e1e")

        self.build_ui()

    def build_ui(self):
        # --- barra superior ---
        top = tk.Frame(self.root, bg="#333333", height=50)
        top.pack(fill=tk.X)

        tk.Button(top, text="Abrir", bg="#555", fg="white",
                  command=self.open_file).pack(side=tk.LEFT, padx=10, pady=10)

        tk.Button(top, text="Guardar", bg="#555", fg="white",
                  command=self.save_file).pack(side=tk.LEFT, padx=10, pady=10)

        # --- contenedor principal (botones izq + editor + consola) ---
        main_container = tk.Frame(self.root, bg="#1e1e1e")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- panel de botones verticales a la izquierda ---
        button_panel = tk.Frame(main_container, bg="#252525", width=120)
        button_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Button(button_panel, text="Borrar", bg="#007acc", fg="white",
                  command=self.clear_editor).pack(fill=tk.X, pady=5, padx=5)

        tk.Button(button_panel, text="Léxico", bg="#007acc", fg="white",
                  command=self.run_lex).pack(fill=tk.X, pady=5, padx=5)

        tk.Button(button_panel, text="Sintáctico", bg="#007acc", fg="white",
                  command=self.run_syn).pack(fill=tk.X, pady=5, padx=5)

        tk.Button(button_panel, text="Semántico", bg="#007acc", fg="white",
                  command=self.run_sem).pack(fill=tk.X, pady=5, padx=5)

        # --- editor de código ---
        editor_frame = tk.Frame(main_container, bg="#1e1e1e")
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(editor_frame, text="Editor de código", fg="white", bg="#1e1e1e").pack(anchor="w")

        self.editor = LineNumberedText(editor_frame)
        self.editor.pack(fill=tk.BOTH, expand=True)

        # --- consola ---
        console_frame = tk.Frame(main_container, bg="#1e1e1e")
        console_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(console_frame, text="Consola", fg="white", bg="#1e1e1e").pack(anchor="w")

        self.console = tk.Text(console_frame, bg="white", fg="black", state="disabled")
        self.console.pack(fill=tk.BOTH, expand=True)

    # ================== Utilidades GUI ==================
    def print_console(self, text):
        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.insert(tk.END, text)
        self.console.config(state="disabled")

    def clear_editor(self):
        self.editor.delete("1.0", tk.END)
        self.print_console("")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Rust files", "*.rs")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
                self.editor.delete("1.0", tk.END)
                self.editor.insert(tk.END, code)

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".rs")
        if path:
            code = self.editor.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)

    # ================== Acciones de los analizadores ==================
    def run_lex(self):
        code = self.editor.get("1.0", tk.END)
        out = analizar_lexico(code)
        self.print_console(out)

    def run_syn(self):
        code = self.editor.get("1.0", tk.END)
        out = analizar_sintactico(code)
        self.print_console(out)

    def run_sem(self):
        code = self.editor.get("1.0", tk.END)
        out = analizar_semantico(code)
        self.print_console(out)


# ================== Lanzar app ==================
if __name__ == "__main__":
    root = tk.Tk()
    RustAnalyzerGUI(root)
    root.mainloop()
