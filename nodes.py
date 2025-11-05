import json
import os
import re
import copy
'''
import google.generativeai as genai  # 導入 Google AI 函式庫
'''


# ==============================================================================
# 步驟 1-3: 加載並提取 config.json 內容
# ==============================================================================
# 獲取 nodes.py 所在的文件夾路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.json")

# 嘗試加載 config.json
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG_DATA = json.load(f)
except FileNotFoundError:
    print(
        f"[JSONTemplateGenerator Error] config.json not found at: {config_path}")
    CONFIG_DATA = {"system_prompt": "ERROR: Configuration file not found.",
                   "template": {}, "camera_settings": {}}
except json.JSONDecodeError:
    print("[JSONTemplateGenerator Error] config.json is invalid JSON.")
    CONFIG_DATA = {"system_prompt": "ERROR: Configuration file is invalid JSON.",
                   "template": {}, "camera_settings": {}}

# 提取 system_prompt
SYSTEM_PROMPT = CONFIG_DATA.get("system_prompt", "System Prompt Missing.")
QUALITY_TARGETS = [
        "accurate limb lengths and joint angles",
        "correct finger count and articulation",
        "realistic fabric tension and folds",
        "accurate winking expression"
    ]
NEGATIVE_PROMPT = [
        "accurate limb lengths and joint angles",
        "correct finger count and articulation",
        "realistic fabric tension and folds",
        "accurate winking expression"
    ]

# 提取 template 字典並將其轉換為帶有縮排的 JSON 字符串，用於代碼塊顯示
TEMPLATE_DICT = CONFIG_DATA.get("template", {})
CAMERA_SETTINGS = CONFIG_DATA.get("camera_settings", {})
# 提取鏡頭選項 (轉換為 f/mm 格式的字符串列表，並在開頭添加默認選項)
LENS_OPTIONS = ["SET BY AI"] + \
    [f"{item['type']} ({item['focal_length_mm']}mm)" for item in CAMERA_SETTINGS.get(
        "lens", [])]
# 提取光圈選項 (轉換為字符串列表，並在開頭添加默認選項)
APERTURE_OPTIONS = ["SET BY AI"] + \
    [f"f/{f}" for f in CAMERA_SETTINGS.get("exposure",
                                           {}).get("aperture_f", [])]
# 提取測光選項
METERING_OPTIONS = ["SET BY AI"] + \
    CAMERA_SETTINGS.get("exposure", {}).get("metering", [])
# 提取方向選項
ORIENTATION_OPTIONS = ["SET BY AI"] + \
    CAMERA_SETTINGS.get("framing", {}).get("orientation", [])
# 提取裁剪選項
CROP_OPTIONS = ["SET BY AI"] + \
    CAMERA_SETTINGS.get("framing", {}).get("crop", [])
# 提取角度選項
ANGLE_OPTIONS = ["SET BY AI"] + \
    CAMERA_SETTINGS.get("framing", {}).get("angle", [])


