"""
AppSweep - Free Windows Uninstaller with Residual Cleaner
开源免费 Windows 卸载工具，支持残留清理
"""
import os
import sys
import shutil
import winreg
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ---------------- i18n ----------------
LANG = {
    "zh": {
        "title": "AppSweep - 免费卸载工具",
        "refresh": "刷新列表",
        "uninstall": "卸载",
        "scan_residual": "扫描残留",
        "clean_residual": "清理选中残留",
        "lang": "EN",
        "col_name": "软件名称",
        "col_publisher": "发布者",
        "col_size": "大小",
        "warning": "⚠️ 风险提示\n\n卸载软件可能导致：\n• 软件无法正常恢复\n• 注册表项被修改\n• 相关文件被删除\n\n请确认你知道自己在做什么。\n本工具按\"原样\"提供，作者不对数据丢失负责。",
        "residual_title": "残留扫描结果",
        "residual_reg": "注册表残留",
        "residual_folder": "文件夹残留",
        "residual_shortcut": "快捷方式残留",
        "no_residual": "未发现明显残留",
        "confirm_clean": "确定清理选中的残留项？此操作不可撤销。",
        "cleaned": "清理完成",
        "uninstall_start": "正在启动卸载程序...",
        "select_one": "请先选中一个软件",
        "scan_done": "扫描完成",
    },
    "en": {
        "title": "AppSweep - Free Uninstaller",
        "refresh": "Refresh",
        "uninstall": "Uninstall",
        "scan_residual": "Scan Residuals",
        "clean_residual": "Clean Selected",
        "lang": "中文",
        "col_name": "Name",
        "col_publisher": "Publisher",
        "col_size": "Size",
        "warning": "⚠️ WARNING\n\nUninstalling software may:\n• Make software unrecoverable\n• Modify registry entries\n• Delete related files\n\nPlease make sure you know what you are doing.\nThis tool is provided \"as-is\" and the author is not responsible for data loss.",
        "residual_title": "Residual Scan Results",
        "residual_reg": "Registry Residuals",
        "residual_folder": "Folder Residuals",
        "residual_shortcut": "Shortcut Residuals",
        "no_residual": "No obvious residuals found",
        "confirm_clean": "Are you sure to clean selected items? This cannot be undone.",
        "cleaned": "Cleaned",
        "uninstall_start": "Starting uninstaller...",
        "select_one": "Please select a software first",
        "scan_done": "Scan complete",
    }
}

LANG_KEY = "zh"

def t(key):
    return LANG[LANG_KEY].get(key, key)


# ---------------- registry scan ----------------
def get_installed_apps():
    apps = []
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for root, path in roots:
        try:
            key = winreg.OpenKey(root, path)
        except OSError:
            continue
        i = 0
        while True:
            try:
                subname = winreg.EnumKey(key, i)
                i += 1
            except OSError:
                break
            try:
                sub = winreg.OpenKey(key, subname)
                name, _ = winreg.QueryValueEx(sub, "DisplayName")
                try:
                    publisher, _ = winreg.QueryValueEx(sub, "Publisher")
                except OSError:
                    publisher = ""
                try:
                    size, _ = winreg.QueryValueEx(sub, "EstimatedSize")
                    size_str = f"{size // 1024} MB"
                except OSError:
                    size_str = ""
                try:
                    uninst, _ = winreg.QueryValueEx(sub, "UninstallString")
                except OSError:
                    uninst = ""
                try:
                    install_loc, _ = winreg.QueryValueEx(sub, "InstallLocation")
                except OSError:
                    install_loc = ""
                apps.append({
                    "name": name,
                    "publisher": publisher,
                    "size": size_str,
                    "uninstall": uninst,
                    "location": install_loc,
                    "reg_path": f"{root}\\{path}\\{subname}",
                })
            except OSError:
                continue
    # dedupe by name
    seen = set()
    out = []
    for a in apps:
        if a["name"] not in seen:
            seen.add(a["name"])
            out.append(a)
    out.sort(key=lambda x: x["name"].lower())
    return out


# ---------------- residual scan ----------------
def scan_residuals(app_name):
    found = {"reg": [], "folder": [], "shortcut": []}

    # registry residuals: search uninstall keys for matching name
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for root, path in roots:
        try:
            key = winreg.OpenKey(root, path)
        except OSError:
            continue
        i = 0
        while True:
            try:
                subname = winreg.EnumKey(key, i)
                i += 1
            except OSError:
                break
            try:
                sub = winreg.OpenKey(key, subname)
                name, _ = winreg.QueryValueEx(sub, "DisplayName")
                if app_name.lower() in name.lower():
                    found["reg"].append(f"{root}\\{path}\\{subname}")
            except OSError:
                continue

    # folder residuals
    candidates = []
    for base in [os.environ.get("ProgramFiles", ""),
                 os.environ.get("ProgramFiles(x86)", ""),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), ""),
                 os.path.join(os.environ.get("APPDATA", ""), "")]:
        if not base or not os.path.isdir(base):
            continue
        try:
            for entry in os.listdir(base):
                if app_name.lower() in entry.lower():
                    candidates.append(os.path.join(base, entry))
        except OSError:
            pass
    found["folder"] = candidates

    # shortcut residuals
    sc_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
    ]
    for d in sc_dirs:
        if not os.path.isdir(d):
            continue
        for root_dir, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(".lnk") and app_name.lower() in f.lower():
                    found["shortcut"].append(os.path.join(root_dir, f))
    return found


