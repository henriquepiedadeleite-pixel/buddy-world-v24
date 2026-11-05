import os, re, requests
from pathlib import Path
from flask import Flask, Response, redirect, request

app = Flask(__name__)
UPSTREAM = "https://rift-forge-arena.andresapiedade1.chatgpt.site"
S = requests.Session()
S.headers.update({"User-Agent":"RIFT-FORGE-QA-Practice/1.0","Accept-Encoding":"identity"})
ADMIN_BOOT = r"""
// RIFT / FORGE ADMIN PRACTICE (offline QA only, never grants server permissions)
const ADMIN_PRACTICE=true;
const qaCatalog=[...WEAPONS,GATEKEEPER];
const qaSkins=[...SKINS];
const qaSelected=[GATEKEEPER.id,qaCatalog[1]?.id,qaCatalog[2]?.id];
let qaSkin=qaSkins[0]?.id;
let qaSlot=0;
function qaInterface(){
  const section=document.querySelector('.lobby');
  if(!section||document.getElementById('qa-open'))return;
  const button=document.createElement('button');
  button.id='qa-open';button.className='play-btn';
  button.textContent='🛠 MODO ADMIN · TESTAR TUDO';
  button.style.cssText='margin:12px 0;background:#ffe29c';
  section.insertBefore(button,document.getElementById('playBtn'));
  const wrap=document.createElement('div');
  wrap.id='qa-panel';wrap.className='modal hidden';
  wrap.innerHTML='<section class="dialog wide" style="max-height:88vh;overflow:auto"><button id="qa-close" class="close" type="button">×</button><div class="eyebrow">RIFT / FORGE · PRACTICE</div><h2>MODO ADMIN DE TESTES</h2><p>Armas e skins disponíveis no Practice. Não desbloqueia contas online.</p><div id="qa-options"></div><button id="qa-done" class="play-btn" type="button">CONFIRMAR</button></section>';
  document.body.append(wrap);
  const options=document.getElementById('qa-options');
  const selectSlot=document.createElement('select');selectSlot.id='qa-slot';selectSlot.style.cssText='width:100%;margin:7px 0';
  for(let n=0;n<3;n++){const op=document.createElement('option');op.value=n;op.textContent='SLOT '+(n+1);selectSlot.append(op);}
  const weaponSearch=document.createElement('input');weaponSearch.placeholder='Pesquisar armas…';weaponSearch.style.cssText='width:100%;margin:7px 0';
  const weaponChoice=document.createElement('select');weaponChoice.size=9;weaponChoice.style.cssText='width:100%;height:190px';
  const skinChoice=document.createElement('select');skinChoice.style.cssText='width:100%;margin:10px 0';
  const label=document.createElement('div');label.style.cssText='font-size:11px;margin:8px 0';
  options.append(selectSlot,weaponSearch,weaponChoice,skinChoice,label);
  function list(){
    weaponChoice.replaceChildren();
    for(const w of qaCatalog.filter(w=>w.name.toLowerCase().includes(weaponSearch.value.toLowerCase())||w.type?.toLowerCase().includes(weaponSearch.value.toLowerCase()))){
      const op=document.createElement('option');op.value=w.id;op.textContent=w.name+' · '+w.type;op.selected=w.id===qaSelected[qaSlot];weaponChoice.append(op);
    }
    label.textContent='Slot '+(qaSlot+1)+': '+(qaCatalog.find(w=>w.id===qaSelected[qaSlot])?.name||'vazio');
  }
  qaSkins.forEach(s=>{const op=document.createElement('option');op.value=s.id;op.textContent=s.name||s.id;skinChoice.append(op);});
  function open(){
    if(document.getElementById('mode')?.value!=='solo' && menu){alert('Modo Admin só no Practice!');return;}
    wrap.classList.remove('hidden');selectSlot.value=String(qaSlot);skinChoice.value=qaSkin;list();
  }
  function close(){wrap.classList.add('hidden');}
  button.onclick=open;document.getElementById('qa-close').onclick=close;document.getElementById('qa-done').onclick=close;
  selectSlot.onchange=()=>{qaSlot=Number(selectSlot.value);list();};
  weaponSearch.oninput=list;
  weaponChoice.onchange=()=>{
    qaSelected[qaSlot]=weaponChoice.value;label.textContent='Equipado: '+(qaCatalog.find(w=>w.id===weaponChoice.value)?.name||'');
    if(active&&mode==='solo'&&roundStarted){
      selectedLoadout[qaSlot]=weaponChoice.value;slotAmmo[qaSlot]=weaponById(weaponChoice.value).mag;
      slotIndex=qaSlot;equip(weaponById(weaponChoice.value));renderWeaponSlots();
    }
  };
  skinChoice.onchange=()=>{
    qaSkin=skinChoice.value;
    if(active&&mode==='solo'){selectedSkin=qaSkin;equip(weapon,false);}
  };
  document.getElementById('mode')?.addEventListener('change',()=>button.classList.toggle('hidden',document.getElementById('mode').value!=='solo'));
  window.addEventListener('keydown',e=>{
    if(e.code==='KeyT'&&!e.repeat&&active&&mode==='solo'&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName)){e.preventDefault();wrap.classList.contains('hidden')?open():close();}
  },true);
  list();
}
setTimeout(qaInterface,0);

// Gatekeeper portal pair: Practice-only, no network or account privileges.
const qaPortals=[null,null];
let qaPortalNext=0,qaPortalCooldown=0,qaLastPosition=null;
function qaClearPortals(){
  for(const p of qaPortals){if(p){scene.remove(p.group);p.group.traverse(o=>{o.geometry?.dispose();if(o.material)o.material.dispose();});}}
  qaPortals[0]=null;qaPortals[1]=null;qaPortalCooldown=0;qaLastPosition=null;qaPortalNext=0;
}
function qaPlacePortal(){
  if(mode!=='solo'||!active||!roundStarted||weapon?.id!==GATEKEEPER.id||!locked)return;
  const dir=camera.getWorldDirection(new V());
  ray.set(camera.position,dir);ray.far=150;
  const hit=ray.intersectObjects(solidMeshes,true)[0];
  if(!hit){toast('NO WALL OR FLOOR IN RANGE',1.2);return;}
  const n=hit.face.normal.clone().transformDirection(hit.object.matrixWorld).normalize();
  const p=hit.point.clone();
  const i=qaPortalNext;qaPortalNext=1-i;
  if(qaPortals[i]){scene.remove(qaPortals[i].group);qaPortals[i].group.traverse(o=>{o.geometry?.dispose();if(o.material)o.material.dispose();});}
  const g=new THREE.Group();
  const color=i===0?'#37baff':'#ffab41';
  const ring=new THREE.Mesh(new THREE.TorusGeometry(.78,.09,12,48),new THREE.MeshBasicMaterial({color,transparent:true,opacity:.98,side:THREE.DoubleSide}));
  const veil=new THREE.Mesh(new THREE.CircleGeometry(.73,48),new THREE.MeshBasicMaterial({color,transparent:true,opacity:.27,side:THREE.DoubleSide,depthWrite:false}));
  g.add(ring,veil);g.position.copy(p).addScaledVector(n,.11);
  g.quaternion.setFromUnitVectors(new V(0,0,1),n);
  scene.add(g);qaPortals[i]={point:p,normal:n,group:g};
  toast('PORTAL '+(i===0?'BLUE':'ORANGE')+' PLACED · '+(qaPortals[0]&&qaPortals[1]?'PAIR READY':'PLACE NEXT PORTAL'),2);
}
function qaPortalFrame(){
  if(mode!=='solo'||!active||!roundStarted)return;
  const center=pos.clone().add(new V(0,slide?.55:.95,0));
  if(!qaLastPosition){qaLastPosition=center;return;}
  if(!qaPortals[0]||!qaPortals[1]||time<qaPortalCooldown){qaLastPosition=center;return;}
  for(let i=0;i<2;i++){
    const a=qaPortals[i],b=qaPortals[1-i];
    const rel=center.clone().sub(a.point),old=qaLastPosition.clone().sub(a.point);
    const signed=rel.dot(a.normal),before=old.dot(a.normal);
    const sideways=rel.addScaledVector(a.normal,-signed).length();
    if(signed>-.3&&signed<1.05&&sideways<.74&&(before>signed+.005||vel.dot(a.normal)<-1)){
      const q=new THREE.Quaternion().setFromUnitVectors(a.normal.clone().negate(),b.normal);
      const facing=camera.getWorldDirection(new V()).applyQuaternion(q);
      vel.applyQuaternion(q);
      pos.copy(b.point).addScaledVector(b.normal,1.45).add(new V(0,-.9,0));
      yaw=Math.atan2(-facing.x,-facing.z);
      pitch=clamp(Math.asin(clamp(facing.y,-1,1)),-1.48,1.48);
      qaPortalCooldown=time+1.2;qaLastPosition=null;
      toast('PORTAL TRANSIT · MOMENTUM KEPT',1.2);burst(pos.clone().add(new V(0,1,0)),'#b991ff',24,9);
      return;
    }
  }
  qaLastPosition=center;
}
canvas.addEventListener('mousedown',e=>{
  if(e.button!==2||mode!=='solo'||!active||!roundStarted||weapon?.id!==GATEKEEPER.id)return;
  if(controlMode==='drag'&&!touchpad)return; // right drag is needed for camera in touchpad mode.
  e.preventDefault();e.stopImmediatePropagation();qaPlacePortal();
},true);
window.addEventListener('keydown',e=>{if(e.code==='KeyP'&&mode==='solo'&&active&&roundStarted&&weapon?.id===GATEKEEPER.id){e.preventDefault();qaPlacePortal();}},true);
"""

