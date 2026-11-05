
// RIFT/FORGE QA portal upgrade -- Practice ONLY.
// All grants are local browser preferences; competitive/server inventory remains untouched.
const QA_PORTAL_RADIUS = 1.38;
const QA_RENDER_SIZE = 384;
const qaPortalCamera = new THREE.PerspectiveCamera(70,1,.08,900);
const qaPortalFlip = new THREE.Quaternion().setFromAxisAngle(new V(0,1,0),Math.PI);
let qaPortalRenderTick=0, qaPlayerIncoming=new V();

function qaDisposeGroup(group){
  if(!group)return;
  scene.remove(group);
  group.traverse(o=>{
    o.geometry?.dispose();
    if(o.material){
      const list=Array.isArray(o.material)?o.material:[o.material];
      list.forEach(mat=>{if(mat!==outlineMaterial)mat.dispose();});
    }
  });
}
function qaClearPortals(){
  for(let i=0;i<2;i++){
    const p=qaPortals[i];
    if(p){qaDisposeGroup(p.group);p.target?.dispose();}
    qaPortals[i]=null;
  }
  qaPortalNext=0;qaPortalCooldown=0;qaLastPosition=null;
  for(const bot of bots){bot.qaPortalUntil=0;bot.qaPortalPrevious=null;}
}
function qaPlacePortal(){
  if(mode!=='solo'||!active||!roundStarted||weapon?.id!==GATEKEEPER.id||!locked)return;
  scene.updateMatrixWorld(true);
  const forward=camera.getWorldDirection(new V());
  ray.set(camera.position,forward);ray.far=150;
  const hit=ray.intersectObjects(solidMeshes,false)[0];
  if(!hit){toast('AIM AT A WALL OR FLOOR TO PLACE A PORTAL',1.8);return;}
  const normal=hit.face.normal.clone().transformDirection(hit.object.matrixWorld).normalize();
  const point=hit.point.clone();
  const index=qaPortalNext;
  qaPortalNext=1-index;
  if(qaPortals[index]){
    qaDisposeGroup(qaPortals[index].group);
    qaPortals[index].target?.dispose();
  }
  const color=index===0?'#31c7ff':'#ff9c35';
  const group=new THREE.Group();
  const border=new THREE.Mesh(new THREE.TorusGeometry(QA_PORTAL_RADIUS,.11,12,64),
    new THREE.MeshBasicMaterial({color,emissive:color,emissiveIntensity:.5,side:THREE.DoubleSide}));
  const surface=new THREE.Mesh(new THREE.CircleGeometry(QA_PORTAL_RADIUS-.08,64),
    new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,transparent:false,toneMapped:false}));
  const lightRing=new THREE.Mesh(new THREE.TorusGeometry(QA_PORTAL_RADIUS-.2,.028,8,56),
    new THREE.MeshBasicMaterial({color:'#d7d9ff',side:THREE.DoubleSide,transparent:true,opacity:.65}));
  surface.position.z=.012;
  lightRing.position.z=.035;
  group.add(border,surface,lightRing);
  group.position.copy(point).addScaledVector(normal,.14);
  group.quaternion.setFromUnitVectors(new V(0,0,1),normal);
  scene.add(group);
  const target=new THREE.WebGLRenderTarget(QA_RENDER_SIZE,QA_RENDER_SIZE,
    {depthBuffer:true,stencilBuffer:false,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter});
  target.texture.colorSpace=THREE.SRGBColorSpace;
  qaPortals[index]={point,normal,group,surface,target};
  toast('PORTAL '+(index===0?'AZUL':'LARANJA')+' · '+(qaPortals[0]&&qaPortals[1]?'LIGAÇÃO ATIVA':'COLOCA O SEGUNDO'),2);
}
function qaPortalRotation(from,to){
  return to.group.quaternion.clone().multiply(qaPortalFlip).multiply(from.group.quaternion.clone().invert()).normalize();
}
function qaPortalFrame(){
  if(mode!=='solo'||!active||!roundStarted||respawnTimer>0)return;
  if(!qaPortals[0]||!qaPortals[1]||time<qaPortalCooldown)return;
  const center=pos.clone().add(new V(0,slide?.62:.91,0));
  for(let i=0;i<2;i++){
    const a=qaPortals[i],b=qaPortals[1-i];
    const relative=center.clone().sub(a.point);
    const face=relative.dot(a.normal);
    const lateral=relative.addScaledVector(a.normal,-face).length();
    const incoming=qaPlayerIncoming.lengthSq()>1?qaPlayerIncoming:vel;
    if(face<1.12&&face>-.4&&lateral<QA_PORTAL_RADIUS-.24&&incoming.dot(a.normal)<-.6){
      const q=qaPortalRotation(a,b);
      const look=camera.getWorldDirection(new V()).applyQuaternion(q);
      const nextVel=incoming.clone().applyQuaternion(q);
      pos.copy(b.point).addScaledVector(b.normal,1.58).add(new V(0,-.9,0));
      vel.copy(nextVel);
      if(vel.dot(b.normal)<1)vel.addScaledVector(b.normal,2-vel.dot(b.normal));
      yaw=Math.atan2(-look.x,-look.z);
      pitch=clamp(Math.asin(clamp(look.y,-1,1)),-1.48,1.48);
      grounded=false;qaPortalCooldown=time+.7;
      toast('PORTAL · MOMENTUM PRESERVADO',1.2);
      burst(pos.clone().add(new V(0,1,0)),'#bd8dfd',18,7);
      return;
    }
  }
}
function qaPortalBotFrame(bot){
  if(mode!=='solo'||!bot||bot.dead>0||!bot.g.visible||!qaPortals[0]||!qaPortals[1])return;
  if(time<(bot.qaPortalUntil||0))return;
  const center=bot.g.position.clone().add(new V(0,.92,0));
  const incoming=bot._qaIncomingVelocity||bot.v;
  for(let i=0;i<2;i++){
    const a=qaPortals[i],b=qaPortals[1-i];
    const r=center.clone().sub(a.point),d=r.dot(a.normal);
    const lateral=r.addScaledVector(a.normal,-d).length();
    if(d<1.12&&d>-.45&&lateral<QA_PORTAL_RADIUS-.25&&incoming.dot(a.normal)<-1){
      const q=qaPortalRotation(a,b);
      bot.g.position.copy(b.point).addScaledVector(b.normal,1.58).add(new V(0,-.9,0));
      bot.v.copy(incoming).applyQuaternion(q);
      if(bot.v.dot(b.normal)<1)bot.v.addScaledVector(b.normal,2-bot.v.dot(b.normal));
      bot.g.rotation.y+=Math.atan2(q.x*2,q.w*q.w-q.y*q.y+q.z*q.z);
      bot.qaPortalUntil=time+.85;
      bot.path=[];bot.routeAt=0;bot.stuck=0;
      bot.grapple=null;
      bot.lastPos.copy(bot.g.position);
      burst(bot.g.position.clone().add(new V(0,1,0)),'#a2ddfa',10,4);
      return;
    }
  }
}
function qaBulletPortal(b,old,step){
  if(mode!=='solo'||!qaPortals[0]||!qaPortals[1]||time<(b.qaPortalUntil||0))return false;
  for(let i=0;i<2;i++){
    const entry=qaPortals[i],exit=qaPortals[1-i];
    const start=old.clone().sub(entry.point).dot(entry.normal);
    const end=old.clone().add(step).sub(entry.point).dot(entry.normal);
    if(start<0||end>0||start===end)continue;
    const t=start/(start-end);
    if(t<0||t>1)continue;
    const crossing=old.clone().addScaledVector(step,t);
    const lateral=crossing.clone().sub(entry.point).addScaledVector(entry.normal,-crossing.clone().sub(entry.point).dot(entry.normal));
    if(lateral.length()>QA_PORTAL_RADIUS-.15)continue;
    const q=qaPortalRotation(entry,exit);
    const remainder=step.clone().multiplyScalar(1-t).applyQuaternion(q);
    b.v.applyQuaternion(q);
    b.g.position.copy(exit.point).add(lateral.applyQuaternion(q)).addScaledVector(exit.normal,.2).add(remainder);
    b.g.quaternion.setFromUnitVectors(new V(0,0,-1),b.v.clone().normalize());
    b.qaPortalUntil=time+.16;
    return true;
  }
  return false;
}
function qaRenderPortals(){
  if(noGL||menu||mode!=='solo'||!qaPortals[0]||!qaPortals[1]||!active||!roundStarted)return;
  qaPortalRenderTick++;
  // Render each exit view every other frame; no recursive feedback.
  const ix=qaPortalRenderTick%2,entry=qaPortals[ix],exit=qaPortals[1-ix];
  if(!entry||!exit)return;
  const rotation=qaPortalRotation(entry,exit);
  qaPortalCamera.position.copy(camera.position).sub(entry.point).applyQuaternion(rotation).add(exit.point).addScaledVector(exit.normal,.15);
  qaPortalCamera.quaternion.copy(rotation).multiply(camera.quaternion);
  qaPortalCamera.fov=camera.fov;qaPortalCamera.aspect=1;
  qaPortalCamera.updateProjectionMatrix();qaPortalCamera.updateMatrixWorld(true);
  const previous=renderer.getRenderTarget();
  const prevClear=renderer.autoClear;
  qaPortals.forEach(p=>{if(p?.surface)p.surface.visible=false;});
  try{
    renderer.setRenderTarget(entry.target);
    renderer.autoClear=true;
    renderer.clear();
    renderer.render(scene,qaPortalCamera);
    entry.surface.material.map=entry.target.texture;
    entry.surface.material.color.set('#ffffff');
    entry.surface.material.needsUpdate=true;
  }finally{
    renderer.setRenderTarget(previous);
    renderer.autoClear=prevClear;
    qaPortals.forEach(p=>{if(p?.surface)p.surface.visible=true;});
  }
}
function qaRedeemPanel(){
  if(document.getElementById('qa-redeem'))return;
  const menuArea=document.querySelector('.inventory-head')?.parentElement||document.getElementById('menu');
  if(!menuArea)return;
  const panel=document.createElement('section');
  panel.id='qa-redeem';
  panel.style.cssText='margin:16px 0;padding:17px;border:2px solid #5aa4dc;border-radius:14px;background:#121d2de8;color:white;max-width:480px;box-shadow:0 5px 22px #0004';
  panel.innerHTML='<div style="font-size:12px;letter-spacing:.15em;color:#9edfff">LOJA · CÓDIGOS DE RESGATE</div><h3 style="margin:7px 0">Código promocional</h3><div style="display:flex;gap:7px"><input id="qa-code" placeholder="Escreve o código..." autocomplete="off" maxlength="32" style="min-width:0;flex:1;background:#e8eef8;border-radius:7px;padding:9px;color:#172536"><button id="qa-code-submit" type="button" style="border-radius:7px;background:#ffcf70;color:#222;font-weight:900;padding:10px">RESGATAR</button></div><p id="qa-code-result" style="margin:9px 0 0;font-size:13px"></p><small style="opacity:.8">Válido apenas nesta versão Practice. Não desbloqueia a conta no servidor público.</small>';
  const header=menuArea.querySelector('.inventory-head');
  if(header)header.after(panel);else menuArea.prepend(panel);
  const input=panel.querySelector('#qa-code');
  const feedback=panel.querySelector('#qa-code-result');
  const redeemed=()=>localStorage.getItem('rift-qa-portal26')==='1';
  const refresh=()=>{if(redeemed())feedback.textContent='✓ GATEKEEPER desbloqueada neste browser de testes · 10 balas';};
  const redeem=()=>{
    const code=input.value.trim().toUpperCase();
    if(code!=='PORTAL26'){feedback.textContent='Código inválido. Experimenta PORTAL26.';return;}
    try{localStorage.setItem('rift-qa-portal26','1');}catch{}
    qaSelected[0]=GATEKEEPER.id;
    if(active&&mode==='solo'){
      selectedLoadout[0]=GATEKEEPER.id;slotAmmo[0]=GATEKEEPER.mag;
      slotIndex=0;ammo=GATEKEEPER.mag;equip(GATEKEEPER);
    }
    feedback.textContent='✓ PORTAL26 RESGATADO! Gatekeeper equipada no slot 1 · 10 balas';
    window.dispatchEvent(new CustomEvent('qa-portal26-redeemed'));
  };
  panel.querySelector('#qa-code-submit').addEventListener('click',redeem);
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();redeem();}});
  const shopTab=document.querySelector('.nav-tabs [data-view="shop"]');
  const show=()=>{panel.style.display=shopTab?.classList.contains('active')?'block':'none';};
  document.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>setTimeout(show,0)));
  document.querySelectorAll('#shopShortcut,#openShop').forEach(btn=>btn.addEventListener('click',()=>setTimeout(show,0)));
  refresh();show();
}
setTimeout(qaRedeemPanel,0);
