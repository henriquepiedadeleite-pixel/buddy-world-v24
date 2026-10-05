import hashlib,json,os,re,sqlite3
from datetime import datetime,timezone
from functools import wraps
from flask import Flask,request,jsonify,abort,Response,render_template_string,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
import qrcode
from pathlib import Path
COSMETICS=json.loads(Path(__file__).with_name('cosmetics.json').read_text())
DB=os.environ.get('BUDDYWORLD_DB','buddyworld.db'); BASE=os.environ.get('BUDDYWORLD_PUBLIC_BASE','').rstrip('/'); ID_RE=re.compile(r'^BDY-[0-9A-F]{8}$')
app=Flask(__name__); app.secret_key=os.environ.get('BUDDYWORLD_SITE_SECRET','change-me'); app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=True,MAX_CONTENT_LENGTH=65536)
CSS='''body{margin:0;background:#050914;color:#e9f7ff;font-family:ui-monospace,monospace}.top{display:flex;justify-content:space-between;gap:10px;padding:16px 22px;border-bottom:1px solid #17334d;background:#08111f}.brand{font-weight:900;color:#fff;text-decoration:none}.brand span{color:#49e7ff}.wrap{max-width:1050px;margin:auto;padding:22px}.panel{background:#0b1423;border:1px solid #17334d;border-radius:16px;padding:18px;margin-bottom:14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}.card{background:#0d1929;border:1px solid #1d3d58;border-radius:12px;padding:13px}.btn,button{background:#0a1626;color:#e9f7ff;border:1px solid #1c3b56;border-radius:9px;padding:10px 12px;text-decoration:none;cursor:pointer}.primary{background:#49e7ff!important;color:#031019!important;border-color:#49e7ff!important;font-weight:800}input,select{width:100%;box-sizing:border-box;background:#07111e;color:#fff;border:1px solid #224562;border-radius:9px;padding:10px;font:inherit;margin:6px 0 12px}.muted{color:#7e9bb0}.flash{padding:10px;border:1px solid #ffc857;background:#2a2108;border-radius:9px;margin-bottom:12px}.ok{color:#4df59b}.warn{color:#ffc857}.bad{color:#ff617d}.trade{border-left:4px solid #49e7ff}.split{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:700px){.split{grid-template-columns:1fr}.top{flex-direction:column}}'''
HOME='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Buddy World</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><a class=btn href=/trades>TRADE BOARD</a></div><main class=wrap>{% for m in get_flashed_messages() %}<div class=flash>{{m}}</div>{% endfor %}<section class=panel><small>BUDDY WORLD V24.3</small><h1>Add Buddy by ID — no ESP Wi‑Fi needed</h1><p class=muted>Open the Buddy's ID screen and type the <b>BDY-XXXXXXXX</b> code here. Choose a site PIN so only you can edit its web trade page.</p><form method=post action=/add><label>Buddy ID</label><input name=buddy_id placeholder="BDY-12AB34CD" maxlength=32 autocapitalize=characters autocomplete=off required><label>Site PIN</label><input name=pin type=password minlength=4 maxlength=12 required><button class=primary>ADD / OPEN BUDDY</button></form></section><section class=grid><div class=card><small>REGISTERED</small><h2>{{stats.buddies}}</h2></div><div class=card><small>FOR TRADE</small><h2>{{stats.items}}</h2></div><div class=card><small>OPEN OFFERS</small><h2>{{stats.offers}}</h2></div></section></main></body></html>'''
PROFILE='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>{{bid}}</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><div><a class=btn href=/trades>TRADES</a>{% if mine %} <a class="btn primary" href="/manage/{{bid}}">MANAGE</a>{% endif %}</div></div><main class=wrap><section class=panel><small>BUDDY PASSPORT</small><h1>{{bid}}</h1><p>{{p.name}} · {{p.mood}} · SCORE {{p.score}}</p><p class=muted>{% if p.site_only %}Added by ID. Device sync is optional.{% else %}Last device sync: {{p.updated_at}}{% endif %}</p></section><section class=panel><h2>FOR TRADE</h2><div class=grid>{% for x in items %}<div class="card trade"><b>#{{x.effect_id}} {{x.name}}</b><br><small>{{x.rarity}}</small></div>{% else %}<div class=muted>No cosmetics listed.</div>{% endfor %}</div></section></main></body></html>'''
MANAGE='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Manage {{bid}}</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><div><a class=btn href="/b/{{bid}}">PUBLIC</a> <a class=btn href=/logout>LOG OUT</a></div></div><main class=wrap>{% for m in get_flashed_messages() %}<div class=flash>{{m}}</div>{% endfor %}<section class=panel><h1>{{bid}}</h1><p class=muted>Website trade planning. Permanent item transfer still happens Buddy-to-Buddy so the physical inventory stays correct.</p></section><div class=split><section class=panel><h2>ADD TO TRADE LIST</h2><form method=post action="/manage/{{bid}}/trade-list/add"><label>Cosmetic</label><select name=effect_id>{% for x in catalog %}<option value="{{x.id}}">#{{x.id}} {{x.name}} · {{x.rarity}}</option>{% endfor %}</select><button class=primary>ADD</button></form></section><section class=panel><h2>YOUR TRADE LIST</h2>{% for x in items %}<div class="card trade"><b>COSMETIC #{{x.effect_id}}</b> · {{x.rarity}}<form method=post action="/manage/{{bid}}/trade-list/remove"><input type=hidden name=effect_id value="{{x.effect_id}}"><button>REMOVE</button></form></div>{% else %}<p class=muted>Nothing listed yet.</p>{% endfor %}</section></div><section class=panel><h2>SEND TRADE OFFER</h2><form method=post action="/manage/{{bid}}/offer"><label>Other Buddy ID</label><input name=to_buddy placeholder="BDY-XXXXXXXX" required><label>I offer</label><select name=offered multiple size=7>{% for x in items %}<option value="{{x.effect_id}}">COSMETIC #{{x.effect_id}} · {{x.rarity}}</option>{% endfor %}</select><label>I want</label><select name=wanted multiple size=7>{% for x in catalog %}<option value="{{x.id}}">COSMETIC #{{x.id}} · {{x.rarity}}</option>{% endfor %}</select><label>Message</label><input name=message maxlength=120 placeholder="Want to swap?"><button class=primary>SEND OFFER</button></form></section><section class=panel><h2>INCOMING</h2><div class=grid>{% for o in incoming %}<div class="card trade"><b>#{{o.id}} FROM {{o.from_buddy}}</b><p>Offers {{o.offered}}</p><p>Wants {{o.wanted}}</p><p class={{o.cls}}>{{o.status|upper}}</p>{% if o.status=='open' %}<form method=post action="/manage/{{bid}}/offer/{{o.id}}/accept"><button class=primary>ACCEPT</button></form><form method=post action="/manage/{{bid}}/offer/{{o.id}}/decline"><button>DECLINE</button></form>{% endif %}</div>{% else %}<p class=muted>No incoming offers.</p>{% endfor %}</div></section><section class=panel><h2>OUTGOING</h2><div class=grid>{% for o in outgoing %}<div class=card><b>#{{o.id}} TO {{o.to_buddy}}</b><p>Offers {{o.offered}}</p><p>Wants {{o.wanted}}</p><p class={{o.cls}}>{{o.status|upper}}</p>{% if o.status=='accepted' %}<b class=ok>READY TO SWAP PHYSICALLY</b>{% endif %}</div>{% else %}<p class=muted>No outgoing offers.</p>{% endfor %}</div></section></main></body></html>'''
TRADES='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Trade Board</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><b>TRADE BOARD</b></div><main class=wrap><section class=panel><h1>Cosmetics for trade</h1><div class=grid>{% for b in board %}<a class="card trade" style="color:inherit;text-decoration:none" href="/b/{{b.id}}"><b>{{b.id}}</b><p>{{b.count}} cosmetic(s)</p><small>{{b.preview}}</small></a>{% else %}<p class=muted>No listings yet.</p>{% endfor %}</div></section></main></body></html>'''

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def con():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.executescript('''CREATE TABLE IF NOT EXISTS buddies(buddy_id TEXT PRIMARY KEY,key_hash TEXT NOT NULL,profile_json TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY AUTOINCREMENT,buddy_id TEXT,event_type TEXT,message TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS buddy_owners(buddy_id TEXT PRIMARY KEY,pin_hash TEXT NOT NULL,claimed_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS trade_items(buddy_id TEXT NOT NULL,effect_id INTEGER NOT NULL,added_at TEXT NOT NULL,PRIMARY KEY(buddy_id,effect_id));CREATE TABLE IF NOT EXISTS trade_offers(id INTEGER PRIMARY KEY AUTOINCREMENT,from_buddy TEXT NOT NULL,to_buddy TEXT NOT NULL,offered_json TEXT NOT NULL,wanted_json TEXT NOT NULL,message TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);''');return c
def parse_buddy_id(x):
 raw=(x or '').strip().upper()
 compact=re.sub(r'[^0-9A-Z]','',raw)
 if compact.startswith('BDY'):compact=compact[3:]
 if re.fullmatch(r'[0-9A-F]{8}',compact):
  return 'BDY-'+compact
 return None

