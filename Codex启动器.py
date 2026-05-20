import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os, subprocess, threading, time, json, pathlib, re

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
MODEL_DIR = r'D:\AI_models\codex_model'
LLAMA_DIR = r'D:\llama-cpp\llama-b9245-bin-win-cuda-12.4-x64'
LLAMA_SERVER = os.path.join(LLAMA_DIR, 'llama-server.exe')
CONFIG_FILE = SCRIPT_DIR / 'config.json'
DEFAULT_CTX = '131072'
DEFAULT_PORT = '8081'

cfg = {'model': '', 'ctx_size': DEFAULT_CTX, 'port': DEFAULT_PORT, 'custom_models': []}
session_start_time = None
pending_new_session = False

def load_config():
    global cfg
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception:
            pass

def save_config():
    cfg['model'] = entry_model.get()
    cfg['ctx_size'] = ctx_var.get()
    cfg['port'] = port_var.get()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def scan_models():
    models = []
    if not os.path.isdir(MODEL_DIR):
        return models
    for f in os.listdir(MODEL_DIR):
        if f.lower().endswith('.gguf'):
            fp = os.path.join(MODEL_DIR, f)
            size_mb = os.path.getsize(fp) / (1024*1024)
            models.append(('auto', fp, f, size_mb))
    models.sort(key=lambda x: -x[3])
    return models

def get_all_models():
    auto = scan_models()
    custom = []
    valid_custom = []
    for m in cfg.get('custom_models', []):
        if os.path.isfile(m):
            size_mb = os.path.getsize(m) / (1024*1024)
            custom.append(('custom', m, os.path.basename(m), size_mb))
        else:
            valid_custom.append(m)
    cfg['custom_models'] = valid_custom
    return auto + custom

def get_llama_pid():
    try:
        r = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq llama-server.exe', '/NH', '/FO', 'CSV'],
            capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.strip().split('\n'):
            parts = line.split(',')
            if len(parts) >= 2 and 'llama-server.exe' in parts[0]:
                return parts[1].strip()
    except Exception:
        pass
    return None

def stop_llama():
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'llama-server.exe'], capture_output=True, timeout=10)
        time.sleep(0.3)
    except Exception:
        pass

def start_llama():
    global session_start_time, pending_new_session
    model = entry_model.get()
    if not model or not os.path.isfile(model):
        messagebox.showwarning('提示', '请先选择有效的模型')
        return
    ctx = ctx_var.get()
    port = port_var.get()
    stop_llama()
    time.sleep(0.5)
    session_start_time = None
    pending_new_session = False
    try:
        log_wid.configure(state=tk.NORMAL)
        log_wid.insert(tk.END, f'[启动] {os.path.basename(model)} | ctx={ctx} | port={port}\n')
        log_wid.see(tk.END)
        log_wid.configure(state=tk.DISABLED)

        cmd = [LLAMA_SERVER, '-m', model, '--host', '0.0.0.0', '--port', port, '--jinja', '--ctx-size', ctx]
        proc = subprocess.Popen(cmd, cwd=LLAMA_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)

        def read_out():
            global session_start_time
            for line in proc.stdout:
                log_wid.configure(state=tk.NORMAL)
                log_wid.insert(tk.END, line)
                log_wid.see(tk.END)
                log_wid.configure(state=tk.DISABLED)

                # 新问题唯一可靠的标志
                if 'cache state: 0 prompts, 0.000 MiB' in line:
                    session_start_time = time.time()
                    root.after(0, lambda: lbl_latency.config(text='处理中...', fg=TEXT_M))

                # 提取 total time，更新总耗时
                match = re.search(r'total time =\s+([\d.]+)\s*ms', line)
                if match and session_start_time:
                    total_elapsed = time.time() - session_start_time
                    root.after(0, lambda t=total_elapsed: lbl_latency.config(text=f'总耗时: {t:.1f} 秒', fg=SUCCESS))
        threading.Thread(target=read_out, daemon=True).start()  # ← 加上这行
        time.sleep(2)

        pid = get_llama_pid()
        if pid:
            lbl_status.config(text=f'运行中 (PID: {pid}) | 端口: {port}', fg=SUCCESS)
            btn_stop.config(state=tk.NORMAL)
        else:
            lbl_status.config(text='启动失败', fg=WARNING)

    except Exception as e:
        lbl_status.config(text=f'错误: {e}', fg=DANGER)

