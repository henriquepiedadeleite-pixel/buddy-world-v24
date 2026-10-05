import hashlib,json,os,re,sqlite3
from datetime import datetime,timezone
from functools import wraps
from flask import Flask,request,jsonify,abort,Response,render_template_string,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
import qrcode
from pathlib import Path
COSMETICS=json.loads(Path(__file__).with_name('cosmetics.json').read_text())
PETS=["NONE","MINI BUDDY","NEON MINI BUDDY","SLEEPY MINI BUDDY","SPACE MINI BUDDY","PIRATE MINI BUDDY","GOLD MINI BUDDY","VOID MINI BUDDY","DRAGON","BABY DRAGON","FIRE DRAGON","ICE DRAGON","STORM DRAGON","VOID DRAGON","SOLAR DRAGON","DOG","SLEEPY DOG","SPACE DOG","ROBOT DOG","GOLD DOG","SNOW DOG","CYBER DOG","CAT","CALICO CAT","SPACE CAT","NINJA CAT","GOLD CAT","GHOST CAT","COSMIC CAT","BIRD","BLUE BIRD","PARROT","OWL","ROBOT BIRD","FIRE BIRD","GALAXY BIRD","FRUIT TREE","APPLE TREE","CHERRY TREE","LEMON TREE","WIND TREE","GOLD TREE","COSMIC TREE","SLIME","MINT SLIME","BUBBLE SLIME","LAVA SLIME","ROBOT SLIME","GOLD SLIME","VOID SLIME","ROBOT","TINY BOT","WHEEL BOT","SCREEN BOT","DRONE BOT","GOLD BOT","OMEGA BOT","GHOST","SHY GHOST","SLEEPY GHOST","PIXEL GHOST","WIZARD GHOST","GOLD GHOST","VOID GHOST","BUNNY","WHITE BUNNY","CARROT BUNNY","SPACE BUNNY","ROBOT BUNNY","GOLD BUNNY","MOON BUNNY","FOX","SNOW FOX","FOREST FOX","SPACE FOX","ROBOT FOX","GOLD FOX","CELESTIAL FOX","TURTLE","BABY TURTLE","SEA TURTLE","SPACE TURTLE","ROBOT TURTLE","GOLD TURTLE","WORLD TURTLE","BEE","HONEY BEE","BUMBLE BEE","SPACE BEE","ROBOT BEE","GOLD BEE","QUEEN BEE","FISH","GOLDFISH","PUFFER FISH","SPACE FISH","ROBOT FISH","GLOW FISH","COSMIC FISH","ALIEN","TINY ALIEN","GREEN ALIEN","SPACE ALIEN","ROBOT ALIEN","GOLD ALIEN","GALAXY ALIEN"]
COLOR_NAMES=['ORANGE','GREEN','CYAN','PINK','YELLOW','RED','PURPLE','MINT','BLUE','WHITE','GOLD','LIME']
COLOR_HEX=['#ff8a00','#54f07a','#49e7ff','#ff70c8','#ffe15a','#ff4f65','#a56cff','#75f5d1','#4888ff','#f7fbff','#ffc857','#baff36']
MUTATION_NAMES=['NONE','RED','BLUE','GREEN','PURPLE','PINK','GOLD','CYAN','ORANGE','WHITE','LIME']
MUTATION_HEX=['#49e7ff','#ff4f65','#4888ff','#54f07a','#a56cff','#ff70c8','#ffc857','#49e7ff','#ff8a00','#f7fbff','#baff36']
DB=os.environ.get('BUDDYWORLD_DB','buddyworld.db'); BASE=os.environ.get('BUDDYWORLD_PUBLIC_BASE','').rstrip('/'); ID_RE=re.compile(r'^BDY-[0-9A-F]{8}$')
app=Flask(__name__); app.secret_key=os.environ.get('BUDDYWORLD_SITE_SECRET','change-me'); app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=True,MAX_CONTENT_LENGTH=65536)
CSS='''body{margin:0;background:#050914;color:#e9f7ff;font-family:ui-monospace,monospace}.top{display:flex;justify-content:space-between;gap:10px;padding:16px 22px;border-bottom:1px solid #17334d;background:#08111f}.brand{font-weight:900;color:#fff;text-decoration:none}.brand span{color:#49e7ff}.wrap{max-width:1050px;margin:auto;padding:22px}.panel{background:#0b1423;border:1px solid #17334d;border-radius:16px;padding:18px;margin-bottom:14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}.card{background:#0d1929;border:1px solid #1d3d58;border-radius:12px;padding:13px}.btn,button{background:#0a1626;color:#e9f7ff;border:1px solid #1c3b56;border-radius:9px;padding:10px 12px;text-decoration:none;cursor:pointer}.primary{background:#49e7ff!important;color:#031019!important;border-color:#49e7ff!important;font-weight:800}input,select{width:100%;box-sizing:border-box;background:#07111e;color:#fff;border:1px solid #224562;border-radius:9px;padding:10px;font:inherit;margin:6px 0 12px}.muted{color:#7e9bb0}.flash{padding:10px;border:1px solid #ffc857;background:#2a2108;border-radius:9px;margin-bottom:12px}.ok{color:#4df59b}.warn{color:#ffc857}.bad{color:#ff617d}.trade{border-left:4px solid #49e7ff}.split{display:grid;grid-template-columns:1fr 1fr;gap:12px}.hero{display:grid;grid-template-columns:minmax(260px,1fr) minmax(280px,420px);gap:20px;align-items:center}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.kpi{background:#07111e;border:1px solid #17334d;border-radius:12px;padding:10px}.pill{display:inline-block;border:1px solid #28516d;border-radius:999px;padding:5px 9px;margin:3px;background:#081625}.livebox{position:relative;min-height:330px;border-radius:22px;overflow:hidden;background:radial-gradient(circle at 50% 45%,#10314a,#07111e 58%,#050914);border:1px solid #224562}.buddyStage{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}.buddyBody{--buddy:#ff8a00;--accent:#49e7ff;position:relative;width:150px;height:150px;border-radius:42% 42% 38% 38%;background:var(--buddy);border:4px solid #fff;box-shadow:0 0 36px var(--accent)}.eyes{position:absolute;left:0;right:0;top:52px;display:flex;justify-content:center;gap:47px}.eye{width:15px;height:22px;background:#031019;border-radius:50%}.mouth{position:absolute;left:50%;top:93px;width:43px;height:20px;transform:translateX(-50%);border-bottom:5px solid #031019;border-radius:0 0 50% 50%}.blush{display:none;position:absolute;top:86px;width:22px;height:8px;border-radius:50%;background:#ff8bb780}.blush.l{left:16px}.blush.r{right:16px}.buddyBody[data-mood='SAD'] .mouth{border-bottom:0;border-top:5px solid #031019;border-radius:50% 50% 0 0;top:105px}.buddyBody[data-mood='SLEEPY'] .eye,.buddyBody[data-mood='BORED'] .eye{height:4px;margin-top:10px;border-radius:2px}.buddyBody[data-mood='SURPRISED'] .mouth{width:21px;height:21px;border:5px solid #031019;border-radius:50%;top:94px}.buddyBody[data-mood='SHY'] .blush{display:block}.buddyBody[data-mood='SHY'] .eye{height:13px;margin-top:7px}.fxIcon{position:absolute;left:50%;top:-48px;transform:translateX(-50%);font-size:48px}.fxName{position:absolute;left:50%;bottom:-58px;transform:translateX(-50%);width:240px;text-align:center;font-weight:900}.petBubble{position:absolute;right:18px;bottom:18px;padding:10px;border-radius:14px;background:#081625e8;border:1px solid #2a5873;text-align:center}.petIcon{font-size:30px}.inventoryBanner{padding:12px;border-radius:12px;border:1px solid #29465b;margin-bottom:12px}.inventoryBanner.good{border-color:#245e47;background:#0b2018}.inventoryBanner.warn{border-color:#705923;background:#241d0a}.ownedtag{color:#4df59b}.missingtag{color:#ffc857}@media(max-width:760px){.hero{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}@media(max-width:700px){.split{grid-template-columns:1fr}.top{flex-direction:column}}'''
HOME='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Buddy World</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><a class=btn href=/trades>TRADE BOARD</a></div><main class=wrap>{% for m in get_flashed_messages() %}<div class=flash>{{m}}</div>{% endfor %}<section class=panel><small>BUDDY WORLD V24.4</small><h1>Add Buddy by ID — no ESP Wi‑Fi needed</h1><p class=muted>Open the Buddy's ID screen and type the <b>BDY-XXXXXXXX</b> code here. Choose a site PIN so only you can edit its web trade page.</p><form method=post action=/add><label>Buddy ID</label><input name=buddy_id placeholder="BDY-12AB34CD" maxlength=32 autocapitalize=characters autocomplete=off required><label>Site PIN</label><input name=pin type=password minlength=4 maxlength=12 required><button class=primary>ADD / OPEN BUDDY</button></form></section><section class=grid><div class=card><small>REGISTERED</small><h2>{{stats.buddies}}</h2></div><div class=card><small>FOR TRADE</small><h2>{{stats.items}}</h2></div><div class=card><small>OPEN OFFERS</small><h2>{{stats.offers}}</h2></div></section></main></body></html>'''
PROFILE='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>{{bid}}</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><div><a class=btn href=/trades>TRADES</a>{% if mine %} <a class="btn primary" href="/manage/{{bid}}">MANAGE</a>{% endif %}</div></div><main class=wrap><section class="panel hero"><div><small>BUDDY PASSPORT</small><h1>{{bid}}</h1><div>{% for x in [view.temperament,view.energy,view.quirk] %}{% if x %}<span class=pill>{{x}}</span>{% endif %}{% endfor %}</div><h2><span id=moodText>{{view.mood}}</span> · <span id=scoreText>{{view.score}}</span> SCORE</h2><p class=muted id=syncText>{% if view.synced %}Last device sync: {{view.updated_at}}{% else %}Added by ID. Sync the Buddy once to import the real collection and look.{% endif %}</p><div class=kpis><div class=kpi><small>OWNED FX</small><b id=ownedCount>{{view.owned_count if view.owned_count is not none else '—'}}</b></div><div class=kpi><small>FRIENDS</small><b>{{view.friend_count}}</b></div><div class=kpi><small>CRATES</small><b>{{view.pending_crates}}</b></div><div class=kpi><small>BOSS WINS</small><b>{{view.boss_wins}}</b></div></div></div><div class=livebox><div class=buddyStage><div id=buddyBody class=buddyBody data-mood="{{view.mood}}" style="--buddy:{{view.color_hex}};--accent:{{view.accent_hex}}"><div id=fxIcon class=fxIcon>{{view.effect_icon}}</div><div class=eyes><i class=eye></i><i class=eye></i></div><i class="blush l"></i><i class="blush r"></i><div class=mouth></div><div id=fxName class=fxName>{{view.effect_name}}</div></div></div><div class=petBubble><div id=petIcon class=petIcon>{{view.pet_icon}}</div><b id=petName>{{view.pet_name}}</b><div class=muted id=petMeta>{{view.pet_meta}}</div></div></div></section><section class=panel><h2>PERSONALITY + LOADOUT</h2><div class=grid><div class=card><small>TEMPERAMENT</small><h3 id=temp>{{view.temperament or '—'}}</h3></div><div class=card><small>ENERGY</small><h3 id=energy>{{view.energy or '—'}}</h3></div><div class=card><small>QUIRK</small><h3 id=quirk>{{view.quirk or '—'}}</h3></div><div class=card><small>COLOR</small><h3 id=colorName>{{view.color_name}}</h3></div><div class=card><small>COSMETIC</small><h3 id=effectName>{{view.effect_name}}</h3><span id=effectMutation>{{view.effect_mutation}}</span></div><div class=card><small>PET</small><h3 id=petLoadout>{{view.pet_name}}</h3><span id=petEvolution>{{view.pet_meta}}</span></div></div></section><section class=panel><h2>FOR TRADE</h2><div class=grid>{% for x in items %}<div class="card trade"><b>#{{x.effect_id}} {{x.name}}</b><br><small>{{x.rarity}}</small></div>{% else %}<div class=muted>No cosmetics listed.</div>{% endfor %}</div></section></main><script>const BID={{bid|tojson}};function fxicon(n){n=(n||'').toUpperCase();if(n.includes('CROWN'))return '👑';if(n.includes('HEAD'))return '🎧';if(n.includes('BOW'))return '🎀';if(n.includes('FIRE')||n.includes('FLAME'))return '🔥';if(n.includes('HALO'))return '✨';if(n.includes('SUNGLASS'))return '😎';if(n.includes('THUNDER')||n.includes('LIGHTNING'))return '⚡';if(n.includes('DRAGON'))return '🐉';if(n.includes('WING'))return '🪽';if(n.includes('WATCH')||n.includes('CLOCK'))return '⌚';return '✦'}function picon(n){n=(n||'').toUpperCase();if(n.includes('DRAGON'))return '🐉';if(n.includes('DOG'))return '🐶';if(n.includes('CAT'))return '🐱';if(n.includes('BIRD'))return '🐦';if(n.includes('GHOST'))return '👻';if(n.includes('BUNNY'))return '🐰';if(n.includes('FOX'))return '🦊';if(n.includes('TURTLE'))return '🐢';if(n.includes('BEE'))return '🐝';if(n.includes('FISH'))return '🐟';if(n.includes('ALIEN'))return '👽';return n==='NONE'?'—':'🤖'}async function refreshBuddy(){try{let r=await fetch('/api/v1/buddy/'+BID,{cache:'no-store'});if(!r.ok)return;let v=(await r.json()).web_view||{};buddyBody.dataset.mood=v.mood||'CALM';buddyBody.style.setProperty('--buddy',v.color_hex||'#ff8a00');buddyBody.style.setProperty('--accent',v.accent_hex||'#49e7ff');moodText.textContent=v.mood||'CALM';scoreText.textContent=v.score||0;ownedCount.textContent=v.owned_count??'—';fxIcon.textContent=fxicon(v.effect_name);fxName.textContent=v.effect_name||'NONE';petIcon.textContent=picon(v.pet_name);petName.textContent=v.pet_name||'NONE';petMeta.textContent=v.pet_meta||'';temp.textContent=v.temperament||'—';energy.textContent=v.energy||'—';quirk.textContent=v.quirk||'—';colorName.textContent=v.color_name||'ORANGE';effectName.textContent=v.effect_name||'NONE';effectMutation.textContent=v.effect_mutation||'';petLoadout.textContent=v.pet_name||'NONE';petEvolution.textContent=v.pet_meta||'';syncText.textContent=v.synced?'Last device sync: '+(v.updated_at||''):'Added by ID. Sync the Buddy once to import the real collection and look.'}catch(e){}}setInterval(refreshBuddy,5000)</script></body></html>'''
MANAGE='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><title>Manage {{bid}}</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><div><a class=btn href="/b/{{bid}}">PUBLIC</a> <a class=btn href=/trades>TRADES</a> <a class=btn href=/logout>LOG OUT</a></div></div><main class=wrap>{% for m in get_flashed_messages() %}<div class=flash>{{m}}</div>{% endfor %}<section class=panel><h1>{{bid}} · TRADE HUB</h1>{% if inventory_synced %}<div class="inventoryBanner good"><b>REAL INVENTORY LOADED</b> · {{owned_count}} owned · {{missing_count}} missing</div>{% else %}<div class="inventoryBanner warn"><b>NO DEVICE INVENTORY YET</b> · sync the Buddy once so the lists can be filtered correctly.</div>{% endif %}</section><div class=split><section class=panel><h2>ADD WHAT I HAVE</h2>{% if inventory_synced and available %}<form method=post action="/manage/{{bid}}/trade-list/add"><select name=effect_id>{% for x in available %}<option value="{{x.id}}">#{{x.id}} {{x.name}} · {{x.rarity}}</option>{% endfor %}</select><button class=primary>ADD TO TRADE LIST</button></form>{% elif inventory_synced %}<p class=muted>No more owned cosmetics available to list.</p>{% else %}<p class=muted>Waiting for a real inventory snapshot.</p>{% endif %}</section><section class=panel><h2>MY TRADE LIST</h2>{% for x in items %}<div class="card trade"><b>#{{x.effect_id}} {{x.name}}</b> · {{x.rarity}}<form method=post action="/manage/{{bid}}/trade-list/remove"><input type=hidden name=effect_id value="{{x.effect_id}}"><button>REMOVE</button></form></div>{% else %}<p class=muted>Nothing listed yet.</p>{% endfor %}</section></div><section class=panel><h2>SEND TRADE OFFER</h2>{% if inventory_synced %}<form method=post action="/manage/{{bid}}/offer"><label>Other Buddy ID</label><input name=to_buddy placeholder="BDY-XXXXXXXX" required><div class=split><div><label>I OFFER — only from my trade list</label><select name=offered multiple size=8>{% for x in items %}<option value="{{x.effect_id}}">#{{x.effect_id}} {{x.name}} · {{x.rarity}}</option>{% endfor %}</select></div><div><label>I WANT — only cosmetics I am missing</label><select name=wanted multiple size=8>{% for x in missing %}<option value="{{x.id}}">#{{x.id}} {{x.name}} · {{x.rarity}}</option>{% endfor %}</select></div></div><input name=message maxlength=120 placeholder="Want to swap?"><button class=primary>SEND OFFER</button></form>{% else %}<p class=muted>Sync the physical Buddy once before creating offers.</p>{% endif %}</section><section class=panel><h2>INCOMING</h2><div class=grid>{% for o in incoming %}<div class="card trade"><b>#{{o.id}} FROM {{o.from_buddy}}</b><p><span class=ownedtag>THEY OFFER</span><br>{{o.offered}}</p><p><span class=missingtag>THEY WANT</span><br>{{o.wanted}}</p><p class={{o.cls}}>{{o.status|upper}}</p>{% if o.status=='open' %}<form method=post action="/manage/{{bid}}/offer/{{o.id}}/accept"><button class=primary>ACCEPT</button></form><form method=post action="/manage/{{bid}}/offer/{{o.id}}/decline"><button>DECLINE</button></form>{% endif %}</div>{% else %}<p class=muted>No incoming offers.</p>{% endfor %}</div></section><section class=panel><h2>OUTGOING</h2><div class=grid>{% for o in outgoing %}<div class=card><b>#{{o.id}} TO {{o.to_buddy}}</b><p>{{o.offered}}</p><p>{{o.wanted}}</p><p class={{o.cls}}>{{o.status|upper}}</p>{% if o.status=='accepted' %}<b class=ok>READY TO SWAP PHYSICALLY</b>{% endif %}</div>{% else %}<p class=muted>No outgoing offers.</p>{% endfor %}</div></section></main></body></html>'''
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
def decode_bitset(hex_string,count):
 try:data=bytes.fromhex(hex_string or '')
 except:return None
 if not data:return None
 return [i for i in range(count) if (i>>3)<len(data) and (data[i>>3] & (1 << (i&7)))]

