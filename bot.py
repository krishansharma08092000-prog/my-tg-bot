# bot.py - FULL MCQ BOT (Render Version)
import telebot
import re
import time
import os

# ==================== CONFIG ====================
BOT_TOKEN = "8912269941:AAGkKwNTZOX4nbiuVl5eE9LOtoths3Oqb4c"
DEMO_CHANNEL = "@demo2bot1"
MAIN_CHANNEL = "@ComputerMCQHub"
CHANNEL_TAG = "♻️ @ComputerMCQHub"
TIME_GAP = 10

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== GLOBAL ====================
current_questions = []
skipped_questions = []
is_processing = False

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "🤖 **MCQ Bot**\n\n📝 मुझे **Text** भेजें जिसमें Questions हों।\n\n✅ **Commands:**\n/skip 2,5,8 - Questions Skip करें\nstop - Process Stop करें\n/sendmain - Main Channel में भेजें\n/status - Current Status देखें",
        parse_mode='Markdown')

@bot.message_handler(commands=['skip'])
def skip_questions(message):
    global skipped_questions
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format: /skip 2,5,8")
            return
        skip_nums = [int(x) for x in re.findall(r'\d+', parts[1])]
        skipped_questions.extend(skip_nums)
        skipped_questions = list(set(skipped_questions))
        bot.reply_to(message, f"✅ Questions {', '.join(map(str, skip_nums))} Skip List में Add कर दिए गए।")
    except Exception as e:
        bot.reply_to(message, f"❌ एरर: {str(e)}")

@bot.message_handler(commands=['status'])
def status(message):
    if not current_questions:
        bot.reply_to(message, "📭 कोई Questions Loaded नहीं हैं।")
        return
    total = len(current_questions)
    skipped = len(skipped_questions)
    remaining = total - skipped
    bot.reply_to(message, f"📊 **Status:**\n✅ Total: {total}\n⚠️ Skipped: {skipped}\n📤 Remaining: {remaining}", parse_mode='Markdown')

@bot.message_handler(commands=['sendmain'])
def send_main(message):
    global is_processing, current_questions, skipped_questions
    if not is_processing or not current_questions:
        bot.reply_to(message, "❌ कोई Questions Loaded नहीं हैं।")
        return
    remaining = [q for q in current_questions if q['number'] not in skipped_questions]
    if not remaining:
        bot.reply_to(message, "✅ सभी Questions Skip कर दिए गए हैं!")
        is_processing = False
        return
    bot.reply_to(message, f"✅ {len(remaining)} Questions भेज रहा हूँ...\n📤 Main Channel: {MAIN_CHANNEL}")
    sent = send_to_channel(MAIN_CHANNEL, remaining)
    bot.reply_to(message, f"📊 **पूरा!**\n✅ {sent} सफल\n⚠️ {len(remaining)-sent} स्किप", parse_mode='Markdown')
    is_processing = False
    current_questions = []
    skipped_questions = []

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_process(message):
    global is_processing, current_questions, skipped_questions
    if is_processing:
        is_processing = False
        current_questions = []
        skipped_questions = []
        bot.reply_to(message, "🛑 Process Stop कर दिया गया है।")
    else:
        bot.reply_to(message, "❌ कोई Process चल नहीं रहा है।")

# ==================== SEND FUNCTION ====================
def send_to_channel(channel, questions):
    sent = 0
    for q in questions:
        if q['number'] in skipped_questions:
            continue
        try:
            final_q = f"🔷 {q['number']}. {q['text']}"
            if q['exam']:
                final_q = f"{final_q} [{q['exam']}]"
            final_q_with_tag = f"{final_q}\n\n{CHANNEL_TAG}"
            if len(final_q_with_tag) > 300:
                print(f"⚠️ Q{q['number']} 300 chars से ज्यादा - Skip")
                continue
            bot.send_poll(
                chat_id=channel,
                question=final_q_with_tag,
                options=q['options'],
                is_anonymous=True,
                type='quiz',
                correct_option_id=q['correct_index'],
                explanation=f"✅ {q['explanation']}",
                explanation_parse_mode=None,
                open_period=None
            )
            sent += 1
            print(f"✅ Q{q['number']} भेजा - {channel}")
            time.sleep(TIME_GAP)
        except Exception as e:
            print(f"❌ Q{q['number']} फेल: {e}")
    return sent

