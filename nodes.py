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
                "include_negative_prompt": ("BOOLEAN", {"default": True, "label_on": "Yes", "label_off": "No"}),
            },
        }

    def format_output(self, llm_output, include_negative_prompt):
        if not llm_output or not isinstance(llm_output, str):
            # 應該接收到 STRING 類型的輸入
            return ("",)
        # 1. 移除 <think>...</think> 標籤及其內容
        # re.DOTALL 確保 . 匹配換行符，以便處理多行 <think> 內容
        # re.IGNORECASE 確保大小寫不敏感
        cleaned_text = re.sub(
            r'<think>.*?</think>',
            '',
            llm_output,
            flags=re.DOTALL | re.IGNORECASE
        )

        # 2. 移除 Markdown 代碼塊標籤
        # 清理首尾空格和換行符
        cleaned_text = cleaned_text.strip()

        # 檢查是否以 ```json 開頭
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()

        # 檢查是否以 ``` 結尾
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")].strip()
        
        prompt_dict = json.loads(cleaned_text)
        prompt_dict["quality_targets"] = QUALITY_TARGETS
        if include_negative_prompt:
            prompt_dict["negative_prompt"] = NEGATIVE_PROMPT
        cleaned_text = json.dumps(prompt_dict, indent=4, ensure_ascii=False)

        # 最終再次清理首尾空格和換行符
        final_output = cleaned_text.strip()

        return (final_output,)


