"""Simple tkinter GUI front-end for download.py.

Usage:
    pythonw gui.py        # no console window
    python gui.py         # with console (for debugging)
"""

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

DEFAULT_OUT = Path(__file__).resolve().parent / "downloads"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Downloader")
        self.geometry("560x560")
        self.q = queue.Queue()
        self.busy = False

        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="URL or search:").pack(anchor="w")
        self.url_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.url_var)
        entry.pack(fill="x", pady=(2, 6))
        entry.bind("<Return>", lambda e: self.add_input())
        ttk.Button(top, text="Add", command=self.add_input).pack(anchor="e")

        self.preview = tk.Text(top, height=4, wrap="word", state="disabled")
        self.preview.pack(fill="x", pady=4)
        btns = ttk.Frame(top)
        btns.pack(fill="x")
        ttk.Button(btns, text="Download", command=self.preview_yes).pack(side="left")
        ttk.Button(btns, text="Skip", command=self.preview_clear).pack(side="left", padx=4)

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
        self.out_var = tk.StringVar(value=str(DEFAULT_OUT))
        ttk.Entry(opts, textvariable=self.out_var).grid(
            row=1, column=1, columnspan=2, sticky="we", pady=4)
        ttk.Button(opts, text="Browse...",
                   command=self.pick_dir).grid(row=1, column=3, padx=(6, 0))
        opts.columnconfigure(1, weight=1)

        queue_frame = ttk.LabelFrame(self, text="Queue", padding=8)
        queue_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.queue_box = tk.Listbox(queue_frame)
        self.queue_box.pack(fill="both", expand=True)
        qbtns = ttk.Frame(queue_frame)
        qbtns.pack(fill="x", pady=(4, 0))
        ttk.Button(qbtns, text="Download Queue",
                   command=self.start_download).pack(side="left")
        ttk.Button(qbtns, text="Remove", command=self.remove_selected).pack(side="left", padx=4)
        ttk.Button(qbtns, text="Clear", command=self.clear_queue).pack(side="left")
        ttk.Button(qbtns, text="Open folder",
                   command=self.open_folder).pack(side="right")

        prog = ttk.Frame(self, padding=8)
        prog.pack(fill="x")
        self.bar = ttk.Progressbar(prog, maximum=100)
        self.bar.pack(fill="x")
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
            self.queue_box.insert("end", text)
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
            self.queue_box.insert("end", url)
        self.preview_clear()

    def preview_clear(self):
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.config(state="disabled")
        self._preview_url = None

    # --- queue -----------------------------------------------------------

    def remove_selected(self):
        for i in reversed(self.queue_box.curselection()):
            self.queue_box.delete(i)

    def clear_queue(self):
        self.queue_box.delete("0", "end")

    def pick_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_var.get() or str(DEFAULT_OUT))
        if d:
            self.out_var.set(d)

    def open_folder(self):
        path = self.out_var.get() or str(DEFAULT_OUT)
        Path(path).mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def start_download(self):
        if self.busy:
            messagebox.showinfo("Busy", "A download is already running.")
            return
        urls = list(self.queue_box.get(0, "end"))
        if not urls:
            return
        self.busy = True
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
        try:
            failed = dl.download(urls, out, audio_only, quality,
                                 assume_yes=True, progress_hook=hook)
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
                elif kind == "done":
                    failed = msg[1]
                    self.busy = False
                    self.bar["value"] = 0
                    if failed:
                        self.set_status(f"Done with {len(failed)} failure(s)")
                    else:
                        self.set_status("Done")
                elif kind == "error":
                    self.busy = False
                    self.bar["value"] = 0
                    self.set_status("Error")
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def _progress(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes", 0)
            pct = (done / total * 100) if total else 0
            spd = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            name = Path(d.get("filename") or "").name
            self.bar["value"] = pct
            self.set_status(f"{pct:.0f}% {name} {spd} ETA {eta}".strip())
        elif d.get("status") == "finished":
            self.bar["value"] = 100
            self.set_status(f"Finished: {Path(d.get('filename') or '').name}")

    def set_status(self, text):
        self.status.set(text)


if __name__ == "__main__":
    App().mainloop()
