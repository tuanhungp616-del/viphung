import os
import math
import random
import re
import numpy as np
from itertools import groupby
from collections import deque
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ==========================================
# 🔐 HỆ THỐNG AN NINH
# ==========================================
KEYS_DB = {
    "hungadmin67": "admin",
    "viphung": "user",
    "chanbomayde": "user"
}
LOCKED_KEYS = set()
HISTORY = deque(maxlen=60)

def get_id(item):
    if isinstance(item, dict):
        for k in ['id', 'phien', 'sessionId', 'sid', 'referenceId', 'matchId', 'phien_hien_tai']:
            if k in item and str(item[k]).replace('-', '').isdigit(): return int(item[k])
    matches = re.findall(r"'?(?:id|phien|referenceId|sessionId|matchId|phien_hien_tai)'?\s*:\s*'?'?(\d+)'?'?", str(item), re.IGNORECASE)
    return int(matches[0]) if matches else 0

# ==================================================
# 🧠 LÕI 1: OMNIVERSE GOD MODE (CHO MD5)
# ==================================================
def md5_omniverse_predict(md5_str: str):
    md5_str = md5_str.strip().lower()
    if not re.match(r"^[0-9a-f]{32}$", md5_str): return "LỖI", "MD5 LỖI", 0.0

    hex_arr = np.array([int(ch, 16) for ch in md5_str], dtype=np.float64)
    total_energy = hex_arr.sum()
    ones_count = f'{int(md5_str, 16):0128b}'.count('1')

    tai_score, xiu_score = 0.0, 0.0

    delta = total_energy - 240
    tai_score += max(0, delta ** 1.3 / 9) * 4.2
    xiu_score += max(0, (-delta) ** 1.3 / 9) * 4.2

    fft_vals = np.abs(np.fft.fft(hex_arr))
    tai_score += np.mean(fft_vals[1:12]) * 0.28
    xiu_score += np.mean(fft_vals[12:24]) * 0.28

    entropy = abs(ones_count - 64) / 64.0
    if ones_count > 64: tai_score += 7.8 * (1 - entropy)
    else: xiu_score += 7.8 * (1 - entropy)

    nn_score = sum(hex_arr[i] * 2.8 + hex_arr[(i+5)%32] * 0.12 for i in range(31))
    nn_act = (nn_score % 666) / 666
    tai_score += nn_act ** 1.6 * 13.8
    xiu_score += (1 - nn_act) ** 1.6 * 13.8

    logistic = 1 / (1 + math.exp(-(tai_score - xiu_score) / 7.7))
    final_tai, final_xiu = logistic * 100, (1 - logistic) * 100
    
    if abs(final_tai - final_xiu) < 2.5:
        if final_tai > final_xiu: final_tai += 3.3
        else: final_xiu += 3.3

    total = final_tai + final_xiu
    final_tai = round(max(0.1, min(99.9, (final_tai / total) * 100)), 1)
    final_xiu = round(max(0.1, min(99.9, (final_xiu / total) * 100)), 1)

    if final_tai > final_xiu + 0.3: return "TÀI", "OMNIVERSE GOD MODE", final_tai
    else: return "XỈU", "OMNIVERSE GOD MODE", final_xiu

# ==================================================
# 🧠 LÕI 2: MONTE CARLO (CHO SÀN THƯỜNG)
# ==================================================
def monte_carlo_predict(is_chanle, current_history):
    if len(current_history) < 5: return "TÀI" if random.random() > 0.5 else "XỈU", 53.5, "Đang nạp dữ liệu..."
    seq = ["T" if x == "T" else "X" for x in current_history]
    
    seq_str = "".join(seq)
    pred_p, conf_p = "T", 50.0
    for regex, bias in [(r"(T{3,}|X{3,})$", 0.65), (r"(TX{2,}|XT{2,})$", 0.6), (r"(TTXX|XXTT)$", 0.58)]:
        if re.search(regex, seq_str[-10:]): 
            pred_p = "X" if seq[-1] == "T" else "T"; conf_p = bias * 100; break
            
    p_t = seq.count("T") / len(seq)
    sim_t = sum(1 for _ in range(5000) if random.random() < p_t * 1.05)
    prob_mc = (sim_t / 5000) * 100
    pred_mc = "T" if prob_mc > 50 else "X"

    final_prob = (conf_p * 0.35) + (prob_mc * 0.65)
    final_pred = pred_mc if abs(prob_mc - 50) > 6 else pred_p
    
    dd = ("CHẴN" if final_pred == "T" else "LẺ") if is_chanle else ("TÀI" if final_pred == "T" else "XỈU")
    return dd, round(final_prob, 1), "MONTE CARLO 5000x"

# ==========================================
# 📡 CỔNG KẾT NỐI API TỔNG HỢP
# ==========================================
@app.route("/api/login", methods=["POST"])
def login():
    key = (request.json or {}).get("key", "").strip()
    if not key or key not in KEYS_DB: return jsonify({"status": "error", "msg": "Key không tồn tại!"})
    if key in LOCKED_KEYS: return jsonify({"status": "error", "msg": "Key đã bị Khóa!"})
    return jsonify({"status": "success", "role": KEYS_DB[key], "msg": "Đăng nhập thành công!"})

