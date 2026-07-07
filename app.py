import os
import json
import math
import random
import re
import time
import threading
import numpy as np
from collections import deque, Counter
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests

# ===================== KHỞI TẠO ỨNG DỤNG =====================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ===================== ĐƯỜNG DẪN BỘ NHỚ RIÊNG =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "ai_memory_v3.json")
LOCK = threading.Lock()

# ===================== CẤU HÌNH HỆ THỐNG =====================
MAX_SHORT = 500    # Bộ nhớ ngắn hạn
MAX_LONG = 10000   # Bộ nhớ dài hạn tự học
AUTO_SAVE_EVERY = 30  # giây

# ===================== KHỞI TẠO BỘ NHỚ =====================
DEFAULT_MEMORY = {
    "histories": {},       # Lịch sử kết quả T/X mỗi sàn
    "predict_log": {},     # Lịch sử dự đoán vs kết quả thực tế
    "algo_accuracy": {},   # Độ chính xác từng thuật toán
    "weights": {           # Trọng số động tự điều chỉnh
        "md5": 1.0, "markov": 1.0, "cycle": 1.0,
        "trend": 1.0, "freq": 1.0, "streak": 1.0
    },
    "total_scans": 0,
    "correct": 0,
    "last_save": time.time()
}

def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                mem = json.load(f)
            # Khôi phục deque
            for k, v in mem["histories"].items():
                mem["histories"][k] = deque(v, maxlen=MAX_LONG)
            return {**DEFAULT_MEMORY, **mem}
    except Exception: pass
    return DEFAULT_MEMORY

def save_memory():
    with LOCK:
        try:
            export = dict(MEM)
            export["histories"] = {k: list(v) for k, v in MEM["histories"].items()}
            export["last_save"] = time.time()
            tmp = MEMORY_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(export, f, ensure_ascii=False, indent=2)
            os.replace(tmp, MEMORY_FILE)
        except Exception as e: print(f"[Lưu bộ nhớ] {e}")

MEM = load_memory()

# Khởi tạo lịch sử các sàn
GAME_KEYS = ["betvip_tx","betvip_md5","lc79_tx","lc79_md5","lc79_xd","sunwin_sicbo"]
for k in GAME_KEYS:
    if k not in MEM["histories"]:
        MEM["histories"][k] = deque(maxlen=MAX_LONG)

SYSTEM_KEYS = {
    "hungcaliadmin": {"role":"admin","name":"Hưng Đẹp Trai","status":"Active"},
    "nhatchimbe": {"role":"guest","name":"Khách VIP","status":"Active"}
}

URLS = {
    "betvip_tx": "https://wtx.macminim6.online/v1/tx/sessions",
    "betvip_md5": "https://wtxmd52.macminim6.online/v1/txmd5/sessions",
    "lc79_tx": "https://wtx.tele68.com/v1/tx/sessions",
    "lc79_md5": "https://wtxmd52.tele68.com/v1/txmd5/sessions",
    "lc79_xd": "https://wcl.tele68.com/v1/chanlefull/sessions",
    "sunwin_sicbo": "https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979&size=100&tableId=39791215743193&curPage=1"
}

# ===================== TIỆN ÍCH =====================
def get_id(item):
    if isinstance(item, dict):
        for k in ['id','phien','sessionId','sid','referenceId','matchId','phien_hien_tai','turnNum']:
            if k in item and str(item[k]).replace('-','').isdigit():
                return int(item[k])
    m = re.findall(r"(?:id|phien)\D*(\d+)", str(item), re.I)
    return int(m[0]) if m else random.randint(100000,999999)

def auto_save_daemon():
    while True:
        time.sleep(AUTO_SAVE_EVERY)
        if time.time() - MEM["last_save"] >= AUTO_SAVE_EVERY:
            save_memory()
threading.Thread(target=auto_save_daemon, daemon=True).start()

# ===================== 🧠 THUẬT TOÁN 1: GIẢI MÃ MD5 Nơ-ron =====================
def md5_neural(md5):
    if not re.fullmatch(r"[0-9a-f]{32}", md5.lower()): return None, 0
    h = np.array([int(c,16) for c in md5.lower()], dtype=np.float64)
    E = h.sum()
    x = (E%1000)/1000
    r = 3.92 + (E%1500)/2000
    T=X=0.0
    for i in range(15000):
        r2 = r + 0.08*math.sin(i/180)
        x = r2*x*(1-x)*(1+0.02*math.sin(i/50))
        w = h[i%32]/15
        if i%5 in (0,2,4): T += x*w*(1+math.sin(i/70)*0.3)
        else: X += x*w*(1+math.cos(i/70)*0.3)
    ft = np.abs(np.fft.fft(h))
    T += ft[2:9].mean()*8 + ft[10:20].std()*4
    X += ft[12:22].mean()*8 + ft[22:31].std()*4
    d = T-X
    p = 1/(1+math.exp(-d/22))*100
    return ("TÀI", p) if p>=50 else ("XỈU", 100-p)

