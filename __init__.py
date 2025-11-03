from .nodes import JSONPromptGenerator, FormatLLMOutput, GeminiPromptNode

# 從 nodes.py 導入所有節點類別

# 節點映射：將類別名稱映射到 ComfyUI 節點名稱
NODE_CLASS_MAPPINGS = {
    JSONPromptGenerator.NODE_NAME: JSONPromptGenerator,
    FormatLLMOutput.NODE_NAME: FormatLLMOutput,
    GeminiPromptNode.NODE_NAME: GeminiPromptNode,
}

# 節點顯示名稱映射
NODE_DISPLAY_NAME_MAPPINGS = {
    JSONPromptGenerator.NODE_NAME: "JSON Prompt Generator",
    FormatLLMOutput.NODE_NAME: "LLM Output Formatting",
    GeminiPromptNode.NODE_NAME: "Gemini Prompt Node",
}

# 輸出插件資訊 (可選)
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
