import re
from telegram.ext import Updater, MessageHandler, Filters

# ====== DÁN TOKEN CỦA BẠN VÀO ĐÂY ======
TOKEN = "8610460982:AAF_SmpXvYbR3Ww9e_2YTp8hfLCPy_UfqDk"

history_sum = []
history_dice = []

# ===== PARSE =====
def parse_input(raw):
    try:
        session = raw.split(":")[0]
        dice_str = re.search(r"\{(\d-\d-\d)\}", raw).group(1)
        d1, d2, d3 = map(int, dice_str.split("-"))
        return session, (d1, d2, d3)
    except:
        return None, None

# ===== CLASSIFY =====
def classify_all(history_sum):
    tx, parity, level, extreme = [], [], [], []
    
    for s in history_sum:
        tx.append("T" if s >= 11 else "X")
        parity.append("C" if s % 2 == 0 else "L")
        level.append("H" if s >= 11 else "L")
        
        if s <= 6:
            extreme.append("EL")
        elif s >= 15:
            extreme.append("EH")
        else:
            extreme.append("N")
    
    return tx, parity, level, extreme

# ===== SIGNALS =====
def trend(tx):
    if len(tx) < 3: return None, 0
    last = tx[-1]
    count = 1
    for i in range(len(tx)-2, -1, -1):
        if tx[i] == last:
            count += 1
        else:
            break
    return (last, 2) if count >= 3 else (None, 0)

def break_signal(tx):
    if len(tx) < 4: return None, 0
    last = tx[-1]
    count = 1
    for i in range(len(tx)-2, -1, -1):
        if tx[i] == last:
            count += 1
        else:
            break
    if count >= 4:
        return ("T" if last == "X" else "X"), 2
    return None, 0

def zigzag(tx):
    if len(tx) < 4: return None, 0
    if tx[-1] != tx[-2] and tx[-2] != tx[-3]:
        return ("T" if tx[-1] == "X" else "X"), 1
    return None, 0

def parity_signal(parity):
    if len(parity) < 3: return None, 0
    last = parity[-3:]
    if last.count("C") >= 2: return "T", 1
    if last.count("L") >= 2: return "X", 1
    return None, 0

def highlow(level):
    if len(level) < 3: return None, 0
    last = level[-3:]
    if last.count("H") >= 2: return "T", 2
    if last.count("L") >= 2: return "X", 2
    return None, 0

def extreme_signal(extreme):
    if len(extreme) < 5: return None, 0
    last5 = extreme[-5:]
    if last5.count("EH") >= 2: return "X", 2
    if last5.count("EL") >= 2: return "T", 2
    return None, 0

def streak(tx):
    if len(tx) < 5: return None, 0
    last = tx[-1]
    count = 1
    for i in range(len(tx)-2, -1, -1):
        if tx[i] == last:
            count += 1
        else:
            break
    if count >= 5:
        return ("T" if last == "X" else "X"), 3
    return None, 0

def bias(tx):
    if len(tx) < 20: return None, 0
    last20 = tx[-20:]
    if last20.count("T") - last20.count("X") >= 6: return "X", 2
    if last20.count("X") - last20.count("T") >= 6: return "T", 2
    return None, 0

def momentum(tx):
    if len(tx) < 15: return None, 0
    last5 = tx[-5:]
    last15 = tx[-15:]
    if last5.count("T") > last15.count("T")/3: return "T", 1
    if last5.count("X") > last15.count("X")/3: return "X", 1
    return None, 0

def dice_bias(history_dice):
    if len(history_dice) < 10: return None, 0
    flat = [d for roll in history_dice[-10:] for d in roll]
    most = max(set(flat), key=flat.count)
    if flat.count(most) >= 5:
        return "T", 1
    return None, 0

# ===== PREDICT =====
def predict():
    tx, parity, level, extreme = classify_all(history_sum)
    
    score = {"T": 0, "X": 0}
    
    modules = [
        trend(tx),
        break_signal(tx),
        zigzag(tx),
        parity_signal(parity),
        highlow(level),
        extreme_signal(extreme),
        streak(tx),
        bias(tx),
        momentum(tx),
        dice_bias(history_dice)
    ]
    
    for sig, w in modules:
        if sig:
            score[sig] += w
    
    if score["T"] == score["X"]:
        return None, score
    
    return ("T" if score["T"] > score["X"] else "X"), score

# ===== TELE HANDLER =====
def handle(update, context):
    text = update.message.text
    
    session, dice = parse_input(text)
    
    if dice is None:
        update.message.reply_text("❌ Sai format!")
        return
    
    d1, d2, d3 = dice
    s = d1 + d2 + d3
    
    history_sum.append(s)
    history_dice.append(dice)
    
    signal, score = predict()
    
    msg = f"""
📊 Phiên: {session}
🎲 Xúc xắc: {d1}-{d2}-{d3}
🔢 Tổng: {s}

🤖 Gợi ý: {signal}
📈 Score: {score}
"""
    
    update.message.reply_text(msg)

# ===== RUN BOT =====
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    
    updater.start_polling()
    print("Bot đang chạy...")
    updater.idle()

if __name__ == "__main__":
    main()
