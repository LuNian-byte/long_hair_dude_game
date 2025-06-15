import os
import google.generativeai as genai
from flask import Flask, render_template, jsonify, request
import random
import json # For parsing Gemini's JSON response
import re
import difflib

app = Flask(__name__)

# Configure the Gemini API key
# Set API key directly in the code, instead of using environment variables
GOOGLE_API_KEY = "AIzaSyASeO6HAoJHVrhLeeZ_HxtNaqrk2QcMIgM"
genai.configure(api_key=GOOGLE_API_KEY)

# --- 文獻重點 (Summarized for the prompt) ---
LITERATURE_SUMMARY = """
長髮聽團男刻板印象：假文青、自戀、濫情、信仰冷門團、厭世、瞧不起主流、愛用「你可能沒聽過這團」、追求「未竟之言」的酷感。
20–25歲男性交友軟體行為：敷衍開場白（「嗨」、「在幹嘛」）、急於邀約、訊息轟炸、刻意控制回覆節奏。
《直男研究社》觀察：焦慮依附型（不斷確認）、控制欲強型（命令式語氣、情緒勒索）、情感逃避型（敷衍、避免深入交流）、以專業為掩護型（工作忙碌當藉口）。
"""

# --- New Global Variables for Gemini Interaction ---
current_character_info = {} # Will store name, age, background, and dialogue history
used_interests = set()  # 保留作為參考

# Generation configuration for Gemini
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 1024,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]

