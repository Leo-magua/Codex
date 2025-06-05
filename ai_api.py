from openai import OpenAI
from config import ZHIPU_API_KEY, ZHIPU_BASE_URL, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from datetime import datetime
import random

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

ZHIPU_CLIENT = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)
DEEPSEEK_CLIENT = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def summarize_text(text: str, max_tokens: int = 400) -> str:
    if not text or len(text.strip()) < 10:
        log("  × 文本过短，跳过摘要")
        return text
    try:
        log("  → 尝试调用智谱免费模型 (glm-4-flash)")
        resp = ZHIPU_CLIENT.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是擅长提炼新闻要点并将其总结为200字左右摘要的AI新闻总结助手。"},
                {"role": "user", "content": text}
            ],
            top_p=0.7, temperature=0.9, max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log(f"  × 智谱免费模型调用失败：{e}")

    try:
        log("  → 尝试调用智谱付费模型 (glm-4-flashx-250414)")
        resp = ZHIPU_CLIENT.chat.completions.create(
            model="glm-4-flashx-250414",
            messages=[
                {"role": "system", "content": "你是擅长提炼新闻要点并将其总结为200字左右摘要的AI新闻总结助手。"},
                {"role": "user", "content": text}
            ],
            top_p=0.7, temperature=0.9, max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log(f"  × 智谱付费模型调用失败：{e}")

    try:
        log("  → 尝试调用 DeepSeek 模型")
        resp = DEEPSEEK_CLIENT.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是擅长提炼新闻要点并将其总结为200字左右摘要的AI新闻总结助手。"},
                {"role": "user", "content": text}
            ],
            temperature=0.7, max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log(f"  × DeepSeek模型调用失败：{e}")
    log("  ! 所有模型调用失败，返回文本截断")
    return text[:500] + ("..." if len(text) > 500 else "")
