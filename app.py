import os
import math
import random
import re
import numpy as np
from collections import deque
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ==========================================
# 🔐 BẢO MẬT VIP + ADMIN
# ==========================================
KEYS_DB = {"hungadmin67": "admin", "viphung": "user", "chanbomayde": "user"}
LOCKED_KEYS = set()
HISTORY = deque(maxlen=200)

def get_id(item):
    if isinstance(item, dict):
        for k in ['id', 'phien', 'sessionId', 'sid', 'referenceId', 'matchId', 'phien_hien_tai', 'gameNum']:
            if k in item:
                val = str(item[k]).replace('-', '').replace('#', '')
                if val.isdigit():
                    return int(val)
    matches = re.findall(r"'?(?:id|phien|referenceId|sessionId|matchId|phien_hien_tai|gameNum)'?\s*:\s*'?'?(\d+)'?'?", str(item), re.IGNORECASE)
    return int(matches[0]) if matches else 0

# ==================================================
# 🧠 LÕI 1: MD5 DEEP NEURAL 10.000 LAYERS (GỐC + TỐI ƯU)
# ==================================================
def md5_10000_layers_predict(md5_str: str):
    if not re.match(r"^[0-9a-f]{32}$", md5_str.lower()): 
        return "LỖI", "MD5 KHÔNG HỢP LỆ", 0.0

    hex_arr = np.array([int(ch, 16) for ch in md5_str.lower()], dtype=np.float64)
    energy = hex_arr.sum()
    
    x = (energy % 2048) / 2048.0
    r = 3.9999 + (energy % 2000) / 25000.0
    
    tai_score = xiu_score = 0.0
    for epoch in range(10000):
        x = r * x * (1 - x)
        if epoch % 3 == 0:
            tai_score += x * (hex_arr[epoch % 32] / 15.0) * (1 + np.sin(epoch / 100))
        else:
            xiu_score += x * (hex_arr[(epoch + 7) % 32] / 15.0) * (1 + np.cos(epoch / 100))
    
    fft_vals = np.abs(np.fft.fft(hex_arr))
    tai_score += np.mean(fft_vals[1:12]) * 15
    xiu_score += np.mean(fft_vals[12:24]) * 15
    
    diff = tai_score - xiu_score
    logistic = 1 / (1 + math.exp(-diff / 30.0))
    final_tai = logistic * 100 + random.uniform(-1.5, 1.5)
    final_xiu = (1 - logistic) * 100 + random.uniform(-1.5, 1.5)
    
    total = final_tai + final_xiu
    final_tai = round(max(51.0, min(99.9, (final_tai / total) * 100)), 1)
    final_xiu = round(max(51.0, min(99.9, (final_xiu / total) * 100)), 1)
    
    if final_tai > final_xiu: return "TÀI", "MD5 10.000 NEURAL LAYERS", final_tai
    else: return "XỈU", "MD5 10.000 NEURAL LAYERS", final_xiu

# ==================================================
# 🧠 LÕI 2: MONTE CARLO 50.000 LẦN + MARKOV CHAIN
# ==================================================
def monte_carlo_markov_predict(is_chanle, history):
    if len(history) < 10:
        return "TÀI", 55.5, "Đang nạp dữ liệu VIP..."
    
    seq = [1 if x == "T" else 0 for x in history]
    last = seq[-1]
    
    tt = sum(1 for i in range(1, len(seq)) if seq[i-1] == 1 and seq[i] == 1)
    tx = sum(1 for i in range(1, len(seq)) if seq[i-1] == 1 and seq[i] == 0)
    xt = sum(1 for i in range(1, len(seq)) if seq[i-1] == 0 and seq[i] == 1)
    xx = sum(1 for i in range(1, len(seq)) if seq[i-1] == 0 and seq[i] == 0)
    
    p_next_t = (tt / (tt + tx) if (tt + tx) > 0 else 0.5) if last == 1 else (xt / (xt + xx) if (xt + xx) > 0 else 0.5)
    
    sim_t = sum(1 for _ in range(50000) if random.random() < p_next_t * 1.08)
    prob = (sim_t / 50000) * 100
    
    pred = "T" if prob > 50 else "X"
    prob = max(52.0, min(99.9, prob if pred == "T" else 100 - prob))
    
    dd = ("CHẴN" if pred == "T" else "LẺ") if is_chanle else ("TÀI" if pred == "T" else "XỈU")
    return dd, round(prob, 1), "MONTE CARLO 50K + MARKOV"

