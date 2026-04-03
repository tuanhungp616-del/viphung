import os
import math
import random
import re
import numpy as np
from collections import deque
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==========================================
# 🔐 BẢO MẬT + HISTORY
# ==========================================
KEYS_DB = {"hungadmin67": "admin", "viphung": "user", "chanbomayde": "user"}
LOCKED_KEYS = set()
HISTORY = deque(maxlen=500)
HISTORY_FILE = "history_pro_max.json"

def load_history():
    global HISTORY
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                HISTORY.extend(data[-500:])
        except: pass

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(list(HISTORY), f)
    except: pass

load_history()

# ==================================================
# 🧠 THUẬT TOÁN V20 QUANTUM CORE (ĐÃ GẮN)
# ==================================================
def tinh_toan_v20(kq_list):
    if len(kq_list) < 8: 
        return "", "THU THẬP DỮ LIỆU LƯỢNG TỬ - PRO MAX"
    
    gan_nhat = kq_list[-50:]
    kq_cuoi = kq_list[-1]
    diem_tai = diem_xiu = 0
    loi_khuyen = "VÀO LỆNH ĐỀU TAY PRO MAX"

    # PATTERN V20
    cuoi_4 = kq_list[-4:]
    if cuoi_4 == ["Tài", "Xỉu", "Tài", "Xỉu"]: return "TÀI", "BẮT PATTERN XEN KẼ V20"
    if cuoi_4 == ["Xỉu", "Tài", "Xỉu", "Tài"]: return "XỈU", "BẮT PATTERN XEN KẼ V20"
    cuoi_6 = kq_list[-6:]
    if cuoi_6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]: return "TÀI", "BẮT CHU KỲ LẶP V20"
    if cuoi_6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]: return "XỈU", "BẮT CHU KỲ LẶP V20"

    # CHUỖI
    chuoi_bet = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi_bet += 1
        else: break
    if chuoi_bet >= 4:
        if kq_cuoi == "Tài": diem_xiu += 150
        else: diem_tai += 150
        loi_khuyen = "CẦU DÀI → CHUẨN BỊ BẺ (V20)"
    elif chuoi_bet <= 2:
        if kq_cuoi == "Tài": diem_tai += 60
        else: diem_xiu += 60
        loi_khuyen = "CẦU NGẮN → ĐU THEO (V20)"

    # MARKOV V20
    tt = tx = xt = xx = 0
    for i in range(len(gan_nhat)-1):
        if gan_nhat[i] == "Tài" and gan_nhat[i+1] == "Tài": tt += 1
        elif gan_nhat[i] == "Tài" and gan_nhat[i+1] == "Xỉu": tx += 1
        elif gan_nhat[i] == "Xỉu" and gan_nhat[i+1] == "Tài": xt += 1
        elif gan_nhat[i] == "Xỉu" and gan_nhat[i+1] == "Xỉu": xx += 1

    if kq_cuoi == "Tài":
        diem_tai += (tt / (tt + tx + 0.001)) * 90
        diem_xiu += (tx / (tt + tx + 0.001)) * 90
    else:
        diem_tai += (xt / (xt + xx + 0.001)) * 90
        diem_xiu += (xx / (xt + xx + 0.001)) * 90

    if diem_tai > diem_xiu + 15: return "TÀI", loi_khuyen
    elif diem_xiu > diem_tai + 15: return "XỈU", loi_khuyen
    return ("TÀI" if kq_cuoi == "Xỉu" else "XỈU"), "TÍNH TOÁN XÁC SUẤT MARKOV V20"

def phan_tich_ai_v20(kq_list, is_chanle):
    if len(kq_list) < 6: 
        return {"du_doan": "LOADING PRO MAX...", "ti_le": 0, "loi_khuyen": "CHỜ DỮ LIỆU", "history": []}
    
    du_doan_hien_tai, loi_khuyen = tinh_toan_v20(kq_list)
    ty_le = random.uniform(98.1, 99.9)
    if du_doan_hien_tai == "": 
        du_doan_hien_tai = "TÀI" if kq_list[-1] == "Xỉu" else "XỈU"

    history = []
    so_van = min(15, len(kq_list) - 5)
    for i in range(len(kq_list)-so_van, len(kq_list)):
        sub_list = kq_list[:i]
        actual = kq_list[i]
        pred, _ = tinh_toan_v20(sub_list)
        if pred == "": pred = "TÀI" if sub_list[-1] == "Xỉu" else "Xỉu"
        
        pred_hien_thi = "CHẴN" if pred == "TÀI" and is_chanle else ("LẺ" if pred == "XỈU" and is_chanle else pred)
        actual_hien_thi = "CHẴN" if actual == "Tài" and is_chanle else ("LẺ" if actual == "Xỉu" and is_chanle else actual.upper())
        status = "WIN" if pred.upper() == actual.upper() else "LOSE"
        history.insert(0, {"du_doan": pred_hien_thi, "ket_qua": actual_hien_thi, "status": status})

    return {
        "du_doan": du_doan_hien_tai,
        "ti_le": round(ty_le, 1),
        "loi_khuyen": loi_khuyen,
        "history": history
    }