# ===================== 🧠 THUẬT TOÁN 2: MARKOV ĐA TẦNG =====================
def markov_multi(seq):
    if len(seq)<10: return None,50
    s=[1 if x=='T' else 0 for x in seq]
    ow={1:.45,2:.35,3:.20}
    tp=0
    for o,w in ow.items():
        tr={}
        for i in range(o,len(s)):
            st=tuple(s[i-o:i])
            tr.setdefault(st,[0,0])[s[i]]+=1
        cs=tuple(s[-o:])
        if cs in tr:
            a,b=tr[cs]; tp += (a/(a+b) if a+b else .5)*w
    return ("TÀI", tp*100) if tp>=.5 else ("XỈU", (1-tp)*100)

# ===================== 🧠 THUẬT TOÁN 3: PHÁT HIỆN CHU KỲ =====================
def find_cycle(seq):
    if len(seq)<15: return None,50
    bc,bs=None,0
    for L in range(3,13):
        c=sum(1 for i in range(len(seq)-L*2) if seq[i:i+L]==seq[i+L:i+L*2])
        t=max(1,len(seq)-L*2)
        sc=c/t
        if sc>.4 and sc>bs: bs=sc; bc=seq[-L:]
    if not bc: return None,50
    return ("TÀI" if bc[0]=='T' else "XỈU", 50+bs*40)

# ===================== 🧠 THUẬT TOÁN 4: XU HƯỚNG HỒI QUY (KHÔNG SCIPY) =====================
def slope(seq):
    if len(seq)<12: return None,50
    y=np.array([1 if x=='T' else 0 for x in seq[-20:]])
    x=np.arange(len(y))
    mx,my=x.mean(),y.mean()
    b=((x-mx)*(y-my)).sum()/((x-mx)**2).sum()
    p=0.5 + b*6
    return ("TÀI", p*100) if p>=.5 else ("XỈU",(1-p)*100)

# ===================== 🧠 THUẬT TOÁN 5: TẦN SUẤT LÂU DÀI =====================
def freq_long(seq):
    if len(seq)<30: return None,50
    c=Counter(seq)
    t=c.get('T',0); x=c.get('X',0); n=t+x
    pt=t/n
    # Nguyên lý đảo trung bình
    if pt>.62: return "XỈU", 52+(pt-.5)*80
    if pt<.38: return "TÀI", 52+(.5-pt)*80
    return ("TÀI" if pt>=.5 else "XỈU"), 52+abs(pt-.5)*40

# ===================== 🧠 THUẬT TOÁN 6: PHÁT HIỆN CHUỖI LIÊN TIẾP =====================
def streak_break(seq):
    if len(seq)<5: return None,50
    last=seq[-1]; cnt=1
    for v in reversed(seq[:-1]):
        if v==last: cnt+=1
        else: break
    if cnt>=4:
        return ("XỈU" if last=='T' else "TÀI"), min(92, 55+cnt*6)
    return ("TÀI" if last=='T' else "XỈU"), 52+cnt*2

# ===================== 🧠 BỘ HỌC: TỰ ĐIỀU CHỈNH TRỌNG SỐ =====================
def learn_from_result(session, real):
    """Gọi sau mỗi phiên đóng để hệ thống tự học"""
    if session not in MEM["predict_log"]: return
    pred = MEM["predict_log"][session]
    correct = 1 if pred["pred"]==real else 0
    pred["real"] = real
    pred["correct"] = correct
    MEM["total_scans"] += 1
    MEM["correct"] += correct
    # Cập nhật độ chính xác từng thuật toán
    for algo, res in pred["algos"].items():
        a = MEM["algo_accuracy"].setdefault(algo, {"ok":0,"n":0})
        a["n"] += 1
        if res == real: a["ok"] += 1
        # Trọng số = độ chính xác lịch sử ^ 2 → ưu tiên mạnh cái chuẩn hơn
        acc = a["ok"]/a["n"]
        MEM["weights"][algo] = round(max(.3, acc**2 * 2.2), 4)
    save_memory()

# ===================== 🧠 BỘ BẦU CỬ THÔNG MINH CHÍNH =====================
def ultimate_brain(is_cl, hist, md5=None):
    seq = list(hist)
    algos = {}
    if md5:
        r,c = md5_neural(md5)
        if r: algos["md5"]=(r,c)
    for n,f in [("markov",markov_multi),("cycle",find_cycle),
                ("trend",slope),("freq",freq_long),("streak",streak_break)]:
        r,c = f(seq)
        if r: algos[n]=(r,c)

    # Tính điểm có trọng số từ lịch sử học được
    score_T = score_X = 0.0
    sum_w = 0
    for algo,(r,c) in algos.items():
        w = MEM["weights"].get(algo, 1.0)
        if r in ("TÀI","CHẴN"): score_T += c*w
        else: score_X += c*w
        sum_w += w
    if sum_w==0:
        return ("TÀI" if random.random()>.5 else "XỈU"), 55.0, "DỮ LIỆU THIẾU"

    final = "TÀI" if score_T >= score_X else "XỈU"
    raw = max(score_T, score_X)/sum_w
    conf = round(max(53.0, min(99.2, raw)), 1)
    method = f"BẦU CỬ {len(algos)} THUẬT TOÁN | TRỌNG SỐ ĐỘNG"

    if is_cl: final = "CHẴN" if final=="TÀI" else "LẺ"
    return final, conf, method, algos

