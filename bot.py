import time
import requests

TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"
ADMIN_ID = 8182419990
CHANNEL_USERNAME = "DAVMTGR" # اسم القناة بدون @

def check_subscription(user_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{CHANNEL_USERNAME}&user_id={user_id}"
        res = requests.get(url).json()
        if res.get("ok"):
            status = res["result"]["status"]
            if status in ["member", "administrator", "creator"]:
                return True
        return False
    except:
        return True

def send_msg(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    except:
        pass

def main():
    offset = 0
    print("Bot started successfully...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=20"
            updates = requests.get(url).json()
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        msg = update["message"]
                        user_id = msg["from"]["id"]
                        
                        if user_id == ADMIN_ID:
                            send_msg(ADMIN_ID, "أهلاً بك يا مالك البوت. هذه لوحة التحكم الخاصة بك.")
                            continue
                            
                        if not check_subscription(user_id):
                            txt = "❌ عذراً عزيزي، يجب عليك الاشتراك في قناة متجر ديف أولاً لاستخدام البوت المطور.\n\nاشترك في القناة ثم أعد إرسال /start 👇\nhttps://t.me/DAVMTGR"
                            send_msg(user_id, txt)
                            continue
                            
                        if msg.get("text") == "/start":
                            send_msg(user_id, "👋 أهلاً بك في قناة متجر ديف!\n\nيسعدنا تواصلك معنا، يمكنك الآن إرسال استفسارك أو رسالتك مباشرة هنا، وسيتم إيصالها للمالك والرد عليك في أقرب وقت ممكن.")
                            continue
                            
                        if "text" in msg:
                            user_name = msg["from"].get("first_name", "") + " " + msg["from"].get("last_name", "")
                            user_username = f"@{msg['from']['username']}" if "username" in msg["from"] else "بدون معرف"
                            
                            admin_message = f"📩 رسالة جديدة من متجر ديف:\n\n👤 الاسم: {user_name}\n🔗 المعرف: {user_username}\n🆔 الآيدي: `{user_id}`\n\n💬 النص:\n{msg['text']}"
                            send_msg(ADMIN_ID, admin_message)
                            send_msg(user_id, "✅ تم إرسال رسالتك إلى إدارة متجر ديف بنجاح، سيتم الرد عليك قريباً.")
        except:
            pass
        time.sleep(1)

if __name__ == '__main__':
    main()