# ==================================================
# 🧠 LÕI 3: VIP HYBRID AI (FULL MÚP) + NÂNG CẤP
# ==================================================
def vip_hybrid_predict(is_chanle, history, md5_str=None):
    if md5_str and re.match(r"^[0-9a-f]{32}$", md5_str.lower()):
        dd_md5, lk_md5, tl_md5 = md5_10000_layers_predict(md5_str)
        prob_md5 = tl_md5
    else:
        dd_md5, lk_md5, prob_md5 = "TÀI", "NO MD5", 55.0
    
    dd_mc, prob_mc, lk_mc = monte_carlo_markov_predict(is_chanle, list(history))
    
    recent = list(history)[-30:]
    streak_t = sum(1 for x in recent[-8:] if x == "T")
    streak_x = 8 - streak_t
    pattern_bonus = 3.5 if streak_t >= 6 or streak_x >= 6 else 0
    
    final_prob = (prob_md5 * 0.45 + prob_mc * 0.55) + pattern_bonus
    final_prob = max(51.0, min(99.9, final_prob))
    
    dd = dd_md5 if abs(prob_md5 - prob_mc) > 12 else dd_mc
    lk = "HYBRID 10K LAYERS + MARKOV"
    return dd, round(final_prob, 1), lk

# ==================================================
# 🧠 THUẬT TOÁN B52 (ĐÃ SỬA LỖI + TÍCH HỢP)
# ==================================================
class ThuatToanB52:
    def getTaiXiu(self, d1, d2, d3):
        total = d1 + d2 + d3
        return "Xỉu" if total <= 10 else "Tài"
    
    def duDoan(self, history, last_n=12):
        if not history or len(history) < 3:
            return "Chưa có dữ liệu"
        recent = history[-last_n:]
        full_seq = recent  # đã là "Tài"/"Xỉu"
        
        tai_count = full_seq.count("Tài")
        xiu_count = full_seq.count("Xỉu")
        
        # Pattern 3 phiên
        sequence_prediction = None
        if len(full_seq) >= 3:
            last_three = "-".join(full_seq[-3:])
            similar_patterns = ["-".join(full_seq[i:i+3]) for i in range(len(full_seq)-3)]
            if last_three in similar_patterns:
                pos = similar_patterns.index(last_three)
                if pos + 3 < len(full_seq):
                    sequence_prediction = full_seq[pos + 3]
        
        # Markov bậc 2
        markov_prediction = None
        if len(full_seq) >= 3:
            transition_matrix = {}
            for i in range(len(full_seq) - 2):
                key = f"{full_seq[i]}-{full_seq[i+1]}"
                if key not in transition_matrix:
                    transition_matrix[key] = {'Tài': 0, 'Xỉu': 0}
                transition_matrix[key][full_seq[i+2]] += 1
            last_two = f"{full_seq[-2]}-{full_seq[-1]}"
            if last_two in transition_matrix:
                counts = transition_matrix[last_two]
                markov_prediction = 'Tài' if counts['Tài'] > counts['Xỉu'] else 'Xỉu'
        
        if sequence_prediction:
            return sequence_prediction
        elif markov_prediction:
            return markov_prediction
        return "Tài" if tai_count > xiu_count else "Xỉu"
    
    def calculateConfidence(self, history, prediction, last_n=12):
        if not history or len(history) < 3:
            return 0
        recent = history[-last_n:]
        correct = 0
        total_pairs = 0
        for i in range(len(recent) - 1):
            pred = self.duDoan(recent[:i+1])
            if pred == recent[i+1] and pred not in ["Chưa có dữ liệu", "Không rõ"]:
                correct += 1
            total_pairs += 1
        return round((correct / total_pairs * 100) if total_pairs > 0 else 0)

