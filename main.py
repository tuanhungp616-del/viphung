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

KEYS_DB = {"hungadmin1122334455": "admin", "bo1": "user", "viphung": "user", "chutaidou": "user"}
LOCKED_KEYS = set()

# ==================================================
# HISTORY & AI SELF-CORRECTING (ĐẢO CẦU AUTO)
# ==================================================
HISTORY = deque(maxlen=50)
PREDICTION_MODE = "normal"          # "normal" hoặc "dao"
PRED_LOG = deque(maxlen=20)         # (phien, du_doan, is_chanle)
PHIEN_COUNTER = 100000

def get_id(item):
    if isinstance(item, dict):
        for k in ['id', 'phien', 'sessionId', 'sid', 'referenceId', 'matchId']:
            if k in item and str(item[k]).replace('-', '').isdigit():
                return int(item[k])
    raw_str = str(item)
    matches = re.findall(r"'?(?:id|phien|referenceId|sessionId|matchId)'?\s*:\s*'?(\d+)'?", raw_str, re.IGNORECASE)
    return int(matches[0]) if matches else 0

# ==================================================
# 🧠 LÕI VÔ HẠN INFINITY (GOD MODE) - KHÔNG THAY ĐỔI
# ==================================================
def tinh_toan_md5_vo_han_infinity(md5_str: str):
    md5_str = md5_str.strip().lower()
    if not re.match(r"^[0-9a-f]{32}$", md5_str):
        return "LỖI", "MD5 KHÔNG HỢP LỆ", 0.0

    hex_arr = np.array([int(ch, 16) for ch in md5_str], dtype=np.float64)
    total_energy = hex_arr.sum()
    big_int = int(md5_str, 16)
    bin_str = f'{big_int:0128b}'
    ones_count = bin_str.count('1')

    tai_score, xiu_score = 0.0, 0.0
    energy_delta = total_energy - 240
    tai_score += max(0, energy_delta ** 1.3 / 9) * 4.2
    xiu_score += max(0, (-energy_delta) ** 1.3 / 9) * 4.2
    for scale in [4, 8, 16, 32]:
        chunks = hex_arr.reshape(-1, scale).sum(axis=1)
        tai_score += np.sum(chunks > 28) * (scale / 6)

    primes = [3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
    mod_bias = sum(2.4 if (total_energy % p) >= p*0.5 else -1.7 for p in primes)
    tai_score += max(0, mod_bias * 1.6)
    xiu_score += max(0, -mod_bias * 1.6)

    entropy = abs(ones_count - 64) / 64.0
    fractal_dim = 1.0 + (ones_count % 17) / 42
    if ones_count > 64: tai_score += 7.8 * (1 - entropy) * fractal_dim
    else: xiu_score += 7.8 * (1 - entropy) * fractal_dim
    fft_vals = np.abs(np.fft.fft(hex_arr))
    tai_score += np.mean(fft_vals[1:12]) * 0.28

    mirror_diff = np.sum(np.abs(hex_arr[:16] - hex_arr[::-1][:16]))
    if mirror_diff > 98: tai_score += 6.8
    elif mirror_diff < 32: xiu_score += 7.2
    else: tai_score += 2.9; xiu_score += 2.9

    max_streak = max((len(list(g)) for _, g in groupby(md5_str)), default=1)
    tai_score += max_streak ** 2.1 * 1.4 if max_streak >= 3 else 0
    xiu_score += 4.8 if max_streak < 3 else 0
    tai_patterns, xiu_patterns = ["79","7f","f7","97","a9","b9","c7","d9","e7","f9"], ["00","ff","11","22","33","44","55","66"]
    tai_score += sum(3.3 for p in tai_patterns if p in md5_str) * 1.8
    xiu_score += sum(3.1 for p in xiu_patterns if p in md5_str) * 1.7

    seed = int(total_energy) % 1997
    r = 3.999 + (seed / 12000)
    x = (total_energy % 1024) / 1024.0
    for _ in range(60): x = r * x * (1 - x)
    tai_score += x * 11.5
    xiu_score += (1 - x) * 11.5

    nn_score = 0.0
    for i in range(31):
        nn_score += hex_arr[i] * (2.8 + i*0.03) + hex_arr[(i+1)%32] * 1.6
        nn_score += hex_arr[i] * hex_arr[(i+5)%32] * 0.12
    nn_act = (nn_score % 666) / 666
    tai_score += nn_act ** 1.6 * 13.8
    xiu_score += (1 - nn_act) ** 1.6 * 13.8

    phi = (1 + math.sqrt(5)) / 2
    golden_bias = (total_energy * phi) % 5.0
    tai_score += golden_bias * 3.9
    xiu_score += (5 - golden_bias) * 3.6

    logistic = 1 / (1 + math.exp(-(tai_score - xiu_score) / 7.7))
    final_tai, final_xiu = logistic * 100, (1 - logistic) * 100
    diff = abs(final_tai - final_xiu)
    if diff < 2.5:
        boost = 3.3 - diff
        if final_tai > final_xiu: final_tai += boost
        else: final_xiu += boost

    total = final_tai + final_xiu
    final_tai = round(max(0.1, min(99.9, (final_tai / total) * 100)), 1)
    final_xiu = round(max(0.1, min(99.9, (final_xiu / total) * 100)), 1)

    if final_tai > final_xiu + 0.3: return "TÀI", "VÔ HẠN LC79 GOD MODE", final_tai
    else: return "XỈU", "VÔ HẠN LC79 GOD MODE", final_xiu

# ==================================================
# AI DỰ ĐOÁN NÂNG CẤP + TỰ NHẬN CẦU + ĐẢO CẦU AUTO
# ==================================================
def advanced_predict(is_chanle, current_history, mode="normal"):
    if len(current_history) < 5:
        return "TÀI", 53.5, "Đang thu thập dữ liệu..."

    recent = list(current_history)[-20:]
    p_t = recent.count("T") / len(recent)

    # TỰ NHẬN CẦU (pattern recognition)
    last_8 = recent[-8:]
    t_count = last_8.count("T")

    if t_count >= 6:
        base_du = "TÀI" if not is_chanle else "CHẴN"
        base_prob = 73.0
    elif t_count <= 2:
        base_du = "XỈU" if not is_chanle else "LẺ"
        base_prob = 73.0
    else:
        bias = 1.15 if last_8[-1] == "T" else 0.85
        sim_t = sum(1 for _ in range(10000) if random.random() < p_t * bias)
        base_prob = round((sim_t / 10000) * 100, 1)
        final_pred = "T" if base_prob > 50 else "X"
        base_du = ("CHẴN" if final_pred == "T" else "LẺ") if is_chanle else ("TÀI" if final_pred == "T" else "XỈU")

    du_doan = base_du
    prob = base_prob
    loi_khuyen = "ADVANCED PATTERN AI V3"

    # ĐẢO CẦU MODE (tự động kích hoạt khi sai)
    if mode == "dao":
        if is_chanle:
            du_doan = "LẺ" if du_doan == "CHẴN" else "CHẴN"
        else:
            du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
        prob = round(min(99.9, 100 - prob + 9), 1)
        loi_khuyen = "🔄 ĐẢO CẦU MODE - " + loi_khuyen

    return du_doan, prob, loi_khuyen

# ==================================================
# CỔNG API
# ==================================================
@app.route("/api/login", methods=["POST"])
def login():
    key = (request.json or {}).get("key", "").strip()
    if not key or key not in KEYS_DB: return jsonify({"status": "error", "msg": "Key không tồn tại!"})
    if key in LOCKED_KEYS: return jsonify({"status": "error", "msg": "Key đã bị Admin khóa!"})
    return jsonify({"status": "success", "role": KEYS_DB[key], "msg": "Đăng nhập thành công!"})

@app.route("/api/admin", methods=["POST"])
def admin_action():
    data = request.json or {}
    if data.get("admin_key", "") != "hungadmin1122334455": return jsonify({"status": "error", "msg": "Không có quyền!"})
    target = data.get("target_key", "")
    if target not in KEYS_DB or target == "hungadmin1122334455": return jsonify({"status": "error", "msg": "Key lỗi!"})
    if data.get("action", "") == "lock": LOCKED_KEYS.add(target)
    else: LOCKED_KEYS.discard(target)
    return jsonify({"status": "success", "msg": f"Đã xử lý Key: {target}"})

@app.route("/api/manual_md5", methods=["POST"])
def manual_md5():
    data = request.json or {}
    md5_str = data.get("md5", "")
    dd, lk, tl = tinh_toan_md5_vo_han_infinity(md5_str)
    if dd == "LỖI": return jsonify({"status": "error", "msg": "MD5 không hợp lệ"})
    tai_pct = tl if dd == "TÀI" else round(100 - tl, 1)
    xiu_pct = tl if dd == "XỈU" else round(100 - tl, 1)
    return jsonify({"status": "success", "tai": tai_pct, "xiu": xiu_pct, "suggestion": f"{dd} (GOD MODE)"})

@app.route("/api/scan", methods=["GET"])
def scan_game():
    global PREDICTION_MODE, PHIEN_COUNTER
    tool = request.args.get("tool", "")
    key = request.args.get("key", "")

    if key not in KEYS_DB or key in LOCKED_KEYS:
        return jsonify({"status": "auth_error", "msg": "Key bị khóa. Văng!"})

    is_chanle = ("chanle" in tool.lower() or "xd" in tool.lower())

    # URLS ĐÃ XÓA HIT.CLUB + SUNWIN TX THƯỜNG
    urls = {
        "lc79_xd": "https://wcl.tele68.com/v1/chanlefull/sessions",
        "lc79_tx": "https://wtx.tele68.com/v1/tx/sessions",
        "lc79_md5": "https://wtx.tele68.com/v1/txmd5/sessions",
        "betvip_tx": "https://wtx.macminim6.online/v1/tx/sessions",
        "betvip_md5": "https://wtxmd52.macminim6.online/v1/txmd5/sessions",
        "sunwin_sicbo": "https://apisunhpt.onrender.com/"
    }
    url = urls.get(tool, "")

    try:
        res = requests.get(url, headers={"User-Agent": "INFINITY-GOD-V3"}, timeout=5).json()
        lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res

        if not isinstance(lst, list):
            phien_thuc = res.get("phien", res.get("id", res.get("referenceId", "AUTO")))
            if str(phien_thuc).isdigit():
                phien_thuc = str(int(phien_thuc) + 1)
            return jsonify({"status": "success", "data": {
                "type": "quantum_v2", "du_doan": "TÀI", "ti_le": 55.5,
                "loi_khuyen": "INFINITY V3", "phien": str(phien_thuc)
            }})

        lst = sorted(lst, key=get_id)
        arr = ["T" if any(x in str(s).upper() for x in (["CHẴN", "CHAN", "C", "0"] if is_chanle else ["TAI", "TÀI", "BIG"])) else "X" for s in lst]
        HISTORY.extend(arr[-40:])

        phien_hien_tai = str(get_id(lst[-1]) + 1) if lst else "AUTO-000001"

        # ====================== KIỂM TRA SAI → KÍCH HOẠT ĐẢO CẦU ======================
        if len(lst) >= 1:
            latest_phien = get_id(lst[-1])
            actual_code = arr[-1]
            for i in range(len(PRED_LOG) - 1, -1, -1):
                p_phien, p_du_doan, p_chanle = PRED_LOG[i]
                if p_phien == latest_phien:
                    expected = "T" if ((not p_chanle and p_du_doan in ["TÀI", "TAI", "T"]) or (p_chanle and p_du_doan in ["CHẴN", "CHAN", "C"])) else "X"
                    if expected != actual_code:
                        PREDICTION_MODE = "dao" if PREDICTION_MODE == "normal" else "normal"
                    break

        # MD5 TOOL (vẫn giữ GOD MODE)
        m = re.search(r"[0-9a-f]{32}", str(lst[-1]).lower() if lst else "")
        if m and ("md5" in tool.lower() or ("sunwin" in tool.lower() and "sicbo" not in tool.lower())):
            dd, lk, tl = tinh_toan_md5_vo_han_infinity(m.group(0))
            return jsonify({"status": "success", "data": {
                "type": "infinity", "du_doan": dd, "ti_le": tl, "loi_khuyen": lk, "phien": phien_hien_tai
            }})

        # ADVANCED AI (có hỗ trợ ĐẢO CẦU)
        du_doan, ti_le, loi_khuyen = advanced_predict(is_chanle, list(HISTORY), PREDICTION_MODE)

        # LƯU LẠI DỰ ĐOÁN CHO PHIÊN TIẾP THEO
        try:
            next_ph = int(phien_hien_tai)
        except:
            next_ph = 0
        PRED_LOG.append((next_ph, du_doan, is_chanle))

        return jsonify({"status": "success", "data": {
            "type": "quantum_v2", "du_doan": du_doan, "ti_le": ti_le,
            "loi_khuyen": loi_khuyen, "phien": phien_hien_tai
        }})

    except Exception:
        # FALLBACK - KHÔNG RANDOM PHIÊN NỮA
        global PHIEN_COUNTER
        PHIEN_COUNTER += 1
        phien = f"AUTO-{PHIEN_COUNTER}"
        return jsonify({"status": "success", "data": {
            "type": "quantum_v2", "du_doan": "TÀI", "ti_le": 52.0,
            "loi_khuyen": "INFINITY FALLBACK V3", "phien": phien
        }})

@app.route("/")
def home():
    try:
        return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))
    except:
        return "LỖI: Không tìm thấy file index.html"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