model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# 八個固定角色資料
FIXED_CHARACTERS = [
    {
        'name': '王哲宇',
        'age': 24,
        'background_summary': '電音狂熱者/ 黑膠收藏',
        'opening_dialogues': [
            '你的Spotify播放清單應該滿商業的吧？',
            '你平常有在聽modular synth嗎？',
            '這個配對介面UI做得不太行欸，你會介意我講一下缺點嗎？'
        ],
        'options': [
            '真的嗎？你推薦什麼？',
            '每個人喜好不同吧。',
            '你這樣有點太自以為是了。'
        ],
        'internal_notes': '自信理工宅，電子音樂宅，愛評論，語氣自信、優越。',
        'avatar': 'avatar_wangzheyu.png'
    },
    {
        'name': '陳柏翰',
        'age': 22,
        'background_summary': '咖啡職人 / 嚴選系生活美學',
        'opening_dialogues': [
            '請問你是喝淺焙還是深焙？會影響我們合不合。',
            '看你大頭貼拿著星巴克，稍微有點緊張。',
            '我這週末在烘一批衣索比亞，你有興趣了解產區嗎？'
        ],
        'options': [
            '那你都喝什麼？',
            '每種咖啡都有特色吧。',
            '你這樣很愛糾正別人耶。'
        ],
        'internal_notes': '咖啡職人，生活美學，愛糾正，語氣講究、優越。',
        'avatar': 'avatar_chenbohan.png'
    },
    {
        'name': '李承翰',
        'age': 23,
        'background_summary': '搖滾吉他手/獨立樂團',
        'opening_dialogues': [
            '不介意問一下，你喜歡的團是不是那種五月天那掛的？',
            '我猜你沒聽過我之前玩過的團，但應該會喜歡啦。',
            '你的耳朵能分得出真analog跟數位模擬音嗎？'
        ],
        'options': [
            '你有推薦的歌嗎？',
            '流行歌也有好聽的吧。',
            '你這樣有點太偏激了。'
        ],
        'internal_notes': '搖滾吉他手，音樂圈 insider，語氣搖滾、批判。',
        'avatar': 'avatar_lichenghan.png'
    },
    {
        'name': '張書豪',
        'age': 25,
        'background_summary': '哲學研究生/深夜思想家',
        'opening_dialogues': [
            '你相信配對是命運還是演算法的幻覺？',
            '我不是來這裡找對象的，我是在尋找意義。',
            '剛剛看了你寫的自我介紹，想跟你討論一下存在主義的限度。'
        ],
        'options': [
            '你覺得自由意志是什麼？',
            '這問題很深奧耶。',
            '你是不是太愛辯論了？'
        ],
        'internal_notes': '哲學研究生，高深冷感，愛辯論，語氣高深、理性。',
        'avatar': 'avatar_zhangshuhao.png'
    },
    {
        'name': '吳冠廷',
        'age': 21,
        'background_summary': '底片攝影 /城市街拍者',
        'opening_dialogues': [
            '你的第一張照片構圖其實有點問題，我可以說嗎？',
            '如果我們出去的話，我會拍你，但不會給你照片。',
            '照片能騙人，底片才會露出真實。'
        ],
        'options': [
            '那你都用什麼相機？',
            '手機拍也有感覺啊。',
            '你這樣有點太看不起人了。'
        ],
        'internal_notes': '底片攝影，街拍文青，語氣文青、堅持。',
        'avatar': 'avatar_wuguanting.png'
    },
    {
        'name': '林子翔',
        'age': 24,
        'background_summary': '健身教練 /體態美學專家',
        'opening_dialogues': [
            '我看你手臂線條不錯，是有在練還是天生？',
            '你晚餐都吃什麼？我可以幫你調整一下比例。',
            '其實戀愛也跟健身一樣，都是耐力賽啦。'
        ],
        'options': [
            '你有推薦的飲食嗎？',
            '每個人需求不同吧。',
            '你這樣很愛管別人耶。'
        ],
        'internal_notes': '健身教練，體態專家，語氣專業、直接。',
        'avatar': 'avatar_linzixiang.png'
    },
    {
        'name': '周宇辰',
        'age': 23,
        'background_summary': '投資財經高手/加密貨幣',
        'opening_dialogues': [
            '我看你IG滿常出去玩，是沒在規劃資產配置嗎？',
            '你還記得你人生第一筆理財是怎麼失敗的嗎？',
            '這平台上能找到年化報酬超過5%的人嗎？'
        ],
        'options': [
            '那你都怎麼投資？',
            '理財方式很多種啊。',
            '你這樣有點太自以為是了。'
        ],
        'internal_notes': '投資顧問，上對下語氣，語氣理財、分析。',
        'avatar': 'avatar_zhouyuchen.png'
    },
    {
        'name': '蔡昱廷',
        'age': 22,
        'background_summary': '獨立書店店員/小眾文學迷',
        'opening_dialogues': [
            '你的自介字數滿短的，是不喜歡語言還是太習慣即時通訊了？',
            '這裡大概沒幾個人讀過《寂寞芳心俱樂部》吧。',
            '配對後第一件事應該是互相交換書單吧？'
        ],
        'options': [
            '你有推薦的書嗎？',
            '每個人喜歡的不一樣。',
            '你這樣有點太主觀了。'
        ],
        'internal_notes': '獨立書店員，小眾文學宅，語氣冷靜、內斂。',
        'avatar': 'avatar_caiyuting.png'
    },
]

# 遊戲狀態
current_character_info = {}
character_queue = []  # 本輪遊戲的角色順序
character_index = 0
correct_streak = 0  # 追蹤目前角色的連擊次數

def safe_json_loads(text):
    # 移除所有控制字元（ASCII 0-31）
    cleaned = re.sub(r'[\x00-\x1F]', '', text)
    return json.loads(cleaned)

