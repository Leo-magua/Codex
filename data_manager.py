import os, pandas as pd, pkgutil, importlib, random, time
from datetime import datetime
from config import EXCEL_FILE, COLUMNS, MIN_DELAY_BETWEEN_DETAILS, MAX_DELAY_BETWEEN_DETAILS, USER_AGENTS
from ai_api import summarize_text


# —— 共用函数 —— #
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


# Playwright 渲染
from playwright.sync_api import sync_playwright


def render_html(url: str, timeout: int = 60000, is_detail_page: bool = False) -> str:
    log(f"  → 渲染页面: {url}")
    user_agent = random.choice(USER_AGENTS)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True,
                                        args=['--disable-blink-features=AutomationControlled'])
            ctx = browser.new_context(user_agent=user_agent,
                                      viewport={'width': 1280, 'height': 800}, locale='zh-CN',
                                      timezone_id='Asia/Shanghai')
            page = ctx.new_page()
            page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            # 深度渲染
            if is_detail_page:
                for _ in range(3):
                    page.mouse.wheel(0, random.randint(200, 600))
                    time.sleep(random.uniform(1, 2))
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        log(f"  × 渲染失败: {e}")
        return ""


# 从 kr36.py 导入更完善的函数
from data_sources.kr36 import fetch_36kr_content


# —— 动态加载所有 data_sources 下的模块 —— #
def load_data_sources():
    import data_sources
    for finder, name, ispkg in pkgutil.iter_modules(data_sources.__path__):
        mod = importlib.import_module(f"data_sources.{name}")
        if hasattr(mod, "fetch_items"):
            yield mod


# —— Excel 操作 —— #
def load_excel() -> pd.DataFrame:
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        # 确保发送状态列存在
        if '发送状态' not in df.columns:
            df['发送状态'] = ''
        log(f"已加载 {len(df)} 条历史")
        return df
    else:
        log("无历史，新建空表")
        return pd.DataFrame(columns=COLUMNS)


def save_excel(df: pd.DataFrame):
    df.to_excel(EXCEL_FILE, index=False)
    sz = os.path.getsize(EXCEL_FILE)
    log(f"已保存 {EXCEL_FILE} ({sz} 字节)")


# —— 主流程：抓取 + 写入 —— #
def fetch_and_save_news():
    log("===== 开始获取新闻 =====")
    success = True

    try:
        # 1. 读历史
        df = load_excel()
        seen_urls = set(df["URL"].dropna())

        # 2. 抓取所有源
        all_items = []
        for src in load_data_sources():
            try:
                items = src.fetch_items()
                all_items.extend(items)
            except Exception as e:
                log(f"× 数据源 {src.__name__} 抓取失败: {e}")
                success = False

        # 3. 筛新
        new_items = [it for it in all_items if it["url"] not in seen_urls]
        if not new_items:
            log("无新内容")
            return success

        log(f"发现 {len(new_items)} 条新新闻，开始处理...")

        # 4. 逐条处理并写入
        for idx, item in enumerate(new_items, 1):
            log(f"处理第 {idx}/{len(new_items)} 条: {item['title']}")
            # 并发/多次防重
            cur = load_excel()
            if item["url"] in set(cur["URL"].dropna()):
                log(f"  ! 跳过重复URL: {item['url']}")
                continue

            try:
                # 4.1 AI 生成摘要
                if item.get("need_render"):
                    full = fetch_36kr_content(item["url"])
                    summary = summarize_text(full or item.get("abstract", ""))
                else:
                    summary = item.get("abstract", "")

                # 4.2 AI 处理状态
                ai_status = "AI处理完成" if summary and summary.strip() else "AI处理失败"

                # 4.3 构建新行
                new_record = pd.DataFrame([{
                    "标题":           item["title"],
                    "来源":           item["source"],
                    "日期":           item["date_str"],
                    "URL":            item["url"],
                    "作者":           item["author"],
                    "内容":           summary,
                    "需要渲染":       str(item.get("need_render", False)),
                    "AI处理状态":     ai_status,
                    "发送状态":       "",    # 空 = 待发送
                    "更新时间":       datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])

                # 4.4 追加并保存
                df = pd.concat([df, new_record], ignore_index=True)
                save_excel(df)
                log(f"  ✓ 已保存: {item['title']}")

            except Exception as e:
                log(f"  × 处理失败: {item['title']} - {e}")
                success = False

        log(f"===== 新闻获取完成，共处理 {len(new_items)} 条 =====")

    except Exception as e:
        log(f"× 获取新闻过程出错: {e}")
        success = False

    return success