# Lightweight diagnostics: do not log passwords, credentials or account requests.
def qa_probe():
    for filename in ("menu.js","net.js","game.js"):
        try:
            res=S.get(UPSTREAM+"/"+filename, timeout=8)
            print("QA_SOURCE",filename,"status",res.status_code,"mime",res.headers.get("Content-Type"),"bytes",len(res.content),flush=True)
            if filename in ("menu.js","net.js") and res.status_code==200:
                for i,line in enumerate(res.text.splitlines()):
                    if any(key in line for key in ("await api(", "api('", 'api("', "getProfile(", "refreshProfile(", "initialize", "window.addEventListener('load'")):
                        print("QA_SOURCE_LINE",filename,i+1,line[:440],flush=True)
        except Exception as e:
            print("QA_SOURCE_FAILED",filename,type(e).__name__,flush=True)
qa_probe()

def modify_js(src):
    # Do not ever grant online inventory or server privileges.
    old_import="import {WEAPONS,SKINS,weaponById,skinById,normalizeWeapon} from './catalog.js';"
    if old_import not in src:
        return src
    src=src.replace(old_import,"import {WEAPONS,SKINS,weaponById as originalWeaponById,skinById,normalizeWeapon as originalNormalizeWeapon} from './catalog.js';",1)
    gatekeeper_boot=("const GATEKEEPER={...(WEAPONS.find(w=>w.type==='sniper')||WEAPONS[0]),"
                     "id:'rift-gatekeeper',name:'Gatekeeper · Portal Sniper',type:'sniper',"
                     "rarity:'legendary',damage:9999,mag:10,reload:2.4,cooldown:.82,"
                     "inaccuracy:0,speed:220,color:'#9b80ff'};"
                     "const weaponById=id=>id===GATEKEEPER.id?GATEKEEPER:originalWeaponById(id);"
                     "const normalizeWeapon=w=>w?.id===GATEKEEPER.id?GATEKEEPER:originalNormalizeWeapon(w);\n")
    src=src.replace("const $=id=>document.getElementById(id)",gatekeeper_boot+"const $=id=>document.getElementById(id)",1)
    src=src.replace("physics(dt);if(spawnShield>0)","qaPlayerIncoming.copy(vel);physics(dt);qaPortalFrame();if(spawnShield>0)",1)
    src=src.replace("function clearWorldActors(){","function clearWorldActors(){qaClearPortals();",1)
    src=src.replace("botMove(b,dt);b.rope.visible","b._qaIncomingVelocity=b.v.clone();botMove(b,dt);qaPortalBotFrame(b);b.rope.visible",1)
    src=src.replace("b.travelled+=len;ray.set(old,step.clone().normalize());","b.travelled+=len;if(qaBulletPortal(b,old,step))continue;ray.set(old,step.clone().normalize());",1)
    src=src.replace("renderer.autoClear=true;renderer.render(scene,camera);","qaRenderPortals();renderer.autoClear=true;renderer.render(scene,camera);",1)
    src=src.replace("aiming?(weapon.type==='sniper'?27:57)","aiming?(weapon.id===GATEKEEPER.id?11:weapon.type==='sniper'?27:57)",1)
    src=src.replace("for(let side of [-1,1]){for(let i=0;i<3;i++)orb(g,", "if(w.id===GATEKEEPER.id){const violet=m('#a084ff',.22,.18,'#5d26e8');for(let i=0;i<5;i++){orb(g,.045,0,.19,-.5+i*.14,violet);}box(g,.3,.04,.65,0,.09,-.36,violet);for(const side of [-1,1]){orb(g,.1,side*.14,.04,-.17,violet);}}for(let side of [-1,1]){for(let i=0;i<3;i++)orb(g,",1)
    point="if(!getProfile()){$('networkStatus').textContent='Wait for your inventory or refresh the balance.';return;}selectedLoadout=[...getProfile().loadout];selectedSkin=getProfile().skin;"
    replacement="if($('mode').value!=='solo'&&!getProfile()){$('networkStatus').textContent='Wait for your inventory or refresh the balance.';return;}selectedLoadout=$('mode').value==='solo'?[...qaSelected]:[...getProfile().loadout];selectedSkin=$('mode').value==='solo'?qaSkin:getProfile().skin;"
    src=src.replace(point,replacement,1)
    src=src.replace("const info=await api(mode==='solo'?'solo':'start',{room});if(mode==='solo')matchId=info.match;beginRound();","if(mode==='solo'){matchId=null;beginRound();return;}const info=await api('start',{room});beginRound();",1)
    src=src.replace("showResults(finalResults);try{const r=await api('reward'","showResults(finalResults);if(mode==='solo')return;try{const r=await api('reward'",1)
    # Character limbs were merged in the original client, sometimes breaking transforms.
    start=src.find("function humanoid(color,skinId='s00'){")
    stop=src.find("function enemyMarker(", start)
    if start>=0 and stop>start:
        stable=("function humanoid(color,skinId='s00'){"
                "const g=buildRetroRunner(THREE,{color,skin:skinById(skinId),material:m});"
                "return outline(g);}\n")
        src=src[:start]+stable+src[stop:]
    src+="\n"+ADMIN_BOOT+"\n"+(Path(__file__).parent/"qa_upgrade.js").read_text(encoding="utf-8")
    return src