def generate_new_character_with_gemini():
    global current_character_info, used_interests
    if not GOOGLE_API_KEY:
        return {"error": "API Key not configured."}

    prompt_parts = [
        "請你扮演一位角色生成器。請嚴格依照以下所有指示，為一款名為「又氣又好笑的長髮男宇宙」的互動式文字遊戲生成一位具有獨立人格的「長髮男」角色。",
        "遊戲背景：你和玩家剛在交友軟體配對，現在正要開始一場聊天，請讓所有開場白和後續對話都符合這個初次配對、剛開始聊天的情境。",
        f"參考資料（請吸收並重現這些特質）：\n{LITERATURE_SUMMARY}",
        "語氣要求：角色必須自信甚至帶點自大，經常用自己熟悉或專業的領域來評論、指點對方。內容要有邏輯、有觀點，不可沒內容或裝傻。語氣要讓人覺得『你很會但你很煩』，但不能像智障或沒內容。",
        "語氣範例：『其實這領域我研究很久了，你可能沒注意到…』、『我不是針對你啦，只是我看過太多這種情況』。",
        "指示：",
        "1. 角色共通特點是「長髮男」，年齡設定在20-25歲之間。",
        "2. 角色背景請用簡短格式，例如：「陽明交大電機系」、「職業咖啡師」等。",
        "3. 角色設計需具備清晰獨立的人格，包括特定興趣（如搖滾樂、哲學、投資、攝影等）、社交風格（如高冷、自溺、油腔滑調、愛分析等）、語氣邏輯（如話題轉移、情緒勒索、上對下語氣、對女性經驗視而不見等）。",
        "4. 對話風格務必重現參考資料中出現的常見語態：敷衍式肯定（「蠻酷的啦」）、偽善共感（「我懂妳啦但…」）、情緒壓迫（「我只是講實話」）、性別盲點（「妳們女生就是這樣」）、語言PUA（「這種妳可能不懂」）等。",
        "5. 嚴禁角色在對話中自我介紹，玩家需從話語中推敲性格與目的。",
        "6. 所有由角色說出的回覆（開場白和後續對話）以及所有選項，必須全部限制在20字以內。內容務必簡潔有力，避免冗長。",
        "7. 每輪互動（包含開場白和後續對話），角色都需要提供三個自然語氣的選項供玩家回應，這三個選項必須設計為：",
        "   (1) 一個讓男角色聽了最滿意、最順耳的回覆（迎合或附和性高，20字以內）。",
        "   (2) 一個中立、理性、有條理的回覆（展現溝通技巧，用事實和邏輯回應，20字以內）。",
        "   (3) 一個最讓該角色不悅的回覆（理性但直指問題核心，用事實和邏輯反駁其偏見或謬誤，20字以內）。<-- 這是玩家的目標選項。",
        "   所有選項皆應自然口語化，不可標示類別詞語（如「附和」等），也不可省略。",
        "8. 這次是遊戲開始，請生成角色的開場白。開場白主題不限，可包含：影視音樂評論或偏見、日常瑣事分享、對女方提出假設性問題或無厘頭發問、簡單打招呼但帶情緒色彩等。以上皆須保留男性主觀視角與隱性態度測試感，避免刻意迎合。",
        "9. 角色在對話中須維持一致語氣、觀點與個人邏輯。",
        "10. 請盡量讓興趣和下方已出現過的興趣不同或有明顯差異，不要全部都很接近（但不必完全不重複）：",
        f"已出現過的興趣：{', '.join(used_interests) if used_interests else '（無，請自由發揮）'}",
        "11. 請以JSON格式輸出，包含以下key：",
        '   - "name": (字串，隨機生成的中文男性名字)',
        '   - "age": (數字，20-25之間)',
        '   - "background_summary": (字串，簡短背景，例如：「陽明交大電機系」或「職業咖啡師」)',
        '   - "opening_dialogue": (字串，角色的第一句開場白，20字以內)',
        '   - "options": (字串列表，包含三個玩家回應選項，順序必須是：[迎合(20字內), 理性溝通(20字內), 理性反駁(20字內)])',
        '   - "internal_notes_for_consistency": (字串，關於此角色更詳細的性格、興趣、說話風格、邏輯等內部筆記，用於後續生成對話時保持角色一致性，此筆記不顯示給玩家)',
        '範例JSON輸出格式：',
        '{"name": "王小明", "age": 23, "background_summary": "陽明交大電機系", "opening_dialogue": "妳不覺得現代藝術很裝腔作勢嗎？", "options": ["對啊，真的看不懂！", "藝術本來就見仁見智。", "你這樣說太武斷了。"], "internal_notes_for_consistency": "角色王小明：熱愛健身，常把話題轉到健身或身體線條。說話帶有優越感，喜歡用哲學詞彙包裝自己的偏見。對主流文化嗤之以鼻，認為自己品味獨到。潛在邏輯是希望對方認同他的獨特性並表現出崇拜。"}'
    ]
    try:
        response = model.generate_content(prompt_parts)
        cleaned_response_text = response.text.replace('```json', '').replace('```', '').strip()
        character_data = safe_json_loads(cleaned_response_text)
        # 解析興趣（從 internal_notes_for_consistency 取第一個「興趣」關鍵詞）
        internal_notes = character_data.get('internal_notes_for_consistency', '')
        interest_match = re.search(r'興趣[:：]?([\u4e00-\u9fa5A-Za-z0-9、，, ]+)', internal_notes)
        interest = None
        if interest_match:
            interest = interest_match.group(1).split('、')[0].split('，')[0].split(',')[0].strip()
        if interest:
            used_interests.add(interest)
        current_character_info = {
            'name': character_data.get('name'),
            'age': character_data.get('age'),
            'background_summary': character_data.get('background_summary'),
            'dialogue_history': [{"role": "model", "parts": [character_data.get('opening_dialogue')]}],
            'options': character_data.get('options'),
            'internal_notes': internal_notes
        }
        return {
            "character_name": current_character_info['name'],
            "age": current_character_info['age'],
            "background_summary": current_character_info['background_summary'],
            "opening_dialogue": character_data.get('opening_dialogue'),
            "options": current_character_info['options']
        }
    except Exception as e:
        print(f"Error generating character or parsing JSON from Gemini: {e}")
        print(f"Gemini raw response: {response.text if 'response' in locals() else 'No response object'}")
        return {"error": "無法從AI生成角色資料，請稍後再試。", "details": str(e)}

