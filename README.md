# Codex CLI + llama.cpp 本地部署教程

完全免费、纯本地、支持 MCP 工具调用的 Codex 编程 Agent 环境。

## 硬件要求

本教程以 RTX 5060 Ti 16GB + 48GB 内存为例。具体看你所下的模型

---

## 一、安装 Codex CLI

### 1.1 安装 Node.js

Codex CLI 依赖 Node.js 运行，首先需要安装 Node.js。

前往 [Node.js 官网](https://nodejs.org/) 下载 LTS（长期支持）版本。推荐使用 18.x 或 20.x LTS 版本。

下载 `.msi` 安装包，双击安装，安装时勾选 **Add to PATH** 选项。

安装完成后，打开终端验证：

```powershell
node -v
npm -v
```

显示版本号即安装成功。

### 1.2 安装 Codex CLI

```powershell
npm install -g @openai/codex
```

安装完成后，Codex 配置目录位于 `C:\Users\你的用户名\.codex`。

> **注意**：`.codex` 是隐藏文件夹，需要在文件管理器中开启"显示隐藏项目"才能看到。`config.toml` 就在该文件夹下，如果没有就自己创建。

## 二、下载 llama.cpp 预编译包

前往 [llama.cpp GitHub Releases](https://github.com/ggml-org/llama.cpp/releases)，下载最新的 Windows CUDA 预编译包。

选择文件名格式为 `llama-bXXXX-bin-win-cuda-12.4-x64.zip` 的包（XXXX 为版本号）。

> **注意**：不要下载带 `cudart` 字样的包，那是 CUDA 运行时补充包，不含主程序。需要下载的是带 `bin` 和 `cuda` 字样的完整包。

下载后解压到**纯英文路径**，例如：

```text
D:\llama-cpp\llama-bXXXX-bin-win-cuda-12.4-x64
```

## 三、下载模型

下载 Unsloth 适配版 Qwen3.6 模型（**UD 型号**专门修复了 Codex 兼容性）：

> **注**：Hugging Face 是国外网站，有梯子挂梯子，无法访问可尝试将 `huggingface.co` 换成国内镜像 [hf-mirror.com](https://hf-mirror.com/unsloth/Qwen3.6-35B-A3B-GGUF)

### 方式一：命令行下载（推荐）

```powershell
pip install -U huggingface_hub
huggingface-cli download unsloth/Qwen3.6-35B-A3B-GGUF --include "*UD-Q4_K_XL*" --local-dir D:\AI_models\codex_model
```

### 方式二：浏览器下载

打开 [unsloth/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF)，手动下载 `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`。

> **为什么必须选 UD 型号？**
> `lmstudio-community` 版本的对话模板与 Codex CLI 不兼容，会报错 `System message must be at the beginning`。Unsloth 的 UD 版本专门修复了此问题。

## 四、配置 Codex

在 `C:\Users\你的用户名\.codex\` 目录下创建或编辑 `config.toml`：

```toml
model_provider = "llama_cpp"
model = "Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
disable_response_storage = true
model_context_window = 1000000
model_auto_compact_token_limit = 900000
oss_provider = "llama_cpp"
model_reasoning_effort = "medium"

[model_providers.llama_cpp]
name = "llama_cpp API"
wire_api = "responses"
requires_openai_auth = false
base_url = "http://localhost:8081/v1"
```

## 五、启动模型服务

### 方式一：使用启动器 GUI（推荐）

1. 在仓库页面点击 **Code → Download ZIP** 下载源码

2. 解压后，用文本编辑器打开 `Codex启动器.py`

3. 找到第 8 行 `LLAMA_DIR`，修改为你自己的 llama.cpp 解压路径：

   ```python
   LLAMA_DIR = r'你的llama.cpp解压路径'
   ```

4. 双击 `start_GUI.bat`

5. 点击 **+ 添加模型**，选择你下载的 `.gguf` 模型文件

6. 点击 **启动**

   **注：**下载 ZIP 解压后，双击bat文件会弹出 SmartScreen 警告。这不是病毒，是 Windows 对所有网络下载文件的统一安全策略，直接点击关闭就可以。

   若要不想每次弹出则：

   1. **在下载的 ZIP 文件上操作**：找到你下载的那个 `.zip` 压缩包，**右键点击** → **“属性”**。

   2. **找到并解除锁定**：在属性窗口的 **“常规”** 选项卡最下方，有一个 **“安全：此文件来自其他计算机，可能被阻止以帮助保护该计算机”** 的提示。**勾选旁边的“解除锁定”复选框**，然后点击“确定”。

      完成这一步后，再解压文件，里面的所有文件就不会再被锁定了。

### 方式二：命令行启动

在 llama.cpp 解压目录的地址栏输入 `cmd` 打开终端，运行：

```powershell
.\llama-server.exe -m "你的模型路径\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf" --host 0.0.0.0 --port 8081 --jinja --ctx-size 131072
```

看到 `server is listening on http://0.0.0.0:8081` 即启动成功。

| 参数              | 说明                           |
| :---------------- | :----------------------------- |
| `--jinja`         | 保证工具调用格式标准（**必须**） |
| `--ctx-size 131072` | 上下文大小，16GB 显存推荐此值  |
| `--port 8081`     | 服务端口                       |

## 六、启动 Codex

打开 PowerShell，进入你的项目目录，输入：

```powershell
codex
```

即可使用本地模型进行编程，支持 MCP 工具调用、文件读写、终端命令等。

## 完整链路

```text
你的问题
    ↓
Codex CLI (config.toml)
    ↓
llama-server (端口8081, --jinja)
    ↓
Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf (本地 GPU)
    ↓
MCP 工具 ✅ | 文件读写 ✅ | 终端命令 ✅
```

## 常见问题

**Q: 启动 Codex 后报错 `exceed_context_size_error`？**

A: 上下文不够了，加大启动命令中的 `--ctx-size` 参数，例如改为 `--ctx-size 262144`。

**Q: 报错 `System message must be at the beginning`？**

A: 模型版本不对，请确认使用的是 **UD 型号** 的 Unsloth 适配版模型。

**Q: 显存不够？**

A: 可下载更小的量化版本，如 `UD-Q3_K_M`（约 16.6GB），或降低 `--ctx-size`。