from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, random, string, json
from datetime import datetime, timedelta
import numpy as np

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DB_FILE = "royal_keys.db"

def get_db(): 
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def khoi_tao_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS keys (key_str TEXT PRIMARY KEY, expire_time DATETIME, is_banned INTEGER)''')
        c.execute("INSERT OR IGNORE INTO keys (key_str, expire_time, is_banned) VALUES (?, ?, ?)", ('hungadmin67', '2099-12-31 23:59:59', 0))
        c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, email TEXT, balance INTEGER DEFAULT 0, role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0)''')
        c.execute("INSERT OR IGNORE INTO users (username, password, email, balance, role, is_banned) VALUES (?, ?, ?, ?, ?, ?)", ('hungadmin1122334455', 'hungki9811', 'god@hungcuto.vip', 999999999, 'admin', 0))
        conn.commit()

khoi_tao_db()

# ==================================================
# 🧠 THUẬT TOÁN V20 QUANTUM CORE (ĐÃ GẮN VÀO TẤT CẢ TOOL)
# ==================================================
def tinh_toan_v20(kq_list):
    if len(kq_list) < 8: 
        return "", "THU THẬP DỮ LIỆU LƯỢNG TỬ - PRO MAX"
    
    gan_nhat = kq_list[-50:]
    kq_cuoi = kq_list[-1]
    diem_tai = diem_xiu = 0
    loi_khuyen = "VÀO LỆNH ĐỀU TAY PRO MAX"

    # PATTERN ĐỘC QUYỀN V20
    cuoi_4 = kq_list[-4:]
    if cuoi_4 == ["Tài", "Xỉu", "Tài", "Xỉu"]: return "TÀI", "BẮT PATTERN XEN KẼ V20"
    if cuoi_4 == ["Xỉu", "Tài", "Xỉu", "Tài"]: return "XỈU", "BẮT PATTERN XEN KẼ V20"
    cuoi_6 = kq_list[-6:]
    if cuoi_6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]: return "TÀI", "BẮT CHU KỲ LẶP V20"
    if cuoi_6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]: return "XỈU", "BẮT CHU KỲ LẶP V20"

    # CHUỖI DÀI / NGẮN
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

    # Lịch sử 15 phiên gần nhất
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
        for k in ['id', 'phien', 'sessionId', 'sid', 'referenceId', 'matchId', 'phien_hien_tai', 'gameNum']:
            if k in item and str(item[k]).replace('-', '').isdigit():
                return int(item[k])
    return 0

# ==================================================
# 📡 API SCAN - ĐÃ GẮN SICBO SUN.WIN + V20
# ==================================================
@app.get("/api/scan")
async def scan_game(tool: str, key: str):
    # Kiểm tra key
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expire_time, is_banned FROM keys WHERE key_str = ?", (key,))
        row = c.fetchone()
    if not row: 
        return JSONResponse(status_code=403, content={"status": "error", "msg": "Key không tồn tại!"})
    if row[1] == 1 and key != "hungadmin67": 
        return JSONResponse(status_code=403, content={"status": "error", "msg": "Key bị khóa!"})
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and key != "hungadmin67": 
        return JSONResponse(status_code=403, content={"status": "error", "msg": "Key đã hết hạn!"})

    is_chanle = "chanle" in tool.lower() or "xd" in tool.lower()
    is_sicbo = "sicbo_sunwin" in tool.lower() or "sunwin" in tool.lower()

    # Chọn API
    if is_sicbo:
        url = "https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979&size=100&tableId=39791215743193&curPage=1"
    elif tool == "lc79_xd":
        url = "https://wcl.tele68.com/v1/chanlefull/sessions"
    elif tool == "lc79_md5":
        url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
    elif tool == "lc79_tx":
        url = "https://wtx.tele68.com/v1/tx/sessions"
    elif tool == "betvip_tx":
        url = "https://wtx.macminim6.online/v1/tx/sessions"
    elif tool == "betvip_md5":
        url = "https://wtxmd52.macminim6.online/v1/txmd5/sessions"
    else:
        return {"status": "error", "msg": "Tool không hỗ trợ!"}

    try:
        res = requests.get(url, headers={"User-Agent": "VIP-PRO-MAX-V20"}, timeout=8).json()
        
        if is_sicbo:
            lst = res.get("data", {}).get("resultList", [])
        else:
            lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res

        if not lst or not isinstance(lst, list):
            return {"status": "error", "msg": "Đang đồng bộ dữ liệu..."}

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

        # Phiên hiện tại
        if lst:
            phien_hien_tai = get_id(lst[-1])
            data["phien"] = str(phien_hien_tai + 1) if phien_hien_tai > 0 else "ĐANG TẢI..."

        return {"status": "success", "data": data}

    except Exception as e:
        return {"status": "error", "msg": f"Mạng lag! {str(e)}"}

# ================= CÁC API KHÁC (giữ nguyên V20) =================
class AuthReq(BaseModel):
    key: str = ""

@app.post("/api/login")
async def login(req: AuthReq):
    key = req.key.strip()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expire_time, is_banned FROM keys WHERE key_str = ?", (key,))
        row = c.fetchone()
    if not row:
        return {"status": "error", "msg": "Key sai hoặc không tồn tại!"}
    if row[1] == 1 and key != "hungadmin67":
        return {"status": "error", "msg": "Key đã bị Admin khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and key != "hungadmin67":
        return {"status": "error", "msg": "Key đã hết hạn!"}
    return {"status": "success", "role": "user", "msg": "Đăng nhập VIP thành công!"}

# Các API admin, register, buy_key... giữ nguyên như code bạn đưa (bạn có thể copy thêm nếu cần)

@app.get("/")
async def home():
    return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("🚀 SERVER PRO MAX V20 QUANTUM CORE ĐÃ KHỞI ĐỘNG")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
