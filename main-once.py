from data_manager import fetch_and_save_news
from send_manager import send_news
from datetime import datetime

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
    main()