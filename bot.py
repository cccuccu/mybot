import time
import requests

TOKEN = "8598589369:AAHVOMO2AfeHxpfQn_1PgtH1l4hKASlCGzs"
OWNER_ID = 8182419990

config = {
    "channel": "DAVMTGR", 
    "admins": [OWNER_ID]  
}

votes_data = {}
user_states = {} # لحفظ حالة المستخدم (انتظار الاسم، انتظار الإيموجي، أو حالات الإدارة)
temp_candidate_data = {} # لحفظ الاسم مؤقتاً لحين اختيار الإيموجي

def check_subscription(user_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{config['channel']}&user_id={user_id}"
        res = requests.get(url).json()
        if res.get("ok"):
            status = res["result"]["status"]
            if status in ["member", "administrator", "creator"]:
                return True
        return False
    except:
        return True

def send_msg_with_buttons(chat_id, text, buttons):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": buttons}
        }
        return requests.post(url, json=payload).json()
    except:
        return None

def answer_callback(callback_query_id, text, show_alert=False):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
        requests.post(url, json={"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert})
    except:
        pass

def edit_msg_buttons(chat_id, message_id, text, buttons):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": buttons}
        }
        requests.post(url, json=payload)
    except:
        pass

def main():
    offset = 0
    print("Custom Emoji Voting Bot started...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=20"
            updates = requests.get(url).json()
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    # 1. التعامل مع الضغط على الأزرار (التصويت والإدارة)
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        cb_id = cb["id"]
                        from_id = cb["from"]["id"]
                        data = cb["data"]
                        msg_id = cb["message"]["message_id"]
                        
                        if data.startswith("vote_"):
                            post_id = data.split("_")[1]
                            if not check_subscription(from_id):
                                answer_callback(cb_id, "❌ يجب عليك الاشتراك في القناة أولاً للتصويت!", show_alert=True)
                                continue
                            if post_id in votes_data:
                                if from_id in votes_data[post_id]["voters"]:
                                    answer_callback(cb_id, "❌ لقد قمت بالتصويت مسبقاً!", show_alert=True)
                                else:
                                    votes_data[post_id]["voters"].append(from_id)
                                    votes_data[post_id]["count"] += 1
                                    emoji = votes_data[post_id]["emoji"]
                                    answer_callback(cb_id, f"{emoji} تم احتساب صوتك بنجاح!")
                                    
                                    name = votes_data[post_id]["name"]
                                    count = votes_data[post_id]["count"]
                                    new_text = f"📊 *منشور مسابقة التصويت الخاص بك*\n\n👤 المتسابق: *{name}*\n\nعدد الأصوات الحالي: {count} {emoji}"
                                    new_buttons = [[{"text": f"صوّت للمتسابق ({count}) {emoji}", "callback_data": f"vote_{post_id}"}]]
                                    edit_msg_buttons(from_id, msg_id, new_text, new_buttons)
                                    
                        elif from_id in config["admins"]:
                            if data == "set_channel":
                                user_states[from_id] = "wait_channel"
                                answer_callback(cb_id, "أرسل معرف القناة الآن")
                                send_msg_with_buttons(from_id, "📢 أرسل الآن معرف القناة الجديد (بدون علامة @)، مثال: `DAVMTGR`", [])
                            elif data == "add_admin":
                                user_states[from_id] = "wait_admin"
                                answer_callback(cb_id, "أرسل آيدي الأدمن الجديد")
                                send_msg_with_buttons(from_id, "👤 أرسل الآن الرقم الخاص (ID) بالأدمن الجديد:", [])
                        continue

                    # 2. استقبال الرسائل والنصوص
                    if "message" in update:
                        msg = update["message"]
                        user_id = msg["from"]["id"]
                        text = msg.get("text")
                        
                        if not text:
                            continue

                        # إذا كان المرسل أدمن ومستجيب لأوامر لوحة التحكم
                        if user_id in config["admins"] and user_id in user_states:
                            state = user_states[user_id]
                            if state == "wait_channel":
                                config["channel"] = text.replace("@", "").strip()
                                del user_states[user_id]
                                send_msg_with_buttons(user_id, f"✅ تم تغيير قناة الاشتراك الإجباري بنجاح إلى: @{config['channel']}", [])
                                continue
                            elif state == "wait_admin":
                                try:
                                    new_admin = int(text.strip())
                                    if new_admin not in config["admins"]:
                                        config["admins"].append(new_admin)
                                    del user_states[user_id]
                                    send_msg_with_buttons(user_id, f"✅ تم إضافة الأدمن الجديد بنجاح بآيدي: `{new_admin}`", [])
                                except:
                                    send_msg_with_buttons(user_id, "❌ خطأ! يرجى إرسال آيدي صحيح (أرقام فقط).", [])
                                continue

                        # عرض لوحة التحكم للأدمنية عند كتابة /start أو /admin
                        if user_id in config["admins"] and text in ["/start", "/admin"]:
                            admin_buttons = [
                                [{"text": "📢 تغيير قناة الاشتراك الإجباري", "callback_data": "set_channel"}],
                                [{"text": "👤 إضافة أدمن جديد للبوت", "callback_data": "add_admin"}]
                            ]
                            current_info = f"⚙️ *لوحة تحكم الإدارة لمتجر ديف:*\n\nقناة الاشتراك الحالية: @{config['channel']}\nعدد الأدمنية الحالي: {len(config['admins'])}"
                            send_msg_with_buttons(user_id, current_info, admin_buttons)
                            continue

                        # فحص الاشتراك الإجباري للمستخدمين العاديين
                        if not check_subscription(user_id):
                            txt = f"❌ عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً لكي تتمكن من استخدام البوت!\n\nاشترك في القناة ثم أعد إرسال الاسم هنا 👇\n@{config['channel']}"
                            buttons = [[{"text": "اضغط هنا للاشتراك في القناة 📢", "url": f"https://t.me/{config['channel']}"}]]
                            send_msg_with_buttons(user_id, txt, buttons)
                            continue
                            
                        if text == "/start":
                            welcome_txt = "👋 *أهلاً بك في بوت مسابقات متجر ديف!* 📊\n\nلإنشاء منشور تصويت خاص بك وتحديد زر التفاعل الذي يعجبك، كل ما عليك فعله هو **إرسال اسمك** هنا الآن!"
                            user_states[user_id] = "wait_name"
                            send_msg_with_buttons(user_id, welcome_txt, [])
                            continue
                        
                        # خطوة اختيار الإيموجي بعد إرسال الاسم
                        if user_states.get(user_id) == "wait_name":
                            temp_candidate_data[user_id] = text  # حفظ الاسم مؤقتاً
                            user_states[user_id] = "wait_emoji"
                            emoji_txt = f"🎯 استلمت اسمك بنجاح: *{text}*\n\nالآن، قم بإرسال **إيموجي التفاعل** الذي تريده أن يظهر تحت منشورك (مثال: ❤️، 👍، 🔥، 🚀 أو أي إيموجي يعجبك بكيفك) 👇"
                            send_msg_with_buttons(user_id, emoji_txt, [])
                            continue
                        
                        # إنشاء المنشور النهائي بعد استقبال الإيموجي من العضو
                        if user_states.get(user_id) == "wait_emoji":
                            chosen_emoji = text.strip()[0] # أخذ أول إيموجي يرسله العضو
                            candidate_name = temp_candidate_data.get(user_id, "متسابق")
                            post_id = str(user_id)
                            
                            # حفظ البيانات النهائية للتصويت
                            votes_data[post_id] = {"name": candidate_name, "count": 0, "voters": [], "emoji": chosen_emoji}
                            
                            # مسح الحالات المؤقتة
                            del user_states[user_id]
                            if user_id in temp_candidate_data:
                                del temp_candidate_data[user_id]
                                
                            # إرسال المنشور المخصص للعضو
                            post_text = f"📊 *منشور مسابقة التصويت الخاص بك*\n\n👤 المتسابق: *{candidate_name}*\n\nعدد الأصوات الحالي: 0 {chosen_emoji}"
                            post_buttons = [[{"text": f"صوّت للمتسابق (0) {chosen_emoji}", "callback_data": f"vote_{post_id}"}]]
                            send_msg_with_buttons(user_id, post_text, post_buttons)
                            
                            # إرسال تنبيه للمالك والأدمنية برابط الحساب المباشر للذين ليس لديهم يوزر
                            first_name = msg["from"].get("first_name", "")
                            user_link = f"[{first_name}](tg://user?id={user_id})"
                            admin_alert = f"📢 *تم إنشاء تصويت مخصص جديد:*\n\n👤 كاتب الاسم: {user_link}\n🆔 الآيدي: `{user_id}`\n📝 الاسم المرسل: *{candidate_name}*\n🎯 الإيموجي المختار: {chosen_emoji}"
                            
                            for admin in config["admins"]:
                                send_msg_with_buttons(admin, admin_alert, [])
                            continue
                            
        except Exception as e:
            pass
        time.sleep(1)

if __name__ == '__main__':
    main()
    
