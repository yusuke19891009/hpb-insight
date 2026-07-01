import tkinter as tk
from tkinter import messagebox

from scraper import open_hotpepper


def start_scraping(url_entry, status):

    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning(
            "入力エラー",
            "URLを入力してください"
        )
        return

    status.config(text="店舗情報取得中...")
    status.update()

    try:

        shop_name = open_hotpepper(url)

        status.config(
            text=f"取得成功：{shop_name}"
        )

    except Exception as e:

        status.config(text="エラー")

        messagebox.showerror(
            "エラー",
            str(e)
        )


def run_app():

    root = tk.Tk()

    root.title("HPB Insight v1.0")

    root.geometry("800x500")

    tk.Label(
        root,
        text="HPB Insight",
        font=("Yu Gothic UI", 22, "bold")
    ).pack(pady=20)

    tk.Label(
        root,
        text="HotPepper URL"
    ).pack()

    url_entry = tk.Entry(
        root,
        width=90
    )

    url_entry.pack(pady=10)

    status = tk.Label(
        root,
        text="待機中"
    )

    tk.Button(
        root,
        text="開始",
        width=20,
        height=2,
        command=lambda: start_scraping(
            url_entry,
            status
        )
    ).pack(pady=15)

    status.pack()

    root.mainloop()