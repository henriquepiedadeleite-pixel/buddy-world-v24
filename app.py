import hashlib,json,os,re,sqlite3
from datetime import datetime,timezone
from flask import Flask,request,jsonify,abort,Response,render_template_string
import qrcode

DB=os.environ.get("BUDDYWORLD_DB","buddyworld.db")
BASE=os.environ.get("BUDDYWORLD_PUBLIC_BASE","").rstrip("/")
ID_RE=re.compile(r"^BDY-[0-9A-F]{8}$")
app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=65536

CSS="""body{margin:0;background:#050914;color:#e9f7ff;font-family:ui-monospace,monospace}.top{display:flex;justify-content:space-between;padding:18px 24px;border-bottom:1px solid #16324a;background:#08111f}.brand{font-weight:900;letter-spacing:.12em}.brand span{color:#49e7ff}.chip{color:#ffc857}.wrap{max-width:1100px;margin:auto;padding:24px}.hero,.panel{background:#0b1423;border:1px solid #17334d;border-radius:18px;padding:22px;margin-bottom:16px;box-shadow:0 0 30px #00d9ff0a}.hero{display:grid;grid-template-columns:1fr 220px;gap:24px;align-items:center}.orb{width:170px;height:170px;border-radius:42%;background:linear-gradient(145deg,#49e7ff,#17485f);border:4px solid white;position:relative;box-shadow:0 0 45px #49e7ff44;margin:auto}.eye{position:absolute;top:58px;width:18px;height:24px;background:#031019;border-radius:50%}.e1{left:42px}.e2{right:42px}.mouth{position:absolute;width:42px;height:18px;border-bottom:5px solid #031019;border-radius:50%;left:60px;top:94px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.stat{background:#0b1423;border:1px solid #17334d;border-radius:14px;padding:16px}.stat small{color:#7e9bb0;display:block}.stat b{font-size:25px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}.card{display:block;text-decoration:none;color:inherit;background:#0d1929;border:1px solid #1d3d58;border-radius:12px;padding:14px}.mut{color:#ffc857}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.tabs button{background:#0a1626;color:#9bb3c5;border:1px solid #1c3b56;border-radius:10px;padding:9px 12px}.tabs button.on{background:#49e7ff;color:#031019}.tab{display:none}.tab.on{display:block}.rows>div{padding:10px;border-bottom:1px solid #162b40}.mutbadge{display:inline-block;padding:2px 6px;border:1px solid #ffc857;color:#ffc857;border-radius:6px;margin-left:6px}@media(max-width:700px){.hero{grid-template-columns:1fr}.orb{display:none}}"""

HOME="""<!doctype html><html><head><meta name=viewport content='width=device-width,initial-scale=1'><title>Buddy World</title><style>{{css}}</style></head><body><div class=top><div class=brand>BUDDY<span>WORLD</span></div><div class=chip>V24 NETWORK</div></div><main class=wrap><section class=hero><div><small>PHYSICAL BUDDIES · DIGITAL PASSPORTS</small><h1>Every Buddy has a story.</h1><p>Permanent profiles for collections, pets, friends, personalities and stats.</p></div><div class=orb><i class='eye e1'></i><i class='eye e2'></i><b class=mouth></b></div></section><section class=grid><div class=stat><small>REGISTERED</small><b id=a>—</b></div><div class=stat><small>MUTATIONS</small><b id=b>—</b></div><div class=stat><small>BOSSES WON</small><b id=c>—</b></div></section><section class=panel><h2>RECENT BUDDIES</h2><div id=recent class=cards></div></section></main><script>fetch('/api/v1/world').then(r=>r.json()).then(d=>{a.textContent=d.total_buddies;b.textContent=d.mutations;c.textContent=d.bosses;recent.innerHTML=d.recent.length?d.recent.map(x=>`<a class=card href="/b/${x.id}"><b>${x.id}</b><div>${x.personality.temperament||''} · ${x.personality.energy||''} · ${x.personality.quirk||''}</div><small>${x.score||0} SCORE · ${x.mood||'CALM'}</small></a>`).join(''):'No Buddies synced yet.'}).catch(()=>recent.textContent='API offline')</script></body></html>"""

