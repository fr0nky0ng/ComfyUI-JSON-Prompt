# ComfyUI JSON PROMPT

## 概述

这是一个ComfyUI自定义节点，可以生成结构化的提示词。只需输入简单的自然语言描述，就可以生成JSON格式的提示词，有助于提高文生图质量。

## 功能特点

- **简单输入**：使用自然语言描述生成复杂的结构化提示。
- **JSON输出**：直接输出可解析的JSON格式，便于后续节点处理。
- **提升生成质量**：通过结构化提示优化Stable Diffusion或其他文生图模型的输出。

## 支持的LLM集成

用户既可以配合Ollama节点运行本地部署的LLM，也可以用Gemini Prompt Node节点通过API请求Google Gemini模型。

### Ollama集成
- 适用于本地部署的开源LLM模型（如Llama系列）。
- 确保已安装Ollama节点，并在ComfyUI中正确配置。

### Gemini集成
- 通过API调用Google Gemini模型生成提示。
- 需要Gemini API密钥，并在Gemini Prompt Node中设置。

## 安装

1. 将本节点文件克隆或下载到ComfyUI的`custom_nodes`目录下。
2. 重启ComfyUI。


## 依赖

- ComfyUI（最新版本）
- Ollama节点（可选，用于本地LLM）
- Gemini Prompt Node（可选，用于Google Gemini API）

## 贡献与问题反馈

欢迎提交Issue或Pull Request。如果遇到问题，请提供详细的错误日志和工作流截图。

## 许可证

MIT License - 免费使用和修改。