def owned_effect_ids(p):
 col=p.get('collection') if isinstance(p.get('collection'),dict) else {}
 ids=decode_bitset(col.get('effects_hex'),min(332,len(COSMETICS)))
 return None if ids is None else {i for i in ids if i>0}

def get_profile(c,b):
 r=c.execute('select * from buddies where buddy_id=?',(b,)).fetchone()
 if not r:return None,None
 p=json.loads(r['profile_json']);p['created_at']=r['created_at'];p['updated_at']=r['updated_at'];return p,r

def effect_icon(n):
 n=(n or '').upper()
 if 'CROWN' in n:return '👑'
 if 'HEAD' in n:return '🎧'
 if 'BOW' in n:return '🎀'
 if 'FIRE' in n or 'FLAME' in n:return '🔥'
 if 'DRAGON' in n:return '🐉'
 if 'WING' in n:return '🪽'
 if 'WATCH' in n or 'CLOCK' in n:return '⌚'
 return '✦'

def pet_icon(n):
 n=(n or '').upper()
 for w,i in [('DRAGON','🐉'),('DOG','🐶'),('CAT','🐱'),('BIRD','🐦'),('GHOST','👻'),('BUNNY','🐰'),('FOX','🦊'),('TURTLE','🐢'),('BEE','🐝'),('FISH','🐟'),('ALIEN','👽')]:
  if w in n:return i
 return '—' if n=='NONE' else '🤖'

