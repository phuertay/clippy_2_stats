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
            # Ensure 1:1 scaling to reduce blurriness
            self.root.call('tk', 'scaling', 1.0)
        except Exception as e:
            # Print error if scaling fails, but don't stop execution
            print(f"Warning: Could not set Tkinter scaling: {e}")

        self.root.title("Clippy Analyzer")
        self.root.geometry("1000x600")

        self.data_entries = []

        # Define the font for consistent styling for general UI elements
        self.the_font = ("Segoe UI", 14)
        self.setup_ui()

    def setup_ui(self):
        """
        Sets up the graphical user interface elements.
        """
        # Main frame to hold all UI elements, with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0)
        main_frame.columnconfigure(2, weight=0)
        main_frame.rowconfigure(2, weight=1)

        # Title label for the application (use ttk.Label for theme background)
        self.title_label = ttk.Label(main_frame, text="Clippy analyzer", font=("Segoe UI", 28, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Frame for file selection and export buttons (side by side)
        file_button_frame = ttk.Frame(main_frame)
        file_button_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        file_button_frame.columnconfigure(0, weight=0)
        file_button_frame.columnconfigure(1, weight=1)
        file_button_frame.columnconfigure(2, weight=0)

        # Button to select the .org file
        self.select_file_btn = tk.Button(file_button_frame, text="Select .org File", command=self.select_file)
        self.select_file_btn["font"] = self.the_font
        self.select_file_btn.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)

        # Label to display the selected file path
        self.file_label = tk.Label(file_button_frame, text="No file selected", anchor="w")
        self.file_label["font"] = self.the_font
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Button to export data to CSV, initially disabled
        self.export_btn = tk.Button(file_button_frame, text="Export CSV", command=self.export_csv, state='disabled')
        self.export_btn["font"] = self.the_font
        self.export_btn.grid(row=0, column=2, padx=(10, 0), sticky=tk.E)

        # Frame to display results in a Treeview
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Define columns for the Treeview
        columns = ('Translation', 'Suggestions', 'Severity', 'Count', 'Score')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        # Set up column headings and their sort commands
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False), anchor="w")

        # Set column widths
        self.tree.column('Translation', width=200)
        self.tree.column('Suggestions', width=300)
        self.tree.column('Severity', width=80)
        self.tree.column('Count', width=80)
        self.tree.column('Score', width=80)

        # Add scrollbars to the Treeview
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Place Treeview and scrollbars in the grid
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Configure Treeview and Treeview.Heading styles for font size
        style = ttk.Style()
        # Use a default theme that supports styling, e.g., 'clam', 'alt', 'default'
        style.theme_use('clam')
        
        # Configure the font for the Treeview rows
        style.configure("Treeview", font=("Segoe UI", 12))
        # Configure the font for the Treeview headings (bold for emphasis)
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))


        # Initially hide the results frame until data is loaded
        results_frame.grid_remove()
        self.results_frame = results_frame

    def select_file(self):
        """
        Opens a file dialog for the user to select a .org file.
        Processes the selected file if one is chosen.
        """
        # Set initial directory to Plover's local app data if it exists, otherwise current working directory
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
        """
        Removes ANSI escape codes from a given string.
        """
        ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
        return ansi_escape.sub('', text)

    def process_file(self, file_path: str):
        """
        Reads and processes the content of the selected file.
        Parses translation entries, suggestions, severity, and calculates scores.
        Populates self.data_entries and displays results.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Strip ANSI codes and leading/trailing whitespace from each line
            lines = [self.strip_ansi(line.strip()) for line in content.split('\n')]
            # Use defaultdict to store aggregated data for each unique translation
            entry_map = defaultdict(lambda: {'count': 0, 'severity': 0, 'suggestions': set()})

            for line in lines:
                # Skip header/footer lines and lines not starting with '*'
                if line.startswith('START') or line.startswith('END') or not line.startswith('*'):
                    continue
                # Regex to extract stars (severity), translation, and suggestion
                match = re.match(r'^(\*+)\s+(.*?)\s{2,}(.+?)\s*<.+$', line)
                if not match:
                    continue

                stars, translation, suggestion = match.groups()
                severity = len(stars) # Severity is determined by the number of stars
                entry = entry_map[translation]
                entry['count'] += 1
                entry['severity'] = severity
                entry['suggestions'].add(suggestion) # Use a set to store unique suggestions

            self.data_entries = []
            # Convert aggregated data into a list of dictionaries for display
            for translation, data in entry_map.items():
                suggestions_str = '; '.join(sorted(data['suggestions'])) # Join suggestions with semicolon
                severity_stars = '*' * data['severity'] # Convert severity back to stars for display
                score = data['severity'] * data['count'] # Calculate score

                self.data_entries.append({
                    'translation': translation,
                    'suggestions': suggestions_str,
                    'severity_stars': severity_stars,
                    'severity': data['severity'], # Keep numeric severity for sorting
                    'count': data['count'],
                    'score': score
                })

            # Sort data by score in descending order by default
            self.data_entries.sort(key=lambda x: x['score'], reverse=True)
            self.display_results()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")

    def display_results(self):
        """
        Clears existing Treeview data and populates it with processed data entries.
        Enables the export button and shows the results frame.
        """
        # Clear existing items in the Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data entries into the Treeview
        for entry in self.data_entries:
            self.tree.insert('', 'end', values=(
                entry['translation'], entry['suggestions'],
                entry['severity_stars'], entry['count'], entry['score']
            ))

        # Show the results frame and enable the export button
        self.results_frame.grid()
        self.export_btn.configure(state='normal')

    def sort_by_column(self, col: str, reverse: bool):
        """
        Sorts the Treeview content by the specified column.
        Handles numeric and string sorting.
        Updates column headings to show sort direction.
        """
        # Get all items from the Treeview and their values for the specified column
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        numeric_cols = {'Count', 'Score', 'Severity'} # Columns that should be sorted numerically

        if col in numeric_cols:
            # Attempt to sort numerically, fallback to string sort if conversion fails
            try:
                data.sort(key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0, reverse=reverse)
            except (ValueError, TypeError):
                data.sort(key=lambda x: x[0], reverse=reverse)
        else:
            # Sort as strings for other columns
            data.sort(key=lambda x: x[0], reverse=reverse)

        # Rearrange Treeview items based on sorted data
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        # Update column headings to show sort direction indicators
        for column in ('Translation', 'Suggestions', 'Severity', 'Count', 'Score'):
            if column == col:
                # Use (desc) for descending and (asc) for ascending
                self.tree.heading(column, text=f"{column} {'(desc)' if reverse else '(asc)'}")
            else:
                self.tree.heading(column, text=column)

        # Toggle sort direction for the next click on the same column
        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def export_csv(self):
        """
        Exports the current data entries to a CSV file.
        Prompts the user for a save location.
        """
        if not self.data_entries:
            messagebox.showwarning("Warning", "No data to export")
            return

        # Suggest downloads directory or current working directory
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
            return # User cancelled the save dialog

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header row
                writer.writerow(['Translation', 'Suggestions', 'Severity', 'Count', 'Score'])
                # Write data rows
                for entry in self.data_entries:
                    writer.writerow([
                        entry['translation'], entry['suggestions'],
                        entry['severity_stars'], entry['count'], entry['score']
                    ])
            messagebox.showinfo("Success", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def run(self):
        """
        Starts the Tkinter event loop.
        """
        self.root.mainloop()


if __name__ == "__main__":
    app = ClippyAnalyzer()
    app.run()

