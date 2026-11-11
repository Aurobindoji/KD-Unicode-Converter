#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KD Unicode Converter — विंडो वाला app.

Kruti Dev 010 जैसा कोई legacy TTF चुनें, Convert दबाएँ, और उसी जैसा दिखने
वाला Unicode देवनागरी फ़ॉन्ट बन जाता है। असली काम
krutidev_to_unicode_font.build() करता है; यह फ़ाइल केवल उसका आवरण है।
"""

import io
import os
import queue
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import krutidev_to_unicode_font as kd

APP_TITLE = "KD Unicode Converter"
APP_VERSION = "1.3"


def resource(*parts):
    """PyInstaller exe में साथ आई फ़ाइलें (_MEIPASS), वरना script का फ़ोल्डर."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


BUNDLED_LATIN = resource("fonts", "Arimo.ttf")


def check_source(path):
    """
    स्रोत फ़ॉन्ट की जाँच: ("ok" | "unsure" | "bad", संदेश).
    Unicode देवनागरी वाला फ़ॉन्ट (जैसे Mangal) Kruti-शैली नहीं है -> bad.
    नाम में "Kruti" न हो -> unsure (दूसरे legacy फ़ॉन्ट भी इसी व्यवस्था के हो सकते हैं).
    """
    from fontTools.ttLib import TTFont
    try:
        f = TTFont(path, lazy=True)
        cmap = f.getBestCmap() or {}
        names = " ".join(str(r) for r in f["name"].names if r.nameID in (1, 4))
    except Exception as e:
        return "bad", "यह फ़ाइल TTF फ़ॉन्ट की तरह नहीं खुली:\n%s" % e
    if any(0x0900 <= c <= 0x097F for c in cmap):
        return "bad", ("यह फ़ॉन्ट पहले से Unicode देवनागरी है (%s)। यह app केवल "
                       "Kruti Dev जैसे पुराने (non-Unicode) फ़ॉन्ट बदलता है।" % names.strip())
    if "kruti" not in names.lower().replace(" ", ""):
        return "unsure", ("इस फ़ॉन्ट के नाम में Kruti नहीं है (%s)। यह app Kruti Dev की "
                          "कुंजी-व्यवस्था मानता है; दूसरे फ़ॉन्ट से बना फ़ॉन्ट ग़लत "
                          "दिख सकता है।" % (names.strip() or "नाम नहीं"))
    return "ok", ""


