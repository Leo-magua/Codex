# -autohome.py
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from ai_api import summarize_text
from config import MAX_ARTICLES_PER_SOURCE
from data_manager import log

# Playwright 相关
from playwright.sync_api import sync_playwright

AUTOME_URL = "https://www.autohome.com.cn/news"


class AutoHomeFetcher:
    def __init__(self):
        # 启动 Playwright
        self.play = sync_playwright().start()
        # 复用同一个浏览器实例和 Context
        self.browser = self.play.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        # 可在此处拦截广告/埋点请求，减少 networkidle 挂起
        self.context.route("**/*", self._route_handler)
        self.page = self.context.new_page()

    def _route_handler(self, route, request):
        url = request.url
        # 简单屏蔽常见广告/埋点域名
        if any(k in url for k in ("doubleclick.net", "adpush", "googlesyndication")):
            return route.abort()
        return route.continue_()

    def fetch_list_items(self, list_url: str):
        """加载列表页，返回 BeautifulSoup 找到的 li 节点列表"""
        self.page.goto(list_url,
                       timeout=60000,              # 最长等 60s
                       wait_until="domcontentloaded"  # 只等 DOMContentLoaded
                       )
        html = self.page.content()
        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all('li', attrs={'data-artidanchor': True})

    def fetch_detail(self, url: str) -> dict:
        """
        加载详情页，返回 dict: { time, author, content }
        如果加载或解析失败，返回空字段，但脚本继续跑
        """
        try:
            # 关掉超时，等 DOMContentLoaded
            self.page.goto(url,
                           timeout=0,
                           wait_until="domcontentloaded")
            # 如果需要，也可在此加 wait_for_selector
            time.sleep(0.5)
            html = self.page.content()
        except Exception as e:
            log(f"  ⚠️ AutoHome 详情页加载失败: {url}\n    {e}")
            return {"time": "", "author": "", "content": ""}

        soup = BeautifulSoup(html, "html.parser")
        # 提取时间
        time_tag = soup.find('span', class_='time')
        date_str = ""
        if time_tag:
            txt = time_tag.text.strip()
            try:
                dt = datetime.strptime(txt, "%Y年%m月%d日 %H:%M")
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                date_str = ""

        # 提取作者
        author_tag = soup.find('a', class_='name')
        author = author_tag.text.strip() if author_tag else ""

        # 提取正文段落
        paras = [p.get_text(strip=True)
                 for p in soup.find_all('p', class_='editor-paragraph')]
        content = "\n".join(paras)
        return {"time": date_str, "author": author, "content": content}

    def close(self):
        """关闭浏览器和 Playwright"""
        try:
            self.browser.close()
            self.play.stop()
        except Exception:
            pass


def fetch_items():
    """
    返回 list[dict]，每条至少包含：
      title, source, date_str, url, abstract, author, need_render=False
    """
    log("→ [AutoHome] 抓列表…")
    fetcher = AutoHomeFetcher()
    out = []
    try:
        lis = fetcher.fetch_list_items(AUTOME_URL)
        # 限制条数
        for li in lis[:MAX_ARTICLES_PER_SOURCE]:
            # 标题 & 链接
            h3 = li.find('h3')
            a_tag = li.find('a', href=True)
            title = h3.get_text(strip=True) if h3 else ""
            url = a_tag['href'] if a_tag else ""
            if url.startswith("//"):
                url = "https:" + url
            if not title or not url:
                continue

            # 抓详情
            detail = fetcher.fetch_detail(url)
            date_str = detail.get("time") or datetime.now().strftime("%Y-%m-%d")
            author = detail.get("author") or "汽车之家编辑部"
            full_txt = detail.get("content", "")

            # 调用 AI 做摘要
            summary = summarize_text(full_txt) if full_txt else ""
            out.append({
                "title": title,
                "source": "汽车之家",
                "date_str": date_str,
                "url": url,
                "abstract": summary,
                "author": author,
                "need_render": False,
            })

            # 随机 sleep，降低被屏蔽风险
            time.sleep(random.uniform(1, 2))
    finally:
        fetcher.close()

    log(f"→ [AutoHome] 共抓到 {len(out)} 条")
    return out


if __name__ == "__main__":
    items = fetch_items()
    for i, it in enumerate(items, 1):
        print(f"{i}. {it['date_str']} - {it['title']} ({it['url']})")