def web_view(p):
 eq=p.get('equipped') if isinstance(p.get('equipped'),dict) else {}
 pe=p.get('personality') if isinstance(p.get('personality'),dict) else {}
 st=p.get('stats') if isinstance(p.get('stats'),dict) else {}
 ci=nint(eq.get('color_id'),0,0,len(COLOR_NAMES)-1);fx=nint(eq.get('effect_id'),0,0,len(COSMETICS)-1);pet=nint(eq.get('pet_id'),0,0,len(PETS)-1);fm=nint(eq.get('effect_mutation'),0,0,10);pm=nint(eq.get('pet_mutation'),0,0,10);evo=nint(eq.get('pet_evolution'),0,0,2);own=owned_effect_ids(p);fn=COSMETICS[fx];pn=PETS[pet]
 return {'synced':not bool(p.get('site_only',False)) and own is not None,'updated_at':p.get('updated_at',''),'mood':str(p.get('mood','OFFLINE'))[:20],'score':nint(p.get('score'),0,0,2147483647),'pending_crates':nint(p.get('pending_crates'),0,0,65535),'boss_wins':nint(st.get('boss_wins'),0,0,2147483647),'friend_count':len(p.get('friends') or []),'owned_count':len(own) if own is not None else None,'temperament':str(pe.get('temperament',''))[:20],'energy':str(pe.get('energy',''))[:20],'quirk':str(pe.get('quirk',''))[:20],'color_name':COLOR_NAMES[ci],'color_hex':COLOR_HEX[ci],'effect_name':fn,'effect_icon':effect_icon(fn),'effect_mutation':('MUT '+MUTATION_NAMES[fm]) if fm else 'NO MUTATION','accent_hex':MUTATION_HEX[fm] if fm else '#49e7ff','pet_name':pn,'pet_icon':pet_icon(pn),'pet_meta':('EVO '+str(evo) if evo else 'BASE')+((' · MUT '+MUTATION_NAMES[pm]) if pm else '')}

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
 b=norm(bid);c=con();p,r=get_profile(c,b)
 if not p:c.close();abort(404)
 it=items(c,b);v=web_view(p);c.close();return render_template_string(PROFILE,css=CSS,bid=b,p=p,view=v,items=it,mine=mine(b))