def do_stop():
    global session_start_time, pending_new_session
    stop_llama()
    session_start_time = None
    pending_new_session = False
    lbl_status.config(text='已停止', fg=WARNING)
    lbl_latency.config(text='等待请求...', fg=TEXT_M)
    btn_stop.config(state=tk.DISABLED)

def refresh_display():
    all_models = get_all_models()
    names = []
    for t, fp, name, size in all_models:
        s = f'{size:.0f}MB' if size < 1024 else f'{size/1024:.1f}GB'
        names.append(f'[{t.upper()}] {name} ({s})')
    combo['values'] = names
    listbox.delete(0, tk.END)
    for t, fp, name, size in all_models:
        src = '目录' if t == 'auto' else '添加'
        s = f'{size:.0f}MB' if size < 1024 else f'{size/1024:.1f}GB'
        listbox.insert(tk.END, f'{name}  [{src}]  {s}')
    restore_selection(all_models)

def restore_selection(all_models):
    current = entry_model.get()
    for i, (_, fp, _, _) in enumerate(all_models):
        if fp == current:
            combo.current(i)
            return

def on_select(*args):
    idx = combo.current()
    all_models = get_all_models()
    if 0 <= idx < len(all_models):
        _, fp, name, size = all_models[idx]
        s = f'{size:.0f}MB' if size < 1024 else f'{size/1024:.1f}GB'
        lbl_info.config(text=f'{name}  |  {s}')
        entry_model.set(fp)

def add_model():
    path = filedialog.askopenfilename(title='添加模型', filetypes=[('GGUF', '*.gguf'), ('所有文件', '*.*')])
    if not path:
        return
    for _, fp, _, _ in get_all_models():
        if fp == path:
            messagebox.showinfo('提示', '已存在')
            return
    cfg.setdefault('custom_models', []).append(path)
    save_config()
    refresh_display()
    entry_model.set(path)

def remove_model(event=None):
    sel = listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    all_models = get_all_models()
    if idx >= len(all_models):
        return
    t, fp, _, _ = all_models[idx]
    if t == 'auto':
        messagebox.showinfo('提示', '目录模型不能移除')
        return
    cfg['custom_models'] = [m for m in cfg.get('custom_models', []) if m != fp]
    save_config()
    refresh_display()

def on_close():
    save_config()
    root.destroy()


# === GUI ===
root = tk.Tk()
root.title('Codex 本地模型启动器')
root.geometry('720x420')
root.configure(bg='#1E1E2E')

BG = '#1E1E2E'
SURFACE = '#313244'
ACCENT = '#89B7FA'
SUCCESS = '#A6E3A1'
WARNING = '#FAB387'
DANGER = '#F38BA8'
TEXT_P = '#CDD6F4'
TEXT_S = '#A6ADC8'
TEXT_M = '#6C7086'

load_config()

# 标题栏
frame_t = tk.Frame(root, bg=BG)
frame_t.pack(fill='x', padx=18, pady=10)
tk.Label(frame_t, text='Codex 本地模型启动器', bg=BG, fg=ACCENT, font=('', 16, 'bold')).pack(side='left')
tk.Button(frame_t, text='刷新', bg=SURFACE, fg=ACCENT, font=('', 9), relief='flat', command=refresh_display).pack(side='right')

# 状态 + 耗时
lbl_status = tk.Label(root, text='已停止', bg=BG, fg=TEXT_M, font=('', 10))
lbl_status.pack(fill='x', padx=18, pady=(0, 2))
lbl_latency = tk.Label(root, text='等待请求...', bg=BG, fg=TEXT_M, font=('', 10, 'bold'))
lbl_latency.pack(fill='x', padx=18, pady=(0, 6))

# 主区域
frame_m = tk.Frame(root, bg=BG)
frame_m.pack(fill='both', expand=True, padx=18, pady=4)

