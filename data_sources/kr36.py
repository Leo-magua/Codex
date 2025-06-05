## -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re, time, random, os
from datetime import datetime, timedelta
from data_manager import log
from config import KR_URLS, MAX_ARTICLES_PER_SOURCE, MIN_DELAY_BETWEEN_DETAILS, MAX_DELAY_BETWEEN_DETAILS
from playwright.sync_api import sync_playwright


def parse_36kr_time(s: str) -> str:
    now = datetime.now()

    # 增加对“秒前”的支持
    if "秒" in s:
        # 提取数字
        sec = int(re.search(r"\d+", s).group())
        # 减去对应秒数，然后格式化到天
        return (now - timedelta(seconds=sec)).strftime("%Y-%m-%d")

    if "分钟" in s:
        return (now - timedelta(minutes=int(re.search(r"\d+", s).group()))).strftime("%Y-%m-%d")
    if "小时" in s:
        return (now - timedelta(hours=int(re.search(r"\d+", s).group()))).strftime("%Y-%m-%d")
    if "昨天" in s:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        return s


def render_html_36kr(url: str, timeout: int = 60000) -> str:
    """专门为36Kr优化的页面渲染函数"""
    log(f"  → 渲染36Kr页面: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            page.goto(url, timeout=timeout)

            # 等待页面加载完成（网络空闲）
            page.wait_for_load_state("networkidle", timeout=timeout)

            # 向下滚动以确保动态内容加载
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
            time.sleep(2)  # 短暂等待以确保内容加载

            html = page.content()
            log(f"    页面渲染完成，HTML长度: {len(html)} 字符")
            return html
        except Exception as e:
            log(f"    × 渲染36Kr页面失败: {e}")
            return ""
        finally:
            browser.close()


# 为了保持兼容性，也需要修改原来的render_html函数导入
def render_html_list(url: str, timeout: int = 60000) -> str:
    """用于列表页面的渲染函数"""
    log(f"  → 渲染页面: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=['--disable-blink-features=AutomationControlled'])
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={'width': 1280, 'height': 800},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            page = context.new_page()
            page.goto(url, timeout=timeout, wait_until='domcontentloaded')

            # 简单滚动
            for _ in range(3):
                page.mouse.wheel(0, random.randint(200, 600))
                time.sleep(random.uniform(1, 2))

            html = page.content()
            return html
        except Exception as e:
            log(f"  × 渲染失败: {e}")
            return ""
        finally:
            browser.close()


def fetch_items():
    out = []
    for src, url in KR_URLS.items():
        log(f"→ [36Kr] 源 {src} 抓列表…")
        time.sleep(random.uniform(5, 8))
        html = render_html_list(url)
        if not html:
            log(f"  × {src} 列表渲染失败")
            continue

        soup = BeautifulSoup(html, "html.parser")
        count = 0
        for art in soup.select("div.information-flow-item"):
            if count >= MAX_ARTICLES_PER_SOURCE:
                break
            a = art.select_one("a.article-item-title")
            if not a: continue
            tm = art.select_one("span.kr-flow-bar-time")
            desc = art.select_one("a.article-item-description")
            author_tag = art.select_one("a.kr-flow-bar-author")
            author = author_tag.get_text(strip=True) if author_tag else "36Kr 编辑部"
            date_str = parse_36kr_time(tm.text) if tm else ""
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.36kr.com" + href

            out.append({
                "title": a.get_text(strip=True),
                "source": src,
                "date_str": date_str,
                "url": href,
                "abstract": desc.get_text(strip=True) if desc else "",
                "author": author,
                "need_render": True
            })
            count += 1
        log(f"→ [36Kr] 从 {src} 抓到 {count} 条")
    log(f"→ [36Kr] 总共 {len(out)} 条")
    return out


def debug_selectors(soup):
    """调试页面上的各种选择器"""
    log("    正在检查页面上的主要容器元素...")

    # 检查所有可能的文章容器选择器
    selectors = [
        "div[data-test='article-content']",
        "div.article-content",
        "div.main-article",
        "div.content",
        "div.articleDetail-content",
        "section.textblock",
        "div.kr-article-content",
        "div.article-text",
        "div#article-content",
        "div.article"
    ]

    found_any = False
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            found_any = True
            log(f"    - 选择器 '{selector}' 找到 {len(elements)} 个元素")
            for i, elem in enumerate(elements[:1]):  # 只显示第一个
                text_length = len(elem.get_text(strip=True))
                log(f"      元素 {i + 1}: 包含文本长度 {text_length} 字符")

    if not found_any:
        log("    ! 所有预定义选择器都未找到元素")
        # 查找所有具有class的div，寻找可能的容器
        all_divs = soup.find_all("div", class_=True)
        class_counts = {}
        for div in all_divs:
            classes = ' '.join(div.get('class', []))
            if 'article' in classes or 'content' in classes or 'text' in classes:
                text_len = len(div.get_text(strip=True))
                if text_len > 100:  # 只考虑有足够内容的
                    if classes not in class_counts:
                        class_counts[classes] = {"count": 0, "max_text_len": 0}
                    class_counts[classes]["count"] += 1
                    class_counts[classes]["max_text_len"] = max(class_counts[classes]["max_text_len"], text_len)

        if class_counts:
            log("    可能与文章相关的DIV类:")
            for cls, info in sorted(class_counts.items(), key=lambda x: x[1]["max_text_len"], reverse=True)[:5]:
                log(f"      class='{cls}': {info['count']}个, 最大文本长度={info['max_text_len']}")


def fetch_36kr_content(url: str) -> str:
    """基于您的测试代码优化的36Kr内容抓取函数"""
    # 添加随机延迟
    delay = random.uniform(MIN_DELAY_BETWEEN_DETAILS, MAX_DELAY_BETWEEN_DETAILS)
    log(f"    等待 {delay:.1f}s 再抓详情：{url}")
    time.sleep(delay)

    # 渲染页面
    html = render_html_36kr(url, timeout=60000)
    if not html:
        log("    × 页面渲染失败")
        return ""

    # 保存原始HTML以便调试
    debug_basename = f"debug_36kr_{int(time.time())}"
    debug_file = f"{debug_basename}.html"
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"    ! 已保存原始HTML: {debug_file} (长度: {len(html)}字符)")

    # 解析HTML
    soup = BeautifulSoup(html, "html.parser")

    # 输出调试信息
    debug_selectors(soup)

    # 依次尝试多种容器选择器（基于您的测试代码）
    div = (
            soup.select_one("div[data-test='article-content']") or
            soup.select_one("div.article-content") or
            soup.select_one("div.main-article") or
            soup.select_one("div.content") or
            soup.select_one("div.articleDetail-content") or
            soup.select_one("section.textblock") or
            soup.select_one("div.kr-article-content") or
            soup.select_one("div.article-text") or
            soup.select_one("div#article-content") or
            soup.select_one("div.article")
    )

    if not div:
        log("    × 未找到文章内容容器")
        # 尝试查找包含最多段落的div
        log("    尝试查找包含最多段落的容器...")
        best_div = None
        max_paragraphs = 0

        for d in soup.find_all("div"):
            paragraphs = d.find_all("p")
            if len(paragraphs) > max_paragraphs:
                text_content = d.get_text(strip=True)
                if len(text_content) > 200:  # 至少200字符
                    max_paragraphs = len(paragraphs)
                    best_div = d

        if best_div:
            log(f"    找到候选容器，包含 {max_paragraphs} 个段落")
            div = best_div
        else:
            log("    × 无法找到合适的内容容器")
            return ""

    # 提取正文文本
    paragraphs = [p.get_text(strip=True) for p in div.find_all("p") if p.get_text(strip=True)]

    if not paragraphs:
        log("    × 找到了容器但没有段落内容，尝试获取全部文本")
        full_text = div.get_text(strip=True)
        if len(full_text) < 100:
            log("    × 文本内容太少")
            return ""
    else:
        full_text = "\n".join(paragraphs)

    log(f"    ✓ 成功提取正文: {len(full_text)} 字符, {len(paragraphs)} 个段落")

    # 保存提取的内容
    with open(f"{debug_basename}_extracted.txt", "w", encoding="utf-8") as f:
        f.write(full_text)

    # 输出部分内容预览，帮助确认质量
    preview = full_text[:150] + "..." if len(full_text) > 150 else full_text
    log(f"    内容预览: {preview}")

    return full_text
