import os

# AI相关
ZHIPU_API_KEY = "mykey1"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
DEEPSEEK_API_KEY = "mykey2"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Webhook & 抓取目标
WEBHOOK = "mywebhookurl"
AI_BOT_URL = "https://ai-bot.cn/daily-ai-news/"
KR_URLS = {
    "36kr-AI": "https://www.36kr.com/information/AI/",
    "36kr-travel": "https://www.36kr.com/information/travel/"
}

# 文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(SCRIPT_DIR, "news.xlsx")

# 其他配置
COLUMNS = ["标题", "来源", "日期", "URL", "作者", "内容", "需要渲染", "发送状态", "更新时间"]
MAX_ARTICLES_PER_SOURCE = 5
MIN_DELAY_BETWEEN_DETAILS = 5
MAX_DELAY_BETWEEN_DETAILS = 10

USER_AGENTS = [
    # ...（省略，拷贝原代码中的 User Agent 列表）...
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]
