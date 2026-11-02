# yuketangHelper - 雨课堂极速刷课与智能答题助手

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rain Classroom](https://img.shields.io/badge/Platform-雨课堂全国主站-blue.svg)](https://www.yuketang.cn/)

专为**雨课堂（以全国通用主站 `www.yuketang.cn` 为主，兼顾各高校雨课堂）**打造的自动化网课学习与 AI 答题辅助工具。零门槛上手，开箱即用。

---

## 🌟 核心特性 (Features)

* 🚀 **双引擎设计，纯刷课零配置**：
  * **模式一：极速纯刷课（默认推荐）**：无需申请或配置任何大模型 API，纯净跳过所有作业、随堂小题与讨论，专注秒刷视频。
  * **模式二：AI 智能答题（可选启用）**：按需开启，接入 OpenAI / DeepSeek / 硅基流动等主流大模型 API，全自动识别并提交作业。
* 🌐 **全面适配全国通用主站**：彻底重构底层 API，原生支持全国主站（`www.yuketang.cn`）以及各高校的专属独立雨课堂。
* 🛡️ **单流防限流调度引擎**：摒弃多线程粗暴并发导致触发雨课堂 HTTP 429（频繁被阻塞 42 秒）的顽疾，采用单流顺序秒级上报，稳定高效不被封。
* 🎯 **全区间补全算法**：心跳进度自动从 `0.0` 开始全区间覆盖，**彻底解决原版因跳帧历史而卡死在 70%~80% 的经典 Bug**，确保每个视频 100% 满进度完成。
* 🎛️ **两层精细交互体验**：
  * **第一层（课程级）**：美化输出课程与教师列表，支持单选（如 `6`）、多选（如 `6 8 10`）、全选（`0`）。
  * **第二层（视频级）**：自动解析课程下全部小节视频，支持按回车一键全刷，或指定挑选单个/多个特定视频单独刷课。
* ⚡ **无视频课程智能跳过**：自动检测体测、线下体育等无网课视频的实体课程，静默安全跳过，绝不卡死崩溃。
* 💾 **免反复扫码与无感运行**：内置配置驱动，自动保存并复用本地 Cookies，下次启动免扫码秒进任务。

---

## 🚀 极简快速上手 (Quick Start)

> 本教程面向纯小白同学，跟着步骤逐行复制命令即可完成。

### 第一步：准备环境与下载项目

1. 确保电脑已安装 **Python 3.8 或更高版本**（安装时务必勾选 `Add Python to PATH`）。
2. 在终端（Windows PowerShell 或 CMD）中执行以下命令克隆并进入项目：
   ```bash
   git clone https://github.com/HaoxiangXia/yuketangHelper.git
   cd yuketangHelper
   ```
3. 安装运行依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 第二步：配置文件初始化

直接复制项目自带的配置模板 `config.example.json` 为 `config.json`：

* **Windows PowerShell**：
  ```powershell
  copy config.example.json config.json
  ```
* **Linux / macOS**：
  ```bash
  cp config.example.json config.json
  ```

> 💡 **提示**：即使忘记手动创建，首次运行脚本时系统也会自动为你生成一份默认的 `config.json`。

### 第三步：一键运行

在项目目录下执行：
```bash
python helper_main.py
```
终端将自动弹出二维码，使用手机微信扫码即可登录，随后按照屏幕提示输入你想刷的课程序号即可！

---

## 📖 详细使用指南 (Usage)

### 模式一：极速纯刷课（默认推荐）

无需填写任何大模型 Key，`config.json` 中保持 `"do_homework": false`：
1. 运行 `python helper_main.py`；
2. 控制台会列出你名下的所有课程（附带任课教师信息）；
3. **输入课程序号**：
   * 输入单门课编号（如 `6`）；
   * 输入多个编号批量刷课（如 `6 8 10` 或 `6, 8`）；
   * 输入 `0` 刷名下所有网课；
4. 进入课程后，直接**按回车**（默认刷该课程全部视频），或输入小节编号指定刷某几个视频；
5. 脚本将秒级上报进度，直至进度全部达到 100.0%。

---

### 模式二：AI 智能答题（可选启用）

若需要脚本自动帮你完成各章节的课后作业，只需两步：

1. 打开 `config.json`，将 `"do_homework"` 改为 `true`，并填入你的大模型 API 参数（支持 ChatGPT、DeepSeek、硅基流动等兼容 OpenAI 格式的接口）：
   ```json
   {
     "domain": "www.yuketang.cn",
     "do_homework": true,
     "base_url": "https://api.deepseek.com/v1",
     "key": "你的API_KEY",
     "model": "deepseek-chat"
   }
   ```
2. 运行 `python helper_main.py`，刷完视频后将自动调用大模型解析题目并提交答案。

---

### 🔑 两种登录方式说明

| 登录方式 | 操作方式 | 适用场景 |
| :--- | :--- | :--- |
| **方式 1：微信扫码（自动）** | 运行程序后会自动弹出二维码图片，手机微信扫码即刻登录并自动生成 `cookie.txt`。 | 绝大部分正常绑定的账号。 |
| **方式 2：浏览器提取 Cookie（100% 避坑备用）** | 若遇到微信扫码报错，直接在已登录雨课堂的浏览器按 `F12`，在 Cookie 中复制 `sessionid` 与 `csrftoken` 写入项目目录下的 `cookie.txt`。 | 微信未绑定教务系统或网络受限时。 |

---

## ⚙️ 配置文件参数详解 (`config.json`)

```json
{
  "domain": "www.yuketang.cn",
  "use_cached_cookies": true,
  "cookie_file": "cookie.txt",
  "course_number": null,
  "do_homework": false,
  "learning_rate": 12,
  "base_url": "https://api.openai.com/v1",
  "key": "",
  "model": "gpt-3.5-turbo",
  "system_prompt": "..."
}
```

| 字段名 | 默认值 | 作用说明 |
| :--- | :--- | :--- |
| `domain` | `"www.yuketang.cn"` | 雨课堂网址（**自动防错**：带 `https://` 或末尾斜杠会自动清洗） |
| `use_cached_cookies` | `true` | 为 `true` 时优先读取本地保存的 `cookie.txt`，免去重复扫码 |
| `cookie_file` | `"cookie.txt"` | Cookie 本地持久化文件名 |
| `course_number` | `null` | 设为 `null` 时启动弹出交互式菜单选课；设为 `0` 自动全刷；设为数字自动刷对应课程 |
| `do_homework` | `false` | `false` 为纯刷视频（跳过答题）；`true` 启用 AI 自动做作业 |
| `learning_rate` | `12` | 播放步进速率 |

---

## ❓ 常见问题与避坑指南 (FAQ)

### Q1: 扫码后提示“登录验证失败，bind_status: false / 身份未绑定”？
* **原因**：该微信没有在雨课堂教务系统中绑定对应高校的学生身份。
* **终极秒解方案（无需扫码）**：
  1. 电脑浏览器打开雨课堂并正常登录你的账号；
  2. 按键盘 **`F12`** 打开开发者工具，点击顶部 **Application（应用）** $\rightarrow$ 左侧 **Cookies** $\rightarrow$ 点击当前网址；
  3. 找到 `sessionid` 和 `csrftoken` 对应的值；
  4. 在本项目根目录下新建一个文本文件 **`cookie.txt`**，填入以下内容并保存：
     ```text
     sessionid=你的sessionid值; csrftoken=你的csrftoken值;
     ```
  5. 重新运行程序，脚本将直接读取该文件登录，100% 成功。

### Q2: 提示“触发雨课堂限流，等待 XX 秒后重试”？
* **说明**：雨课堂服务器设有短时间访问频率保护。本项目内置了**自动退避机制**，程序会自动等待几十秒后自动续播，期间**无需人工干预**，静候片刻即可。

### Q3: 为什么有的课程（如体测、线下实践课）提示“没有检测到线上视频，跳过”？
* **说明**：这是正常且受保护的机制。线下体育或无网课章节的课程不包含线上播放节点，程序会自动识别并优雅跳过，不会产生报错。

---

## ⚖️ 免责声明 (Disclaimer)

1. 本项目仅供 Python 编程技术交流与学习研究使用，严禁用于任何商业用途或不正当牟利。
2. 使用本脚本所产生的一切网络交互记录与平台责任均由使用者自行承担，请合理安排学习进度。

---

## 🙏 致谢 (Acknowledgements)

本项目基于开源社区相关雨课堂辅助脚本进行深度重构与升级开发，在此向以下优秀的原项目作者及贡献者致谢：
* 原脚本逻辑思路参考：@[heyblackC/yuketangHelper](https://github.com/heyblackC/yuketangHelper)
* 社区二次开发参考：@[Cat1007/yuketangHelperSCUTLite](https://github.com/Cat1007/yuketangHelperSCUTLite)
