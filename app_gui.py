"""ezzyScrapper - OCR the business-lead screenshots and export them to CSV."""

import csv
import os
import queue
import subprocess
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core import scrape_images

ACCENT = "#22c55e"
BG = "#0f172a"
CARD = "#0b1522"
TXT = "#f8fafc"
MUTED = "#94a3b8"
BTN = "#1e293b"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("ezzyScrapper — Lead Screenshots to CSV")
        self._fit_to_screen()
        self.configure(fg_color=BG)

        self.images = []
        self.check_vars = {}
        self.queue = queue.Queue()
        self._rows = []
        self._save_path = None
        self._busy = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._build_header()
        self._build_controls()
        self._build_list()
        self._build_progress()
        self._build_preview()
        self._build_footer()

        self.status.configure(text="Add screenshots to get started.")
        self.after(120, self._poll)

    def _fit_to_screen(self):
        def scale():
            try:
                return ctk.ScalingTracker.get_window_dpi_scaling(self)
            except Exception:
                return 1.0
        s = scale()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        avail_w = int(sw / s) - 16
        avail_h = int(sh / s) - 60
        w = min(940, avail_w)
        h = min(660, avail_h)
        self.geometry(f"{w}x{h}")
        self.minsize(min(720, avail_w), min(520, avail_h))

    # ------------------------------------------------------------------ UI
    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=26, pady=(14, 2))
        ctk.CTkLabel(
            head, text="ezzyScrapper",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), text_color=TXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            head, text="Lead screenshots  →  structured CSV",
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color=MUTED,
        ).pack(anchor="w")

    def _build_controls(self):
        c = ctk.CTkFrame(self, fg_color="transparent")
        c.grid(row=1, column=0, sticky="ew", padx=26, pady=4)

        self.btn_images = ctk.CTkButton(
            c, text="+  Select Images", command=self.pick_images,
            fg_color=ACCENT, hover_color="#16a34a", height=40, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        )
        self.btn_images.pack(side="left", padx=(0, 8))

        self.btn_folder = ctk.CTkButton(
            c, text="Open Folder", command=self.pick_folder,
            fg_color=BTN, hover_color="#334155", height=40, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
        )
        self.btn_folder.pack(side="left")

        self.lbl_count = ctk.CTkLabel(c, text="0 files", text_color=MUTED,
                                      font=ctk.CTkFont(family="Segoe UI", size=13))
        self.lbl_count.pack(side="right")

    def _build_list(self):
        box = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        box.grid(row=2, column=0, sticky="nsew", padx=26, pady=4)

        bar = ctk.CTkFrame(box, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(bar, text="Scans", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cbd5e1").pack(side="left")
        self.btn_all = ctk.CTkButton(bar, text="Select All", width=96, height=26,
                                     command=self.select_all, fg_color=BTN,
                                     hover_color="#334155", font=ctk.CTkFont(size=12))
        self.btn_all.pack(side="right", padx=4)
        self.btn_none = ctk.CTkButton(bar, text="Clear", width=70, height=26,
                                      command=self.select_none, fg_color=BTN,
                                      hover_color="#334155", font=ctk.CTkFont(size=12))
        self.btn_none.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(box, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.empty_label = ctk.CTkLabel(
            self.scroll, text="No images loaded yet.\n\nClick “+ Select Images” to pick files\nor “Open Folder” to scan a directory.",
            font=ctk.CTkFont(family="Segoe UI", size=14), text_color=MUTED,
        )
        self.empty_label.pack(pady=70)

    def _build_progress(self):
        card = ctk.CTkFrame(self, fg_color="transparent")
        card.grid(row=3, column=0, sticky="ew", padx=26, pady=(2, 0))
        self.progress = ctk.CTkProgressBar(card, height=12, corner_radius=6,
                                           fg_color=BTN, progress_color=ACCENT)
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 4))
        self.status = ctk.CTkLabel(card, text="", text_color=MUTED, anchor="w",
                                   font=ctk.CTkFont(family="Segoe UI", size=12))
        self.status.pack(fill="x")

    def _build_preview(self):
        self.prev = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        self.prev.grid(row=4, column=0, sticky="nsew", padx=26, pady=4)
        self.prev_title = ctk.CTkLabel(self.prev, text="Result preview",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       text_color="#cbd5e1", anchor="w")
        self.prev_title.pack(fill="x", padx=12, pady=(10, 2))
        self.prev_box = ctk.CTkTextbox(
            self.prev, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=CARD, text_color="#e2e8f0", border_width=0, corner_radius=0,
        )
        self.prev_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.prev_box.insert("1.0", "—")
        self.prev_box.configure(state="disabled")

    def _build_footer(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=5, column=0, sticky="ew", padx=26, pady=(4, 10))

        self.btn_scrape = ctk.CTkButton(
            f, text="Start Scraping", command=self.start_scraping,
            fg_color=ACCENT, hover_color="#16a34a", height=44, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        )
        self.btn_scrape.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.btn_save = ctk.CTkButton(
            f, text="Save CSV…", command=self.save_csv, state="disabled",
            fg_color=BTN, hover_color="#334155", height=44, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(8, 8))

        self.btn_open = ctk.CTkButton(
            f, text="Open output", command=self.open_csv, state="disabled",
            fg_color=BTN, hover_color="#334155", height=44, corner_radius=10, width=130,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.btn_open.pack(side="left")

    # -------------------------------------------------------------- actions
    def pick_images(self):
        files = filedialog.askopenfilenames(
            title="Select screenshot images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.gif")],
        )
        if files:
            self._add_images(list(files))

    def pick_folder(self):
        folder = filedialog.askdirectory(title="Select folder with screenshots")
        if not folder:
            return
        files = [
            os.path.join(folder, f)
            for f in sorted(os.listdir(folder))
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".gif"))
        ]
        if files:
            self._add_images(files)

    def _add_images(self, files):
        drop = [f for f in files if f not in self.images]
        if not drop:
            return
        self.images.extend(drop)
        for f in drop:
            var = ctk.StringVar(value="on")
            cb = ctk.CTkCheckBox(
                self.scroll, text=os.path.basename(f), variable=var,
                onvalue="on", offvalue="off",
                font=ctk.CTkFont(family="Consolas", size=13),
                fg_color=ACCENT, hover_color="#16a34a",
                checkbox_width=22, checkbox_height=22,
            )
            cb.pack(fill="x", anchor="w", padx=8, pady=2)
            self.check_vars[f] = var
        if self.empty_label is not None:
            self.empty_label.pack_forget()
            self.empty_label = None
        self.lbl_count.configure(text=f"{len(self.images)} files")
        self.status.configure(text=f"{len(drop)} image(s) added — {len(self.images)} total.")

    def _selected(self):
        return [f for f, var in self.check_vars.items() if var.get() == "on"]

    def select_all(self):
        for var in self.check_vars.values():
            var.set("on")

    def select_none(self):
        for var in self.check_vars.values():
            var.set("off")

    def _set_busy(self, busy):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for w in (self.btn_images, self.btn_folder, self.btn_all, self.btn_none):
            w.configure(state=state)
        self.btn_scrape.configure(state=state,
                                  text="Processing…" if busy else "Start Scraping")

    def start_scraping(self):
        if self._busy:
            return
        selected = self._selected()
        if not selected:
            messagebox.showwarning("Nothing to scrape", "Select at least one image first.")
            return
        self.progress.set(0)
        self.btn_save.configure(state="disabled")
        self.btn_open.configure(state="disabled")
        self._rows = []
        self._set_busy(True)
        self.status.configure(text="Initialising OCR engine — loading models…")

        def work():
            rows = scrape_images(selected, progress_cb=self._progress_cb)
            self.queue.put({"type": "done", "rows": rows})

        threading.Thread(target=work, daemon=True).start()

    def _progress_cb(self, i, total, name):
        self.queue.put({"type": "progress", "value": i / total, "i": i,
                        "total": total, "name": name})

    def _poll(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg["type"] == "progress":
                    self.progress.set(min(msg["value"], 1.0))
                    self.status.configure(text=
                        f"Processing {msg['i']}/{msg['total']} — {msg['name']}")
                elif msg["type"] == "done":
                    self._set_busy(False)
                    self.progress.set(1.0)
                    self._on_done(msg["rows"])
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def _on_done(self, rows):
        self._rows = rows or []
        if not rows:
            self.status.configure(text="No leads parsed — check that screenshots contain business data.")
            return
        self.status.configure(text=f"Done — {len(rows)} unique leads extracted.")
        self._show_preview(rows)
        self.btn_save.configure(state="normal")
        self.btn_open.configure(state="normal")

    def _show_preview(self, rows):
        self.prev_box.configure(state="normal")
        self.prev_box.delete("1.0", "end")
        self.prev_box.insert("1.0", "Business Name\tCategory\tAddress\tPhone\n")
        for r in rows[:500]:
            self.prev_box.insert("end", "\t".join(r) + "\n")
        if len(rows) > 500:
            self.prev_box.insert("end", f"\n… and {len(rows) - 500} more rows.")
        self.prev_box.configure(state="disabled")
        self.prev_title.configure(text=f"Result preview ({len(rows)} rows)")

    def save_csv(self):
        if not self._rows:
            return
        path = filedialog.asksaveasfilename(
            title="Save CSV", defaultextension=".csv", initialfile="leads.csv",
            filetypes=[("CSV file", "*.csv")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(["Business Name", "Category", "Address", "Phone"])
                writer.writerows(self._rows)
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return
        self._save_path = path
        self.status.configure(text=f"Saved {len(self._rows)} rows → {path}")
        messagebox.showinfo("Saved", f"CSV saved with {len(self._rows)} leads.")

    def open_csv(self):
        if not self._save_path:
            return
        try:
            os.startfile(self._save_path)
        except Exception:
            subprocess.Popen(["cmd", "/c", "start", "", self._save_path])


def main():
    App().mainloop()


if __name__ == "__main__":
    main()