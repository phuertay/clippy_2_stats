#!/usr/bin/env python3
"""
Clippy Analyzer - Python GUI Application

MIT License

Copyright (c) Pedro Huerta
Copyright (c) River Tae Smith <river@r-tae.dev>
Copyright (c) Sindre Sorhus <sindresorhus@gmail.com> (https://sindresorhus.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Credits to River Tae Smith <river@r-tae.dev> for coming up with the idea!
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set, Any


class ClippyAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        try:
            self.root.call('tk', 'scaling', 1.0)  # Ensure 1:1 scaling to reduce blurriness
        except:
            pass
        self.root.title("Clippy Analyzer")
        self.root.geometry("1000x600")

        self.data_entries = []

        self.colors = {
            'dark': {
                'bg': '#002b36', 'bg_alt': '#073642', 'fg': '#839496',
                'fg_alt': '#93a1a1', 'accent': '#2aa198',
                'button': '#268bd2', 'button_fg': '#fdf6e3'
            },
            'light': {
                'bg': '#fdf6e3', 'bg_alt': '#eee8d5', 'fg': '#657b83',
                'fg_alt': '#586e75', 'accent': '#657b83',
                'button': '#268bd2', 'button_fg': '#fdf6e3'
            }
        }

        self.the_font = ("Segoe UI", 14)
        self.current_theme = 'dark'
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        self.title_label = tk.Label(main_frame, text="Clippy Analyzer", font=("Segoe UI", 28, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        file_frame.columnconfigure(1, weight=1)

        self.select_file_btn = tk.Button(file_frame, text="Select .org File", command=self.select_file)
        self.select_file_btn["font"]=self.the_font
        self.select_file_btn.grid(row=0, column=0, padx=(0, 10))

        self.file_label = tk.Label(file_frame, text="No file selected", anchor="w")
        self.file_label["font"]=self.the_font
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=2, padx=(20, 0))

        self.export_btn = tk.Button(button_frame, text="Export CSV", command=self.export_csv, state='disabled')
        self.export_btn["font"]=self.the_font
        self.export_btn.grid(row=0, column=0, padx=(0, 10))

        self.theme_btn = tk.Button(button_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_btn["font"]=self.the_font
        self.theme_btn.grid(row=0, column=1)

        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        columns = ('Translation', 'Suggestions', 'Severity', 'Count', 'Score')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False), anchor="w")

        self.tree.column('Translation', width=200)
        self.tree.column('Suggestions', width=300)
        self.tree.column('Severity', width=80)
        self.tree.column('Count', width=80)
        self.tree.column('Score', width=80)

        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        results_frame.grid_remove()
        self.results_frame = results_frame

    def apply_theme(self):
        theme = self.colors[self.current_theme]

        self.root.configure(bg=theme['bg'])
        self.title_label.configure(bg=theme['bg'], fg=theme['accent'])
        self.file_label.configure(bg=theme['bg'], fg=theme['fg'])

        for btn in [self.select_file_btn, self.export_btn, self.theme_btn]:
            btn.configure(bg=theme['button'], fg=theme['button_fg'],
                          activebackground=theme['accent'], activeforeground=theme['button_fg'])

        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Treeview", background=theme['bg_alt'], foreground=theme['fg'],
                        fieldbackground=theme['bg_alt'], selectbackground=theme['accent'],
                        selectforeground=theme['bg'], font=self.the_font)
        style.configure("Treeview.Heading", background=theme['fg_alt'],
                        foreground=theme['bg'], relief='flat', font=self.the_font + ("bold",))
        style.configure("TFrame", background=theme['bg'])

    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.apply_theme()

    def select_file(self):
        initial_dir = os.path.expandvars(r'%LOCALAPPDATA%\\plover\\plover')
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        file_path = filedialog.askopenfilename(
            title="Select Clippy output file",
            initialdir=initial_dir,
            filetypes=[("Org files", "*.org"), ("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            self.file_label.configure(text=f"Selected: {file_path}")
            self.process_file(file_path)

    def strip_ansi(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
        return ansi_escape.sub('', text)

    def process_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            lines = [self.strip_ansi(line.strip()) for line in content.split('\n')]
            entry_map = defaultdict(lambda: {'count': 0, 'severity': 0, 'suggestions': set()})

            for line in lines:
                if line.startswith('START') or line.startswith('END') or not line.startswith('*'):
                    continue
                match = re.match(r'^(\*+)\s+(.*?)\s{2,}(.+?)\s*<.+$', line)
                if not match:
                    continue

                stars, translation, suggestion = match.groups()
                severity = len(stars)
                entry = entry_map[translation]
                entry['count'] += 1
                entry['severity'] = severity
                entry['suggestions'].add(suggestion)

            self.data_entries = []
            for translation, data in entry_map.items():
                suggestions_str = '; '.join(sorted(data['suggestions']))
                severity_stars = '*' * data['severity']
                score = data['severity'] * data['count']

                self.data_entries.append({
                    'translation': translation,
                    'suggestions': suggestions_str,
                    'severity_stars': severity_stars,
                    'severity': data['severity'],
                    'count': data['count'],
                    'score': score
                })

            self.data_entries.sort(key=lambda x: x['score'], reverse=True)
            self.display_results()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")

    def display_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for entry in self.data_entries:
            self.tree.insert('', 'end', values=(
                entry['translation'], entry['suggestions'],
                entry['severity_stars'], entry['count'], entry['score']
            ))

        self.results_frame.grid()
        self.export_btn.configure(state='normal')

    def sort_by_column(self, col: str, reverse: bool):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        numeric_cols = {'Count', 'Score', 'Severity'}
        if col in numeric_cols:
            try:
                data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=reverse)
            except (ValueError, TypeError):
                data.sort(key=lambda x: x[0], reverse=reverse)
        else:
            data.sort(key=lambda x: x[0], reverse=reverse)

        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        for column in ('Translation', 'Suggestions', 'Severity', 'Count', 'Score'):
            if column == col:
                self.tree.heading(column, text=f"{column} {'\u2193' if reverse else '\u2191'}")
            else:
                self.tree.heading(column, text=column)

        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def export_csv(self):
        if not self.data_entries:
            messagebox.showwarning("Warning", "No data to export")
            return

        downloads_dir = Path.home() / "Downloads"
        if not downloads_dir.exists():
            downloads_dir = Path.cwd()

        file_path = filedialog.asksaveasfilename(
            title="Save CSV file",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(downloads_dir),
            initialfile="sorted_translations.csv"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Translation', 'Suggestions', 'Severity', 'Count', 'Score'])
                for entry in self.data_entries:
                    writer.writerow([
                        entry['translation'], entry['suggestions'],
                        entry['severity_stars'], entry['count'], entry['score']
                    ])
            messagebox.showinfo("Success", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ClippyAnalyzer()
    app.run()

