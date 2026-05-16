# Windows Live Caption Translator

这是一个在 Windows 后台运行的辅助工具，专为 Windows 11 实时字幕（Live Captions）设计。它能够在你观看没有中文字幕的英文视频、会议或音频时，为你提供即时的单词翻译和生词记录功能。

## ✨ 核心功能

1. **自动启动实时字幕**：程序启动时，自动调用 `Win + Ctrl + L` 快捷键打开 Windows 的实时字幕功能。
2. **悬停智能取词**：无需点击！只需将鼠标悬停在字幕中不认识的英文单词上约1秒钟，程序会自动精准截取并识别该单词。
3. **精准高亮框选**：基于 OCR 的单词边界识别，确保**完整**框选并高亮目标单词，避免只取到半截单词的问题。
4. **悬浮翻译气泡**：调用有道词典 API，支持显示单词的时态、复数等复杂词性，翻译结果以悬浮窗形式在鼠标旁展现。
5. **生词本自动记录**：查询过的单词会自动保存到桌面上的 `vocabulary_book.txt` 中，并带有时间戳，方便日后复习。程序会去重，避免重复记录。

## 🛠️ 安装与运行

### 1. 安装 Tesseract-OCR 引擎 (必备)
程序需要依赖 OCR 引擎来“看”清屏幕上的单词：
- 请前往 [Tesseract-OCR 下载页面](https://github.com/UB-Mannheim/tesseract/wiki) 下载 Windows 安装包并安装。
- 安装完毕后，请确保 `live_caption_translator.py` 代码中 `tesseract_cmd` 的路径与你的实际安装路径一致（默认通常是 `C:\Program Files\Tesseract-OCR\tesseract.exe`）。

### 2. 安装 Python 依赖
打开命令行（CMD 或 PowerShell），运行以下命令安装必要的 Python 库：
```bash
pip install pynput pyautogui pytesseract Pillow
```

### 3. 运行程序
在命令行中执行：
```bash
python live_caption_translator.py
```

## 📝 贡献与修改
你可以根据自己的需求修改代码，比如：
- 更改悬浮窗和高亮框的颜色（代码中的 `Tooltip` 和 `HighlightBox` 类）。
- 更改生词本的保存路径（代码中的 `VOCAB_FILE` 常量）。