@app.route("/")
def root():
    return redirect("/arena", code=302)
@app.route("/<path:path>",methods=["GET"])
def mirror(path):
    if path.startswith(("api/","_internal/","admin/")):
        return Response("Online accounts and admin privileges disabled in this QA sandbox.",status=403)
    try:
        target=UPSTREAM+"/"+path
        resp=S.get(target,params=request.args,timeout=19,allow_redirects=True)
    except requests.RequestException as exc:
        return Response("Could not load original RIFT / FORGE assets from its public website. "+type(exc).__name__,status=502)
    content_type=resp.headers.get("Content-Type","application/octet-stream")
    data=resp.content
    if resp.status_code==200 and ("javascript" in content_type or path.split("/")[-1].split("?")[0].startswith("game.js")) and ("game.js" in path):
        script=resp.text
        if "const $=id=>document.getElementById(id)" in script and "selectedLoadout" in script:
            data=modify_js(script).encode("utf-8")
    if resp.status_code==200 and "text/html" in content_type:
        text=resp.text
        text=text.replace("</head>","<style>#qa-notice{position:fixed;bottom:4px;left:8px;z-index:99;padding:5px 8px;background:#15222ee8;color:white;font:11px Arial;border-radius:5px;pointer-events:none}</style></head>",1)
        text=text.replace("</body>",'<div id="qa-notice">Modo Admin de Testes · apenas Practice · não é o servidor original</div></body>',1)
        data=text.encode("utf-8")
    headers={"Content-Type":content_type.split(";")[0]+"; charset=utf-8" if any(x in content_type for x in ("text/","javascript","json")) else content_type,
             "X-Robots-Tag":"noindex,nofollow","Cache-Control":"public,max-age=30" if ("javascript" in content_type or "css" in content_type) else "no-store"}
    return Response(data,status=resp.status_code,headers=headers)