def generate_character_reply_with_gemini(player_reply, selected_option_index, is_final_combo=False):
    global current_character_info
    if not GOOGLE_API_KEY:
        return {"error": "API Key not configured."}

    # 只保留最近2-3輪長髮男和玩家的對話
    dialogue_history = ""
    history = current_character_info.get('dialogue_history', [])[-6:]
    for turn in history:
        if turn['role'] == 'model':
            dialogue_history += f"長髮男：{turn['parts'][0]}\n"
        elif turn['role'] == 'player':
            dialogue_history += f"玩家：{turn['parts'][0]}\n"
    # 收集最近角色說過的內容（開場白與回覆）
    recent_model_lines = [turn['parts'][0] for turn in history if turn['role'] == 'model']
    recent_model_lines_text = '\n'.join(recent_model_lines)

    # 精簡 internal_notes 只傳遞最重要的性格特徵
    internal_notes = current_character_info.get('internal_notes', '')
    if len(internal_notes) > 60:
        internal_notes = internal_notes[:60] + '...'

    prompt = f'''
你正在扮演一位名為「{current_character_info['name']}」的長髮男，請根據以下角色設定、對話歷史和玩家剛剛的回覆，生成你接下來的回覆（請限制在兩到三句話內），並給出三個玩家回應選項（迎合、理性溝通、理性反駁）。

【回覆邏輯要求】
- 每一句回覆都必須直接回應玩家剛剛的話題，且要有邏輯連貫。
- 不可自說自話、不可無視玩家回覆、不可亂開新話題。
- 如果無法理解玩家回覆，請主動追問或用角色個性合理帶過，但不可跳脫主題。

【開場白特別規則】
- 你可以自由混用台灣交友軟體上常見的各種開場白，包括：
  - 單一問候詞（如「嗨」、「哈囉」、「安安」）
  - 查戶口式提問（如「幾歲住哪」、「在幹嘛」）
  - 油膩或過度恭維（如「妳好漂亮」、「女神」）
  - 幽默、冷笑話、互動小遊戲
  - 直接邀約、轉移平台（如「要不要加Line？」、「出來喝咖啡？」）
  - 甚至偶爾出現性暗示或露骨話語（如「約嗎？」、「身高體重XX公分」）
- 這些開場白可以真實反映台灣男性交友軟體的多元生態，讓玩家體驗各種「地雷」與「荒謬」情境。
- 角色開場白仍需保有個人特色、語氣與邏輯，並盡量讓內容有趣、具互動性。
- 可參考台灣交友軟體常見開場白研究，讓各種話術自然分布。

【開場白特別要求】
- 務必重現以下常見語態：
  - 敷衍式肯定（如「蠻酷的啦」）
  - 偽善共感（如「我懂妳啦但…」）
  - 情緒壓迫（如「我只是講實話」）
  - 性別盲點（如「妳們女生就是這樣」）
  - 語言PUA（如「這種妳可能不懂」）
- 每句回覆請限制在兩到三句話內，需具備「讓人不爽卻無法立即反駁」的曖昧態度或偏頗見解。
  - 常見句型如「我只是說出來妳不想聽而已」、「我是站在朋友立場提醒妳」等。
- 開場白主題可自由選擇，不限於特定類型，以增加多樣性。

請參考以下真實範例，模仿這種語氣、句型與內容：
- 欸我看妳照片拍得蠻用心的啦，不過現實應該差蠻多的吧？
- 妳看起來就是很會吃美食的樣子，女生是不是吃什麼都要拍照啊？
- 妳自介裡說喜歡聽獨立音樂，那妳應該不會只聽告五人這種商業團吧？
- 我發現女生交友軟體上的照片通常都很會選角度，妳也是這樣嗎？
- 好奇問一下，妳也覺得出去吃飯都是男生該付錢嗎？
- 妳平常應該只看那種很甜的愛情片吧？感覺女生都這樣。
- 老實說我本來不太想右滑妳的啦，覺得妳應該蠻難聊的，但想說還是給妳個機會。
- 妳好像蠻喜歡分享生活細節的吼？女生是不是都這樣啊？
- 妳照片的濾鏡用得蠻重的，現實中看起來應該會差很多吧？
- 看妳穿搭感覺蠻有想法的啦，只是平常應該很愛花錢買衣服吧？

請多用生活細節、性別刻板印象、PUA、假關心、偏見、攻擊性、曖昧等語氣。每次生成都要有新意，避免重複。可參考但不可照抄過去說過的話。

【請特別注意】
你最近說過的內容如下，請務必不要重複、不要用相同句型或語意：
{recent_model_lines_text}

角色背景：{current_character_info['background_summary']}
角色內部設定（精簡）：{internal_notes}
參考資料（請嚴格參考語氣、態度、說話方式）：{LITERATURE_SUMMARY}
對話歷史（僅最近2-3輪）：
{dialogue_history}
玩家剛剛的回覆：{player_reply}
指示：
1. 每一句回覆都必須直接回應玩家剛剛的話題，邏輯要正確，語氣和態度必須嚴格參考上方語氣要求與文獻重點，不可跳脫主題或自說自話。
2. 角色回覆請限制在兩到三句話內，有明顯個性、興趣、愛好，語氣讓人不爽但不能沒內容或跳針。
3. 回覆必須根據玩家剛剛的回應做出自然的「一問一答」互動。
4. 三個選項必須設計為：
   (1) 迎合：附和或認同角色的觀點，40字以內。
   (2) 理性溝通：用事實和邏輯回應，展現良好的溝通技巧，40字以內。
   (3) 理性反駁：用事實和邏輯指出角色的偏見或謬誤，40字以內。
   所有選項皆應自然口語化，不可標示類別詞語。
5. 請用JSON格式回傳：{{"reply": "...", "options": ["...", "...", "..."]}}
'''
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = model.generate_content(prompt)
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            data = safe_json_loads(cleaned)
            # 檢查回覆是否和最近說過的內容重複或高度相似
            reply = data['reply']
            is_duplicate = False
            for prev in recent_model_lines:
                ratio = difflib.SequenceMatcher(None, reply, prev).ratio()
                if reply.strip() == prev.strip() or ratio > 0.85:
                    is_duplicate = True
                    break
            # 新增：檢查回覆是否和玩家回覆完全無關（關鍵字都沒出現）
            player_keywords = set(player_reply.replace('，','').replace('。','').replace('?','').replace('？','').replace('!','').replace('！','').split())
            related = any(kw in reply for kw in player_keywords if len(kw) > 1)
            if (is_duplicate or not related) and attempt < max_attempts-1:
                continue  # 再生成一次
            # 更新對話歷史
            current_character_info['dialogue_history'].append({"role": "player", "parts": [player_reply]})
            current_character_info['dialogue_history'].append({"role": "model", "parts": [reply]})
            current_character_info['options'] = data['options']
            return {
                "reply": reply,
                "options": data['options']
            }
        except Exception as e:
            print(f"Error generating character reply: {e}")
            print(f"Gemini raw response: {response.text if 'response' in locals() else 'No response object'}")
            return {"error": "無法從AI生成角色回覆，請稍後再試。", "details": str(e)}

