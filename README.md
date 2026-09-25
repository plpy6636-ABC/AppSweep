# AppSweep

**Free, open-source Windows uninstaller with residual cleaner. 免费开源的 Windows 卸载工具，支持残留清理。**

---

## English

### Features
- 📋 List all installed software from the Windows registry
- 🚀 Launch the original uninstaller with one click
- 🧹 Scan and clean residuals after uninstall:
  - Registry leftover entries
  - Remaining folders in `Program Files`, `AppData`
  - Leftover shortcuts in Start Menu / Desktop
- 🌍 Bilingual UI: Chinese / English (toggle in one click)
- 🪶 Single-file exe, no installation required

### Download
Go to [Releases](https://github.com/plpy6636-ABC/AppSweep/releases) and download `AppSweep.exe`.

### Build from source
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AppSweep app_sweep.py
```

### ⚠️ Disclaimer / Risk Warning
Uninstalling software and cleaning registry entries may cause:
- Software to become unrecoverable
- System or other apps to misbehave
- Accidental deletion of user data

**Use at your own risk. The author is not responsible for any data loss or system issues caused by using this tool.**

Always create a system restore point before cleaning residuals.

### License
MIT

---

## 中文

### 功能
- 📋 从 Windows 注册表列出所有已安装软件
- 🚀 一键启动软件自带的卸载程序
- 🧹 卸载后扫描并清理残留：
  - 注册表残留项
  - `Program Files`、`AppData` 下的残留文件夹
  - 开始菜单 / 桌面的残留快捷方式
- 🌍 中英文双语界面，一键切换
- 🪶 单文件 exe，无需安装

### 下载
前往 [Releases](https://github.com/plpy6636-ABC/AppSweep/releases) 下载 `AppSweep.exe`。

### 从源码构建
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AppSweep app_sweep.py
```

### ⚠️ 风险提示
卸载软件并清理注册表可能导致：
- 软件无法恢复
- 系统或其他程序异常
- 误删用户数据

**请自行承担风险。作者不对因使用本工具造成的任何数据丢失或系统问题负责。**

清理残留前建议创建系统还原点。

### 开源协议
MIT