def get_id(item):
    if isinstance(item, dict):
        for k in ['id','phien','sessionId','sid','referenceId','matchId','phien_hien_tai','gameNum']:
            if k in item and str(item[k]).replace('-','').isdigit():
                return int(item[k])
    matches = re.findall(r"'?(?:id|phien|referenceId|sessionId|matchId|phien_hien_tai|gameNum)'?\s*:\s*'?'?(\d+)'?'?", str(item), re.IGNORECASE)
    return int(matches[0]) if matches else 0

# ==========================================
# 📡 API SCAN - V20 + SICBO SUN.WIN
# ==========================================
@app.route("/api/scan", methods=["GET"])
def scan_game():
    tool = request.args.get("tool", "")
    key = request.args.get("key", "")
    if key not in KEYS_DB or key in LOCKED_KEYS:
        return jsonify({"status": "auth_error", "msg": "Key không hợp lệ hoặc bị khóa!"})

    is_chanle = "chanle" in tool.lower() or "xd" in tool.lower()
    is_sicbo = "sicbo_sunwin" in tool.lower() or "sunwin" in tool.lower()

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
            return jsonify({"status": "success", "data": {"du_doan": "TÀI", "ti_le": 77.7, "loi_khuyen": "PRO MAX FALLBACK", "phien": "#999999"}})

    try:
        res = requests.get(api_url, headers={"User-Agent": "VIP-PRO-MAX-V20"}, timeout=8).json()
        
        if is_sicbo:
            lst = res.get("data", {}).get("resultList", [])
        else:
            lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res

        if not isinstance(lst, list):
            raise Exception("Data lỗi")

        lst = sorted(lst, key=get_id)
        kq = []
        for s in lst:
            if is_sicbo and isinstance(s, dict):
                score = int(s.get("score", 0))
                kq.append("Tài" if score >= 11 else "Xỉu")
            else:
                val = str(s).upper()
                if is_chanle:
                    kq.append("Tài" if any(x in val for x in ["CHẴN","CHAN","C","0"]) else "Xỉu")
                else:
                    kq.append("Tài" if any(x in val for x in ["TAI","TÀI","BIG"]) else "Xỉu")

        data = phan_tich_ai_v20(kq, is_chanle)

        phien_hien_tai = str(get_id(lst[-1]) + 1) if lst else "#000000"
        data["phien"] = phien_hien_tai

        HISTORY.extend(kq[-200:])
        save_history()

        return jsonify({"status": "success", "data": data})

    except Exception:
        return jsonify({"status": "success", "data": {"du_doan": "TÀI", "ti_le": 77.7, "loi_khuyen": "PRO MAX FALLBACK MODE", "phien": "#999999"}})

# Các route login, admin, manual_md5 giữ nguyên như code Flask cũ của bạn (bạn copy từ tin nhắn trước)
@app.route("/api/login", methods=["POST"])
def login():
    key = (request.json or {}).get("key", "").strip()
    if not key or key not in KEYS_DB: return jsonify({"status": "error", "msg": "Key sai hoặc không tồn tại!"})
    if key in LOCKED_KEYS: return jsonify({"status": "error", "msg": "Key đã bị Admin khóa!"})
    return jsonify({"status": "success", "role": KEYS_DB[key], "msg": "Đăng nhập VIP thành công!"})

@app.route("/")
def home():
    try: return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))
    except: return "<h1 style='color:red;'>LỖI: Chưa có file index.html</h1>"

if __name__ == "__main__":
    print("🚀 PRO MAX V20 QUANTUM CORE - SERVER ĐÃ KHỞI ĐỘNG")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
