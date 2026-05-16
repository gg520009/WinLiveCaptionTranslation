import os
import time
import threading
import tkinter as tk
from pynput import mouse, keyboard
import pyautogui
from PIL import ImageGrab
import pytesseract
import urllib.request
import urllib.parse
import json
import datetime
import sys
import subprocess

# ==========================================
# 配置说明:
# 1. 请确保安装了 Tesseract-OCR (https://github.com/UB-Mannheim/tesseract/wiki)
# 2. 根据你的安装路径，修改下面的 tesseract_cmd 路径。
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 单词本保存路径（保存在桌面上）
VOCAB_FILE = os.path.join(os.path.expanduser('~'), 'Desktop', 'vocabulary_book.txt')
saved_words = set()

def load_vocab():
    """程序启动时读取已存在的单词本，避免重复记录"""
    if os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if ' : ' in line:
                    word = line.split(' : ')[0].strip()
                    saved_words.add(word.lower())

def save_to_vocab(word, translation):
    """将新查询的单词保存到单词本中"""
    word_lower = word.lower()
    if word_lower not in saved_words:
        with open(VOCAB_FILE, 'a', encoding='utf-8') as f:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 将多行翻译合并为单行，方便在 TXT 中阅读
            clean_trans = translation.replace('\n', ' | ')
            f.write(f"{word} : {clean_trans}  [{now}]\n")
        saved_words.add(word_lower)
        print(f"[{word}] 已自动加入生词本！")

translation_cache = {}

def get_youdao_translation(word):
    """使用有道词典的 Suggest API，专门用于查单词"""
    word_lower = word.lower()
    if word_lower in translation_cache:
        return translation_cache[word_lower]
        
    try:
        url = f"http://dict.youdao.com/suggest?num=1&doctype=json&q={urllib.parse.quote(word)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('result', {}).get('code') == 200:
                entries = data.get('data', {}).get('entries', [])
                if entries:
                    trans = entries[0].get('explain', '')
                    translation_cache[word_lower] = trans
                    return trans
    except Exception as e:
        pass
    return ""

class HighlightBox:
    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.wm_attributes("-topmost", True)
        
        # 设置透明色掩码，使窗口中间透明，只保留边框
        trans_color = '#000001'
        self.win.wm_attributes("-transparentcolor", trans_color)
        self.win.config(bg=trans_color)
        
        # 绘制绿色高亮边框，包裹整个单词
        self.frame = tk.Frame(self.win, bg=trans_color, highlightbackground="#00FF00", highlightthickness=2)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.win.withdraw() # 初始隐藏
        self.is_visible = False

    def show(self, x, y, w, h):
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.deiconify()
        self.is_visible = True

    def hide(self):
        if self.is_visible:
            self.win.withdraw()
            self.is_visible = False

class Tooltip:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.config(bg="#ffffe0") # 浅黄色背景
        
        self.label = tk.Label(self.root, text="", bg="#ffffe0", font=("Microsoft YaHei", 12), fg="#333333", justify="left", wraplength=300)
        self.label.pack(padx=8, pady=4)
        
        self.root.withdraw()
        self.is_visible = False

    def show(self, x, y, title, content):
        text = f"{title}\n{content}"
        self.label.config(text=text)
        self.root.update_idletasks()
        self.root.geometry(f"+{x + 15}+{y + 15}")
        self.root.deiconify()
        self.is_visible = True

    def hide(self):
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False

tooltip = None
highlight = None
current_mouse_pos = (0, 0)
last_mouse_move_time = time.time()
last_translated_word = ""

def on_move(x, y):
    global current_mouse_pos, last_mouse_move_time, tooltip, highlight
    if abs(current_mouse_pos[0] - x) > 5 or abs(current_mouse_pos[1] - y) > 5:
        current_mouse_pos = (x, y)
        last_mouse_move_time = time.time()
        if tooltip:
            tooltip.hide()
        if highlight:
            highlight.hide()