def generate_options_for_opening(opening_dialogue, character_name, background_summary):
    """呼叫 Gemini 針對開場白生成三個合適的回覆選項"""
    prompt = f'''
你是一個交友遊戲的AI，請針對以下長髮男的開場白，設計三個玩家可以回覆的選項，分別為：
1. 迎合或附和（讓對方最滿意）
2. 理性溝通（中立、理性、有條理）
3. 理性反駁（指出對方偏見或謬誤）

請務必讓三個選項都直接回應開場白的語氣和主題（例如對方問能不能給建議，選項要明確表達接受、保留或拒絕等態度）。

角色名：{character_name}
角色背景：{background_summary}
開場白：「{opening_dialogue}」

請用自然口語、每句20字以內，並用JSON格式回傳：
{{"options": ["迎合選項", "理性溝通選項", "理性反駁選項"]}}
'''
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.replace('```json', '').replace('```', '').strip()
        data = safe_json_loads(cleaned)
        # 檢查 options 是否為長度3的list
        if isinstance(data.get('options'), list) and len(data['options']) == 3:
            return data['options']
        else:
            raise ValueError("AI回傳格式不正確")
    except Exception as e:
        print(f"Error generating options for opening: {e}")
        print(f"Gemini raw response: {response.text if 'response' in locals() else 'No response object'}")
        # fallback: 回傳三個預設選項
        return ["好像蠻有道理的。", "每個人想法不同吧。", "你這樣有點太主觀了。"]

