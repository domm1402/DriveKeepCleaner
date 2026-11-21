import os, sys, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
try:
    from send2trash import send2trash
except ImportError:
    send2trash=None

APP_TITLE="DriveKeepCleaner"
PROTECTED_NAMES={"Windows","Program Files","Program Files (x86)","ProgramData","$Recycle.Bin","System Volume Information"}
class App:
 def __init__(self,root):
  self.root=root; root.title("DriveKeepCleaner"); root.geometry("900x650"); root.minsize(760,560)
  root.configure(bg="#11151d")
  self.target=tk.StringVar(); self.keeps=set(); self.items=[]
  self.build()
 def build(self):
  style=ttk.Style(); style.theme_use("clam")
  style.configure("TButton",padding=7); style.configure("Treeview",rowheight=25)
  tk.Label(self.root,text="DriveKeep",font=("Segoe UI",25,"bold"),bg="#11151d",fg="#eaf1ff").pack(anchor="w",pad=(22,4))
  tk.Label(self.root,text="Keep what matters. Clean the rest.",font=("Segoe UI",11),bg="#11151d",fg="#8c9ab1").pack(anchor="w",pad=(24,12))
  bar=tk.Frame(self.root,bg="#1a202b"); bar.pack(fill="x",pad=16)
  tk.Label(bar,text="Target drive/folder:",bg="#1a202b",fg="white").pack(side="left",pad=10)
  ttk.Entry(bar,textvariable=self.target,width=55).pack(side="left",pad=8)
  ttk.Button(bar,text="Browse…",command=self.choose).pack(side="left",pad=8)
  controls=tk.Frame(self.root,bg="#11151d"); controls.pack(fill="x",pad=12)
  ttk.Button(controls,text="Add keep item",command=self.add_keep).pack(side="left",pad=5)
  ttk.Button(controls,text="Remove selected keep item",command=self.remove_keep).pack(side="left",pad=5)
  ttk.Button(controls,text="Scan target",command=self.scan).pack(side="left",pad=5)
  tk.Label(self.root,text="Keep list (items here will be preserved)",bg="#11151d",fg="#b8c8e8").pack(anchor="w",pad=(22,4))
  self.keepbox=tk.Listbox(self.root,height=5,bg="#1a202b",fg="#eaf1ff",selectbackground="#3468c9",borderwidth=0)
  self.keepbox.pack(fill="x",pad=(18,8))
  tk.Label(self.root,text="Deletion preview (everything not covered by keep list)",bg="#11151d",fg="#b8c8e8").pack(anchor="w",pad=(22,4))
  cols=("path","type","status")
  self.tree=ttk.Treeview(self.root,columns=cols,show="headings")
  self.tree.heading("path",text="Item"); self.tree.heading("type",text="Type"); self.tree.heading("status",text="Action")
  self.tree.column("path",width=580); self.tree.column("type",width=100); self.tree.column("status",width=120)
  self.tree.pack(fill="both",expand=True,padx=18,pady=8)
  bottom=tk.Frame(self.root,bg="#11151d"); bottom.pack(fill="x",pad=12)
  ttk.Button(bottom,text="Preview cleanup",command=self.scan).pack(side="left",pad=5)
  ttk.Button(bottom,text="Move unchecked to Recycle Bin",command=self.clean).pack(side="right",pad=5)
  tk.Label(self.root,text="System folders are blocked. Cleanup uses Recycle Bin where supported; preview before proceeding.",bg="#11151d",fg="#7f8da6").pack(anchor="w",pad=(22,12))
 def choose(self):
  p=filedialog.askdirectory(title="Select target folder/drive")
  if p: self.target.set(p); self.scan()
 def add_keep(self):
  p=filedialog.askopenfilename(title="Choose item to keep")
  if not p: p=filedialog.askdirectory(title="Or choose a folder to keep")
  if p and p not in self.keeps:
   self.keeps.add(p); self.refresh_keep(); self.scan()
 def remove_keep(self):
  sel=self.keepbox.curselection()
  if sel:
   value=self.keepbox.get(sel[0]); self.keeps.discard(value); self.refresh_keep(); self.scan()
 def refresh_keep(self):
  self.keepbox.delete(0,tk.END)
  for p in sorted(self.keeps): self.keepbox.insert(tk.END,p)
 def blocked(self,root,item):
  rel=item.relative_to(root)
  if root == Path(root.anchor) and rel.parts and rel.parts[0] in PROTECTED_NAMES: return True
  if any(part in PROTECTED_NAMES for part in rel.parts): return True
  if root == Path(root.anchor) and str(root).lower().startswith("c:"): return True
  return False
 def scan(self):
  self.tree.delete(*self.tree.get_children()); self.items=[]
  root=Path(self.target.get()).resolve()
  if not root.exists() or not root.is_dir(): return
  try:
   for child in root.iterdir():
    keep=any(Path(k).resolve()==child.resolve() or Path(k).resolve() in child.resolve().parents for k in self.keeps if Path(k).exists())
    protected=self.blocked(root,child)
    status="KEEP" if keep else ("PROTECTED" if protected else "REMOVE")
    typ="Folder" if child.is_dir() else "File"
    self.tree.insert("",tk.END,values=(str(child),typ,status))
    if status=="REMOVE": self.items.append(child)
  except PermissionError: messagebox.showwarning("Permission","Some items cannot be scanned due to permissions.")
 def clean(self):
  if not self.items: messagebox.showinfo("Nothing to clean","Scan first. No removable top-level items found."); return
  if send2trash is None: messagebox.showerror("Missing dependency","Recycle Bin support missing. This build should include send2trash."); return
  names="\n".join(str(p) for p in self.items[:15])
  if len(self.items)>15: names+=f"\n…and {len(self.items)-15} more"
  if not messagebox.askyesno("Confirm cleanup",f"Send {len(self.items)} unchecked item(s) to Recycle Bin?\n\n{names}\n\nThis action can be difficult to undo. Continue?"): return
  errors=[]; count=0
  for p in self.items:
   try:
    if self.blocked(Path(self.target.get()).resolve(),p): continue
    send2trash(str(p)); count+=1
   except Exception as e: errors.append(f"{p}: {e}")
  messagebox.showinfo("Cleanup finished",f"Sent {count} item(s) to Recycle Bin.\nErrors: {len(errors)}")
  self.scan()
if __name__=="__main__":
 root=tk.Tk(); App(root); root.mainloop()