# pending to debug
'''
class GeminiPromptNode:
    NODE_NAME = "Gemini_Prompt_Node"
    CATEGORY = "LLM"  # 將其放在一個新的類別 "LLM" 中
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "call_gemini"

    @classmethod
    def INPUT_TYPES(s):
        """
        定義輸入參數：
        1. prompt: 用於接收提示詞的輸入阜。
        2. api_key: 用於填寫 API KEY 的輸入框。
        3. gemini_version: 用於選擇 Gemini 模型的下拉選單。
        """
        return {
            "required": {
                "prompt": ("STRING", {"forceInput": True}),
                "api_key": ("STRING", {"multiline": False, "default": ""}),
                "gemini_version": (
                    [
                        "gemini-2.5-flash",
                        "gemini-2.5-flash-lite",
                        "gemini-2.5-pro",
                        # 如果需要，可以添加更多模型
                    ],
                    {"default": "gemini-2.5-flash"},
                ),
            }
        }

    def call_gemini(self, prompt, api_key, gemini_version):
        """
        調用 Gemini API 並返回結果。
        """
        # 1. 檢查 API Key 是否提供
        if not api_key:
            return ("ERROR: API Key is missing.",)

        # 2. 配置 API Key
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            return (f"ERROR: Failed to configure Gemini API. {e}",)

        # 3. 創建模型實例
        try:
            model = genai.GenerativeModel(gemini_version)
        except Exception as e:
            return (f"ERROR: Failed to create Gemini model. {e}",)

        # 4. 提交 prompt 並獲取結果
        try:
            response = model.generate_content(prompt)
            # 處理可能沒有 text 的情況
            if response.parts:
                result_text = response.text
            else:
                # 如果沒有可顯示的文本部分，返回提示信息
                # 您可以檢查 response.prompt_feedback 來了解原因
                return (f"Warning: No valid text part in response. Finish reason: {response.prompt_feedback.block_reason.name}", )
        except Exception as e:
            return (f"ERROR: An error occurred while calling the API. {e}",)

        # 5. 返回結果
        return (result_text,)



class GeminiImageNode:
    """
    ComfyUI 自定義節點：用於調用 Gemini/Imagen API 進行圖片生成。
    """
    NODE_NAME = "Gemini_Image_Node"
    CATEGORY = "LLM/Image"
    RETURN_TYPES = ("IMAGE",)  # ComfyUI 圖片類型
    RETURN_NAMES = ("image",)
    FUNCTION = "generate_image"

    # 用於將用戶友好的比例映射到 API 所需的格式
    ASPECT_RATIO_MAPPING = {
        "1:1": "1:1",
        "9:16": "9:16_P",  # 肖像
        "16:9": "16:9_L",  # 風景
        "3:4": "3:4_P",
        "4:3": "4:3_L",
        "2:3": "2:3_P",
        "3:2": "3:2_L",
    }

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"forceInput": True, "multiline": True, "default": ""}),
                "api_key": ("STRING", {"multiline": False, "default": ""}),
                "image_model": (
                    [
                        "gemini-2.5-flash-image",
                        "imagen-4.0-generate-001",
                        "imagen-4.0-ultra-generate-001",
                    ],
                    {"default": "imagen-4.0-generate-001"},
                ),
                "aspect_ratio": (
                    list(s.ASPECT_RATIO_MAPPING.keys()),
                    {"default": "1:1"},
                ),
            },
        }

    def generate_image(self, prompt, api_key, image_model, aspect_ratio):
        """
        調用 Gemini/Imagen API 進行圖片生成，並將結果轉換為 ComfyUI 的 IMAGE 類型。
        """
        # 1. 檢查 API Key 和 Prompt
        if not api_key:
            raise ValueError("ERROR: API Key is missing.")
        if not prompt or not prompt.strip():
            # 為了避免 API 調用錯誤，對空 Prompt 進行處理
            return (torch.zeros((1, 64, 64, 3)),)  # 返回一個空圖片張量作為提示

        # 2. 配置 API Client
        try:
            # 圖片生成要求使用 genai.Client
            client = genai.Client(api_key=api_key)
        except AttributeError:
            # 處理您遇到的錯誤：模塊沒有 Client 屬性，通常是版本過舊
            raise RuntimeError(
                "ERROR: Failed to initialize Gemini Client. "
                "The 'google-generativeai' library is likely outdated. "
                "Please run: 'pip install --upgrade google-generativeai'"
            )
        except Exception as e:
            raise RuntimeError(
                f"ERROR: Failed to initialize Gemini Client. Details: {e}")

        # 3. 獲取 API 格式的 Aspect Ratio
        api_ratio = self.ASPECT_RATIO_MAPPING.get(aspect_ratio, "1:1")

        # 4. 提交 prompt 並獲取結果
        try:
            # 使用 client.models.generate_images 進行文生圖調用 (官方推薦方式)
            response = client.models.generate_images(
                model=image_model,
                prompt=prompt,
                config=dict(
                    number_of_images=1,  # 默認只生成一張圖片
                    aspect_ratio=api_ratio,
                )
            )

            # 5. 處理結果並轉換為 ComfyUI IMAGE 張量
            if not response.generated_images:
                # 檢查是否有 block_reason
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise RuntimeError(
                        f"Image generation blocked. Reason: {response.prompt_feedback.block_reason.name}")
                raise RuntimeError("ERROR: API returned no generated images.")

            # 提取第一張圖片的 base64 編碼數據
            # generated_images[0].image.image_bytes 包含 base64 編碼的 bytes
            image_data_base64 = response.generated_images[0].image.image_bytes
            image_bytes = base64.b64decode(image_data_base64)

            # 使用 PIL 讀取圖片
            img = Image.open(io.BytesIO(image_bytes))

            # 將 PIL Image 轉換為 NumPy Array
            # 格式：(Height, Width, Channel)，並將值歸一化到 0-1
            image_array = np.array(img).astype(np.float32) / 255.0

            # 轉換為 PyTorch 張量，並添加 Batch 維度
            # 格式：(Batch_Size, Height, Width, Channel)
            image_tensor = torch.from_numpy(image_array).unsqueeze(0)

            # 6. 返回結果
            return (image_tensor,)

        except Exception as e:
            # 將錯誤信息包裝為 ComfyUI 節點錯誤
            raise RuntimeError(
                f"ERROR: An error occurred during image generation. Details: {e}")
'''