class QueueWriter(io.TextIOBase):
    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s:
            self.q.put(("log", s))
        return len(s)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("%s %s" % (APP_TITLE, APP_VERSION))
        self.minsize(640, 460)
        self.q = queue.Queue()
        self.last_out = None

        self.src = tk.StringVar()
        self.out = tk.StringVar()
        self.family = tk.StringVar(value="KD Unicode 010")
        self.has_bundled = os.path.isfile(BUNDLED_LATIN)
        self.latin_mode = tk.StringVar(value="bundled" if self.has_bundled else "none")
        self.latin_file = tk.StringVar()

        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text="Kruti Dev फ़ॉन्ट (.ttf):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=self.src).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(f, text="चुनें…", command=self.pick_src).grid(row=0, column=2, **pad)

        ttk.Label(f, text="नया फ़ॉन्ट कहाँ सहेजें:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=self.out).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(f, text="चुनें…", command=self.pick_out).grid(row=1, column=2, **pad)

        ttk.Label(f, text="फ़ॉन्ट का नाम:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=self.family).grid(row=2, column=1, sticky="ew", **pad)

        lf = ttk.LabelFrame(f, text="अंग्रेज़ी (Latin) अक्षर", padding=6)
        lf.grid(row=3, column=0, columnspan=3, sticky="ew", **pad)
        lf.columnconfigure(1, weight=1)
        rb = ttk.Radiobutton(lf, text="साथ आया Arimo (SIL OFL 1.1)",
                             variable=self.latin_mode, value="bundled")
        rb.grid(row=0, column=0, columnspan=3, sticky="w")
        if not self.has_bundled:
            rb.state(["disabled"])
        ttk.Radiobutton(lf, text="दूसरी Latin फ़ाइल:", variable=self.latin_mode,
                        value="file").grid(row=1, column=0, sticky="w")
        ttk.Entry(lf, textvariable=self.latin_file).grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Button(lf, text="चुनें…", command=self.pick_latin).grid(row=1, column=2)
        ttk.Radiobutton(lf, text="अंग्रेज़ी अक्षर न जोड़ें", variable=self.latin_mode,
                        value="none").grid(row=2, column=0, columnspan=3, sticky="w")

        bf = ttk.Frame(f)
        bf.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)
        self.btn = ttk.Button(bf, text="Convert", command=self.start)
        self.btn.pack(side="left")
        self.btn_open = ttk.Button(bf, text="फ़ॉन्ट खोलें (Install)", command=self.open_font,
                                   state="disabled")
        self.btn_open.pack(side="left", padx=6)
        self.btn_dir = ttk.Button(bf, text="फ़ोल्डर खोलें", command=self.open_dir,
                                  state="disabled")
        self.btn_dir.pack(side="left")
        self.bar = ttk.Progressbar(bf, mode="indeterminate", length=160)
        self.bar.pack(side="right")

        self.log = tk.Text(f, height=10, wrap="word", state="disabled")
        self.log.grid(row=5, column=0, columnspan=3, sticky="nsew", **pad)
        f.rowconfigure(5, weight=1)

        ttk.Label(
            f, foreground="#a33",
            text="सूचना: Kruti Dev की आकृतियाँ उसके मूल स्वामी की हैं। बना फ़ॉन्ट केवल "
                 "निजी/आंतरिक उपयोग के लिए है, उसे आगे न बाँटें।",
            wraplength=600, justify="left",
        ).grid(row=6, column=0, columnspan=3, sticky="w", **pad)

        self.after(100, self.poll)

    # ---- फ़ाइल चुनना
    def pick_src(self):
        p = filedialog.askopenfilename(title="Kruti Dev फ़ॉन्ट चुनें",
                                       filetypes=[("TrueType फ़ॉन्ट", "*.ttf"), ("सभी", "*.*")])
        if p:
            self.src.set(p)
            stem = os.path.splitext(os.path.basename(p))[0]
            self.out.set(os.path.join(os.path.dirname(p), stem + "-Unicode.ttf"))

    def pick_out(self):
        p = filedialog.asksaveasfilename(title="नया फ़ॉन्ट कहाँ सहेजें",
                                         defaultextension=".ttf",
                                         filetypes=[("TrueType फ़ॉन्ट", "*.ttf")])
        if p:
            self.out.set(p)

    def pick_latin(self):
        p = filedialog.askopenfilename(title="Latin फ़ॉन्ट चुनें",
                                       filetypes=[("TrueType फ़ॉन्ट", "*.ttf"), ("सभी", "*.*")])
        if p:
            self.latin_file.set(p)
            self.latin_mode.set("file")

    # ---- बदलना
    def write_log(self, s):
        self.log.configure(state="normal")
        self.log.insert("end", s)
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        src, out, fam = self.src.get().strip(), self.out.get().strip(), self.family.get().strip()
        if not os.path.isfile(src):
            messagebox.showerror(APP_TITLE, "पहले Kruti Dev फ़ॉन्ट (.ttf) चुनें।")
            return
        if not out:
            messagebox.showerror(APP_TITLE, "नया फ़ॉन्ट कहाँ सहेजना है, यह चुनें।")
            return
        if os.path.abspath(out) == os.path.abspath(src):
            messagebox.showerror(APP_TITLE, "नया फ़ॉन्ट मूल फ़ाइल के ऊपर नहीं सहेजा जा सकता।")
            return
        if not fam:
            messagebox.showerror(APP_TITLE, "फ़ॉन्ट का नाम लिखें।")
            return
        verdict, info = check_source(src)
        if verdict == "bad":
            messagebox.showerror(APP_TITLE, info)
            return
        if verdict == "unsure" and not messagebox.askyesno(
                APP_TITLE, "%s\n\nफिर भी convert करें?" % info):
            return
        mode = self.latin_mode.get()
        latin = {"bundled": BUNDLED_LATIN, "file": self.latin_file.get().strip()}.get(mode)
        if mode == "file" and not os.path.isfile(latin or ""):
            messagebox.showerror(APP_TITLE, "Latin फ़ॉन्ट फ़ाइल नहीं मिली।")
            return
        self.btn.state(["disabled"])
        self.btn_open.state(["disabled"])
        self.btn_dir.state(["disabled"])
        self.bar.start(12)
        self.write_log("\n— %s → %s\n" % (os.path.basename(src), out))
        threading.Thread(target=self.work, args=(src, out, fam, latin), daemon=True).start()

    def work(self, src, out, fam, latin):
        w = QueueWriter(self.q)
        try:
            with redirect_stdout(w), redirect_stderr(w):
                kd.HALF_LIG.clear()
                kd.build(src, out, fam, latin)
            self.q.put(("done", out))
        except KeyError as e:
            self.q.put(("fail", "यह फ़ॉन्ट Kruti Dev कुंजी-व्यवस्था वाला नहीं लगता.\n%s" % e))
        except Exception:
            self.q.put(("fail", traceback.format_exc()))

    def poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self.write_log(val)
                    continue
                self.bar.stop()
                self.btn.state(["!disabled"])
                if kind == "done":
                    self.last_out = val
                    self.btn_open.state(["!disabled"])
                    self.btn_dir.state(["!disabled"])
                    messagebox.showinfo(APP_TITLE, "फ़ॉन्ट बन गया:\n%s\n\n'फ़ॉन्ट खोलें' से "
                                        "Install कर सकते हैं।" % val)
                else:
                    self.write_log("त्रुटि:\n%s\n" % val)
                    messagebox.showerror(APP_TITLE, "फ़ॉन्ट नहीं बन सका।\n\n%s" % val[-600:])
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def open_font(self):
        if self.last_out and os.path.isfile(self.last_out):
            os.startfile(self.last_out)  # Windows font viewer, उसमें Install बटन

    def open_dir(self):
        if self.last_out:
            os.startfile(os.path.dirname(os.path.abspath(self.last_out)))


if __name__ == "__main__":
    App().mainloop()