def check_hover():
    global tooltip, highlight, last_translated_word
    while True:
        time.sleep(0.05)
        if time.time() - last_mouse_move_time > 0.3 and tooltip and not tooltip.is_visible:
            x, y = current_mouse_pos
            
            box_width, box_height = 80, 20
            bbox = (x - box_width, y - box_height, x + box_width, y + box_height)
            
            try:
                img = ImageGrab.grab(bbox)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                target_x, target_y = box_width, box_height
                found_word = ""
                found_word_bbox = None
                
                for i in range(len(data['text'])):
                    word = data['text'][i].strip()
                    if not word:
                        continue
                        
                    wx = data['left'][i]
                    wy = data['top'][i]
                    ww = data['width'][i]
                    wh = data['height'][i]
                    
                    if wx <= target_x <= wx + ww and wy <= target_y <= wy + wh:
                        clean_word = ''.join(c for c in word if c.isalpha() or c == '-')
                        clean_word = clean_word.strip('-')
                        if clean_word:
                            found_word = clean_word
                            abs_x = (x - box_width) + wx
                            abs_y = (y - box_height) + wy
                            found_word_bbox = (abs_x - 2, abs_y - 2, ww + 4, wh + 4)
                            break
                
                # 为了防止鼠标轻微抖动造成同一单词反复查询/闪烁
                if found_word and found_word_bbox and found_word != last_translated_word:
                    print(f"检测到单词: {found_word}")
                    translation = get_youdao_translation(found_word)
                    if translation:
                        # 1. 高亮单词
                        hx, hy, hw, hh = found_word_bbox
                        highlight.show(hx, hy, hw, hh)
                        # 2. 气泡翻译
                        tooltip.show(x, y, found_word, translation)
                        # 3. 自动加入单词本
                        save_to_vocab(found_word, translation)
                        
                        last_translated_word = found_word
                        
            except Exception as e:
                pass
                
        time.sleep(0.2)

def monitor_live_captions():
    """监控实时字幕进程，如果关闭则自动退出本程序"""
    # 刚启动时给系统实时字幕一点时间打开
    time.sleep(5)
    while True:
        try:
            # 使用 tasklist 检查进程是否存在
            output = subprocess.check_output('tasklist /FI "IMAGENAME eq livecaptions.exe" /NH', shell=True).decode('utf-8', errors='ignore')
            if 'livecaptions.exe' not in output.lower():
                print("Windows 实时字幕已关闭，后台工具自动退出。")
                os._exit(0)
        except Exception:
            pass
        time.sleep(3)

def main():
    global tooltip, highlight
    # 读取历史单词记录
    load_vocab()
    
    # 因为要隐藏黑框，我们需要提供一个退出方式
    def on_quit():
        print("工具已退出。")
        os._exit(0)
        
    hotkey_listener = keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+q': on_quit
    })
    hotkey_listener.start()
    
    print("正在尝试打开 Windows 11 实时字幕 (快捷键 Win + Ctrl + L)...")
    pyautogui.hotkey('win', 'ctrl', 'l')
    time.sleep(1)
    
    print("后台查词工具已启动！")
    print(f"所有查询过的单词将会自动保存在: {VOCAB_FILE}")
    print("使用方法：将鼠标悬停在屏幕上的英文单词上约1秒钟，即可高亮该单词并显示中文解释。")
    print("按下 Ctrl+Alt+Q 可以彻底退出该后台工具。")
    
    listener = mouse.Listener(on_move=on_move)
    listener.start()
    
    tooltip = Tooltip()
    highlight = HighlightBox(tooltip.root)
    
    hover_thread = threading.Thread(target=check_hover, daemon=True)
    hover_thread.start()
    
    # 启动进程监控线程
    monitor_thread = threading.Thread(target=monitor_live_captions, daemon=True)
    monitor_thread.start()
    
    try:
        tooltip.root.mainloop()
    except KeyboardInterrupt:
        print("工具已退出。")

if __name__ == "__main__":
    main()
