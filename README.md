<p align="center">
  <img src="assets/icon.png" width="128" height="128" />
  <h1 align="center">Ultimate Launcher</h1>
  <p align="center">A high-performance, desktop launcher utilizing native Python bindings and Qt pipelines, supercharging productivity across Windows, macOS, and Linux.</p>
</p>

## ✨ Features

- **Feauture 1**: Clean, minimalistic, keyboard-first user interface sporting fluid component rendering, contextual actions, and asynchronous non-blocking search algorithms.
- **Deep Plugin Ecosystem**: Native compatibility with the [Flow Launcher](https://github.com/Flow-Launcher/Flow.Launcher) registry. Download, extract, and execute C#/Python community extensions spanning calculators, clipboard managers, web searchers, and dictionary definitions all completely natively.
- **Advanced Contextual Math Engine**: Dedicated complex equation evaluator rendering customized large-scale widget panels seamlessly outside standard list bindings.
- **Automated Update Subsystem**: Connects directly to the GitHub Release API to seamlessly deploy `.zip` payloads backwards over local code execution environments without destroying personal user config states or registry keys.
- **Theme Transpiler**: Directly mathematically transpiles XAML and JSON styles (from standard Flow community themes) into active global PyQt6 CSS overrides asynchronously on launch.

## 🚀 Download & Installation

The fastest way to install Ultimate Launcher is to download the natively compiled standalone installer directly from the GitHub Releases tab! No Python environment required.

- **[Download Windows Portable (.zip)](https://github.com/mukunthpr/UltimateLauncher/releases/latest)**
- **[Download MacOS Archive (.tar.gz)](https://github.com/mukunthpr/UltimateLauncher/releases/latest)**
- **[Download Linux Executable (.tar.gz)](https://github.com/mukunthpr/UltimateLauncher/releases/latest)**

*(Note: Apple MacOS users may inherently need to authorize the application actively via System Settings > Security as the current build drops un-Notarized.)*

---

## 🛠️ Build from Source (Developer Mode)

Ultimate Launcher can also execute directly from source via your system's Python distribution, enabling highly aggressive extensibility natively.

```bash
# 1. Clone the repository
git clone https://github.com/mukunthpr/UltimateLauncher.git
cd UltimateLauncher

# 2. Build the lightweight virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install core framework pipelines
pip install PyQt6 keyboard requests psutil Send2Trash python-dotenv

# 4. Boot the OS daemon!
python main.py
```

## ⚙️ How it Works

The backend runs asynchronously inside a Qt loop. When `Alt+Space` is initiated globally, Win32 `SetForegroundWindow` commands aggressively intercept application contexts globally, overriding standard `ForegroundLockTimeout` race conditions within a secure 25ms timer block to guarantee keystroke stability perfectly onto the search bar. 

To hide the UI, simply click outside the pane, press `Escape`, or wait for the 5-second Activity Monitor to drop it securely into the background.

## 📂 Architecture

- **`core/`**: Non-visual system abstractions (Store Scrapers, JSON-RPC bridges, Core config states).
- **`ui/`**: Interface rendering handlers encompassing `main_window`, Sidebar-based Settings panes, and floating contextual actionable popup menus. 
- **`plugins/`**: Your active extensions registry.

## 🌐 Auto Updates

To ensure parity and functionality remain robust, `core/updater.py` acts as a proxy checking Release trees against `version.json`. If a new commit manifests, it initiates an implicit hot-swap and forcefully triggers process execution loops to restart intelligently automatically.

---
*Made with ❤️ by Mukunth P.R. Built on Python, completely open source.*