@app.get('/manage/<bid>')
@auth
def manage(bid):
 c=con();p,_=get_profile(c,bid);own=owned_effect_ids(p or {});it=items(c,bid);listed={x['effect_id'] for x in it};cat=catalog();available=[x for x in cat if own is not None and x['id'] in own and x['id'] not in listed];missing=[x for x in cat if own is not None and x['id'] not in own];inc=[off(x) for x in c.execute('select * from trade_offers where to_buddy=? order by id desc limit 40',(bid,))];out=[off(x) for x in c.execute('select * from trade_offers where from_buddy=? order by id desc limit 40',(bid,))];c.close();return render_template_string(MANAGE,css=CSS,bid=bid,items=it,available=available,missing=missing,incoming=inc,outgoing=out,inventory_synced=own is not None,owned_count=len(own) if own is not None else 0,missing_count=len(missing))
@app.post('/manage/<bid>/trade-list/add')
@auth
def trade_add(bid):
 i=nint(request.form.get('effect_id'),-1,-1,331);c=con();p,_=get_profile(c,bid);own=owned_effect_ids(p or {})
 if own is None:c.close();flash('Sync the physical Buddy once before adding trade items.');return redirect(url_for('manage',bid=bid))
 if i not in own:c.close();flash('That cosmetic is not in this Buddy real collection.');return redirect(url_for('manage',bid=bid))
 c.execute('insert or ignore into trade_items values(?,?,?)',(bid,i,now()));c.commit();c.close();return redirect(url_for('manage',bid=bid))
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
 c=con();ensure(c,to);p,_=get_profile(c,bid);own=owned_effect_ids(p or {});allowed={r[0] for r in c.execute('select effect_id from trade_items where buddy_id=?',(bid,))};offered=[x for x in offered if x in allowed and (own is None or x in own)];wanted=[x for x in wanted if own is None or x not in own]
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
def health():return jsonify(ok=True,version='24.4')
@app.get('/api/v1/world')
def world():
 c=con();d={'total_buddies':c.execute('select count(*) from buddies').fetchone()[0],'trade_items':c.execute('select count(*) from trade_items').fetchone()[0],'open_offers':c.execute("select count(*) from trade_offers where status='open'").fetchone()[0]};c.close();return jsonify(d)