# ==================== PARSE FUNCTION ====================
def parse_single_question(block):
    try:
        # Number
        num_match = re.search(r'^(\d+)\.', block.strip())
        if not num_match:
            return None
        q_num = int(num_match.group(1))
        
        # Remove Number
        rest = re.sub(r'^\d+\.\s*', '', block.strip())
        
        # Exam Name
        exam_match = re.search(r'\[([^\]]+)\]', rest)
        exam_name = exam_match.group(1) if exam_match else ""
        rest = re.sub(r'\s*\[[^\]]+\]', '', rest)
        
        # Options
        options = []
        option_lines = re.findall(r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|\s*ANSWER|\s*$)', rest, re.DOTALL)
        if not option_lines:
            option_lines = re.findall(r'([A-E])\.\s*(.*?)(?=\s*[A-E]\.|\s*ANSWER|\s*$)', rest, re.DOTALL)
        for letter, opt_text in option_lines:
            opt_clean = opt_text.strip().replace('\n', ' ')
            if opt_clean:
                options.append(opt_clean)
        if len(options) < 2:
            return None
        
        # Answer
        ans_match = re.search(r'ANSWER\s*[:=]\s*([A-E])', rest, re.IGNORECASE)
        if not ans_match:
            return None
        answer = ans_match.group(1).upper()
        
        # Answer Text
        answer_text = ""
        for letter, opt_text in option_lines:
            if letter.upper() == answer:
                answer_text = opt_text.strip()
                break
        
        # Explanation
        exp_match = re.search(r'EXPLANATION\s*[:=]\s*(.*?)(?=\[END_QUESTION\]|$)', rest, re.IGNORECASE | re.DOTALL)
        if exp_match:
            explanation = exp_match.group(1).strip().replace('\n', ' ')
        else:
            explanation = f"({answer}) {answer_text}" if answer_text else answer
        
        # Question Text
        first_opt_match = re.search(r'[A-E][\)\.]', rest)
        if first_opt_match:
            q_text = rest[:first_opt_match.start()].strip()
        else:
            q_text = rest.strip()
        q_text = re.sub(r'\s+', ' ', q_text).strip()
        
        # Correct Index
        idx = ord(answer) - ord('A')
        if idx >= len(options):
            idx = 0
        
        return {
            'number': q_num,
            'text': q_text,
            'exam': exam_name,
            'options': options,
            'answer': answer,
            'correct_index': idx,
            'explanation': explanation
        }
    except Exception as e:
        print(f"❌ Parse एरर: {e}")
        return None

# ==================== TEXT HANDLER ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    global current_questions, is_processing, skipped_questions
    if is_processing:
        bot.reply_to(message, "⏳ पहले Questions Process हो रहे हैं। `stop` टाइप करें।", parse_mode='Markdown')
        return
    text = message.text
    if text.startswith('/') or text.lower() == 'stop':
        return
    bot.reply_to(message, "⏳ Questions Parse हो रहे हैं...")
    blocks = re.findall(r'\[START_QUESTION\](.*?)\[END_QUESTION\]', text, re.DOTALL | re.IGNORECASE)
    if not blocks:
        blocks = re.split(r'\n(?=\d+\.)', text)
        blocks = [b.strip() for b in blocks if re.match(r'\d+\.', b.strip())]
    if not blocks:
        bot.reply_to(message, "❌ कोई प्रश्न नहीं मिला!")
        return
    parsed_questions = []
    for block in blocks:
        parsed = parse_single_question(block)
        if parsed:
            parsed_questions.append(parsed)
    if not parsed_questions:
        bot.reply_to(message, "❌ कोई वैध प्रश्न नहीं मिला!")
        return
    current_questions = parsed_questions
    is_processing = True
    skipped_questions = []
    bot.reply_to(message, f"✅ {len(parsed_questions)} प्रश्न मिले।\n📤 Demo Channel ({DEMO_CHANNEL}) में भेज रहा हूँ...")
    sent = send_to_channel(DEMO_CHANNEL, parsed_questions)
    if is_processing:
        remaining = [q for q in parsed_questions if q['number'] not in skipped_questions]
        if remaining:
            bot.reply_to(message, f"✅ Demo Complete! {len(remaining)} Questions Remaining.\n📌 /sendmain - Main Channel में भेजें\n⏭️ /skip 2,5,8\n🛑 stop")
        else:
            bot.reply_to(message, "✅ सभी Questions Skip कर दिए गए हैं!")
            is_processing = False

# ==================== RUN ====================
print("=" * 50)
print("🤖 MCQ BOT STARTING ON RENDER...")
print(f"✅ Demo: {DEMO_CHANNEL}")
print(f"✅ Main: {MAIN_CHANNEL}")
print(f"⏰ Time Gap: {TIME_GAP} सेकंड")
print("=" * 50)

# Webhook हटाएं
try:
    bot.remove_webhook()
    print("✅ Webhook हटा दिया गया")
except:
    pass

bot.polling(none_stop=True)
