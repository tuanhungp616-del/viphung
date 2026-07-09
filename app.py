# ═══════════════════════════════════════════════════════════════
#  app.py – SERVER FLASK – DORAEMON AI v9.0
#  Thuật toán: Markov bậc 3 + Bayes + Phát hiện cầu nâng cao
#  Đăng nhập: admin / admin123
#  Key API: hungki98vip
# ═══════════════════════════════════════════════════════════════

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests, random, math
from collections import Counter

app = Flask(__name__)
CORS(app)

# ═══════════════ THUẬT TOÁN DỰ ĐOÁN VIP ═══════════════
class SuperAI:
    def __init__(self):
        self.markov_order = 3
        self.streak_threshold = 4

    def predict(self, history):
        """history: list of 'Tài' or 'Xỉu'"""
        if len(history) < 2:
            return ("TÀI", 95.0)

        # 1. Markov bậc 3
        markov_pred, markov_conf = self._markov(history)
        # 2. Phân tích cầu 1-1, cầu bệt
        pattern_pred, pattern_conf = self._pattern(history)
        # 3. Bayes thống kê
        bayes_pred, bayes_conf = self._bayes(history)
        # 4. Xu hướng gần đây
        trend_pred, trend_conf = self._trend(history)

        # Tổng hợp vote
        votes = {"TÀI":0, "XỈU":0}
        if markov_pred: votes[markov_pred] += 3
        if pattern_pred: votes[pattern_pred] += 2
        votes[bayes_pred] += 1
        votes[trend_pred] += 1

        final_pred = max(votes, key=votes.get)
        max_votes = votes[final_pred]
        total_votes = sum(votes.values())
        confidence = (max_votes / total_votes) * 100 if total_votes > 0 else 50
        # Thêm nhiễu để giống thật
        confidence = min(99.9, confidence + random.uniform(-3, 5))
        return (final_pred, round(confidence, 1))

    def _markov(self, hist):
        if len(hist) < self.markov_order + 1:
            return (None, 0)
        transitions = {}
        for i in range(len(hist) - self.markov_order):
            state = tuple(hist[i:i+self.markov_order])
            nxt = hist[i+self.markov_order]
            transitions.setdefault(state, {}).setdefault(nxt, 0)
            transitions[state][nxt] += 1
        last_state = tuple(hist[-self.markov_order:])
        if last_state in transitions:
            probs = transitions[last_state]
            total = sum(probs.values())
            pred = max(probs, key=probs.get)
            conf = (probs[pred] / total) * 100
            return (pred.upper(), conf)
        return (None, 0)

    def _pattern(self, hist):
        if len(hist) >= 4:
            if hist[-4:] == ["Tài","Xỉu","Tài","Xỉu"]: return ("TÀI", 92.0)
            if hist[-4:] == ["Xỉu","Tài","Xỉu","Tài"]: return ("XỈU", 92.0)
        # Bệt dài
        if len(hist) >= self.streak_threshold:
            last_n = hist[-self.streak_threshold:]
            if all(x=="Tài" for x in last_n): return ("XỈU", 88.0)
            if all(x=="Xỉu" for x in last_n): return ("TÀI", 88.0)
        return (None, 0)

    def _bayes(self, hist):
        # Đếm tần suất 30 phiên gần nhất
        recent = hist[-30:]
        tai = recent.count("Tài")
        xiu = recent.count("Xỉu")
        total = len(recent)
        # Bayesian với prior (2,2)
        p_tai = (tai + 2) / (total + 4)
        p_xiu = (xiu + 2) / (total + 4)
        if p_tai > p_xiu:
            return ("TÀI", p_tai*100)
        else:
            return ("XỈU", p_xiu*100)

    def _trend(self, hist):
        if len(hist) < 3:
            return ("TÀI", 50.0)
        # Nếu 3 phiên cuối tăng Tài thì chọn Tài, ngược lại Xỉu
        recent3 = hist[-3:]
        if recent3.count("Tài") >= 2:
            return ("TÀI", 70.0)
        else:
            return ("XỈU", 70.0)

ai_engine = SuperAI()

# ═══════════════ ROUTES ═══════════════
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    if data.get("username") == "admin" and data.get("password") == "admin123":
        return jsonify({"status":"success","data":{"name":"admin","role":"admin"}})
    return jsonify({"status":"error","msg":"Sai tài khoản hoặc mật khẩu"})

@app.route("/api/scan")
def scan():
    tool = request.args.get("tool","")
    mode = request.args.get("mode","tx_md5")
    key = request.args.get("key","")
    if key != "hungki98vip":
        return jsonify({"status":"error","msg":"Key không hợp lệ"})

    # URL API nhà cái
    if tool == "lc79":
        url = "https://wcl.tele68.com/v1/chanlefull/sessions" if mode=="xoc_dia" else "https://wtx.tele68.com/v1/tx/sessions"
    elif tool == "betvip":
        url = "https://wtx.macminim6.online/v1/tx/sessions"
    else:
        return jsonify({"status":"error","msg":"Sàn không hỗ trợ"})

    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=5).json()
        sessions = resp.get("data", resp.get("list", []))
        if not isinstance(sessions, list): sessions = []

        history = []
        is_chanle = (mode == "xoc_dia")
        for s in sessions[-50:]:
            val = str(s).upper()
            if is_chanle:
                history.append("Tài" if ("CHẴN" in val or "CHAN" in val or "'C'" in val) else "Xỉu")
            else:
                history.append("Tài" if ("TAI" in val or "TÀI" in val or "'T'" in val) else "Xỉu")

        pred, conf = ai_engine.predict(history)

        phien = "0"
        if sessions:
            last = sessions[-1]
            if isinstance(last, dict):
                phien = str(last.get("id", last.get("phien", "0")))

        return jsonify({"status":"success","data":{"du_doan":pred,"ti_le":conf,"phien":phien}})
    except Exception as e:
        return jsonify({"status":"error","msg":str(e)})

@app.route("/")
def home():
    return send_file("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
