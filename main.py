
import telebot
from PyPDF2 import PdfReader
import io
import re
import time

API_TOKEN = '8856211781:AAEn34bZKEOQU5VRSu-D4cqNP38iJ6w6OSg'
bot = telebot.TeleBot(API_TOKEN)
CHANNEL_ID = '@ComputerMCQHub'
user_start_numbers = {}

try:
    bot.delete_webhook()
    print("Webhook successfully removed!")
except Exception as e:
    pass

@bot.message_handler(commands=['startfrom'])
def set_start_number(message):
    try:
        parts = message.text.split()
        if len(parts) > 1 and parts[1].isdigit():
            num = int(parts[1])
            user_start_numbers[message.chat.id] = num
            bot.reply_to(message, f"🎯 Thik hai! Ab bot sawal number {num} se shuru karega.")
        else:
            bot.reply_to(message, "❌ Sahi format: /startfrom 4")
    except Exception as e:
        pass

@bot.message_handler(content_types=['document'])
def handle_pdf(message):
    if message.document.mime_type == 'application/pdf':
        chat_id = message.chat.id
        bot.reply_to(message, "⏳ PDF mil gayi hai! Sawal process kiye ja rahe hain...")
        
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            pdf_file = io.BytesIO(downloaded_file)
            reader = PdfReader(pdf_file)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            question_regex = r'(Q\d+[\s\S]*?)(?=Q\d+|$)'
            questions_blocks = re.findall(question_regex, full_text)
            
            if not questions_blocks:
                bot.send_message(chat_id, "❌ PDF mein koi bhi sawal formatted (Q1, Q2) nahi mila.")
                return
                
            target_start = user_start_numbers.get(chat_id, 1)
            sent_count = 0
            
            for block in questions_blocks:
                num_match = re.search(r'Q(\d+)', block)
                q_num_str = num_match.group(1) if num_match else ""
                
                if num_match and int(num_match.group(1)) < target_start:
                    continue
                
                q_match = re.search(r'(?:Q\d+\.?|Q\)\.?)\s*([\s\S]*?)(?=A\)|\[Exam)', block)
                a_match = re.search(r'A\)\s*([\s\S]*?)(?=B\))', block)
                b_match = re.search(r'B\)\s*([\s\S]*?)(?=C\))', block)
                c_match = re.search(r'C\)\s*([\s\S]*?)(?=D\))', block)
                d_match = re.search(r'D\)\s*([\s\S]*?)(?=ANS|Correct|Explanation|$)', block)
                ans_match = re.search(r'(?:ANSWER|ANS|Correct\s*Answer)[:\s]*\(?([A-D])\)?', block, re.IGNORECASE)
                
                if q_match and a_match and b_match and c_match and d_match and ans_match:
                    if sent_count > 0:
                        time.sleep(10)
                    
                    clean_q = re.sub(r'\s+', ' ', q_match.group(1)).strip()
                    
                    options = [
                        re.sub(r'\s+', ' ', a_match.group(1)).strip(),
                        re.sub(r'\s+', ' ', b_match.group(1)).strip(),
                        re.sub(r'\s+', ' ', c_match.group(1)).strip(),
                        re.sub(r'\s+', ' ', d_match.group(1)).strip()
                    ]
                    
                    cleaned_options = []
                    for opt in options:
                        if len(opt) > 100:
                            opt = opt[:97] + "..."
                        cleaned_options.append(opt)
                    
                    ans_char = ans_match.group(1).upper().strip()
                    correct_idx = {'A': 0, 'B': 1, 'C': 2, 'D': 3}[ans_char]

question_text = f"♻️ @ComputerMCQHub\n\n[Q{q_num_str}] {clean_q}"
                    explanation_text = f"Correct Answer: {ans_char}"
                    
                    bot.send_poll(
                        chat_id=CHANNEL_ID,
                        question=question_text,
                        options=cleaned_options,
                        type='quiz',
                        correct_option_id=correct_idx,
                        explanation=explanation_text,
                        is_anonymous=True
                    )
                    sent_count += 1
            
            bot.send_message(chat_id, f"✅ Safalta! Kul {sent_count} sawal bhej diye gaye hain.")
            user_start_numbers[chat_id] = 1
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)}")

print("Bot live ho raha hai...")
bot.infinity_polling()
