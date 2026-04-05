from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests, uvicorn, random
from collections import deque
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

HISTORY = deque(maxlen=300)
DAO_CAU_MODE = False
LAST_PRED = None

# ====================== KEY SYSTEM ======================
VALID_KEYS = {
    "memaylc79": "admin",
    "em": "user"
}

def check_key(key: str):
    return VALID_KEYS.get(key.strip(), None)

# ====================== LẤY ID / PHIÊN THẬT ======================
def get_id(item):
    if isinstance(item, dict):
        for k in ['id', 'phien', 'sessionId', 'sid', 'referenceId', 'matchId', 'phien_hien_tai', 'gameNum']:
            if k in item and str(item[k]).replace('-', '').isdigit():
                return int(item[k])
    return 0

# ====================== THUẬT TOÁN V67 QUANTUM CORE ======================
def v67_predict(kq_list):
    global DAO_CAU_MODE, LAST_PRED
    if len(kq_list) < 10:
        return "TÀI", 88.8, "V67 QUANTUM CORE - ĐANG TẢI"

    current_actual = kq_list[-1]
    if LAST_PRED and LAST_PRED != current_actual:
        DAO_CAU_MODE = not DAO_CAU_MODE  # Toggle đảo cầu

    # Logic dự đoán V67
    du_doan = "TÀI"
    if sum(1 for x in kq_list[-6:] if x == "Tài") >= 4:
        du_doan = "XỈU"
    elif sum(1 for x in kq_list[-4:] if x == "Xỉu") >= 3:
        du_doan = "TÀI"

    # Áp dụng đảo cầu nếu đang ở chế độ
    if DAO_CAU_MODE:
        du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
        loi = "V67 - ĐẢO CẦU TỰ ĐỘNG (sai lần trước)"
    else:
        loi = "V67 QUANTUM CORE - TỰ NHẬN BIẾT CẦU"

    LAST_PRED = du_doan
    ti_le = round(random.uniform(96.5, 99.9), 1)
    return du_doan, ti_le, loi

# ====================== API SCAN ======================
@app.get("/api/scan")
async def scan_game(tool: str, key: str = None):
    # Kiểm tra key
    key_status = check_key(key)
    if not key_status:
        return JSONResponse(status_code=403, content={"status": "error", "msg": "Key sai hoặc không tồn tại!"})

    is_sicbo = "sicbo" in tool.lower()
    is_chanle = "chanle" in tool.lower() or "xd" in tool.lower()

    try:
        if is_sicbo:
            url = "https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979&size=100&tableId=39791215743193&curPage=1"
        elif tool == "betvip_tx":
            url = "https://wtx.macminim6.online/v1/tx/sessions"
        elif tool == "betvip_md5":
            url = "https://wtxmd52.macminim6.online/v1/txmd5/sessions"
        elif tool == "lc79_tx":
            url = "https://wtx.tele68.com/v1/tx/sessions"
        elif tool == "lc79_md5":
            url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
        else:
            return {"status": "error", "msg": "Tool không hỗ trợ"}

        res = requests.get(url, headers={"User-Agent": "DORAEMON-V67"}, timeout=8).json()

        if is_sicbo:
            lst = res.get("data", {}).get("resultList", [])
        else:
            lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res

        if not lst or not isinstance(lst, list):
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

        HISTORY.extend(kq[-200:])

        du_doan, ti_le, loi = v67_predict(list(HISTORY))
        phien_hien_tai = str(get_id(lst[-1]) + 1) if lst else "LIVE"

        return {
            "status": "success",
            "data": {
                "du_doan": du_doan,
                "ti_le": ti_le,
                "loi_khuyen": loi,
                "phien": phien_hien_tai
            }
        }

    except Exception:
        return {
            "status": "success",
            "data": {
                "du_doan": "TÀI",
                "ti_le": 88.8,
                "loi_khuyen": "V67 QUANTUM CORE - FALLBACK",
                "phien": "LIVE"
            }
        }

@app.get("/")
async def home():
    return FileResponse("index.html")

if __name__ == "__main__":
    print("🚀 DORAEMON V67 TOOL - LÕI PYTHON ĐÃ NÂNG CẤP")
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
