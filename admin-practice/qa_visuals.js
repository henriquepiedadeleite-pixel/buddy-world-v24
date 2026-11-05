
// RIFT / FORGE - QA visual pass (Practice only).
// Geometry is deliberately local and light enough for a browser shooter; GLB scenery loads asynchronously.
// Additional optional GLB props: Kenney CC0 (https://kenney.nl).
function qaBuildAvatar(teamColor,skinId='s00'){
  const root=new THREE.Group();
  const shellColor=new THREE.Color(skinById(skinId)?.color||'#7ad9ee');
  const team=new THREE.Color(teamColor||'#ff9d70');
  const armor=new THREE.MeshStandardMaterial({color:shellColor,roughness:.42,metalness:.42});
  const primary=new THREE.MeshStandardMaterial({color:'#142338',roughness:.55,metalness:.15});
  const plating=new THREE.MeshStandardMaterial({color:'#334c64',roughness:.35,metalness:.58});
  const graphite=new THREE.MeshStandardMaterial({color:'#0b1726',roughness:.68,metalness:.12});
  const accent=new THREE.MeshStandardMaterial({color:team,emissive:team,emissiveIntensity:.38,roughness:.28,metalness:.32});
  const visor=new THREE.MeshStandardMaterial({color:'#9ff8ff',emissive:'#58daee',emissiveIntensity:.8,roughness:.08,metalness:.8});
  const gold=new THREE.MeshStandardMaterial({color:'#eac980',metalness:.72,roughness:.23});
  const box=(group,w,h,d,x,y,z,mat,rx=0,ry=0,rz=0)=>{
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);
    mesh.position.set(x,y,z);mesh.rotation.set(rx,ry,rz);mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);return mesh;
  };
  const cyl=(group,r1,r2,h,x,y,z,mat,seg=12)=>{
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,seg),mat);
    mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);return mesh;
  };
  // Broad armored shoulders, layered vest and articulated abdomen.
  box(root,.83,.72,.36,0,1.30,0,primary);
  box(root,.73,.48,.43,0,1.35,-.01,armor);
  box(root,.66,.22,.09,0,1.48,-.235,plating);
  box(root,.33,.2,.095,0,1.34,-.26,accent);
  box(root,.11,.11,.11,0,1.34,-.32,visor);
  box(root,.79,.19,.4,0,.90,0,graphite);
  box(root,.67,.115,.41,0,.89,-.02,gold);
  box(root,.25,.15,.12,0,.86,-.24,plating);
  box(root,.59,.46,.29,0,.57,.075,primary);
  // Energy core and back-mounted twin thrusters.
  box(root,.53,.63,.24,0,1.20,.28,plating);
  for(const side of [-1,1]){
    box(root,.23,.53,.32,side*.31,1.2,.36,graphite);
    cyl(root,.125,.15,.36,side*.32,.99,.43,armor,12);
    cyl(root,.09,.09,.05,side*.32,.79,.43,visor,16);
    box(root,.13,.5,.08,side*.3,1.37,-.275,plating,0,0,side*.08);
  }
  // Smooth helmet with luminous visor and vent details.
  const head=new THREE.Group();head.position.y=1.68;root.add(head);
  const helmet=new THREE.Mesh(new THREE.IcosahedronGeometry(.305,2),armor);
  helmet.scale.set(1.14,1,.98);helmet.castShadow=true;head.add(helmet);
  box(head,.56,.19,.18,0,.06,-.245,graphite);
  box(head,.50,.13,.055,0,.075,-.344,visor);
  box(head,.25,.075,.095,0,-.125,-.295,gold);
  for(const side of [-1,1]){
    box(head,.13,.18,.14,side*.31,-.025,.03,plating);
    box(head,.07,.11,.15,side*.34,.01,.015,accent);
    box(head,.08,.08,.12,side*.22,.235,-.01,graphite);
  }
  // Pair of aerodynamic animated arms.
  const arms=[];
  for(const side of [-1,1]){
    const arm=new THREE.Group();arm.position.set(side*.48,1.55,0);root.add(arm);
    box(arm,.32,.28,.39,side*.025,-.07,0,armor,0,0,side*.12);
    box(arm,.37,.11,.34,side*.02,-.02,-.07,accent);
    box(arm,.22,.39,.25,0,-.33,0,primary);
    box(arm,.27,.3,.31,0,-.59,-.025,plating);
    box(arm,.23,.17,.3,0,-.79,-.045,graphite);
    box(arm,.09,.17,.065,0,-.56,-.192,visor);
    arms.push(arm);
  }
  // Animated exo-boots with shin guards.
  const legs=[];
  for(const side of [-1,1]){
    const leg=new THREE.Group();leg.position.set(side*.225,.76,.01);root.add(leg);
    box(leg,.29,.42,.34,0,-.17,0,primary);
    box(leg,.34,.21,.36,0,-.33,-.05,armor);
    box(leg,.31,.3,.33,0,-.50,-.035,plating);
    box(leg,.14,.22,.04,0,-.51,-.21,accent);
    box(leg,.36,.18,.49,0,-.68,-.08,graphite);
    box(leg,.31,.075,.14,0,-.70,-.31,gold);
    legs.push(leg);
  }
  // Animated body parts expected by the original FPS bot animator.
  root.userData.legL=legs[0];root.userData.legR=legs[1];
  root.userData.armL=arms[0];root.userData.armR=arms[1];
  root.userData.head=head;root.userData.current='Idle';
  root.scale.setScalar(1.03);
  return root;
}

