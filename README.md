# web/ — 个人网页项目

本目录是「资料库」个人网页 + API 额度实时查询面板的完整项目，可独立部署到任意电脑。

## 文件说明

| 文件 | 作用 |
|---|---|
| `资料库.html` | 个人资料库单页应用（localStorage 本地存储），内含「API 额度实时查询」面板，每 30 秒自动刷新 |
| `quota_server.py` | 本地额度查询服务器（127.0.0.1:8720），读取三个 Key 实时查询 DeepSeek / OpenRouter / 智谱额度 |
| `启动额度服务器.bat` | 一键启动服务器（Windows） |

## 使用步骤

1. **准备 Key 文件**：在 `quota_server.py` 同目录建 `keys/` 文件夹，放入三个文件（每行一个 Key，支持 `#` 注释）：
   - `zhipu.txt`：以 `df1344...` 开头的智谱 API Key
   - `deepseek.txt`：以 `sk-` 开头的 DeepSeek API Key
   - `openrouter.txt`：以 `sk-or-` 开头的 OpenRouter API Key
   - 也可以设置环境变量 `QUOTA_KEY_DIR` 指定 Key 目录
2. **启动服务器**：双击 `启动额度服务器.bat`（或命令行 `python quota_server.py`）
3. **打开网页**：浏览器打开 `资料库.html`，概览下方即显示三家额度，每 30 秒自动刷新

## 说明

- 网页本身不含任何 API Key，Key 只保存在本地 `keys/` 目录，由 `quota_server.py` 读取，安全。
- 智谱没有公开用量查询 API，面板对其显示资源包说明与「打开控制台」链接。
- 服务器仅绑定 `127.0.0.1`（仅本机可访问），15 秒缓存防止频繁请求。