PROFILE="""<!doctype html><html><head><meta name=viewport content='width=device-width,initial-scale=1'><title>{{bid}} · Buddy World</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/ style='color:inherit;text-decoration:none'>BUDDY<span>WORLD</span></a><div class=chip id=status>LOADING</div></div><main class=wrap><section class=hero><div><small>BUDDY PASSPORT</small><h1 id=name>DESK BUDDY</h1><h3>{{bid}}</h3><div id=traits></div></div><div class=orb id=orb><i class='eye e1'></i><i class='eye e2'></i><b class=mouth></b></div></section><section class=grid><div class=stat><small>SCORE</small><b id=score>0</b></div><div class=stat><small>MOOD</small><b id=mood>—</b></div><div class=stat><small>FRIENDS</small><b id=friendsn>0</b></div><div class=stat><small>CRATES</small><b id=crates>0</b></div></section><div class=tabs><button class=on data-t=p>PROFILE</button><button data-t=f>FRIENDS</button><button data-t=s>STATS</button><button data-t=a>ACTIVITY</button></div><section id=p class='tab on panel rows'></section><section id=f class='tab panel cards'></section><section id=s class='tab panel rows'></section><section id=a class='tab panel rows'></section></main><script>const bid={{bid|tojson}};document.querySelectorAll('button[data-t]').forEach(x=>x.onclick=()=>{document.querySelectorAll('.tab,button[data-t]').forEach(y=>y.classList.remove('on'));x.classList.add('on');document.getElementById(x.dataset.t).classList.add('on')});fetch('/api/v1/buddy/'+bid).then(r=>{if(!r.ok)throw 0;return r.json()}).then(d=>{status.textContent='ONLINE';name.textContent=d.name;score.textContent=d.score;mood.textContent=d.mood;friendsn.textContent=d.friends.length;crates.textContent=d.pending_crates;let q=d.personality||{};traits.innerHTML=`<span class=mutbadge>${q.temperament||''}</span> <span class=mutbadge>${q.energy||''}</span> <span class=mutbadge>${q.quirk||''}</span>`;let e=d.equipped||{};p.innerHTML=`<div><b>PERSONALITY</b> #${q.id||0} / 575</div><div><b>COSMETIC</b> #${e.effect_id||0} ${e.effect_mutation?'<span class=mutbadge>MUT '+e.effect_mutation+'</span>':''}</div><div><b>PET</b> #${e.pet_id||0} · EVO ${e.pet_evolution||0} ${e.pet_mutation?'<span class=mutbadge>MUT '+e.pet_mutation+'</span>':''}</div>`;f.innerHTML=d.friends.length?d.friends.map(x=>`<a class=card href="/b/${x.id}"><b>${x.id}</b><small>MET ${x.meets} TIMES</small></a>`).join(''):'No friends yet.';let st=d.stats||{};s.innerHTML=Object.entries(st).map(([k,v])=>`<div><b>${k.replaceAll('_',' ').toUpperCase()}</b> · ${v}</div>`).join('');a.innerHTML=(d.activity||[]).map(x=>`<div><b>${x.event_type.toUpperCase()}</b> · ${x.message}<br><small>${x.created_at}</small></div>`).join('')||'No activity yet.'}).catch(()=>{status.textContent='NOT SYNCED';p.innerHTML='This Buddy has not synced yet.'})</script></body></html>"""

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def con():
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    c.executescript("CREATE TABLE IF NOT EXISTS buddies(buddy_id TEXT PRIMARY KEY,key_hash TEXT NOT NULL,profile_json TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY AUTOINCREMENT,buddy_id TEXT,event_type TEXT,message TEXT,created_at TEXT);")
    return c
def norm(x):
    x=(x or "").strip().upper()
    if not ID_RE.fullmatch(x): abort(400)
    return x
def iv(x,d=0,lo=0,hi=2**31-1):
    try:x=int(x)
    except:return d
    return max(lo,min(hi,x))