class JSONPromptGenerator:
    """
    ComfyUI 自訂義節點：用於生成包含用戶描述、System Prompt 和 JSON 模板的完整提示字串。
    """

    # 節點的元數據
    NODE_NAME = "JSON_Prompt_Generator"
    CATEGORY = "Utils/Text"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_to_llm",)
    FUNCTION = "generate_prompt"

    # 將提取的常量作為類別屬性，供方法調用
    SYSTEM_PROMPT = SYSTEM_PROMPT
    TEMPLATE_DICT = TEMPLATE_DICT

    @classmethod
    def INPUT_TYPES(s):
        """
        步驟 1: 定義輸入和文本輸入框的 placeholder。
        """
        return {
            "required": {
                "text_description": ("STRING", {
                    "multiline": True,  # 設定為多行文本框
                    "default": "",
                    "placeholder": "Describe the image you want to generate using the natural language you are best at (such as Chinese)."
                }),
                "lens": (LENS_OPTIONS, {"default": "SET BY AI"}),
                "aperture": (APERTURE_OPTIONS, {"default": "SET BY AI"}),
                "metering": (METERING_OPTIONS, {"default": "SET BY AI"}),
                "orientation": (ORIENTATION_OPTIONS, {"default": "SET BY AI"}),
                "crop": (CROP_OPTIONS, {"default": "SET BY AI"}),
                "angle": (ANGLE_OPTIONS, {"default": "SET BY AI"}),
            },
        }

    def generate_prompt(self, text_description, lens, aperture, metering, orientation, crop, angle):
        """
        步驟 4: 按照指定順序組合字符串並輸出。
        """

        user_input = text_description.strip()

        # 將可能修改後的模板轉換為 JSON 字符串
        template_str = json.dumps(self.TEMPLATE_DICT, indent=4, ensure_ascii=False)

        # 構建用戶選擇的 JSON 結構
        user_config_json = {}

        # 處理 Lens 選擇
        if lens != "SET BY AI":
            # 從字符串中解析 type 和 focal_length_mm
            match = re.search(r'(.+?)\s\((.+?)mm\)', lens)
            if match:
                lens_type = match.group(1).strip()
                focal_length_mm = int(match.group(2))
                user_config_json.setdefault(
                    "camera", {}).setdefault("lens", {})
                user_config_json["camera"]["lens"]["type"] = lens_type
                user_config_json["camera"]["lens"]["focal_length_mm"] = focal_length_mm

        # 處理 Aperture 選擇
        if aperture != "SET BY AI":
            # f/X.X 格式
            aperture_f = float(aperture.replace("f/", ""))
            user_config_json.setdefault(
                "camera", {}).setdefault("exposure", {})
            user_config_json["camera"]["exposure"]["aperture_f"] = aperture_f

        # 處理 Metering 選擇
        if metering != "SET BY AI":
            user_config_json.setdefault(
                "camera", {}).setdefault("exposure", {})
            user_config_json["camera"]["exposure"]["metering"] = metering

        # 處理 Orientation 選擇
        if orientation != "SET BY AI":
            user_config_json.setdefault("camera", {}).setdefault("framing", {})
            user_config_json["camera"]["framing"]["orientation"] = orientation

        # 處理 Crop 選擇
        if crop != "SET BY AI":
            user_config_json.setdefault("camera", {}).setdefault("framing", {})
            user_config_json["camera"]["framing"]["crop"] = crop

        # 處理 Angle 選擇
        if angle != "SET BY AI":
            user_config_json.setdefault("camera", {}).setdefault("framing", {})
            user_config_json["camera"]["framing"]["angle"] = angle

        # 將用戶配置轉換為 JSON 字符串，如果非空
        user_config_str = ""
        if user_config_json:
            user_config_str = f"Please include the following specific camera settings in your generated JSON:\n```json\n{json.dumps(user_config_json, indent=4, ensure_ascii=False)}\n```\n"

        # 組合最終輸出字串： 輸入文本 + 用戶配置 JSON + system_prompt + 模板
        template_block = f"\n\n```json\n{template_str}\n```\n"

        output_string = (
            f"{user_input}\n\n"
            f"{user_config_str}\n\n"
            f"{self.SYSTEM_PROMPT}"
            f"{template_block}"
        )

        return (output_string,)


class FormatLLMOutput:
    NODE_NAME = "Format_LLM_Output"
    CATEGORY = "Utils/Text"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("cleaned_json_string",)
    FUNCTION = "format_output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "llm_output": ("STRING", {"forceInput": True}),
                "include_quality_prompt": ("BOOLEAN", {"default": False, "label_on": "Yes", "label_off": "No"}),
                "include_negative_prompt": ("BOOLEAN", {"default": False, "label_on": "Yes", "label_off": "No"}),
            },
        }

    def format_output(self, llm_output, include_quality_prompt, include_negative_prompt):
        cleaned_text = ""
        if not llm_output or not isinstance(llm_output, str):
            # 應該接收到 STRING 類型的輸入
            return ("",)
        if llm_output.strip().startswith("{") and llm_output.strip().endswith("}"):
            cleaned_text = llm_output.strip()
        else:
            # 正则表达式：匹配 ```json 开头（允许空白和换行），捕获中间内容，到 ``` 结尾
            pattern = r'```json\s*\n?(.*?)\n?\s*```'
            match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE) 
            if match:
                cleaned_text = match.group(1).strip()
        prompt_dict = json.loads(cleaned_text)
        if include_quality_prompt:
            prompt_dict["quality_targets"] = QUALITY_TARGETS
        if include_negative_prompt:
            prompt_dict["negative_prompt"] = NEGATIVE_PROMPT
        cleaned_text = json.dumps(prompt_dict, indent=4, ensure_ascii=False)

        # 最終再次清理首尾空格和換行符
        final_output = cleaned_text.strip()
        return (final_output,)
