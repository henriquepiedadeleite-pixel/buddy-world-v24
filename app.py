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
CSS=''':root{--ink:#29243c;--muted:#7b758d;--paper:#fffdfa;--lav:#eeeaff;--lav2:#d5ccff;--sky:#d8f2ff;--pink:#ffd7ea;--mint:#d8f8e9;--yellow:#fff0b9;--line:#dfdaef;--shadow:0 18px 50px rgba(65,50,110,.12)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-height:100vh;color:var(--ink);font:15px/1.5 Inter,ui-rounded,"SF Pro Rounded",system-ui,sans-serif;background:radial-gradient(circle at 90% 10%,#d9f2ff 0 12%,transparent 34%),radial-gradient(circle at 3% 86%,#ffd8eb 0 10%,transparent 31%),linear-gradient(180deg,#f7f4ff 0,#fffdfa 54%,#f4fbff 100%);overflow-x:hidden}.top{position:sticky;top:0;z-index:20;display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px max(18px,calc((100vw - 1120px)/2));background:#fffdfae8;border-bottom:1px solid #ded9efb8;backdrop-filter:blur(16px)}.brand{font-weight:950;color:var(--ink);text-decoration:none;letter-spacing:-.03em;font-size:20px}.brand:before{content:'•ᴗ•';display:inline-grid;place-items:center;width:42px;height:34px;margin-right:10px;background:var(--lav2);border:2px solid var(--ink);border-radius:14px;box-shadow:3px 4px 0 var(--ink);font-size:13px;letter-spacing:0}.brand span{color:#7563cf}.wrap{max-width:1120px;margin:auto;padding:30px 18px 70px}.panel{background:#fffdfae8;border:1px solid var(--line);border-radius:28px;padding:22px;margin-bottom:16px;box-shadow:var(--shadow)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:15px;box-shadow:0 8px 22px #5f51940d}.btn,button{background:#fff;color:var(--ink);border:1.5px solid var(--line);border-radius:14px;padding:10px 13px;text-decoration:none;cursor:pointer;font:inherit;font-weight:850;transition:.18s ease}.btn:hover,button:hover{transform:translateY(-1px);border-color:#a89be7}.primary{background:var(--ink)!important;color:#fff!important;border-color:var(--ink)!important;box-shadow:0 5px 0 #c8bef4}.primary:hover{transform:translateY(-2px)}input,select{width:100%;box-sizing:border-box;background:#fff;color:var(--ink);border:1.5px solid var(--line);border-radius:14px;padding:12px 13px;font:inherit;margin:6px 0 12px;outline:none}input:focus,select:focus{border-color:#8f7be9;box-shadow:0 0 0 4px #8f7be914}.muted{color:var(--muted)}.flash{padding:13px 15px;border:1px solid #cebff7;background:#fff;border-radius:16px;margin-bottom:14px;box-shadow:var(--shadow)}.ok{color:#25855a}.warn{color:#936a12}.bad{color:#cf4860}.trade{border-left:5px solid #8b79df}.split{display:grid;grid-template-columns:1fr 1fr;gap:14px}.hero{display:grid;grid-template-columns:minmax(260px,1fr) minmax(300px,430px);gap:24px;align-items:center}.hero>div:first-child>small,.panel>small,.card>small{font-size:11px;font-weight:950;letter-spacing:.14em;color:#7869bf}.hero h1,.panel h1{font-size:clamp(34px,5vw,54px);line-height:1.02;letter-spacing:-.045em;margin:8px 0 14px}.hero h2{letter-spacing:-.025em}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:18px}.kpi{background:linear-gradient(145deg,#fff,#f7f4ff);border:1px solid var(--line);border-radius:18px;padding:13px}.kpi b{display:block;font-size:23px}.pill{display:inline-block;border:1px solid #d5cdf6;border-radius:999px;padding:6px 10px;margin:3px;background:var(--lav);font-size:11px;font-weight:850}.livebox{position:relative;min-height:350px;border-radius:28px;overflow:hidden;background:radial-gradient(circle at 50% 46%,#fff 0 12%,#e8f8ff 37%,#e9e4ff 78%);border:1px solid var(--line)}.livebox:before,.livebox:after{content:'✦';position:absolute;color:#fff;font-size:28px;text-shadow:0 2px 0 #a496e2;animation:twinkle 1.9s ease-in-out infinite}.livebox:before{left:28px;top:35px}.livebox:after{right:34px;top:75px;animation-delay:.7s}.buddyStage{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}.buddyBody{--buddy:#ff9f54;--accent:#7fe7ff;position:relative;width:168px;height:150px;border-radius:46% 46% 40% 40%;background:var(--buddy);border:4px solid var(--ink);box-shadow:0 10px 0 #c9bff4,0 24px 42px #66599d2a;animation:buddyFloat 3.7s ease-in-out infinite}.buddyBody:before,.buddyBody:after{content:'';position:absolute;width:42px;height:55px;background:var(--buddy);border:4px solid var(--ink);border-radius:55% 55% 25% 25%;top:12px;z-index:-1}.buddyBody:before{left:-25px;transform:rotate(-22deg)}.buddyBody:after{right:-25px;transform:rotate(22deg)}.eyes{position:absolute;left:0;right:0;top:51px;display:flex;justify-content:center;gap:48px}.eye{position:relative;width:16px;height:23px;background:var(--ink);border-radius:50%;animation:blink 5.2s infinite}.eye:after{content:'';position:absolute;width:5px;height:6px;background:#fff;border-radius:50%;left:4px;top:3px}.mouth{position:absolute;left:50%;top:92px;width:45px;height:20px;transform:translateX(-50%);border-bottom:5px solid var(--ink);border-radius:0 0 50% 50%}.blush{display:none;position:absolute;top:87px;width:24px;height:9px;border-radius:50%;background:#ff85ad7e}.blush.l{left:14px}.blush.r{right:14px}.buddyBody[data-mood='SAD'] .mouth,.buddyBody[data-mood='ANGRY'] .mouth{border-bottom:0;border-top:5px solid var(--ink);border-radius:50% 50% 0 0;top:105px}.buddyBody[data-mood='SLEEPY'] .eye,.buddyBody[data-mood='BORED'] .eye{height:4px;margin-top:10px;border-radius:2px}.buddyBody[data-mood='SURPRISED'] .mouth{width:21px;height:21px;border:5px solid var(--ink);border-radius:50%;top:94px}.buddyBody[data-mood='SHY'] .blush{display:block}.buddyBody[data-mood='SHY'] .eye{height:13px;margin-top:7px}.fxIcon{position:absolute;left:50%;top:-54px;transform:translateX(-50%);font-size:52px;filter:drop-shadow(2px 3px 0 #ffffff80)}.fxName{position:absolute;left:50%;bottom:-60px;transform:translateX(-50%);width:250px;text-align:center;font-weight:950;font-size:12px;background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 10px;box-shadow:0 7px 20px #66599d18}.petBubble{position:absolute;right:18px;bottom:18px;padding:10px 12px;border-radius:18px;background:#fff;border:2px solid var(--ink);text-align:center;box-shadow:5px 6px 0 #c9bff4;animation:petBob 2.9s ease-in-out infinite}.petIcon{font-size:31px}.inventoryBanner{padding:13px 15px;border-radius:16px;border:1px solid var(--line);margin-bottom:12px}.inventoryBanner.good{border-color:#a8ddc3;background:#e9fff3}.inventoryBanner.warn{border-color:#ead49b;background:#fff7d9}.ownedtag{color:#25855a;font-weight:900}.missingtag{color:#936a12;font-weight:900}.homeHero{display:grid;grid-template-columns:1.25fr .75fr;gap:26px;align-items:center;min-height:410px}.homeHero h1{font-size:clamp(38px,6vw,68px);line-height:.98;letter-spacing:-.055em;margin:8px 0 16px}.homeHero p{max-width:680px;font-size:17px}.claim{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;margin-top:22px}.homeArt{position:relative;min-height:310px;display:grid;place-items:center}.homeArt .buddyBody{transform:scale(1.18)}.homeArt .petBubble{right:8%;bottom:8%}.miniStats .card{text-align:center}.miniStats h2{font-size:32px;margin:7px 0 0}.trade form{margin-top:8px}.trade button{padding:7px 10px}.panel form label{font-size:12px;color:var(--muted);font-weight:850}.panel select[multiple]{min-height:190px}.panel h2{letter-spacing:-.035em}.panel h3{margin:7px 0 2px}.top>div{display:flex;gap:7px;flex-wrap:wrap}@keyframes buddyFloat{50%{transform:translateY(-8px) rotate(1deg)}}@keyframes petBob{50%{transform:translateY(-5px) rotate(-3deg)}}@keyframes blink{0%,45%,49%,100%{transform:scaleY(1)}47%{transform:scaleY(.08)}}@keyframes twinkle{50%{transform:scale(.7);opacity:.5}}@media(prefers-reduced-motion:reduce){*{animation:none!important;scroll-behavior:auto!important}}@media(max-width:820px){.hero,.homeHero{grid-template-columns:1fr}.homeArt{min-height:300px}.kpis{grid-template-columns:repeat(2,1fr)}.claim{grid-template-columns:1fr}.livebox{min-height:320px}}@media(max-width:700px){.split{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.wrap{padding:18px 10px 55px}.panel{border-radius:22px;padding:17px}.grid{grid-template-columns:1fr 1fr}.hero h1,.panel h1{font-size:36px}.homeHero h1{font-size:45px}}@media(max-width:450px){.grid{grid-template-columns:1fr}.kpis{grid-template-columns:1fr 1fr}.brand{font-size:18px}.buddyBody{transform:scale(.9)}.homeArt .buddyBody{transform:scale(1)}}'''
HOME='''<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1"><meta name=theme-color content="#f7f4ff"><title>Buddy World</title><style>{{css}}</style></head><body><div class=top><a class=brand href=/>BUDDY<span>WORLD</span></a><a class=btn href=/trades>TRADE HUB</a></div><main class=wrap>{% for m in get_flashed_messages() %}<div class=flash>{{m}}</div>{% endfor %}<section class="panel homeHero"><div><small>BUDDY WORLD V25</small><h1>Your Buddy has a tiny life online.</h1><p class=muted>Live mood, personality, outfit, pet and real collection — plus trades that only use cosmetics the physical Buddy actually owns.</p><form class=claim method=post action=/add><label>Buddy ID<input name=buddy_id placeholder="BDY-12AB34CD" maxlength=32 autocapitalize=characters autocomplete=off required></label><label>Site PIN<input name=pin type=password minlength=4 maxlength=12 placeholder="4–12 characters" required></label><button class=primary>OPEN MY BUDDY ✦</button></form></div><div class=homeArt><div class=livebox style="width:100%;min-height:300px"><div class=buddyStage><div class=buddyBody data-mood="HAPPY" style="--buddy:#7fe7ff;--accent:#9c86ff"><div class=fxIcon>👑</div><div class=eyes><i class=eye></i><i class=eye></i></div><i class="blush l"></i><i class="blush r"></i><div class=mouth></div><div class=fxName>YOUR LIVE BUDDY</div></div></div><div class=petBubble><div class=petIcon>🐉</div><b>pet buddy</b></div></div></div></section><section class="grid miniStats"><div class=card><small>REGISTERED</small><h2>{{stats.buddies}}</h2></div><div class=card><small>FOR TRADE</small><h2>{{stats.items}}</h2></div><div class=card><small>OPEN OFFERS</small><h2>{{stats.offers}}</h2></div></section></main></body></html>'''
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
def placeholder(b):return {'id':b,'name':'DESK BUDDY','firmware':'UNSYNCED','site_only':True,'score':0,'mood':'OFFLINE','personality':{},'equipped':{},'friends':[],'stats':{},'collection':{}}
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
def health():return jsonify(ok=True,version='25.0')
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