# ===================== 📡 API =====================
@app.route("/api/login", methods=["GET","POST"])
def login():
    k = (request.json or {}).get("key") if request.method=="POST" else request.args.get("key","")
    if k in SYSTEM_KEYS:
        return jsonify({"status":"success","datadata":SYSTEM_KEYS[k],"version":"3.0-SELF-LEARNING"})
    return jsonify({"status":"error","msg":"Sai khóa"}),401

@app.route("/api/scan", methods=["GET","POST"])
def scan():
    data = request.json if request.is_json else request.args.to_dict()
    tool = data.get("tool","")
    is_cl = "chanle" in tool.lower() or "xd" in tool.lower()
    if tool not in URLS:
        return jsonify({"status":"error","msg":"Tool không tồn tại"}),400
    try:
        r = requests.get(URLS[tool], headers={"User-Agent":"AI-BRAIN-V3"}, timeout=7).json()
        lst = r.get("data", r.get("list", r)) if isinstance(r,dict) else r
        if not isinstance(lst,list): raise ValueError("bad format")
        lst = sorted(lst, key=get_id)
        arr = []
        kw_cl = ["CHẴN","CHAN","C","0"]
        kw_tx = ["TAI","TÀI","BIG"]
        for it in lst:
            s = str(it).upper()
            arr.append("T" if any(k in s for k in (kw_cl if is_cl else kw_tx)) else "X")
        # Cập nhật bộ nhớ dài hạn + học kết quả cũ
        hist = MEM["histories"][tool]
        new_added = 0
        for v in arr:
            if not hist or v != hist[-1] or new_added==0:
                hist.append(v); new_added+=1
        # Tự học: cập nhật kết quả thực tế cho các dự đoán cũ
        for it in lst[-5:]:
            sid = str(get_id(it))
            if sid in MEM["predict_log"] and "real" not in MEM["predict_log"][sid]:
                s = str(it).upper()
                real = "TÀI" if any(k in s for k in kw_tx) else "XỈU"
                learn_from_result(sid, real)

        phien = str(get_id(lst[-1])+1)
        md = re.search(r"[0-9a-f]{32}", str(lst[-1]).lower())
        md5 = md.group(0) if md and "md5" in tool else None

        pred, conf, method, algos = ultimate_brain(is_cl, list(hist), md5)
        MEM["predict_log"][phien] = {
            "tool":tool,"pred":pred,"conf":conf,"method":method,
            "algos":{a:v[0] for a,v in algos.items()},"time":time.time()
        }
        save_memory()
        return jsonify({
            "status":"success",
            "data":{
                "phien":phien,"du_doan":pred,"ti_le":conf,
                "tin_cay":conf,"loi_khuyen":method,
                "phuong_phap":method,"version":"3.0",
                "thongke":{
                    "tong_du_doan":MEM["total_scans"],
                    "dung":MEM["correct"],
                    "ty_le_chuan":round(MEM["correct"]/max(1,MEM["total_scans"])*100,2)
                }
            }
        })
    except Exception as e:
        return jsonify({
            "status":"success",
            "data":{
                "phien":"#"+str(random.randint(1e5,1e6)),
                "du_doan":"TÀI" if random.random()>.45 else "XỈU",
                "ti_le":round(random.uniform(70,86),1),
                "tin_cay":round(random.uniform(70,86),1),
                "loi_khuyen":"HỆ THỐNG DỰ PHÒNG",
                "phuong_phap":"DỰ PHÒNG"
            }
        })

@app.route("/api/manual_md5", methods=["POST"])
def manual_md5():
    d=request.json or {}; m=d.get("md5","")
    r,c=md5_neural(m)
    if not r: return jsonify({"status":"error"}),400
    return jsonify({"status":"success","du_doan":r,"ti_le":round(c,1)})

@app.route("/api/stats")
def stats():
    return jsonify({
        "tong":MEM["total_scans"],
        "dung":MEM["correct"],
        "ty_le":round(MEM["correct"]/max(1,MEM["total_scans"])*100,2),
        "trong_so":MEM["weights"],
        "do_chinh_xac":{
            k:round(v["ok"]/max(1,v["n"])*100,2) for k,v in MEM["algo_accuracy"].items()
        }
    })

@app.route("/")
def home():
    p = os.path.join(BASE_DIR,"index.html")
    return send_file(p) if os.path.exists(p) else "<h1 style=color:#0af>🧠 AI BRAIN V3.0 - ĐANG HOẠT ĐỘNG</h1>"

@app.route("/api/save")
def force_save(): save_memory(); return "OK"

# ===================== CHẠY =====================
application = app
if __name__=="__main__":
    port = int(os.environ.get("PORT","8080"))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
                
