"""Simple tkinter GUI front-end for download.py.

Usage:
    pythonw gui.py        # no console window
    python gui.py         # with console (for debugging)
"""

import json
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# pythonw / windowed exe have no console streams; redirect so download.py's
# prints don't crash the worker thread.
_devnull = open(os.devnull, "w")
if sys.stdout is None:
    sys.stdout = _devnull
if sys.stderr is None:
    sys.stderr = _devnull

sys.path.insert(0, str(Path(__file__).resolve().parent))
import download as dl

DEFAULT_OUT = Path.home() / "Downloads"
CONFIG_PATH = Path.home() / ".video_downloader.json"


def _read_config():
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {}


def load_out_dir():
    saved = _read_config().get("out_dir")
    if saved and Path(saved).is_dir():
        return saved
    return str(DEFAULT_OUT)


def save_out_dir(path):
    try:
        cfg = _read_config()
        cfg["out_dir"] = str(path)
        CONFIG_PATH.write_text(json.dumps(cfg))
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Video Downloader v{dl.__version__}")
        self.geometry("560x580")
        self.minsize(560, 400)
        self.q = queue.Queue()
        self.busy = False
        style = ttk.Style()
        style.configure("Slim.Horizontal.TProgressbar", thickness=8)

        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="YouTube & Facebook — videos, reels & shorts",
                  foreground="gray").pack(anchor="w")
        ttk.Label(top, text="URL or search:").pack(anchor="w", pady=(4, 0))
        self.url_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.url_var)
        entry.pack(fill="x", pady=(2, 6))
        entry.bind("<Return>", lambda e: self.add_input())
        ttk.Button(top, text="Add", command=self.add_input).pack(anchor="e")

        preview_box = ttk.LabelFrame(top, text="Preview", padding=4)
        preview_box.pack(fill="x", pady=4)
        self.preview = tk.Text(preview_box, height=5, wrap="word", state="disabled")
        self.preview.pack(fill="x")
        btns = ttk.Frame(preview_box)
        btns.pack(fill="x", pady=(4, 0))
        ttk.Button(btns, text="Add to Queue", command=self.preview_yes).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.preview_clear).pack(side="left", padx=4)

        opts = ttk.LabelFrame(self, text="Options", padding=8)
        opts.pack(fill="x", padx=8, pady=4)
        ttk.Label(opts, text="Quality:").grid(row=0, column=0, sticky="w")
        self.quality_var = tk.StringVar(value="1080p")
        ttk.Combobox(opts, textvariable=self.quality_var, state="readonly",
                     values=["1080p", "720p", "480p", "Best"],
                     width=8).grid(row=0, column=1, sticky="w")
        self.audio_var = tk.BooleanVar()
        ttk.Checkbutton(opts, text="Audio only (mp3)",
                        variable=self.audio_var).grid(row=0, column=2, padx=12)
        ttk.Label(opts, text="Save to:").grid(row=1, column=0, sticky="w", pady=4)
        self.out_var = tk.StringVar(value=load_out_dir())
        ttk.Entry(opts, textvariable=self.out_var).grid(
            row=1, column=1, columnspan=2, sticky="we", pady=4)
        ttk.Button(opts, text="Browse...",
                   command=self.pick_dir).grid(row=1, column=3, padx=(6, 0))
        opts.columnconfigure(1, weight=1)

        queue_frame = ttk.LabelFrame(self, text="Queue", padding=8)
        queue_frame.pack(fill="x", padx=8, pady=4)
        canvas = tk.Canvas(queue_frame, height=110, highlightthickness=0)
        sb = ttk.Scrollbar(queue_frame, orient="vertical", command=canvas.yview)
        self.rows_inner = ttk.Frame(canvas)
        self.rows_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.rows_inner, anchor="nw", tags="win")
        canvas.configure(yscrollcommand=sb.set)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure("win", width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.rows = []

        prog = ttk.Frame(self, padding=8)
        prog.pack(fill="x", side="bottom", before=queue_frame)
        qbtns = ttk.Frame(prog)
        qbtns.pack(fill="x", pady=(0, 4))
        ttk.Button(qbtns, text="Download Queue",
                   command=self.start_download).pack(side="left")
        ttk.Button(qbtns, text="Clear", command=self.clear_queue).pack(side="left", padx=4)
        ttk.Button(qbtns, text="Open folder",
                   command=self.open_folder).pack(side="right")
        self.status = tk.StringVar(value="Ready")
        ttk.Label(prog, textvariable=self.status).pack(anchor="w")

        self.after(100, self.poll)

    # --- input / preview -------------------------------------------------

    def add_input(self):
        text = self.url_var.get().strip()
        if not text:
            return
        self.url_var.set("")
        if text.startswith(("http://", "https://")):
            self._add_row(text)
            return
        self.set_status(f"Searching: {text}")
        threading.Thread(target=self._search, args=(text,), daemon=True).start()

    def _search(self, query):
        try:
            entries = [e for e in dl.search(query)
                       if "watch?v=" in (e.get("url") or "")
                       or "watch?v=" in (e.get("webpage_url") or "")]
            entry = entries[0] if entries else None
            self.q.put(("preview", entry, query))
        except Exception as e:
            self.q.put(("error", f"Search failed: {e}"))

    def show_preview(self, entry, query):
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        if entry:
            self.preview.insert("end", dl.describe_str(entry))
            self._preview_url = entry.get("webpage_url") or entry.get("url")
        else:
            self.preview.insert("end", f"No results for: {query}")
            self._preview_url = None
        self.preview.config(state="disabled")

    def preview_yes(self):
        url = getattr(self, "_preview_url", None)
        if url:
            self._add_row(url)
        self.preview_clear()

    def preview_clear(self):
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.config(state="disabled")
        self._preview_url = None

    # --- queue -----------------------------------------------------------

    def _add_row(self, url):
        row = ttk.Frame(self.rows_inner)
        row.pack(fill="x")
        bar = ttk.Progressbar(row, maximum=100, length=120, style="Slim.Horizontal.TProgressbar")
        pct = ttk.Label(row, text="", width=5, anchor="e")
        entry = {"url": url, "frame": row, "bar": bar, "pct": pct}
        ttk.Button(row, text="×", width=3,
                   command=lambda e=entry: self._remove_row(e)).pack(side="right", padx=(4, 0))
        pct.pack(side="right")
        bar.pack(side="right", padx=4)
        ttk.Label(row, text=url, anchor="w").pack(side="left", fill="x", expand=True)
        self.rows.append(entry)

    def _remove_row(self, entry):
        if self.busy:
            return
        entry["frame"].destroy()
        self.rows.remove(entry)

    def clear_queue(self):
        if self.busy:
            return
        for entry in self.rows:
            entry["frame"].destroy()
        self.rows.clear()

    def pick_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_var.get() or str(DEFAULT_OUT))
        if d:
            self.out_var.set(d)
            save_out_dir(d)

    def open_folder(self):
        path = self.out_var.get() or str(DEFAULT_OUT)
        Path(path).mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def start_download(self):
        if self.busy:
            messagebox.showinfo("Busy", "A download is already running.")
            return
        urls = [r["url"] for r in self.rows]
        if not urls:
            return
        self.busy = True
        self.set_status(f"Downloading {len(urls)} item(s)...")
        self.cur_item = -1
        for r in self.rows:
            r["bar"]["value"] = 0
            r["pct"]["text"] = "0%"
        q = self.quality_var.get()
        quality = 0 if q == "Best" else int(q.rstrip("p"))
        out = self.out_var.get() or str(DEFAULT_OUT)
        threading.Thread(
            target=self._worker,
            args=(urls, out, self.audio_var.get(), quality),
            daemon=True,
        ).start()

    def _worker(self, urls, out, audio_only, quality):
        hook = lambda d: self.q.put(("prog", d))
        item_hook = lambda i, n, url: self.q.put(("item", i, n, url))
        try:
            failed = dl.download(urls, out, audio_only, quality,
                                 assume_yes=True, progress_hook=hook,
                                 item_hook=item_hook)
            self.q.put(("done", failed))
        except Exception as e:
            self.q.put(("error", f"Download failed: {e}"))

    # --- UI polling ------------------------------------------------------

    def poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "preview":
                    self.show_preview(msg[1], msg[2])
                    self.set_status("Preview ready")
                elif kind == "prog":
                    self._progress(msg[1])
                elif kind == "status":
                    self.set_status(msg[1])
                elif kind == "item":
                    _, i, n, url = msg
                    self.cur_item = i - 1
                    self.set_status(f"Fetching {i}/{n}: {url[:70]}")
                elif kind == "done":
                    failed = msg[1]
                    self.busy = False
                    out = self.out_var.get() or str(DEFAULT_OUT)
                    if failed:
                        self.set_status(f"Done with {len(failed)} failure(s)")
                        messagebox.showwarning(
                            "Finished with errors",
                            f"{len(failed)} download(s) failed:\n\n"
                            + "\n\n".join(f"{u}\n{err[:300]}" for u, err in failed)
                            + f"\n\nDetails: {dl.LOG_PATH}\nOutput folder: {out}")
                    else:
                        self.set_status("Done — all downloads finished")
                elif kind == "error":
                    self.busy = False
                    self.set_status("Error")
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def _progress(self, d):
        if not (0 <= self.cur_item < len(self.rows)):
            return
        row = self.rows[self.cur_item]
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes", 0)
            pct = (done / total * 100) if total else 0
            spd = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            name = Path(d.get("filename") or "").name
            row["bar"]["value"] = pct
            row["pct"]["text"] = f"{pct:.0f}%"
            self.set_status(f"{name} {spd} ETA {eta}".strip())
        elif d.get("status") == "finished":
            row["bar"]["value"] = 100
            row["pct"]["text"] = "Done"
            self.set_status(f"Finished: {Path(d.get('filename') or '').name}")

    def set_status(self, text):
        self.status.set(text)


if __name__ == "__main__":
    App().mainloop()
