import os, json, math, random, re, time, threading
import numpy as np
from collections import deque, Counter
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

BASE = os.path.dirname(os.path.abspath(__file__))
MEM_FILE = os.path.join(BASE, "ai_memory_v3.json")
LOCK = threading.Lock()

DEF = {
    "histories": {}, "predict_log": {}, "algo_accuracy": {},
    "weights": {"md5":1.0,"markov":1.0,"cycle":1.0,"trend":1.0,"freq":1.0,"streak":1.0},
    "total_scans":0,"correct":0,"last_save":time.time()
}

def load_mem():
    try:
        if os.path.exists(MEM_FILE):
            m = json.load(open(MEM_FILE,encoding="utf8"))
            m["histories"] = {k:deque(v,maxlen=10000) for k,v in m["histories"].items()}
            return {**DEF,**m}
    except: pass
    return DEF

MEM = load_mem()
GAMES = ["betvip_tx","betvip_md5","lc79_tx","lc79_md5","lc79_xd","sunwin_sicbo"]
for k in GAMES: MEM["histories"].setdefault(k, deque(maxlen=10000))

KEYS = {"hungcaliadmin":{"role":"admin","name":"Hưng Đẹp Trai"},"nhatchimbe":{"role":"guest","name":"Khách VIP"}}
URLS = {
    "betvip_tx":"https://wtx.macminim6.online/v1/tx/sessions",
    "betvip_md5":"https://wtxmd52.macminim6.online/v1/txmd5/sessions",
    "lc79_tx":"https://wtx.tele68.com/v1/tx/sessions",
    "lc79_md5":"https://wtxmd52.tele68.com/v1/txmd5/sessions",
    "lc79_xd":"https://wcl.tele68.com/v1/chanlefull/sessions",
    "sunwin_sicbo":"https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979&size=100&tableId=39791215743193&curPage=1"
}

def gid(i):
    if isinstance(i,dict):
        for k in ['id','phien','sessionId','referenceId']:
            if k in i and str(i[k]).replace('-','').isdigit(): return int(i[k])
    m=re.findall(r"(?:id|phien)\D*(\d+)",str(i),re.I)
    return int(m[0]) if m else random.randint(100000,999999)

def save():
    with LOCK:
        try:
            x=dict(MEM); x["histories"]={k:list(v) for k,v in x["histories"].items()}; x["last_save"]=time.time()
            t=MEM_FILE+".tmp"; json.dump(x,open(t,"w",encoding="utf8"),ensure_ascii=False,indent=2); os.replace(t,MEM_FILE)
        except: pass

def autosave():
    while True:
        time.sleep(45)
        if time.time()-MEM["last_save"]>=45: save()
threading.Thread(target=autosave,daemon=True).start()

# ========== 6 THUẬT TOÁN ==========
def md5_nn(m):
    if not re.fullmatch(r"[0-9a-f]{32}",m.lower()): return None,0
    h=np.array([int(c,16) for c in m.lower()]); E=h.sum(); x=(E%1000)/1000; r=3.92+(E%1500)/2000; T=X=0.0
    for i in range(12000):
        x=(r+0.08*math.sin(i/180))*x*(1-x)*(1+0.02*math.sin(i/50)); w=h[i%32]/15
        if i%5 in(0,2,4): T+=x*w*(1+math.sin(i/70)*.3)
        else: X+=x*w*(1+math.cos(i/70)*.3)
    f=np.abs(np.fft.fft(h)); T+=f[2:9].mean()*8+f[10:20].std()*4; X+=f[12:22].mean()*8+f[22:31].std()*4
    p=1/(1+math.exp(-(T-X)/22))*100
    return ("TÀI",p) if p>=50 else ("XỈU",100-p)

def markov(sq):
    if len(sq)<10: return None,50
    s=[1 if x=='T' else 0 for x in sq]; tp=0
    for o,w in [(1,.45),(2,.35),(3,.20)]:
        tr={}
        for i in range(o,len(s)):
            st=tuple(s[i-o:i]); tr.setdefault(st,[0,0])[s[i]]+=1
        cs=tuple(s[-o:])
        if cs in tr: a,b=tr[cs]; tp+=(a/(a+b)if a+b else .5)*w
    return ("TÀI",tp*100) if tp>=.5 else ("XỈU",(1-tp)*100)

def cycle(sq):
    if len(sq)<15: return None,50
    bc,bs=None,0
    for L in range(3,13):
        c=sum(1 for i in range(len(sq)-L*2) if sq[i:i+L]==sq[i+L:i+L*2]); t=max(1,len(sq)-L*2); sc=c/t
        if sc>.4 and sc>bs: bs=sc; bc=sq[-L:]
    if not bc: return None,50
    return ("TÀI" if bc[0]=='T' else "XỈU",50+bs*40)

def trend(sq):
    if len(sq)<12: return None,50
    y=np.array([1 if x=='T' else 0 for x in sq[-20:]]); x=np.arange(len(y)); mx,my=x.mean(),y.mean()
    b=((x-mx)*(y-my)).sum()/((x-mx)**2).sum(); p=.5+b*6
    return ("TÀI",p*100) if p>=.5 else ("XỈU",(1-p)*100)