def norm(x):
 b=parse_buddy_id(x)
 if not b:abort(400)
 return b
def nint(x,d=0,lo=0,hi=331):
 try:x=int(x)
 except:return d
 return max(lo,min(hi,x))
def rarity(i):
 if 132<=i<=171 or 232<=i<=271:return 'RARE'
 if 172<=i<=201 or 272<=i<=301:return 'EPIC'
 if 202<=i<=221 or 302<=i<=321:return 'MYTHIC'
 if 222<=i<=231 or 322<=i<=331:return 'LEGEND'
 if i<48:return 'RARE'
 if i<89:return 'EPIC'
 if i<124:return 'MYTHIC'
 return 'LEGEND'
def catalog():return [{'id':i,'name':COSMETICS[i],'rarity':rarity(i)} for i in range(1,min(332,len(COSMETICS)))]
def placeholder(b):return {'id':b,'name':'DESK BUDDY','firmware':'V24.3','site_only':True,'score':0,'mood':'OFFLINE','personality':{},'equipped':{},'friends':[],'stats':{},'collection':{}}
def ensure(c,b):
 if not c.execute('select 1 from buddies where buddy_id=?',(b,)).fetchone():
  t=now();c.execute('insert into buddies values(?,?,?,?,?)',(b,'SITE:UNSYNCED',json.dumps(placeholder(b)),t,t));c.commit()
