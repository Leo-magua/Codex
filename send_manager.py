import requests
import pandas as pd
from datetime import datetime
import random
import time
from config import *
from data_manager import load_excel, save_excel, log

# Feishu 会话
session = requests.Session()
session.headers.update({
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "application/json"
})


def send_to_feishu(item: dict, summary: str) -> bool:
    """发送单条新闻到飞书"""
    payload = {
        "msg_type": "text",
        "content": {
            "title": item["title"],
            "author": item["author"],
            "date_str": item["date_str"],
            "url": item["url"],
            "content": summary,
            "source": item["source"]
        }
    }

    try:
        resp = session.post(WEBHOOK, json=payload, timeout=10)
        log(f"  → Feishu 返回 {resp.status_code}")
        return 200 <= resp.status_code < 300
    except Exception as e:
        log(f"  × Feishu 发送异常：{e}")
        return False


def send_news():
    log("===== 开始发送新闻 =====")
    success = True
    try:
        df = load_excel()

        # 保底初始化列
        if '发送状态' not in df.columns:
            df['发送状态'] = ''
        if 'AI处理状态' not in df.columns:
            df['AI处理状态'] = 'AI处理完成'  # 兼容旧数据

        # 只处理未发送且AI处理完成的
        ready_mask = (
            (df['发送状态'].fillna('') == '') &
            (df['AI处理状态'] == "AI处理完成") &
            (df['内容'].notna()) &
            (df['内容'].str.strip() != "")
        )
        ready_indexes = df[ready_mask].index.tolist()

        if not ready_indexes:
            log("没有准备好发送的新闻")
            return True

        log(f"找到 {len(ready_indexes)} 条准备发送的新闻…")

        sent_count = 0
        failed_count = 0

        for idx in ready_indexes:
            row = df.loc[idx]
            title = row["标题"]
            log(f"发送第 {sent_count + failed_count + 1}/{len(ready_indexes)} 条: {title}")

            item = {
                "title":    title,
                "source":   row["来源"],
                "date_str": row["日期"],
                "url":      row["URL"],
                "author":   row["作者"]
            }
            summary = row["内容"]

            send_ok = send_to_feishu(item, summary)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if send_ok:
                df.at[idx, "发送状态"] = "已发送"
                sent_count += 1
                log("  ✓ 发送成功")
            else:
                df.at[idx, "发送状态"] = "发送失败"
                failed_count += 1
                success = False
                log("  × 发送失败")

            df.at[idx, "更新时间"] = now_str
            save_excel(df)  # 每条都保存，防止脚本中断重复发送

            # 随机延迟
            if idx != ready_indexes[-1]:
                delay = random.uniform(1, 2)
                log(f"  等待 {delay:.1f}s…")
                time.sleep(delay)

        log(f"===== 发送完成: 成功 {sent_count} 条，失败 {failed_count} 条 =====")

    except Exception as e:
        log(f"× 发送过程出错: {e}")
        success = False

    return success