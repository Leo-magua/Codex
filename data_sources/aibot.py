# aibot.py
from bs4 import BeautifulSoup
import re
from datetime import datetime
from data_manager import render_html, log
from config import AI_BOT_URL

def parse_date(raw_date: str) -> str:
    """
    将类似 “6月5日”、“6月5·周四”、“6月5” 等格式，
    统一清洗成 "YYYY-MM-DD"。
    不匹配时返回原始 raw_date。
    """
    # 去掉所有非数字、非“月”、“日”字符
    cleaned = re.sub(r"[^\d月日]", "", raw_date)
    # 匹配 “X月Y日” 或 “X月Y”
    m = re.search(r"(\d{1,2})月(\d{1,2})日?", cleaned)
    if m:
        year  = datetime.now().year
        month = int(m.group(1))
        day   = int(m.group(2))
        return f"{year}-{month:02d}-{day:02d}"
    else:
        return raw_date

def fetch_items():
    """
    返回列表，每项 dict 包含：
      title, source, date_str, url, abstract, author, need_render=False
    """
    log("→ [AI-BOT] 抓列表…")
    html = render_html(AI_BOT_URL)
    if not html:
        log("  × AI-BOT 页面渲染失败")
        return []

    soup = BeautifulSoup(html, "html.parser")
    blocks = []
    for el in soup.select("div.news-date, div.news-item"):
        cls = el.get("class", [])
        if "news-date" in cls:
            blocks.append({"date": el.text.strip(), "items": []})
        elif "news-item" in cls and blocks:
            blocks[-1]["items"].append(el)

    out = []
    for blk in blocks[:2]:
        # 把原始日期传给 parse_date
        date_str = parse_date(blk["date"])
        for it in blk["items"]:
            a = it.find("h2").find("a")
            abstract = it.find("p", class_="text-muted text-sm")
            author_tag = abstract.find("span", class_="news-time text-xs") if abstract else None
            author = author_tag.text.replace("来源：", "").strip() if author_tag else "AI-BOT 编辑部"
            out.append({
                "title":      a.text.strip(),
                "source":     "AI-BOT",
                "date_str":   date_str,
                "url":        a["href"],
                "abstract":   abstract.get_text(strip=True) if abstract else "",
                "author":     author,
                "need_render": False
            })

    log(f"→ [AI-BOT] 抓到 {len(out)} 条")
    return out