def mine(b):return b in session.get('owned',[])
def auth(fn):
 @wraps(fn)
 def w(bid,*a,**k):
  b=norm(bid)
  if not mine(b):flash('Open this Buddy with its site PIN first.');return redirect(url_for('home'))
  return fn(b,*a,**k)
 return w
def items(c,b):return [{'effect_id':r['effect_id'],'name':COSMETICS[r['effect_id']] if 0<=r['effect_id']<len(COSMETICS) else 'COSMETIC','rarity':rarity(r['effect_id'])} for r in c.execute('select effect_id from trade_items where buddy_id=? order by effect_id',(b,))]
def fmtids(s):
 try:a=json.loads(s)
 except:a=[]
 return ', '.join('#'+str(x)+' '+(COSMETICS[x] if isinstance(x,int) and 0<=x<len(COSMETICS) else 'COSMETIC') for x in a) or '—'
def off(r):
 d=dict(r);d['offered']=fmtids(d['offered_json']);d['wanted']=fmtids(d['wanted_json']);d['cls']='ok' if d['status']=='accepted' else ('bad' if d['status']=='declined' else 'warn');return d
def base():return BASE or request.host_url.rstrip('/')

@app.errorhandler(400)
def bad_request(e):
 flash('Invalid Buddy ID or form value. Check the code shown on the Buddy and try again.')
 return redirect(url_for('home'))

