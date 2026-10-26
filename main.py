import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
import pandas as pd
import openpyxl

# --- RENDER WEB SERVER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")
        
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()
# -------------------------

TOKEN = "8811580035:AAGCA8etTHC8TDyt4DlGsJfqiZFzQ2bmyME"
bot = telebot.TeleBot(TOKEN)

user_classes = {}
EXCEL_FILE = "DARS JADVALI OXIRGISI.xlsx"

def get_schedule(class_name, day_name):
    if not os.path.exists(EXCEL_FILE):
        return "Excel fayl topilmadi!"

    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="1", header=None)
    except Exception as e:
        return f"Xatolik: {e}"

    day_mapping = {
        "Dushanba": "Понедельник",
        "Seshanba": "Вторник",
        "Chorshanba": "Среда",
        "Payshanba": "Четверг",
        "Juma": "Пятница",
        "Shanba": "Суббота",
    }

    target_day = day_mapping.get(day_name, day_name)

    class_start_idx = -1
    for idx, row in df.iterrows():
        val = str(row.values[0]) if pd.notna(row.values[0]) else ""
        if "Класс -" in val or "Класс-" in val:
            c_name = val.split("-")[-1].strip().replace(" ", "")
            if c_name.lower() == class_name.lower():
                class_start_idx = idx
                break

    if class_start_idx == -1:
        return f"{class_name} sinfi topilmadi."

    sub_df = df.iloc[class_start_idx : class_start_idx + 22, :].reset_index(drop=True)
    header_days = sub_df.iloc[1]
    day_col_idx = -1
    for col_idx, cell_val in enumerate(header_days):
        if pd.notna(cell_val) and str(cell_val).strip() == target_day:
            day_col_idx = col_idx
            break

    if day_col_idx == -1:
        return f"{day_name} kuni uchun jadval topilmadi."

    lessons = []
    for r in range(3, len(sub_df)):
        row = sub_df.iloc[r]
        num = row.iloc[0]
        if pd.isna(num) or not str(num).isdigit():
            if r > 10 and not lessons:
                break
            continue

        subject = row.iloc[day_col_idx]
        subj_str = str(subject).strip() if pd.notna(subject) else "Bosh"
        if subj_str == "nan" or subj_str == "":
            subj_str = "Bosh"

        lessons.append(f"{num}-dars: {subj_str}")

    if not lessons:
        return f"{class_name} sinf uchun {day_name} kuni darslar yo'q."

    result = f"{class_name} sinf - {day_name} kuni:\n\n"
    result += "\n".join(lessons)
    return result

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("1A", "1B", "1V", "2A", "2B", "2V")
    markup.add("3A", "3B", "3V", "4A", "4B", "4V")
    markup.add("5A", "5B", "5V", "6A", "6B")
    markup.add("7A", "7B", "8A", "8B", "9A", "9B")
    markup.add("10A", "10B", "11A", "11B")
    bot.send_message(message.chat.id, "Salom! Sinfingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    chat_id = message.chat.id

    all_classes = [
        "1A", "1B", "1V", "2A", "2B", "2V",
        "3A", "3B", "3V", "4A", "4B", "4V",
        "5A", "5B", "5V", "6A", "6B",
        "7A", "7B", "8A", "8B", "9A", "9B",
        "10A", "10B", "11A", "11B",
    ]

    if text in all_classes:
        user_classes[chat_id] = text
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Dushanba", "Seshanba", "Chorshanba")
        markup.add("Payshanba", "Juma", "Shanba")
        markup.add("⬅️ Sinfni ozgartirish")
        bot.send_message(chat_id, f"Siz {text} sinfni tanladingiz. Kunni tanlang:", reply_markup=markup)
    elif text == "⬅️ Sinfni ozgartirish":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("1A", "1B", "1V", "2A", "2B", "2V")
        markup.add("3A", "3B", "3V", "4A", "4B", "4V")
        markup.add("5A", "5B", "5V", "6A", "6B")
        markup.add("7A", "7B", "8A", "8B", "9A", "9B")
        markup.add("10A", "10B", "11A", "11B")
        bot.send_message(chat_id, "Qaytadan sinfni tanlang:", reply_markup=markup)
    elif text in ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]:
        current_class = user_classes.get(chat_id)
        if not current_class:
            bot.send_message(chat_id, "Avval sinfingizni tanlang!")
            return
        schedule_text = get_schedule(current_class, text)
        bot.send_message(chat_id, schedule_text)
    else:
        bot.send_message(chat_id, "Tugmalardan foydalaning!")

print("Bot ishga tushdi!")
bot.infinity_polling()