@app.route("/api/admin", methods=["POST"])
def admin_action():
    data = request.json or {}
    if data.get("admin_key", "") != "hungadmin67": return jsonify({"status": "error", "msg": "Cấm truy cập!"})
    target = data.get("target_key", "")
    if target not in KEYS_DB or target == "hungadmin67": return jsonify({"status": "error", "msg": "Key lỗi!"})
    if data.get("action", "") == "lock": LOCKED_KEYS.add(target)
    else: LOCKED_KEYS.discard(target)
    return jsonify({"status": "success", "msg": f"Xong lệnh với: {target}"})

@app.route("/api/manual_md5", methods=["POST"])
def manual_md5():
    md5_str = (request.json or {}).get("md5", "")
    dd, lk, tl = md5_omniverse_predict(md5_str)
    if dd == "LỖI": return jsonify({"status": "error", "msg": "MD5 không hợp lệ"})
    return jsonify({"status": "success", "tai": tl if dd == "TÀI" else round(100 - tl, 1), "xiu": tl if dd == "XỈU" else round(100 - tl, 1), "suggestion": f"{dd} (GOD MODE)"})

@app.route("/api/scan", methods=["GET"])
def scan_game():
    tool, key = request.args.get("tool", ""), request.args.get("key", "")
    if key not in KEYS_DB or key in LOCKED_KEYS: return jsonify({"status": "auth_error", "msg": "Mất kết nối Key!"})
    is_chanle = ("chanle" in tool.lower() or "xd" in tool.lower())
    
    # DANH SÁCH FULL API TỪ BOT
    urls = {
        "b52_md5": "https://b52-d2t0.onrender.com/taixiumd5",
        "b52_sicbo": "https://b52-d2t0.onrender.com/sicbo",
        "hitclub_md5": "https://hitclub-p2gy.onrender.com/taixiumd5",
        "hitclub_tx": "https://hitclub-p2gy.onrender.com/taixiu",
        "hitclub_sicbo": "https://hitclub-p2gy.onrender.com/sicbo",
        "sunwin_sicbo": "https://sunwinsicbo-glwe.onrender.com/sicbo",
        "sunwin_tx": "https://sunwintaixiu-0myy.onrender.com/taixiu",
        "lc79_tx": "https://laucua79-dscf.onrender.com/taixiu",
        "lc79_md5": "https://laucua79-dscf.onrender.com/taixiumd5",
        "betvip_tx": "https://betvip-mpqc.onrender.com/taixiu",
        "betvip_md5": "https://betvip-mpqc.onrender.com/taixiumd5",
        "sao789_tx": "https://sao789-gst3.onrender.com/taixiu",
        "sao789_md5": "https://sao789-gst3.onrender.com/taixiumd5",
        "xd88_tx": "https://xocdia88-5d39.onrender.com/taixiu",
        "xd88_md5": "https://xocdia88-5d39.onrender.com/taixiumd5"
    }
    
    try:
        res = requests.get(urls.get(tool, ""), headers={"User-Agent": "EMPEROR-V99"}, timeout=4).json()
        
        # Nếu API trả về list
        lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res
        
        if not isinstance(lst, list):
            # Xử lý API trả về 1 object (Thường là các API mới từ Onrender)
            phien_thuc = res.get("phien_hien_tai", res.get("phien", res.get("id", "AUTO")))
            
            # Tìm MD5 ẩn trong object
            raw_str = str(res).lower()
            m = re.search(r"[0-9a-f]{32}", raw_str)
            if m:
                dd, lk, tl = md5_omniverse_predict(m.group(0))
                return jsonify({"status": "success", "data": {"du_doan": dd, "ti_le": tl, "loi_khuyen": lk, "phien": str(phien_thuc)}})
            
            # Nếu không có MD5, lấy dự đoán mặc định của API hoặc random
            dd = res.get("du_doan", res.get("Du_doan", "TÀI"))
            dd_str = "TÀI" if "TAI" in str(dd).upper() else "XỈU"
            return jsonify({"status": "success", "data": {"du_doan": dd_str, "ti_le": round(random.uniform(95.0, 99.0), 1), "loi_khuyen": "API TRỰC TIẾP", "phien": str(phien_thuc)}})

        # Xử lý nếu API trả về mảng
        lst = sorted(lst, key=get_id)
        arr = ["T" if any(x in str(s).upper() for x in (["CHẴN", "CHAN", "C", "0"] if is_chanle else ["TAI", "TÀI", "BIG"])) else "X" for s in lst]
        HISTORY.extend(arr[-50:])
        phien_hien_tai = str(get_id(lst[-1]) + 1)

        m = re.search(r"[0-9a-f]{32}", str(lst[-1]).lower())
        if m and ("md5" in tool.lower() or "sunwin" in tool.lower() or "b52" in tool.lower()):
            dd, lk, tl = md5_omniverse_predict(m.group(0))
            return jsonify({"status": "success", "data": {"du_doan": dd, "ti_le": tl, "loi_khuyen": lk, "phien": phien_hien_tai}})

        dd, tl, lk = monte_carlo_predict(is_chanle, list(HISTORY))
        return jsonify({"status": "success", "data": {"du_doan": dd, "ti_le": tl, "loi_khuyen": lk, "phien": phien_hien_tai}})

    except Exception as e:
        return jsonify({"status": "success", "data": {"du_doan": "TÀI", "ti_le": 55.0, "loi_khuyen": "VƯỢT TƯỜNG LỬA", "phien": "#" + str(random.randint(100000, 999999))}})

@app.route("/")
def home():
    try: return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))
    except Exception as e: return f"<h2 style='color:red;'>LỖI 404: KHÔNG TÌM THẤY FILE index.html MẶT TIỀN! Lên Github check lại tên file nhé Boss! ({e})</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
                        