@app.get('/')
def home():
 c=con();s={'buddies':c.execute('select count(*) from buddies').fetchone()[0],'items':c.execute('select count(*) from trade_items').fetchone()[0],'offers':c.execute("select count(*) from trade_offers where status='open'").fetchone()[0]};c.close();return render_template_string(HOME,css=CSS,stats=s)
@app.post('/add')
def add():
 b=parse_buddy_id(request.form.get('buddy_id'));pin=(request.form.get('pin') or '').strip()
 if not b:
  flash('Invalid Buddy ID. Use the 8 hexadecimal characters shown on the Buddy, e.g. BDY-12AB34CD.')
  return redirect(url_for('home'))
 if not 4<=len(pin)<=12:flash('PIN must be 4–12 characters.');return redirect(url_for('home'))
 c=con();ensure(c,b);o=c.execute('select pin_hash from buddy_owners where buddy_id=?',(b,)).fetchone()
 if o and not check_password_hash(o['pin_hash'],pin):c.close();flash('Wrong site PIN.');return redirect(url_for('home'))
 if not o:c.execute('insert into buddy_owners values(?,?,?)',(b,generate_password_hash(pin),now()));c.commit()
 c.close();a=session.get('owned',[]);a=[x for x in a if x!=b]+[b];session['owned']=a[-8:];return redirect(url_for('manage',bid=b))
@app.get('/logout')
def logout():session.clear();return redirect(url_for('home'))
@app.get('/b/<bid>')
def profile(bid):
 b=norm(bid);c=con();r=c.execute('select * from buddies where buddy_id=?',(b,)).fetchone()
 if not r:c.close();abort(404)
 p=json.loads(r['profile_json']);p['updated_at']=r['updated_at'];it=items(c,b);c.close();return render_template_string(PROFILE,css=CSS,bid=b,p=p,items=it,mine=mine(b))
@app.get('/manage/<bid>')
@auth
def manage(bid):
 c=con();it=items(c,bid);inc=[off(x) for x in c.execute('select * from trade_offers where to_buddy=? order by id desc limit 40',(bid,))];out=[off(x) for x in c.execute('select * from trade_offers where from_buddy=? order by id desc limit 40',(bid,))];c.close();return render_template_string(MANAGE,css=CSS,bid=bid,items=it,catalog=catalog(),incoming=inc,outgoing=out)
@app.post('/manage/<bid>/trade-list/add')
@auth
def trade_add(bid):
 i=nint(request.form.get('effect_id'),-1,-1,331);c=con()
 if i>0:c.execute('insert or ignore into trade_items values(?,?,?)',(bid,i,now()));c.commit()
 c.close();return redirect(url_for('manage',bid=bid))
@app.post('/manage/<bid>/trade-list/remove')
@auth
def trade_remove(bid):
 i=nint(request.form.get('effect_id'),-1,-1,331);c=con();c.execute('delete from trade_items where buddy_id=? and effect_id=?',(bid,i));c.commit();c.close();return redirect(url_for('manage',bid=bid))
@app.post('/manage/<bid>/offer')
@auth
def offer(bid):
 to=parse_buddy_id(request.form.get('to_buddy'))
 if not to:
  flash('Invalid other Buddy ID. Use BDY-XXXXXXXX.')
  return redirect(url_for('manage',bid=bid))
 if to==bid:flash('Choose another Buddy.');return redirect(url_for('manage',bid=bid))
 offered=sorted({nint(x,-1,-1,331) for x in request.form.getlist('offered') if nint(x,-1,-1,331)>0});wanted=sorted({nint(x,-1,-1,331) for x in request.form.getlist('wanted') if nint(x,-1,-1,331)>0})
 c=con();ensure(c,to);allowed={r[0] for r in c.execute('select effect_id from trade_items where buddy_id=?',(bid,))};offered=[x for x in offered if x in allowed]
 if not offered:c.close();flash('Select something from your trade list.');return redirect(url_for('manage',bid=bid))
 t=now();c.execute('insert into trade_offers(from_buddy,to_buddy,offered_json,wanted_json,message,status,created_at,updated_at) values(?,?,?,?,?,?,?,?)',(bid,to,json.dumps(offered),json.dumps(wanted),(request.form.get('message') or '')[:120],'open',t,t));c.commit();c.close();flash('Offer sent.');return redirect(url_for('manage',bid=bid))
