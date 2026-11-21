import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

PROTECTED = {"Windows", "Program Files", "Program Files (x86)", "ProgramData", "$Recycle.Bin", "System Volume Information"}

class DriveKeepCleaner:
    def __init__(self, root):
        self.root = root
        root.title("DriveKeepCleaner")
        root.geometry("920x680")
        root.minsize(780, 560)
        root.configure(bg="#11151d")
        self.target = tk.StringVar()
        self.keep_paths = set()
        self.remove_items = []
        self.build_ui()

    def build_ui(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TButton", padding=7)
        style.configure("Treeview", rowheight=25)
        tk.Label(self.root, text="DriveKeep", font=("Segoe UI", 25, "bold"), bg="#11151d", fg="#eaf1ff").pack(anchor="w", padx=22, pady=4)
        tk.Label(self.root, text="Keep what matters. Clean the rest.", font=("Segoe UI", 11), bg="#11151d", fg="#8c9ab1").pack(anchor="w", padx=24, pady=12)

        bar = tk.Frame(self.root, bg="#1a202b")
        bar.pack(fill="x", padx=16, pady=8)
        tk.Label(bar, text="Target drive/folder:", bg="#1a202b", fg="white").pack(side="left", padx=10, pady=10)
        ttk.Entry(bar, textvariable=self.target, width=55).pack(side="left", padx=8, pady=8)
        ttk.Button(bar, text="Browse…", command=self.choose_target).pack(side="left", padx=8, pady=8)

        controls = tk.Frame(self.root, bg="#11151d")
        controls.pack(fill="x", padx=12, pady=8)
        ttk.Button(controls, text="Add keep file/folder", command=self.add_keep).pack(side="left", padx=5, pady=5)
        ttk.Button(controls, text="Remove selected keep item", command=self.remove_keep).pack(side="left", padx=5, pady=5)
        ttk.Button(controls, text="Scan target", command=self.scan).pack(side="left", padx=5, pady=5)

        tk.Label(self.root, text="Keep list (items here will be preserved)", bg="#11151d", fg="#b8c8e8").pack(anchor="w", padx=22, pady=4)
        self.keepbox = tk.Listbox(self.root, height=5, bg="#1a202b", fg="#eaf1ff", selectbackground="#3468c9", borderwidth=0)
        self.keepbox.pack(fill="x", padx=18, pady=8)
        tk.Label(self.root, text="Deletion preview", bg="#11151d", fg="#b8c8e8").pack(anchor="w", padx=22, pady=4)
        self.tree = ttk.Treeview(self.root, columns=("path", "type", "action"), show="headings")
        self.tree.heading("path", text="Item")
        self.tree.heading("type", text="Type")
        self.tree.heading("action", text="Action")
        self.tree.column("path", width=580)
        self.tree.column("type", width=100)
        self.tree.column("action", width=120)
        self.tree.pack(fill="both", expand=True, padx=18, pady=8)
        bottom = tk.Frame(self.root, bg="#11151d")
        bottom.pack(fill="x", padx=12, pady=8)
        ttk.Button(bottom, text="Preview cleanup", command=self.scan).pack(side="left", padx=5, pady=5)
        ttk.Button(bottom, text="Move unchecked to Recycle Bin", command=self.clean).pack(side="right", padx=5, pady=5)
        tk.Label(self.root, text="Review the preview carefully. Cleanup sends items to the Recycle Bin.", bg="#11151d", fg="#7f8da6").pack(anchor="w", padx=22, pady=12)

    def choose_target(self):
        path = filedialog.askdirectory(title="Select target drive or folder")
        if path:
            self.target.set(path)
            self.scan()

    def add_keep(self):
        path = filedialog.askopenfilename(title="Choose a file to keep")
        if not path:
            path = filedialog.askdirectory(title="Choose a folder to keep")
        if path and path not in self.keep_paths:
            self.keep_paths.add(path)
            self.refresh_keep_list()
            self.scan()

    def remove_keep(self):
        selection = self.keepbox.curselection()
        if selection:
            self.keep_paths.discard(self.keepbox.get(selection[0]))
            self.refresh_keep_list()
            self.scan()

    def refresh_keep_list(self):
        self.keepbox.delete(0, tk.END)
        for path in sorted(self.keep_paths):
            self.keepbox.insert(tk.END, path)

    def is_protected(self, root, item):
        relative = item.relative_to(root)
        if any(part in PROTECTED for part in relative.parts):
            return True
        if root == Path(root.anchor) and root.anchor.upper().startswith("C:"):
            return True
        return False

    def is_kept(self, item):
        item = item.resolve()
        for saved in self.keep_paths:
            kept = Path(saved).resolve()
            if item == kept or kept in item.parents:
                return True
        return False

    def scan(self):
        self.tree.delete(*self.tree.get_children())
        self.remove_items = []
        raw = self.target.get().strip()
        if not raw:
            messagebox.showinfo("Select target", "Choose a drive or folder first.")
            return
        root = Path(raw).resolve()
        if not root.is_dir():
            messagebox.showerror("Invalid target", "Selected target is not a valid folder/drive.")
            return
        try:
            for child in root.iterdir():
                kept = self.is_kept(child)
                protected = self.is_protected(root, child)
                action = "KEEP" if kept else ("PROTECTED" if protected else "REMOVE")
                item_type = "Folder" if child.is_dir() else "File"
                self.tree.insert("", tk.END, values=(str(child), item_type, action))
                if action == "REMOVE":
                    self.remove_items.append(child)
        except OSError as exc:
            messagebox.showwarning("Scan issue", f"Some items could not be scanned:\n{exc}")

    def clean(self):
        if not self.remove_items:
            messagebox.showinfo("Nothing to clean", "Scan first. No unchecked items are queued for removal.")
            return
        if send2trash is None:
            messagebox.showerror("Unavailable", "Recycle Bin support is missing in this build.")
            return
        listed = "\n".join(str(p) for p in self.remove_items[:12])
        if len(self.remove_items) > 12:
            listed += f"\n…and {len(self.remove_items) - 12} more"
        if not messagebox.askyesno("Confirm cleanup", f"Send {len(self.remove_items)} unchecked item(s) to the Recycle Bin?\n\n{listed}\n\nContinue?"):
            return
        success = 0
        failed = []
        root = Path(self.target.get()).resolve()
        for item in self.remove_items:
            try:
                if self.is_protected(root, item) or self.is_kept(item):
                    continue
                send2trash(str(item))
                success += 1
            except Exception as exc:
                failed.append(f"{item}: {exc}")
        messagebox.showinfo("Cleanup complete", f"Moved {success} item(s) to Recycle Bin.\nFailed: {len(failed)}")
        self.scan()

if __name__ == "__main__":
    window = tk.Tk()
    DriveKeepCleaner(window)
    window.mainloop()