# 左：选择 + 参数
frame_l = tk.Frame(frame_m, bg=BG)
frame_l.pack(side='left', fill='both', expand=True, padx=(0, 8))

tk.Label(frame_l, text='选择模型:', bg=BG, fg=TEXT_S, font=('', 9)).pack(anchor='w')
entry_model = tk.StringVar()
combo = ttk.Combobox(frame_l, textvariable=entry_model, font=('', 9), state='readonly', width=44)
combo.pack(fill='x', pady=(0, 2))
combo.bind('<<ComboboxSelected>>', on_select)

lbl_info = tk.Label(frame_l, text='', bg=BG, fg=TEXT_M, font=('', 8))
lbl_info.pack(anchor='w', pady=(0, 6))

tk.Label(frame_l, text='参数:', bg=BG, fg=TEXT_S, font=('', 9)).pack(anchor='w')
frm_param = tk.Frame(frame_l, bg=BG)
frm_param.pack(fill='x', pady=(2, 6))
tk.Label(frm_param, text='ctx:', bg=BG, fg=TEXT_S, font=('', 8)).pack(side='left')
ctx_var = tk.StringVar(value=cfg.get('ctx_size', DEFAULT_CTX))
tk.Entry(frm_param, textvariable=ctx_var, width=12, bg='#181825', fg=TEXT_P, font=('Consolas', 8)).pack(side='left', padx=(4, 10))
tk.Label(frm_param, text='端口:', bg=BG, fg=TEXT_S, font=('', 8)).pack(side='left')
port_var = tk.StringVar(value=cfg.get('port', DEFAULT_PORT))
tk.Entry(frm_param, textvariable=port_var, width=8, bg='#181825', fg=TEXT_P, font=('Consolas', 8)).pack(side='left', padx=4)

tk.Button(frame_l, text='+ 添加模型', bg=SURFACE, fg=ACCENT, font=('', 9), relief='flat', command=add_model).pack(anchor='w')

# 右：模型列表
frame_r = tk.Frame(frame_m, bg=BG)
frame_r.pack(side='right', fill='both', padx=(8, 0))
tk.Label(frame_r, text='模型列表 (双击移除已添加):', bg=BG, fg=TEXT_S, font=('', 9)).pack(anchor='w')
listbox = tk.Listbox(frame_r, bg=SURFACE, fg=TEXT_P, font=('Consolas', 8), height=6, selectbackground=ACCENT, selectforeground=BG, relief='flat', exportselection=False)
listbox.pack(fill='both', expand=True)
listbox.bind('<Double-Button-1>', remove_model)

# 按钮
frame_b = tk.Frame(root, bg=BG)
frame_b.pack(fill='x', padx=18, pady=8)
tk.Button(frame_b, text='启动', bg=SURFACE, fg=SUCCESS, font=('', 10, 'bold'), relief='flat', command=start_llama).pack(side='left', fill='x', expand=True, padx=(0, 6))
btn_stop = tk.Button(frame_b, text='停止', bg=SURFACE, fg=DANGER, font=('', 10, 'bold'), relief='flat', state=tk.DISABLED, command=do_stop)
btn_stop.pack(side='left', fill='x', expand=True)

# 日志
frame_g = tk.Frame(root, bg=BG)
frame_g.pack(fill='both', expand=True, padx=18, pady=(4, 8))
tk.Label(frame_g, text='日志:', bg=BG, fg=TEXT_S, font=('', 9)).pack(anchor='w')
log_wid = tk.Text(frame_g, bg='#181825', fg=TEXT_S, font=('Consolas', 8), height=4, relief='flat', insertbackground=TEXT_P, state=tk.DISABLED)
log_wid.pack(fill='both', expand=True)

refresh_display()

def refresh_status():
    pid = get_llama_pid()
    if pid:
        lbl_status.config(text=f'运行中 (PID: {pid})', fg=SUCCESS)
        btn_stop.config(state=tk.NORMAL)
    else:
        lbl_status.config(text='已停止', fg=TEXT_M)
        btn_stop.config(state=tk.DISABLED)
    root.after(2000, refresh_status)
refresh_status()

root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()