@app.post('/manage/<bid>/offer/<int:oid>/<action>')
@auth
def offer_action(bid,oid,action):
 if action not in ('accept','decline'):abort(400)
 c=con();r=c.execute('select 1 from trade_offers where id=? and to_buddy=?',(oid,bid)).fetchone()
 if not r:c.close();abort(404)
 st='accepted' if action=='accept' else 'declined';c.execute('update trade_offers set status=?,updated_at=? where id=?',(st,now(),oid));c.commit();c.close();flash('Accepted — complete the real swap Buddy-to-Buddy.' if st=='accepted' else 'Declined.');return redirect(url_for('manage',bid=bid))
@app.get('/trades')
def trades():
 c=con();board=[]
 for r in c.execute('select buddy_id,count(*) n from trade_items group by buddy_id order by n desc'):
  xs=[x['effect_id'] for x in items(c,r['buddy_id'])];board.append({'id':r['buddy_id'],'count':r['n'],'preview':', '.join('#'+str(x) for x in xs[:8])})
 c.close();return render_template_string(TRADES,css=CSS,board=board)
@app.get('/healthz')
def health():return jsonify(ok=True,version='24.3')
@app.get('/api/v1/world')
def world():
 c=con();d={'total_buddies':c.execute('select count(*) from buddies').fetchone()[0],'trade_items':c.execute('select count(*) from trade_items').fetchone()[0],'open_offers':c.execute("select count(*) from trade_offers where status='open'").fetchone()[0]};c.close();return jsonify(d)
@app.get('/api/v1/buddy/<bid>')
def api_buddy(bid):
 b=norm(bid);c=con();r=c.execute('select * from buddies where buddy_id=?',(b,)).fetchone()
 if not r:c.close();abort(404)
 p=json.loads(r['profile_json']);p['created_at']=r['created_at'];p['updated_at']=r['updated_at'];p['trade_list']=items(c,b);c.close();return jsonify(p)
@app.post('/api/v1/buddy/<bid>/sync')
def sync(bid):
 b=norm(bid);key=request.headers.get('X-Buddy-Key','')
 if not 24<=len(key)<=96:abort(401)
 raw=request.get_json(silent=True)
 if not isinstance(raw,dict):abort(400)
 raw['id']=b;raw['site_only']=False;raw['firmware']=str(raw.get('firmware','V24.3'))[:16];kh=hashlib.sha256(key.encode()).hexdigest();t=now();c=con();r=c.execute('select * from buddies where buddy_id=?',(b,)).fetchone()
 if r and not str(r['key_hash']).startswith('SITE:') and r['key_hash']!=kh:c.close();abort(403)
 enc=json.dumps(raw,separators=(',',':'))
 if r:c.execute('update buddies set key_hash=?,profile_json=?,updated_at=? where buddy_id=?',(kh,enc,t,b))
 else:c.execute('insert into buddies values(?,?,?,?,?)',(b,kh,enc,t,t))
 c.commit();c.close();return jsonify(ok=True,profile_url=f'{base()}/b/{b}',server_time=t)
@app.get('/api/v1/buddy/<bid>/qr.txt')
def qr(bid):
 b=norm(bid);q=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=1,border=0);q.add_data(f'{base()}/b/{b}');q.make(fit=True);m=q.get_matrix();n=len(m);pack=bytearray();v=k=0
 for row in m:
  for z in row:
   v=(v<<1)|(1 if z else 0);k+=1
   if k==8:pack.append(v);v=k=0
 if k:pack.append(v<<(8-k))
 return Response(f'{n}\n{pack.hex().upper()}\n',mimetype='text/plain')
con().close()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT','8080')))