let qaScenery=null;
const qaModelSets={
  urban:[['city-industrial','building-c.glb',25],['city-industrial','building-m.glb',32],['space-station','container-tall.glb',10]],
  orbital:[['space','structure_detailed.glb',28],['space','satelliteDish_detailed.glb',19],['space','rock_crystalsLargeA.glb',12]],
  wild:[['nature','rock_largeA.glb',11],['nature','plant_bushDetailed.glb',7],['nature','rock_tallA.glb',13]],
  factory:[['space-station','structure.glb',22],['space-station','container-wide.glb',12],['space','machine_generatorLarge.glb',15]]
};
function qaModelTheme(id){
  const n=String(id).toLowerCase();
  if(/lunar|moon|space|orbit|cosmic|astro/.test(n))return 'orbital';
  if(/nature|forest|jungle|canyon|island|oasis|temple/.test(n))return 'wild';
  if(/industrial|factory|forge|foundry|reactor|desert/.test(n))return 'factory';
  return 'urban';
}
function qaSeeded(n){let seed=2166136261;for(const char of String(n)){seed=Math.imul(seed^char.charCodeAt(0),16777619);}return ()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;};}
function qaDisposeScenery(){
  if(!qaScenery)return;
  qaScenery.removeFromParent();
  qaScenery.traverse(obj=>{
    if(obj.geometry)obj.geometry.dispose();
    if(obj.material){const ms=Array.isArray(obj.material)?obj.material:[obj.material];for(const mat of ms){mat.map?.dispose();mat.dispose();}}
  });
  qaScenery=null;
}
function qaDecorateArena(id){
  if(mode!=='solo')return;
  qaDisposeScenery();
  const group=new THREE.Group();group.name='QA · cinematic background (non-colliding)';
  mapWorld.add(group);qaScenery=group;
  const theme=qaModelTheme(id),rng=qaSeeded(id);
  const tone=new THREE.Color(arena?.spec?.sky||'#4e7899');
  const tint=new THREE.Color(arena?.spec?.horizon||'#9fc1c4');
  // Two instanced horizons: 72 towering structures + 44 mountainous silhouettes.
  const towerMat=new THREE.MeshStandardMaterial({color:tone.clone().lerp(new THREE.Color('#33435f'),.65),roughness:.86,metalness:.18,flatShading:true});
  const mountainsMat=new THREE.MeshStandardMaterial({color:tint.clone().lerp(new THREE.Color('#38465b'),.68),roughness:.96,flatShading:true});
  const towers=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),towerMat,72);
  const mounts=new THREE.InstancedMesh(new THREE.ConeGeometry(1,1,6),mountainsMat,44);
  towers.castShadow=false;towers.receiveShadow=false;mounts.castShadow=false;
  const dummy=new THREE.Object3D();
  for(let i=0;i<72;i++){
    const angle=i*Math.PI*2/72+(rng()-.5)*.06;
    const distance=320+rng()*135, height=18+rng()*65;
    dummy.position.set(Math.cos(angle)*distance,height/2-2,Math.sin(angle)*distance);
    dummy.scale.set(8+rng()*14,height,8+rng()*14);
    dummy.rotation.set(0,angle,0);dummy.updateMatrix();towers.setMatrixAt(i,dummy.matrix);
  }
  for(let i=0;i<44;i++){
    const a=i*Math.PI*2/44,dist=370+rng()*180,height=35+rng()*120;
    dummy.position.set(Math.cos(a)*dist,height/2-5,Math.sin(a)*dist);
    dummy.scale.set(28+rng()*36,height,28+rng()*36);dummy.rotation.set(0,a,0);dummy.updateMatrix();mounts.setMatrixAt(i,dummy.matrix);
  }
  towers.instanceMatrix.needsUpdate=true;mounts.instanceMatrix.needsUpdate=true;
  group.add(mounts,towers);
  // Glowing distant skyline seams, still instanced: low GPU overhead.
  const emissive=new THREE.MeshBasicMaterial({color:theme==='orbital'?'#72f9f2':'#f5c17a',transparent:true,opacity:.7,depthWrite:false});
  const strips=new THREE.InstancedMesh(new THREE.BoxGeometry(.2,1,.2),emissive,72);
  for(let i=0;i<72;i++){
    const angle=i*Math.PI*2/72+(rng()-.5)*.08,dist=318+rng()*145,h=8+rng()*30;
    dummy.position.set(Math.cos(angle)*dist,h/2+1,Math.sin(angle)*dist);
    dummy.scale.set(1,h,1);dummy.rotation.set(0,0,0);dummy.updateMatrix();strips.setMatrixAt(i,dummy.matrix);
  }
  strips.instanceMatrix.needsUpdate=true;group.add(strips);
  // Far-off floating cloud layers and celestial bodies. Never block the walkable arena.
  const haze=new THREE.MeshBasicMaterial({color:tint,transparent:true,opacity:.13,depthWrite:false});
  for(let i=0;i<18;i++){
    const a=rng()*Math.PI*2,d=190+rng()*225;
    const cloud=new THREE.Mesh(new THREE.IcosahedronGeometry(1,1),haze);
    cloud.position.set(Math.cos(a)*d,52+rng()*85,Math.sin(a)*d);
    cloud.scale.set(18+rng()*25,3+rng()*5,12+rng()*18);
    group.add(cloud);
  }
  const sunColor=theme==='orbital'?'#aa9bff':'#ffe2a2';
  const sunMat=new THREE.MeshBasicMaterial({color:sunColor,transparent:true,opacity:.75,depthWrite:false,fog:false});
  const sun=new THREE.Mesh(new THREE.SphereGeometry(30,24,16),sunMat);
  sun.position.set(-380,210,-580);group.add(sun);
  // Real Kenney CC0 3D prop models: nonblocking decorative background assets.
  const loader=new GLTFLoader();
  const models=qaModelSets[theme];
  models.forEach(([kit,file,size],index)=>{
    const url='/qa-model/'+kit+'/'+file;
    loader.load(url,gltf=>{
      if(qaScenery!==group||!group.parent)return;
      const original=gltf.scene;
      const bounds=new THREE.Box3().setFromObject(original);
      const span=bounds.getSize(new V());
      const natural=Math.max(1,span.y);
      const scale=Math.min(90,size/natural);
      for(let j=0;j<5;j++){
        const mesh=original.clone(true);
        mesh.scale.setScalar(scale*(.8+rng()*.6));
        const a=(index*5+j)*Math.PI*2/(models.length*5),distance=190+rng()*130;
        mesh.position.set(Math.cos(a)*distance,-2,Math.sin(a)*distance);
        mesh.rotation.y=a+rng();mesh.traverse(o=>{if(o.isMesh){o.castShadow=false;o.receiveShadow=true;}});
        group.add(mesh);
      }
    },undefined,()=>{}); // Art is optional: connection failure never blocks the game.
  });
}