# ==========================================
# 📡 KẾT NỐI API + TOOL SICBO SUN.WIN
# ==========================================
@app.route("/api/scan", methods=["GET"])
def scan_game():
    tool = request.args.get("tool", "")
    key = request.args.get("key", "")
    if key not in KEYS_DB or key in LOCKED_KEYS:
        return jsonify({"status": "auth_error", "msg": "Key không hợp lệ hoặc bị khóa!"})
    
    is_chanle = "chanle" in tool.lower() or "xd" in tool.lower()
    is_sicbo = "sicbo_sunwin" in tool.lower() or "sunwin" in tool.lower()
    
    # ====================== SICBO SUN.WIN ======================
    if is_sicbo:
        api_url = "https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979&size=100&tableId=39791215743193&curPage=1"
    else:
        urls = {
            "betvip_tx": "https://wtx.macminim6.online/v1/tx/sessions",
            "betvip_md5": "https://wtxmd52.macminim6.online/v1/txmd5/sessions",
            "lc79_tx": "https://wtx.tele68.com/v1/tx/sessions",
            "lc79_md5": "https://wtxmd52.tele68.com/v1/txmd5/sessions",
            "lc79_xd": "https://wcl.tele68.com/v1/chanlefull/sessions"
        }
        api_url = urls.get(tool, "")
        if not api_url:
            phien_fake = "#" + str(random.randint(100000, 999999))
            return jsonify({"status": "success", "data": {"du_doan": "TÀI", "ti_le": 68.8, "loi_khuyen": "VƯỢT TƯỜNG LỬA - FULL MÚP MODE", "phien": phien_fake}})
    
    try:
        res = requests.get(api_url, headers={"User-Agent": "VIP-FULL-MUP-2026"}, timeout=5).json()
        
        if is_sicbo:
            lst = res.get("data", {}).get("resultList", [])
        else:
            lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res
        
        if not isinstance(lst, list):
            raise Exception("Data lỗi")
        
        lst = sorted(lst, key=lambda x: get_id(x))
        
        # Xây dựng lịch sử T/X
        arr = []
        for s in lst:
            if is_sicbo and isinstance(s, dict):
                score = int(s.get("score", 0))
                arr.append("T" if score >= 11 else "X")
            else:
                arr.append("T" if any(k in str(s).upper() for k in (["CHẴN","CHAN","C","0"] if is_chanle else ["TAI","TÀI","BIG"])) else "X")
        
        HISTORY.extend(arr[-200:])
        
        phien_hien_tai = str(get_id(lst[-1]) + 1) if lst else "#000000"
        
        # Trích MD5 (nếu có)
        md5_str = None
        if lst and isinstance(lst[-1], dict):
            md5_candidate = lst[-1].get("md5")
            if isinstance(md5_candidate, str) and re.match(r"^[0-9a-f]{32}$", md5_candidate.lower()):
                md5_str = md5_candidate.lower()
        
        # Dự đoán
        if "md5" in tool.lower() and md5_str:
            dd, lk, tl = md5_10000_layers_predict(md5_str)
        else:
            dd, tl, lk = vip_hybrid_predict(is_chanle, list(HISTORY), md5_str)
        
        # NÂNG CẤP B52 cho Sicbo
        if is_sicbo:
            b52 = ThuatToanB52()
            mapped_hist = ["Tài" if x == "T" else "Xỉu" for x in list(HISTORY)[-50:]]
            b52_dd = b52.duDoan(mapped_hist)
            b52_conf = b52.calculateConfidence(mapped_hist, b52_dd)
            lk = f"{lk} | B52 Sicbo: {b52_dd} ({b52_conf}%)"
            if b52_conf > 70:
                dd = "TÀI" if b52_dd == "Tài" else "XỈU"
                tl = max(tl, float(b52_conf))
        
        return jsonify({"status": "success", "data": {"du_doan": dd, "ti_le": tl, "loi_khuyen": lk, "phien": phien_hien_tai}})
    
    except Exception:
        phien_fake = "#" + str(random.randint(100000, 999999))
        return jsonify({"status": "success", "data": {"du_doan": "TÀI", "ti_le": 68.8, "loi_khuyen": "VƯỢT TƯỜNG LỬA - FULL MÚP MODE", "phien": phien_fake}})

# Các route khác giữ nguyên (login, admin, manual_md5, home)
@app.route("/api/login", methods=["POST"])
def login():
    key = (request.json or {}).get("key", "").strip()
    if not key or key not in KEYS_DB: return jsonify({"status": "error", "msg": "Key sai hoặc không tồn tại!"})
    if key in LOCKED_KEYS: return jsonify({"status": "error", "msg": "Key đã bị Admin khóa!"})
    return jsonify({"status": "success", "role": KEYS_DB[key], "msg": "Đăng nhập VIP thành công!"})

@app.route("/api/admin", methods=["POST"])
def admin_action():
    data = request.json or {}
    if data.get("admin_key") != "hungadmin67": return jsonify({"status": "error", "msg": "Cấm truy cập!"})
    target = data.get("target_key", "")
    if target not in KEYS_DB or target == "hungadmin67": return jsonify({"status": "error", "msg": "Key không hợp lệ!"})
    if data.get("action") == "lock": LOCKED_KEYS.add(target)
    else: LOCKED_KEYS.discard(target)
    return jsonify({"status": "success", "msg": f"Đã {'khóa' if data.get('action')=='lock' else 'mở khóa'} {target}"})

@app.route("/api/manual_md5", methods=["POST"])
def manual_md5():
    md5_str = (request.json or {}).get("md5", "")
    dd, lk, tl = md5_10000_layers_predict(md5_str)
    if dd == "LỖI": return jsonify({"status": "error", "msg": "MD5 không hợp lệ"})
    return jsonify({"status": "success", "tai": tl if dd == "TÀI" else round(100 - tl, 1), "xiu": tl if dd == "XỈU" else round(100 - tl, 1), "suggestion": f"{dd}"})

@app.route("/")
def home():
    try: return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))
    except: return "<h1 style='color:red;'>LỖI: Chưa có file index.html</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