@app.get('/api/v1/buddy/<bid>')
def api_buddy(bid):
 b=norm(bid);c=con();p,r=get_profile(c,b)
 if not p:c.close();abort(404)
 p['trade_list']=items(c,b);p['web_view']=web_view(p);c.close();resp=jsonify(p);resp.headers['Cache-Control']='no-store';return resp
@app.post('/api/v1/buddy/<bid>/sync')
def sync(bid):
 b=norm(bid);key=request.headers.get('X-Buddy-Key','')
 if not 24<=len(key)<=96:abort(401)
 raw=request.get_json(silent=True)
 if not isinstance(raw,dict):abort(400)
 raw['id']=b;raw['site_only']=False;raw['firmware']=str(raw.get('firmware','V24.4'))[:16];kh=hashlib.sha256(key.encode()).hexdigest();t=now();c=con();r=c.execute('select * from buddies where buddy_id=?',(b,)).fetchone()
 if r and not str(r['key_hash']).startswith('SITE:') and r['key_hash']!=kh:c.close();abort(403)
 enc=json.dumps(raw,separators=(',',':'))
 if r:c.execute('update buddies set key_hash=?,profile_json=?,updated_at=? where buddy_id=?',(kh,enc,t,b))
 else:c.execute('insert into buddies values(?,?,?,?,?)',(b,kh,enc,t,t))
 own=owned_effect_ids(raw)
 if own is not None:
  for rr in list(c.execute('select effect_id from trade_items where buddy_id=?',(b,))):
   if rr[0] not in own:c.execute('delete from trade_items where buddy_id=? and effect_id=?',(b,rr[0]))
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