# ---------------- GUI ----------------
class App:
    def __init__(self, root):
        self.root = root
        self.apps = []
        self.residuals = {}
        self._build_ui()
        self.refresh()
        messagebox.showinfo(t("title"), t("warning"))

    def _build_ui(self):
        self.root.title(t("title"))
        self.root.geometry("860x560")

        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(top, text=t("refresh"), command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(top, text=t("uninstall"), command=self.do_uninstall).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=t("scan_residual"), command=self.do_scan).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=t("clean_residual"), command=self.do_clean).pack(side=tk.LEFT, padx=4)
        self.lang_btn = ttk.Button(top, text=t("lang"), command=self.toggle_lang)
        self.lang_btn.pack(side=tk.RIGHT)

        cols = ("name", "publisher", "size")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        self.tree.heading("name", text=t("col_name"))
        self.tree.heading("publisher", text=t("col_publisher"))
        self.tree.heading("size", text=t("col_size"))
        self.tree.column("name", width=380)
        self.tree.column("publisher", width=260)
        self.tree.column("size", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.status = ttk.Label(self.root, text="", anchor=tk.W)
        self.status.pack(fill=tk.X, padx=8, pady=4)

    def toggle_lang(self):
        global LANG_KEY
        LANG_KEY = "en" if LANG_KEY == "zh" else "zh"
        self.root.title(t("title"))
        self.tree.heading("name", text=t("col_name"))
        self.tree.heading("publisher", text=t("col_publisher"))
        self.tree.heading("size", text=t("col_size"))
        self.lang_btn.config(text=t("lang"))

    def refresh(self):
        self.status.config(text=t("scan_done") + "...")
        self.root.update()
        self.apps = get_installed_apps()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for a in self.apps:
            self.tree.insert("", tk.END, values=(a["name"], a["publisher"], a["size"]))
        self.status.config(text=f"{len(self.apps)} " + t("scan_done"))

    def _selected_name(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(t("title"), t("select_one"))
            return None
        return self.tree.item(sel[0])["values"][0]

    def do_uninstall(self):
        name = self._selected_name()
        if not name:
            return
        app = next((a for a in self.apps if a["name"] == name), None)
        if not app or not app["uninstall"]:
            messagebox.showwarning(t("title"), t("select_one"))
            return
        self.status.config(text=t("uninstall_start") + name)
        try:
            subprocess.Popen(app["uninstall"], shell=True)
        except Exception as e:
            messagebox.showerror(t("title"), str(e))

    def do_scan(self):
        name = self._selected_name()
        if not name:
            return
        self.residuals = scan_residuals(name)
        items = []
        for r in self.residuals["reg"]:
            items.append(("REG", r))
        for f in self.residuals["folder"]:
            items.append(("DIR", f))
        for s in self.residuals["shortcut"]:
            items.append(("LNK", s))
        if not items:
            messagebox.showinfo(t("residual_title"), t("no_residual"))
            return
        win = tk.Toplevel(self.root)
        win.title(t("residual_title") + " - " + name)
        win.geometry("700x380")
        self.res_tree = ttk.Treeview(win, columns=("type", "path"), show="headings")
        self.res_tree.heading("type", text="Type")
        self.res_tree.heading("path", text="Path")
        self.res_tree.column("type", width=80)
        self.res_tree.column("path", width=600)
        self.res_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for typ, p in items:
            self.res_tree.insert("", tk.END, values=(typ, p))

    def do_clean(self):
        if not hasattr(self, "res_tree") or not self.res_tree:
            messagebox.showinfo(t("residual_title"), t("no_residual"))
            return
        sel = self.res_tree.selection()
        if not sel:
            messagebox.showinfo(t("residual_title"), t("no_residual"))
            return
        if not messagebox.askyesno(t("title"), t("confirm_clean")):
            return
        for s in sel:
            typ, path = self.res_tree.item(s)["values"]
            try:
                if typ == "DIR":
                    shutil.rmtree(path, ignore_errors=True)
                elif typ == "LNK":
                    os.remove(path)
                elif typ == "REG":
                    # path like HKEY_LOCAL_MACHINE\SOFTWARE\...
                    parts = path.split("\\", 1)
                    root_name = parts[0]
                    root_key = winreg.HKEY_LOCAL_MACHINE if "LOCAL" in root_name else winreg.HKEY_CURRENT_USER
                    winreg.DeleteKey(root_key, parts[1])
            except Exception:
                pass
            self.res_tree.delete(s)
        messagebox.showinfo(t("title"), t("cleaned"))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