def freq(sq):
    if len(sq)<30: return None,50
    from collections import Counter as C
    c=C(sq); t=c.get('T',0); x=c.get('X',0); n=t+x; pt=t/n
    if pt>.62: return "XỈU",52+(pt-.5)*80
    if pt<.38: return "TÀI",52+(.5-pt)*80
    return ("TÀI" if pt>=.5 else "XỈU"),52+abs(pt-.5)*40

def streak(sq):
    if len(sq)<5: return None,50
    last=sq[-1]; cnt=1
    for v in reversed(sq[:-1]):
        if v==last: cnt+=1
        else: break
    if cnt>=4: return ("XỈU" if last=='T' else "TÀI"),min(92,55+cnt*6)
    return ("TÀI" if last=='T' else "XỈU"),52+cnt*2

def learn(sid,real):
    if sid not in MEM["predict_log"]: return
    p=MEM["predict_log"][sid]
    ok=1 if p["pred"]==real else 0
    p["real"]=real; p["correct"]=ok
    MEM["total_scans"]+=1; MEM["correct"]+=ok
    for a,r in p["algos"].items():
        x=MEM["algo_accuracy"].setdefault(a,{"ok":0,"n":0}); x["n"]+=1
        if r==real: x["ok"]+=1
        acc=x["ok"]/x["n"]; MEM["weights"][a]=round(max(.3,acc**2*2.2),4)
    save()

def brain(cl,hist,md5=None):
    sq=list(hist); A={}
    if md5:
        r,c=md5_nn(md5)
        if r: A["md5"]=(r,c)
    for n,f in [("markov",markov),("cycle",cycle),("trend",trend),("freq",freq),("streak",streak)]:
        r,c=f(sq)
        if r: A[n]=(r,c)
    ST=SX=SW=0
    for a,(r,c) in A.items():
        w=MEM["weights"].get(a,1.0)
        if r in("TÀI","CHẴN"): ST+=c*w
        else: SX+=c*w
        SW+=w
    if SW==0: return ("TÀI" if random.random()>.5 else "XỈU"),55.0,"THIẾU DỮ LIỆU",A
    F="TÀI" if ST>=SX else "XỈU"
    cf=round(max(53.0,min(99.2,max(ST,SX)/SW)),1)
    if cl: F="CHẴN" if F=="TÀI" else "LẺ"
    return F,cf,f"BẦU CỬ {len(A)} THUẬT TOÁN TRỌNG SỐ",A

# ========== API ==========
@app.route("/api/login",methods=["GET","POST"])
def login():
    k=(request.json or {}).get("key") if request.method=="POST" else request.args.get("key","")
    if k in KEYS: return jsonify({"status":"success","data":KEYS[k]})
    return jsonify({"status":"error"}),401

@app.route("/api/scan",methods=["GET","POST"])
def scan():
    d=request.json if request.is_json else request.args.to_dict()
    tool=d.get("tool",""); cl="chanle" in tool.lower() or "xd" in tool.lower()
    if tool not in URLS: return jsonify({"status":"error"}),400
    try:
        r=requests.get(URLS[tool],headers={"User-Agent":"AI-V3"},timeout=7).json()
        lst=r.get("data",r.get("list",r)) if isinstance(r,dict) else r
        if not isinstance(lst,list): raise ValueError
        lst=sorted(lst,key=gid)
        KTX=["TAI","TÀI","BIG"]; KCL=["CHẴN","CHAN","C","0"]; KW=KCL if cl else KTX
        arr=["T" if any(k in str(s).upper() for k in KW) else "X" for s in lst]
        hist=MEM["histories"][tool]
        for v in arr: hist.append(v)
        for it in lst[-5:]:
            sid=str(gid(it))
            if sid in MEM["predict_log"] and "real" not in MEM["predict_log"][sid]:
                real="TÀI" if any(k in str(it).upper() for k in KTX) else "XỈU"
                learn(sid,real)
        ph=str(gid(lst[-1])+1)
        md=re.search(r"[0-9a-f]{32}",str(lst[-1]).lower())
        pr,cf,mt,al=brain(cl,list(hist),md.group(0) if md and "md5" in tool else None)
        MEM["predict_log"][ph]={"tool":tool,"pred":pr,"conf":cf,"algos":{a:v[0] for a,v in al.items()},"time":time.time()}
        save()
        return jsonify({"status":"success","data":{"phien":ph,"du_doan":pr,"ti_le":cf,"tin_cay":cf,"phuong_phap":mt,"thongke":{"tong":MEM["total_scans"],"dung":MEM["correct"],"ty_le":round(MEM["correct"]/max(1,MEM["total_scans"])*100,2)}}})
    except:
        return jsonify({"status":"success","data":{"phien":"#"+str(random.randint(1e5,1e6)),"du_doan":"TÀI" if random.random()>.45 else "XỈU","ti_le":round(random.uniform(70,86),1),"phuong_phap":"DỰ PHÒNG"}})

@app.route("/")
def home():
    p=os.path.join(BASE,"index.html")
    return send_file(p) if os.path.exists(p) else "<h1 style=color:#0af>🧠 AI BRAIN V3 OK</h1>"

application=app
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")),debug=False,threaded=True)
        