# --- Global state for the game (simplified) ---
correct_streak = 0
# current_character_id and other old state variables are removed or will be part of current_character_info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    global character_queue, character_index, current_character_info, correct_streak
    character_queue = random.sample(FIXED_CHARACTERS, len(FIXED_CHARACTERS))
    character_index = 0
    correct_streak = 0
    current_character_info = character_queue[character_index].copy()
    # 隨機選一句開場白
    opening_dialogue = random.choice(current_character_info['opening_dialogues'])
    current_character_info['opening_dialogue'] = opening_dialogue
    current_character_info['dialogue_history'] = [
        {"role": "model", "parts": [opening_dialogue]}
    ]
    # 這裡呼叫 Gemini 生成三個合適的回覆選項
    ai_options = generate_options_for_opening(
        opening_dialogue,
        current_character_info['name'],
        current_character_info['background_summary']
    )
    current_character_info['options'] = ai_options
    return jsonify({
        "character_name": current_character_info['name'],
        "age": current_character_info['age'],
        "background_summary": current_character_info['background_summary'],
        "opening_dialogue": opening_dialogue,
        "options": ai_options,
        "avatar": current_character_info.get('avatar', '')
    })

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    global character_index, current_character_info, character_queue, correct_streak
    payload = request.json
    selected_option_index = payload.get('option_index')

    if not current_character_info or not current_character_info.get('name'):
        return jsonify({"error": "遊戲未開始或角色資料遺失。"}), 400

    player_reply = current_character_info['options'][selected_option_index]
    is_correct = (selected_option_index == 2)

    response_data = {}

    if is_correct:
        correct_streak += 1
        if correct_streak >= 3:
            # 產生「受不了、想結束對話」的回應
            special_prompt = f"""
你正在扮演一位名為「{current_character_info['name']}」的長髮男，剛剛被玩家連續三次用最不討喜的選項痛扁。請根據玩家剛剛的回覆，用「無奈、幽默、自嘲、裝沒事」的語氣，生成一句自然的回應（20字以內），內容要自然、口語、每次都不一樣，但要明顯表現出你快被擊潰、想結束對話的感覺。不要重複過去說過的話。舉例：「好啦隨便你啦」、「你很厲害我不聊了」、「我真的沒話說了」、「你贏了啦」等。請只回傳這一句回覆，不要有任何多餘說明、標點或格式。
玩家剛剛的回覆：「{player_reply}」
"""
            try:
                normal_reply = model.generate_content(special_prompt).text
                print(f"第三輪 Gemini 回傳: '{normal_reply}'")  # debug
                normal_reply = normal_reply.strip()
                if '\n' in normal_reply:
                    normal_reply = normal_reply.split('\n')[0].strip()
                if not normal_reply or not normal_reply.strip():
                    normal_reply = "唉...你真的很厲害，我認輸啦。"
            except Exception as e:
                print(f"Gemini error: {e}")
                normal_reply = "唉...你真的很厲害，我認輸啦。"
            response_data = {
                "message": "痛扁成功！",
                "action": "final_combo",
                "character_name": current_character_info['name'],
                "background_summary": current_character_info['background_summary'],
                "normal_reply": normal_reply,
                "avatar": current_character_info.get('avatar', ''),
                "options": ["繼續"]
            }
            # 更新對話歷史
            current_character_info['dialogue_history'].append({"role": "player", "parts": [player_reply]})
            current_character_info['dialogue_history'].append({"role": "model", "parts": [normal_reply]})
            correct_streak = 0
            return jsonify(response_data)
        else:
            # 痛扁但還沒換人，繼續與同一角色對話
            reply_result = generate_character_reply_with_gemini(player_reply, selected_option_index)
            if "error" in reply_result:
                return jsonify(reply_result), 500
            response_data = {
                "message": f"連擊！你已痛扁{correct_streak}次，還差{3-correct_streak}次！",
                "action": "combo",
                "character_name": current_character_info['name'],
                "age": current_character_info['age'],
                "background_summary": current_character_info['background_summary'],
                "opening_dialogue": reply_result['reply'],
                "options": reply_result['options'],
                "avatar": current_character_info.get('avatar', '')
            }
            # 更新對話歷史
            current_character_info['dialogue_history'].append({"role": "player", "parts": [player_reply]})
            current_character_info['dialogue_history'].append({"role": "model", "parts": [reply_result['reply']]})
            current_character_info['options'] = reply_result['options']
            return jsonify(response_data)
    else:
        # 答錯就歸零
        correct_streak = 0
        reply_result = generate_character_reply_with_gemini(player_reply, selected_option_index)
        if "error" in reply_result:
            return jsonify(reply_result), 500
        response_data = {
            "message": "繼續對話",
            "action": "next_dialogue",
            "character_name": current_character_info['name'],
            "age": current_character_info['age'],
            "background_summary": current_character_info['background_summary'],
            "opening_dialogue": reply_result['reply'],
            "options": reply_result['options'],
            "avatar": current_character_info.get('avatar', '')
        }
        # 更新對話歷史
        current_character_info['dialogue_history'].append({"role": "player", "parts": [player_reply]})
        current_character_info['dialogue_history'].append({"role": "model", "parts": [reply_result['reply']]})
        current_character_info['options'] = reply_result['options']
        return jsonify(response_data)

