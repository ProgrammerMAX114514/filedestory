# FileDestory

**A command-line utility to selectively corrupt bytes in a file for testing, simulation, or security research purposes. It preserves the first and last 1024 bytes of the file and allows customizable corruption intervals and byte counts.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)  
[📘 中文说明（README.zh-CN.md）](README.zh-CN.md)  <!-- 指向中文版 README -->

---

## 📌 What is this?

**FileDestory** is a Python-based CLI tool designed to **corrupt specific portions of a file's content on purpose**, primarily for:

- Security research & testing  
- Data destruction simulation  
- Educational or development experiments  

It **avoids modifying the first and last 1024 bytes** (protected regions) of the file and allows you to define:

- The **interval (in KB)** at which corruption occurs  
- The **number of bytes to corrupt** each time  
- Optional **backup generation** before corruption  
- A **progress bar** (with `rich`, if installed) for real-time feedback  

---

## ✨ Features

- 🎯 **Targeted Corruption**: Corrupt bytes at customizable KB intervals, while protecting the first/last 1024 bytes.
- ⚙️ **Customizable**: Set the corruption interval (e.g., 1KB, 2KB) and the number of bytes to damage each time.
- 🛡️ **Safe by Default**: Protects file header and footer (1024B each) from any modification.
- 💾 **Optional Backup**: Automatically creates a `.bak` backup before corruption (can be disabled).
- 📊 **Progress Tracking**: Real-time progress bar with speed (KB/s, MB/s, etc.) using the [`rich`](https://github.com/Textualize/rich) library (optional but recommended).
- 🖥️ **Dual Mode Support**:
  - Interactive CLI (user prompts)
  - Command-line arguments (script-friendly, e.g. `python filedestory.py -f file.bin -s 1KB -d 4`)

---

## 🛠️ Installation & Usage

### 1. Prerequisites

- Python **3.8 or higher**
- (Optional) [`rich`](https://pypi.org/project/rich/) library for colored progress bars:
  
```bash
pip install rich tqdm
```

### 2. Clone or Download the Project

```bash
git clone https://github.com/ProgrammerMAX114514/filedestory.git
cd filedestory
```

### 3. Run the Tool

#### ▶️ Option 1: Interactive Mode (Recommended for beginners)

Just run the script and follow the on-screen prompts:

```bash
python filedestory.py
```

You will be asked to provide:

- The target file path
- Corruption interval (step, e.g. `1KB`)
- Number of bytes to corrupt (destory)
- Whether to create a backup
- A final confirmation before execution

#### ▶️ Option 2: Command-Line Arguments (Scripting / Automation)

```bash
python filedestory.py -f "path/to/your/file.bin" -s 1KB -d 4
```

##### Supported Arguments

| Argument         | Description                                      | Example              |
|------------------|--------------------------------------------------|----------------------|
| `-f`, `--file`   | **Required.** Path to the target file.           | `-f test.bin`        |
| `-s`, `--step`   | Interval in KB between corruptions (default: 1KB)| `-s 2KB` or `-s 1`   |
| `-d`, `--destory`| Number of bytes to corrupt each interval         | `-d 5`               |
| `--no-backup`    | Disable automatic backup (default: enabled)      | `--no-backup`        |

> ℹ️ The `step` argument accepts integers (e.g. `1` = 1KB) or strings with unit (e.g. `1KB`).

---

## ⚠️ Disclaimer & Notes

> ⚠️ **This tool is for legal, ethical, and authorized use only** — such as security research, penetration testing (with permission), data destruction simulation, or educational demos.  
> The author is **not responsible** for any misuse, data loss, or legal consequences arising from the use of this tool.  
> Always ensure you have **proper authorization** before running this tool on any file or system.

### Other Notes

- The first and last **1024 bytes** of the file are **never modified**.
- If you enable backup (`-no-backup` not used), a `.bak` copy will be created before any destructive operation.
- If the `rich` library is installed, you’ll get a colorful, dynamic progress bar showing speed (auto-scaled: KB/s, MB/s...).
- If `rich` is not installed, a simplified text-based output will be used.

---

## 🤝 Contribution & License

- ✅ **Feel free to fork, report issues, or submit PRs** for improvements!
- 📜 **Licensed under the MIT License** – see [LICENSE](LICENSE) for details.

> Copyright © 2025 ProgrammerMAX114514.
