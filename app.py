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

# ================== KEY LOGIN ==================
KEYS_DB = {
    "hungne": "admin",
    "67": "user"
}

HISTORY = deque(maxlen=60)
PREDICTION_MODE = "normal"
PRED_LOG = deque(maxlen=30)
consecutive_losses = 0  # Từ code Node.js

def get_id(item):
    if isinstance(item, dict):
        for k in ['id', 'phien', 'sessionId', 'sid', 'referenceId', 'matchId', 'gameNum']:
            if k in item and str(item[k]).replace('-', '').isdigit():
                return int(item[k])
    raw_str = str(item)
    matches = re.findall(r"'?(?:id|phien|referenceId|sessionId|matchId|gameNum)'?\s*:\s*'?(\d+)'?", raw_str, re.IGNORECASE)
    return int(matches[0]) if matches else 0

# LÕI MD5 VÔ HẠN (GIỮ NGUYÊN)
def tinh_toan_md5_vo_han_infinity(md5_str: str):
    # ... (giữ nguyên toàn bộ hàm MD5 cũ của bạn, tôi không paste lại để ngắn)
    # Bạn copy hàm MD5 từ code cũ của bạn vào đây
    pass  # ← Thay bằng hàm MD5 cũ của bạn

# ================== THUẬT TOÁN TỪ NODE.JS (ĐÃ CHUYỂN SANG PYTHON) ==================
def get_simple_prediction(history):
    global consecutive_losses
    if len(history) < 3:
        return {"du_doan": "XỈU", "do_tin_cay": 65, "phuong_phap": "Mặc định"}

    recent = history[-5:]
    tai_count = sum(1 for r in recent if r == "T")
    xiu_count = len(recent) - tai_count
    last = history[-1]

    if consecutive_losses >= 2:
        du_doan = "XỈU" if last == "T" else "TÀI"
        do_tin_cay = 85
        phuong_phap = "Phá cầu (thua 2 tay)"
        consecutive_losses = 0
    elif tai_count > xiu_count:
        du_doan = "XỈU"
        do_tin_cay = 60 + (tai_count - xiu_count) * 8
        phuong_phap = "Bẻ cầu Tài"
    elif xiu_count > tai_count:
        du_doan = "TÀI"
        do_tin_cay = 60 + (xiu_count - tai_count) * 8
        phuong_phap = "Bẻ cầu Xỉu"
    else:
        du_doan = "TÀI" if last == "T" else "XỈU"
        do_tin_cay = 70
        phuong_phap = "Theo cầu"

    do_tin_cay = min(95, max(55, int(do_tin_cay)))
    return {"du_doan": du_doan, "do_tin_cay": do_tin_cay, "phuong_phap": phuong_phap}

# AI NHẬN CẦU V6 (KẾT HỢP THUẬT TOÁN NODE.JS)
def advanced_predict(is_chanle, current_history, mode="normal"):
    if len(current_history) < 5:
        return "TÀI", 55.0, "Đang thu thập dữ liệu..."

    # Sử dụng thuật toán từ Node.js
    pred = get_simple_prediction(current_history)
    du_doan = pred["du_doan"]
    prob = pred["do_tin_cay"]
    loi = pred["phuong_phap"]

    if mode == "dao":
        du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
        prob = round(min(99.9, 100 - prob + 18), 1)
        loi = "🔥 ĐẢO CẦU V6"

    return du_doan, prob, loi

# API SCAN
@app.route("/api/scan", methods=["GET"])
def scan_game():
    global PREDICTION_MODE
    tool = request.args.get("tool", "")
    is_chanle = ("chanle" in tool.lower() or "xd" in tool.lower())

    urls = {
        "lc79_xd": "https://wcl.tele68.com/v1/chanlefull/sessions",
        "lc79_tx": "https://wtx.tele68.com/v1/tx/sessions",
        "lc79_md5": "https://wtx.tele68.com/v1/txmd5/sessions",
        "betvip_tx": "https://wtx.macminim6.online/v1/tx/sessions",
        "betvip_md5": "https://wtxmd52.macminim6.online/v1/txmd5/sessions",
        "sunwin_sicbo": "https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979&size=100&tableId=39791215743193&curPage=1"
    }
    url = urls.get(tool, "")

    try:
        res = requests.get(url, headers={"User-Agent": "INFINITY-GOD-V6"}, timeout=5).json()
        lst = res.get("data", res.get("list", res.get("resultList", []))) if isinstance(res, dict) else res

        if tool == "sunwin_sicbo" and isinstance(lst, list):
            arr = ["T" if (item.get("score", item.get("total", 0)) >= 11) else "X" for item in lst]
        else:
            arr = ["T" if any(x in str(s).upper() for x in (["CHẴN","CHAN","C","0"] if is_chanle else ["TAI","TÀI","BIG"])) else "X" for s in lst]

        HISTORY.extend(arr[-50:])
        phien_hien_tai = str(get_id(lst[-1]) + 1) if lst else "AUTO"

        m = re.search(r"[0-9a-f]{32}", str(lst[-1]).lower() if lst else "")
        if m and "md5" in tool.lower():
            dd, lk, tl = tinh_toan_md5_vo_han_infinity(m.group(0))
            return jsonify({"status": "success", "data": {"du_doan": dd, "ti_le": tl, "loi_khuyen": lk, "phien": phien_hien_tai}})

        du_doan, ti_le, loi_khuyen = advanced_predict(is_chanle, list(HISTORY), PREDICTION_MODE)
        PRED_LOG.append((int(phien_hien_tai) if phien_hien_tai.isdigit() else 0, du_doan, is_chanle))

        return jsonify({"status": "success", "data": {
            "du_doan": du_doan, "ti_le": ti_le, "loi_khuyen": loi_khuyen, "phien": phien_hien_tai
        }})

    except:
        return jsonify({"status": "success", "data": {
            "du_doan": "TÀI", "ti_le": 53.0, "loi_khuyen": "INFINITY V6 FALLBACK", "phien": "AUTO"
        }})

@app.route("/api/login", methods=["POST"])
def login():
    key = (request.json or {}).get("key", "").strip()
    if key in KEYS_DB:
        return jsonify({"status": "success", "role": KEYS_DB[key]})
    return jsonify({"status": "error", "msg": "Key không hợp lệ!"})

@app.route("/")
def home():
    try:
        return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))
    except:
        return "LỖI: Không tìm thấy index.html"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