@app.route("/__health")
def health():
    try:
        r=S.get(UPSTREAM+"/arena",timeout=8)
        return {"upstream_status":r.status_code,"upstream_type":r.headers.get("content-type","")}, (200 if r.status_code==200 else 503)
    except requests.RequestException as e:
        return {"error":type(e).__name__},503


@app.route("/__audit")
def audit():
    import json
    from urllib.parse import urljoin
    try:
        home=S.get(UPSTREAM+"/arena",timeout=14)
        links=re.findall(r"<script[^>]+src=[\"']([^\"']+)",home.text)
        names=re.findall(r"<link[^>]+href=[\"']([^\"']+)",home.text)
        reports={"page":home.status_code,"size":len(home.content),"scripts":[],"styles":[]}
        for src in links[:12]:
            uri=urljoin(home.url,src)
            res=S.get(uri,timeout=12)
            k={"src":src,"status":res.status_code,"type":res.headers.get("content-type",""),"bytes":len(res.content)}
            if "game.js" in src and res.status_code==200:
                k["patch_anchor"]=("if(!getProfile()){" in res.text)
                k["modules"]=re.findall(r"from ['\"]([^'\"]+)",res.text)[:20]
            reports["scripts"].append(k)
        for href in names[:6]:
            uri=urljoin(home.url,href)
            res=S.get(uri,timeout=12)
            reports["styles"].append({"href":href,"status":res.status_code,"bytes":len(res.content)})
        print("RIFT_AUDIT "+json.dumps(reports),flush=True)
        return reports
    except Exception as e:
        print("RIFT_AUDIT_ERROR "+repr(e),flush=True)
        return {"error":str(e)},503
