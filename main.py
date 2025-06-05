from data_manager import fetch_and_save_news
from send_manager import send_news
import schedule
import time as schedule_time
from datetime import datetime, timedelta

def log_next_run():
    next_run = datetime.now().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 下一次计划运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===== 脚本启动 =====")
    try:
        fetch_success = fetch_and_save_news()
        if not fetch_success:
            print("获取新闻过程中出现错误，但将继续尝试发送已有新闻")
        send_success = send_news()
        if not send_success:
            print("发送新闻过程中出现错误")
        print("===== 脚本执行完成 =====")
        return fetch_success and send_success
    except Exception as e:
        print(f"脚本执行出错: {e}")
        return False

if __name__ == "__main__":
    try:
        main()
        schedule.every().hour.do(main)
        log_next_run()
        print("===== 已设置每小时自动运行 =====\n程序将保持运行状态，等待定时执行...")
        while True:
            schedule.run_pending()
            schedule_time.sleep(60)
    except KeyboardInterrupt:
        print("程序被用户手动中断")
    except Exception as e:
        print(f"脚本执行出错: {e}")