def clean(b,r):
    p=r.get("personality") if isinstance(r.get("personality"),dict) else {}
    e=r.get("equipped") if isinstance(r.get("equipped"),dict) else {}
    st=r.get("stats") if isinstance(r.get("stats"),dict) else {}
    fs=[]
    for x in (r.get("friends") or [])[:24]:
        if isinstance(x,dict) and ID_RE.fullmatch(str(x.get("id","")).upper()):
            fs.append({"id":str(x["id"]).upper(),"meets":iv(x.get("meets"),1,1,65535)})
    return {"id":b,"name":str(r.get("name","DESK BUDDY"))[:32],"firmware":str(r.get("firmware","V24"))[:16],"score":iv(r.get("score"),0,0,2**32-1),"pending_crates":iv(r.get("pending_crates"),0,0,65535),"mood":str(r.get("mood","CALM"))[:20],"personality":{"id":iv(p.get("id"),0,0,575),"temperament":str(p.get("temperament","CHILL"))[:20],"energy":str(p.get("energy","ZEN"))[:20],"quirk":str(p.get("quirk","GAMER"))[:20]},"equipped":{"effect_id":iv(e.get("effect_id"),0,0,511),"effect_mutation":iv(e.get("effect_mutation"),0,0,10),"pet_id":iv(e.get("pet_id"),0,0,105),"pet_mutation":iv(e.get("pet_mutation"),0,0,10),"pet_evolution":iv(e.get("pet_evolution"),0,0,2)},"friends":fs,"stats":{k:iv(st.get(k),0,0,2**32-1) for k in ["boss_wins","rps_wins","crates_opened","tv_episodes","social_actions"]},"collection":r.get("collection") if isinstance(r.get("collection"),dict) else {}}
def base():
    return BASE or request.host_url.rstrip("/")

@app.get("/")
def home(): return render_template_string(HOME,css=CSS)
@app.get("/b/<bid>")
def page(bid): return render_template_string(PROFILE,css=CSS,bid=norm(bid))
@app.get("/healthz")
def health(): return jsonify(ok=True)
@app.get("/api/v1/world")
def world():
    c=con();rows=c.execute("select * from buddies order by updated_at desc limit 12").fetchall();allr=c.execute("select profile_json from buddies").fetchall()
    recent=[];mut=0;boss=0
    for r in rows:
        p=json.loads(r["profile_json"]);recent.append({"id":r["buddy_id"],"score":p.get("score",0),"mood":p.get("mood","CALM"),"personality":p.get("personality",{})})
    for r in allr:
        p=json.loads(r[0]);col=p.get("collection",{});mut+=len(col.get("effect_mutations",[]))+len(col.get("pet_mutations",[]));boss+=p.get("stats",{}).get("boss_wins",0)
    return jsonify(total_buddies=len(allr),mutations=mut,bosses=boss,recent=recent)
@app.get("/api/v1/buddy/<bid>")
def api_buddy(bid):
    bid=norm(bid);c=con();r=c.execute("select * from buddies where buddy_id=?",(bid,)).fetchone()
    if not r: abort(404)
    p=json.loads(r["profile_json"]);p["created_at"]=r["created_at"];p["updated_at"]=r["updated_at"];p["activity"]=[dict(x) for x in c.execute("select event_type,message,created_at from activity where buddy_id=? order by id desc limit 24",(bid,))]
    return jsonify(p)
@app.post("/api/v1/buddy/<bid>/sync")
def sync(bid):
    bid=norm(bid);key=request.headers.get("X-Buddy-Key","")
    if not 24<=len(key)<=96: abort(401)
    raw=request.get_json(silent=True)
    if not isinstance(raw,dict): abort(400)
    p=clean(bid,raw);enc=json.dumps(p,separators=(",",":"));kh=hashlib.sha256(key.encode()).hexdigest();t=now();c=con();r=c.execute("select * from buddies where buddy_id=?",(bid,)).fetchone()
    if r and r["key_hash"]!=kh: abort(403)
    if r:c.execute("update buddies set profile_json=?,updated_at=? where buddy_id=?",(enc,t,bid))
    else:
        c.execute("insert into buddies values(?,?,?,?,?)",(bid,kh,enc,t,t));c.execute("insert into activity(buddy_id,event_type,message,created_at) values(?,?,?,?)",(bid,"registered","Buddy joined Buddy World",t))
    c.commit();return jsonify(ok=True,profile_url=f"{base()}/b/{bid}",server_time=t)
@app.get("/api/v1/buddy/<bid>/qr.txt")
def qr(bid):
    bid=norm(bid);q=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=1,border=0);q.add_data(f"{base()}/b/{bid}");q.make(fit=True);m=q.get_matrix();n=len(m);pack=bytearray();v=0;k=0
    for row in m:
        for z in row:
            v=(v<<1)|(1 if z else 0);k+=1
            if k==8:pack.append(v);v=0;k=0
    if k:pack.append(v<<(8-k))
    return Response(f"{n}\n{pack.hex().upper()}\n",mimetype="text/plain")

con().close()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")))
