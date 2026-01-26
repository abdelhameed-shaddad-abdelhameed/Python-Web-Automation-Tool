# 🚀 Jaco Async Bot (Low Data Edition)

A high-performance, asynchronous automation tool for **Jaco Live**, built with Python and **Playwright**. This edition is specifically optimized to **minimize data usage** and maximize stealth, allowing for efficient multi-account management.

## ✨ Key Features

* **📉 Low Data Mode:** Automatically intercepts and blocks images, videos, audio, and fonts to significantly reduce bandwidth consumption and speed up loading times.
* **⚡ Async & Concurrent:** Powered by `asyncio`, allowing you to run multiple browser contexts simultaneously (configurable via `CONCURRENT`).
* **🕵️ Stealth & Incognito:**
    * Each session runs in a separate, isolated context (no cookie/cache overlap).
    * Includes advanced stealth scripts to patch `navigator.webdriver`, WebGL, and permissions to evade bot detection.
* **🤖 Human-like Interaction:**
    * **Non-linear Mouse Movement:** Simulates natural hand movements rather than direct jumps.
    * **Human Typing:** Types numbers with variable delays to mimic real user behavior.
* **🌍 Smart Country Detection:** Automatically parses the phone number to detect the country code and selects it from the UI dropdown (Supports KSA, Egypt, UAE, US, and many more).

## 🛠️ Prerequisites

Ensure you have **Python 3.8+** installed.

### 1. Install Dependencies
Run the following command to install Playwright:

```bash
pip install playwright
2. Install BrowsersDownload the required browser binaries (Chromium):Bashplaywright install chromium

📂 SetupCreate a file named numbers.txt in the same directory as the script.Add your phone numbers (one per line). Include the country code.Example numbers.txt:Plaintext966500000000
201000000000
971500000000

🚀 UsageRun the script using Python:Bashpython jaco_async_incognito_lowdata.py

⚙️ ConfigurationYou can tweak the constants at the top of the script to fit your environment:VariableDescriptionDefaultCONCURRENTNumber of browsers to run simultaneously.1LAUNCH_OPTIONSSet "headless": True to run in the background (invisible), or False to see the browser.FalseINPUT_FILEThe text file containing phone numbers."numbers.txt"

⚠️ Important NotesVisual Layout: Because this script blocks images and fonts to save data, the browser window might look "broken" or unstyled. This is intentional and does not affect functionality.Rate Limiting: If running many concurrent threads, ensure your IP is not rate-limited by the target site. Using proxies is recommended for high-volume usage.

📝 DisclaimerThis tool is for educational and research purposes only.
 The developer is not responsible for any misuse or potential violations of the target platform's Terms of Service.