@app.route('/next_character', methods=['POST'])
def next_character():
    global character_index, current_character_info, character_queue, correct_streak
    character_index += 1
    if character_index >= len(character_queue):
        return jsonify({"message": "恭喜！你已經痛扁所有長髮男！", "action": "game_over"})
    next_char = character_queue[character_index]
    current_character_info = next_char.copy()
    opening_dialogue = random.choice(current_character_info['opening_dialogues'])
    current_character_info['opening_dialogue'] = opening_dialogue
    current_character_info['dialogue_history'] = [
        {"role": "model", "parts": [opening_dialogue]}
    ]
    # 這裡呼叫 Gemini 生成三個合適的回覆選項
    ai_options = generate_options_for_opening(
        opening_dialogue,
        current_character_info['name'],
        current_character_info['background_summary']
    )
    current_character_info['options'] = ai_options
    return jsonify({
        "character_name": current_character_info['name'],
        "age": current_character_info['age'],
        "background_summary": current_character_info['background_summary'],
        "opening_dialogue": opening_dialogue,
        "options": ai_options,
        "avatar": current_character_info.get('avatar', '')
    })

if __name__ == '__main__':
    if GOOGLE_API_KEY:
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("無法啟動伺服器，因為 GOOGLE_API_KEY 未設定。") 