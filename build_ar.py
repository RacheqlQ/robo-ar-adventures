#!/usr/bin/env python3
"""Builds one self-contained camera-AR web page per Robo book (three.js r128 from cdnjs)."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out') + '/'
os.makedirs(OUT, exist_ok=True)

CSS = '''
:root{--bg:#EAF4FF;--fg:#1F2A44;--card:#fff;--mut:#4A5878;--at:__AC__;--ac:__AC__;box-sizing:border-box}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0F1A30;--fg:#EEF3FF;--card:#1B2742;--mut:#AEBBD8;--at:#8EC5FF}}
:root[data-theme=dark]{--bg:#0F1A30;--fg:#EEF3FF;--card:#1B2742;--mut:#AEBBD8;--at:#8EC5FF}
html,body{height:100%;margin:0;overflow:hidden}
body{background:var(--bg);background:linear-gradient(160deg,var(--bg),color-mix(in srgb,var(--ac) 28%,var(--bg)));color:var(--fg);font:16px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
#cam{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;display:none}
body.live #cam{display:block}
#gl{position:fixed;inset:0;width:100%;height:100%;touch-action:none}
#top{position:fixed;top:0;left:0;right:0;display:flex;justify-content:space-between;align-items:center;gap:8px;padding:calc(10px + env(safe-area-inset-top,0px)) 12px 10px;pointer-events:none}
#top b{background:var(--card);padding:6px 12px;border-radius:999px;font-size:14px}
button{font:inherit;cursor:pointer;pointer-events:auto}
#gbtn{background:var(--card);color:var(--fg);border:2px solid var(--ac);border-radius:999px;padding:6px 12px;font-weight:700;font-size:14px}
#dock{position:fixed;left:0;right:0;bottom:0;display:flex;flex-direction:column;gap:8px;padding:10px 12px calc(12px + env(safe-area-inset-bottom,0px));pointer-events:none}
#cap{background:var(--card);border-radius:18px;padding:12px 14px;box-shadow:0 4px 18px rgba(0,0,0,.25);pointer-events:auto}
#cap b{font-size:18px}#cap p{margin:4px 0 0}#capQ{color:var(--at);font-weight:600}
#extra,#modes{display:flex;gap:8px;overflow-x:auto}
#extra button,#modes button{flex:1 0 auto;background:var(--card);color:var(--fg);border:2px solid var(--ac);border-radius:999px;padding:10px 14px;font-weight:700}
#modes button.on{background:var(--ac);color:#fff}
#frame{position:fixed;left:14%;right:14%;top:20%;bottom:44%;border:4px solid #fff;border-radius:18px;box-shadow:0 0 0 100vmax rgba(0,0,0,.28);pointer-events:none}
#flash{position:fixed;inset:0;background:#fff;opacity:0;pointer-events:none;transition:opacity .3s}#flash.on{opacity:.9;transition:none}
.sheet{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(10,20,40,.55);overflow:auto}
.sheet[hidden],[hidden]{display:none!important}
.card{background:var(--card);border-radius:24px;padding:22px;max-width:520px;width:100%;box-shadow:0 8px 30px rgba(0,0,0,.3)}
.card h1,.card h2{margin:6px 0;color:var(--at)}.card h3{margin:14px 0 4px;color:var(--at)}
.card small{display:block;margin-top:12px;color:var(--mut)}.card li{margin:5px 0}
.em{font-size:44px}
.big{background:var(--ac);color:#fff;border:0;border-radius:999px;padding:14px 26px;font-weight:700;font-size:18px;margin:8px 8px 0 0}
.ghost{background:transparent;color:var(--at);border:2px solid var(--ac);border-radius:999px;padding:12px 20px;font-weight:700;margin-top:8px}
'''

COMMON_JS = r'''
const $=s=>document.querySelector(s);
let renderer,scene,cam,stage,interact=[],useGyro=false,a0=null,gy=[0,0,0],yaw=0,pitch=0,onTap=null,animFns=[],ac=null,nz=null;
const clock=new THREE.Clock(),ray=new THREE.Raycaster();
const mat=c=>new THREE.MeshLambertMaterial({color:c});
const mesh=(g,c)=>new THREE.Mesh(g,mat(c));
function say(t,b,q){$('#capT').textContent=t;$('#capB').textContent=b;$('#capQ').textContent=q?('Grown-up asks: '+q):'';$('#cap').hidden=false}
function place(o,deg,y,r){r=r||3.2;const a=deg*Math.PI/180;o.position.set(Math.sin(a)*r,y,-Math.cos(a)*r);o.userData.home=o.position.clone();return o}
function lab(txt,k){k=k||1;const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d');x.font='700 52px system-ui,sans-serif';x.textAlign='center';x.textBaseline='middle';const w=Math.min(500,x.measureText(txt).width+48);x.fillStyle='rgba(18,34,70,.88)';x.beginPath();if(x.roundRect)x.roundRect((512-w)/2,14,w,100,40);else x.rect((512-w)/2,14,w,100);x.fill();x.fillStyle='#fff';x.fillText(txt,256,66);const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthTest:false}));s.scale.set(1.6*k,.4*k,1);return s}
function robo(){const g=new THREE.Group(),B=new THREE.MeshBasicMaterial({color:0xffd84a});const b=mesh(new THREE.BoxGeometry(.5,.5,.38),0x2f73c4),h=mesh(new THREE.SphereGeometry(.34,20,14),0x2f73c4);h.position.y=.55;const f=mesh(new THREE.BoxGeometry(.4,.26,.1),0x10243f);f.position.set(0,.55,.28);[-.1,.1].forEach(x=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.055,10,8),B);e.position.set(x,.57,.34);g.add(e)});const a=mesh(new THREE.CylinderGeometry(.015,.015,.22),0x12365e);a.position.y=.98;const t=mesh(new THREE.SphereGeometry(.05,8,8),0x4fa3ff);t.position.y=1.1;const w=mesh(new THREE.SphereGeometry(.18,14,10),0x3c4a5e);w.position.y=-.3;g.add(b,h,f,a,t,w);return g}
function guide(){const r=robo();place(r,72,-.5,2.6);r.lookAt(0,r.position.y,0);stage.add(r);animFns.push(t=>{r.position.y=r.userData.home.y+Math.sin(t*2)*.04})}
function echo(){const g=new THREE.Group(),K=new THREE.MeshBasicMaterial({color:0x1f2a44});const e=mesh(new THREE.SphereGeometry(.5,24,18),0xffffff);e.scale.y=1.15;const f=mesh(new THREE.SphereGeometry(.34,20,14),0xff9f4a);f.scale.set(1,.85,.5);f.position.set(0,.05,.38);[-.1,.1].forEach(x=>{const k=new THREE.Mesh(new THREE.SphereGeometry(.045,10,8),K);k.position.set(x,.12,.52);g.add(k)});[-.55,.55].forEach(x=>{const c=mesh(new THREE.CylinderGeometry(.14,.14,.12,16),0xf7943d);c.rotation.z=Math.PI/2;c.position.set(x,.05,0);g.add(c)});const a=mesh(new THREE.CylinderGeometry(.02,.02,.25),0xf7943d);a.position.y=.68;const t=mesh(new THREE.SphereGeometry(.06,10,8),0xf7943d);t.position.y=.82;g.add(e,f,a,t);return g}
function A(){if(!ac)ac=new(window.AudioContext||window.webkitAudioContext)();if(ac.state==='suspended')ac.resume();return ac}
function tone(f,d,t0,ty){try{const a=A(),o=a.createOscillator(),g=a.createGain(),s=a.currentTime+(t0||0);o.type=ty||'sine';o.frequency.value=f;g.gain.setValueAtTime(0,s);g.gain.linearRampToValueAtTime(.18,s+.03);g.gain.exponentialRampToValueAtTime(.001,s+d);o.connect(g);g.connect(a.destination);o.start(s);o.stop(s+d+.05)}catch(e){}}
function noise(on){try{if(on&&!nz){const a=A(),b=a.createBuffer(1,a.sampleRate*2,a.sampleRate),d=b.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*(Math.random()<.002?1:.35);const s=a.createBufferSource();s.buffer=b;s.loop=true;const g=a.createGain();g.gain.value=.1;s.connect(g);g.connect(a.destination);s.start();nz=s}else if(!on&&nz){nz.stop();nz=null}}catch(e){}}
function xbtn(t,fn){const b=document.createElement('button');b.textContent=t;b.onclick=fn;$('#extra').appendChild(b)}
function flash(){const f=$('#flash');f.classList.add('on');setTimeout(()=>f.classList.remove('on'),90)}
function pick(x,y){if(!cam)return;ray.setFromCamera(new THREE.Vector2(x/innerWidth*2-1,-(y/innerHeight)*2+1),cam);const h=ray.intersectObjects(interact,true);let o=h.length?h[0].object:null;while(o&&!o.userData.tap)o=o.parent;if(onTap)onTap(x,y,o);else if(o)o.userData.tap(o)}
let pd=null;
addEventListener('pointerdown',e=>{if(e.target.id==='gl')pd={x:e.clientX,y:e.clientY,t:Date.now(),a:yaw,b:pitch}});
addEventListener('pointermove',e=>{if(!pd||useGyro)return;yaw=pd.a+(e.clientX-pd.x)*.005;pitch=Math.max(-1,Math.min(1,pd.b+(e.clientY-pd.y)*.005))});
addEventListener('pointerup',e=>{if(!pd)return;if(Math.hypot(e.clientX-pd.x,e.clientY-pd.y)<10&&Date.now()-pd.t<500)pick(e.clientX,e.clientY);pd=null});
addEventListener('deviceorientation',e=>{if(e.alpha==null)return;useGyro=true;if(a0===null)a0=e.alpha;gy=[(e.alpha-a0)*Math.PI/180,e.beta*Math.PI/180,e.gamma*Math.PI/180]});
function tick(){const dt=Math.min(clock.getDelta(),.05),t=clock.elapsedTime;
if(useGyro){const o=(screen.orientation?screen.orientation.angle:(window.orientation||0))*Math.PI/180,q=cam.quaternion;q.setFromEuler(new THREE.Euler(gy[1],gy[0],-gy[2],'YXZ'));q.multiply(new THREE.Quaternion(-Math.SQRT1_2,0,0,Math.SQRT1_2));q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),-o))}else cam.rotation.set(pitch,yaw,0,'YXZ');
animFns.forEach(f=>f(t,dt));renderer.render(scene,cam)}
function resize(){renderer.setSize(innerWidth,innerHeight,false);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix()}
function setMode(i){document.querySelectorAll('#modes button').forEach((b,k)=>b.classList.toggle('on',k===i));$('#extra').innerHTML='';$('#frame').hidden=true;onTap=null;animFns.length=0;interact.length=0;noise(false);if(stage)scene.remove(stage);stage=new THREE.Group();scene.add(stage);MODES[i].f()}
function init(){renderer=new THREE.WebGLRenderer({canvas:$('#gl'),alpha:true,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));scene=new THREE.Scene();cam=new THREE.PerspectiveCamera(62,1,.1,50);scene.add(new THREE.HemisphereLight(0xffffff,0x8899aa,.95));const d=new THREE.DirectionalLight(0xffffff,.7);d.position.set(2,4,3);scene.add(d);resize();addEventListener('resize',resize);
MODES.forEach((m,i)=>{const b=document.createElement('button');b.textContent=m.n;b.onclick=()=>setMode(i);$('#modes').appendChild(b)});setMode(0);renderer.setAnimationLoop(tick)}
async function start(withCam){$('#start').hidden=true;
try{if(window.DeviceOrientationEvent&&DeviceOrientationEvent.requestPermission)await DeviceOrientationEvent.requestPermission()}catch(e){}
if(withCam){try{const s=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});const v=$('#cam');v.srcObject=s;await v.play();document.body.classList.add('live')}catch(e){}}
init();if(!document.body.classList.contains('live'))say('Camera is off','Drag the screen to look around the 3D scene. Reload and allow the camera to see it in your room.','')}
$('#go').onclick=()=>start(true);$('#nocam').onclick=()=>start(false);
$('#gbtn').onclick=()=>$('#guide').hidden=false;$('#gclose').onclick=()=>$('#guide').hidden=true;
'''

SHELL = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>__TITLE__ \u2013 AR Adventure</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<style>__CSS__</style></head><body>
<video id="cam" playsinline muted></video><canvas id="gl"></canvas>
<div id="frame" hidden></div><div id="flash"></div>
<div id="top"><b>__EMOJI__ __TITLE__</b><button id="gbtn">Grown-up guide</button></div>
<div id="dock"><div id="cap" hidden><b id="capT"></b><p id="capB"></p><p id="capQ"></p></div><div id="extra"></div><div id="modes"></div></div>
<section id="start" class="sheet"><div class="card"><div class="em">__EMOJI__</div><h1>__TITLE__</h1><p>__INTRO__</p>
<button id="go" class="big">Start AR</button><button id="nocam" class="ghost">Play without camera</button>
<small>__NOTE__ The camera only shows the room behind the characters. Nothing is recorded or sent anywhere.</small></div></section>
<section id="guide" class="sheet" hidden><div class="card"><h2>Grown-up guide</h2><ol>__STEPS__</ol><h3>Talk about it</h3><ul>__ASKS__</ul><button id="gclose" class="big">Back to the adventure</button></div></section>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
__BOOKJS__
__COMMON__
</script></body></html>
'''

B1 = r'''
const MODES=[{n:'Look',f:look},{n:'Pattern',f:pattern},{n:'Camera',f:camera}];
const OBJ=[['ball',0xe5483d,'red','round',()=>new THREE.SphereGeometry(.36,24,16),.1,'a ball'],['sun',0xffd84a,'yellow','round',()=>new THREE.SphereGeometry(.44,24,16),.9,'the sun'],['block',0x2f73c4,'blue','square',()=>new THREE.BoxGeometry(.62,.62,.62),0,'a window'],['cone',0x8e5bd0,'purple','pointy',()=>new THREE.ConeGeometry(.38,.8,24),.1,'a party hat']];
function addObjs(angs){OBJ.forEach((o,i)=>{const m=mesh(o[4](),o[1]);place(m,angs[i],o[5]);m.userData.o=o;m.userData.tap=hit;stage.add(m);interact.push(m);animFns.push(t=>{m.position.y=m.userData.home.y+Math.sin(t*1.6+i)*.06;m.rotation.y=t*.5})})}
function hit(m){const o=m.userData.o,bad=o[0]==='block';say('A '+o[2]+' '+o[0]+'!','Color: '+o[2]+'. Shape: '+o[3]+'. Robo guesses: \u201c'+o[6]+'\u201d'+(bad?' \u2014 oops, that guess is wrong! Check the clues together.':'. Does that match the clues?'),'What color and shape clues can you name?')}
function look(){guide();addObjs([-40,-12,16,44]);say('Look closely!','Find Robo\u2019s floating shapes and tap one.','Can you name one thing you notice before Robo does?')}
function pattern(){guide();[0xe5483d,0x2f73c4,0xe5483d,0x2f73c4].forEach((c,i)=>{const m=mesh(new THREE.SphereGeometry(.28,20,14),c);place(m,-30+i*15,.3,3);stage.add(m)});
const q=mesh(new THREE.SphereGeometry(.28,20,14),0x9aa7bf);place(q,30,.3,3);const l=lab('?',.5);l.position.y=.5;q.add(l);let k=-1;const seq=[0x2f73c4,0xe5483d,0xffd84a];
q.userData.tap=()=>{k=(k+1)%3;q.material.color.setHex(seq[k]);if(k===1)say('Red, blue, red, blue, red!','You found the pattern. It repeats!','How did you know red comes next?');else say('Look at the pattern again','Red, blue, red, blue\u2026 what comes next? Tap the ball to try another color.','What repeats?')};stage.add(q);interact.push(q);
say('Red, blue, red, blue\u2026','What comes next? Tap the gray ball to try a color.','Can you say the pattern out loud?')}
function camera(){guide();addObjs([-55,-18,18,55]);$('#frame').hidden=false;say('Click a picture!','Line things up inside the frame, then tap anywhere to take a picture.','What do you think the camera will leave out?');
onTap=()=>{const r=$('#frame').getBoundingClientRect(),i=[],o=[];stage.children.forEach(m=>{if(!m.userData.o)return;const p=m.position.clone().project(cam),x=(p.x+1)/2*innerWidth,y=(1-p.y)/2*innerHeight;(p.z<1&&x>r.left&&x<r.right&&y>r.top&&y<r.bottom?i:o).push(m.userData.o[2]+' '+m.userData.o[0])});flash();say('Click, click!','In the picture: '+(i.join(', ')||'nothing')+'. Left out: '+(o.join(', ')||'nothing')+'.','Why did the camera miss some things?')}}
'''

B2 = r'''
const MODES=[{n:'Sort by color',f:()=>sortGame('color')},{n:'Sort by shape',f:()=>sortGame('shape')},{n:'Steps',f:steps}];
const GS={round:()=>new THREE.SphereGeometry(.3,20,14),square:()=>new THREE.BoxGeometry(.5,.5,.5),pointy:()=>new THREE.ConeGeometry(.3,.6,20)};
const TOYS=[['red','round',0xe5483d],['red','square',0xe5483d],['red','pointy',0xe5483d],['blue','round',0x2f73c4],['blue','square',0x2f73c4],['blue','pointy',0x2f73c4]];
function sortGame(rule){guide();let sel=null,done=0;
const BK=rule==='color'?[['red',0xe5483d,-30],['blue',0x2f73c4,30]]:[['round',0xf5a623,-40],['square',0x8e5bd0,0],['pointy',0x2eae6b,40]];
BK.forEach(b=>{const g=new THREE.Group(),c=mesh(new THREE.CylinderGeometry(.55,.4,.5,24,1,true),b[1]);c.material.side=THREE.DoubleSide;const f=mesh(new THREE.CylinderGeometry(.4,.4,.04,24),b[1]);f.position.y=-.25;const l=lab(b[0]+' basket',.9);l.position.y=.6;g.add(c,f,l);place(g,b[2],-.7,2.8);g.userData.tap=()=>drop(b[0],g);stage.add(g);interact.push(g)});
TOYS.forEach((t,i)=>{const m=mesh(GS[t[1]](),t[2]);place(m,-50+i*20,.7,3.2);m.userData.t=t;m.userData.tap=()=>{if(m.userData.done)return;if(sel)sel.scale.setScalar(1);sel=m;m.scale.setScalar(1.3);say('Toy picked!','Which basket does this '+t[0]+' '+t[1]+' toy belong in? Tap a basket.','What is our rule?')};stage.add(m);interact.push(m);animFns.push(tm=>{if(!m.userData.done)m.position.y=m.userData.home.y+Math.sin(tm*1.6+i)*.05;m.rotation.y=tm*.6})});
function drop(key,g){if(!sel)return say('Pick a toy first','Tap a floating toy, then tap a basket.','');const t=sel.userData.t;
if(t[rule==='color'?0:1]===key){const m=sel;m.userData.done=1;m.scale.setScalar(.8);m.position.set(g.position.x+(done%3-1)*.17,g.position.y+.05,g.position.z);done++;sel=null;say(done===6?'Algorithm complete!':'Nice sorting!',done===6?'Notice, plan, sort, check, fix. Every step helped!':done+' of 6 toys sorted. Keep going!','How can we check our work?')}
else say('Bug found!','A '+t[0]+' '+t[1]+' toy does not belong in the '+key+' basket. Finding a mistake is called debugging. Try another basket!','How can we fix it?')}
say(rule==='color'?'Rule: sort by color':'New rule: sort by shape','Tap a toy, then tap the basket it belongs in.','What is the first step of our plan?')}
function steps(){guide();['1 Notice a problem','2 Make a plan','3 Sort by the rule','4 Check our work','5 Fix the mistake'].forEach((s,i)=>{const l=lab(s,1.3);place(l,0,1.5-i*.5,3);stage.add(l)});say('An algorithm is steps in order','Try the two Sort modes to follow these steps with Robo.','Which step do you do first when cleaning up?')}
'''

B3 = r'''
const MODES=[{n:'High & low',f:pitchMode},{n:'Prompts',f:prompts},{n:'Noise',f:noisy}];
let E,hop=0,wob=0,spin=false,rings=[];
function mk(){hop=0;wob=0;spin=false;rings=[];E=echo();place(E,0,.2,3);E.lookAt(0,.2,0);stage.add(E);interact.push(E);
E.userData.tap=()=>{hop=1;tone(660,.15);say('Hi, I\u2019m Echo!','I listen with my digital ears.','What sounds can you hear right now?')};
animFns.push((t,dt)=>{E.position.y=.2+Math.sin(t*2)*.05+Math.sin(Math.min(hop,1)*Math.PI)*.4;hop=Math.max(0,hop-dt*1.6);E.rotation.z=wob?Math.sin(t*14)*.18:0;if(spin)E.rotation.y+=dt*5;
rings=rings.filter(r=>{r.scale.addScalar(dt*r.userData.s);r.material.opacity=Math.max(0,1-(r.scale.x-1)/2.2);if(r.material.opacity<=0){stage.remove(r);return false}return true})})}
function ring(s,c){const r=new THREE.Mesh(new THREE.RingGeometry(.55,.6,48),new THREE.MeshBasicMaterial({color:c,transparent:true,side:THREE.DoubleSide}));r.position.copy(E.position);r.lookAt(0,E.position.y,0);r.userData.s=s;rings.push(r);stage.add(r)}
function burst(n,gap,s,c){for(let i=0;i<n;i++)setTimeout(()=>{if(E&&E.parent)ring(s,c)},i*gap)}
function pitchMode(){mk();xbtn('High (squeaky)',()=>{tone(880,.5);burst(6,90,2.6,0xe86aa6);say('High sound','High sounds wiggle fast: lots of waves every second. Computers measure that as frequency.','Can you make a squeaky voice?')});
xbtn('Low (deep)',()=>{tone(196,.7);burst(2,420,.9,0x2f73c4);say('Low sound','Low sounds wiggle slowly: only a few waves every second.','Can you make a deep voice like a bear?')});
say('High and low','Tap High or Low to hear a sound and watch Echo\u2019s sound waves.','Which sound is higher, a bird or a bear?')}
function prompts(){mk();xbtn('\u201cDo something!\u201d',()=>{wob=1;setTimeout(()=>wob=0,900);tone(180,.25,0,'triangle');say('Hmm?','Echo isn\u2019t sure what to do. A fuzzy prompt does not say what you want.','How could we make that clearer?')});
xbtn('\u201cEcho, make a happy beep!\u201d',()=>{hop=1;tone(660,.15);tone(880,.25,.18);burst(3,150,1.6,0xf5a623);say('Happy beep!','A clear prompt tells Echo exactly what to do.','What clear prompt would you give Echo?')});
say('Give Echo a prompt','The words we say to an AI are called prompts. Tap one to try it.','Which prompt will help Echo most?')}
function noisy(){mk();xbtn('Noisy room',()=>{noise(true);spin=true;wob=1;say('Too much noise!','Echo gets confused when lots of sounds happen at once.','How can we help Echo hear better?')});
xbtn('Quiet room',()=>{noise(false);spin=false;wob=0;E.lookAt(0,E.position.y,0);hop=1;tone(660,.15);tone(990,.2,.15);say('Now Echo hears clearly!','Turning off the noise helps people and computers listen.','What do we do when it is too noisy to hear?')});
say('Quiet or noisy?','Try the noisy room, then the quiet room. Keep the volume low.','What do we do when it is too noisy to hear?')}
'''

BOOKS = [
    dict(f='AR-Book-1-Robo-Learns-To-See.html', title='Robo Learns to See', emoji='\U0001F916', ac='#1F5C99', js=B1,
         intro='Step into Robo\u2019s world! Find floating shapes, finish a pattern, and click a picture to see what a camera includes and leaves out.',
         note='Hold the device upright and move slowly to look around.',
         steps=['Press <b>Start AR</b> and allow the camera. Hold the device upright.',
                'Turn slowly until you spot Robo\u2019s floating shapes.',
                '<b>Look</b>: tap each shape and name its color and shape together.',
                '<b>Pattern</b>: tap the gray ball to finish red, blue, red, blue\u2026',
                '<b>Camera</b>: tap to \u201cclick\u201d a picture, then talk about what the frame included and left out.',
                'Remind your child that a computer\u2019s guess is a guess to check.'],
         asks=['What colors and shapes can you find in our room?', 'What did the camera leave out?', 'How can we check if Robo\u2019s guess is right?']),
    dict(f='AR-Book-2-The-Sorting-Basket.html', title='The Sorting Basket', emoji='\U0001F9FA', ac='#1E4F9C', js=B2,
         intro='Help Robo sort floating toys into baskets! Follow a rule, catch a bug, fix it, and then change the rule.',
         note='Hold the device upright and move slowly to find the toys and baskets.',
         steps=['Press <b>Start AR</b> and allow the camera. Hold the device upright.',
                'Look around to find the floating toys and the baskets below them.',
                '<b>Sort by color</b>: tap a toy, then tap the basket it belongs in.',
                'When a <b>bug</b> appears, name the mistake together and try again.',
                '<b>Sort by shape</b>: the rule changed! Sort again with the new rule.',
                '<b>Steps</b>: talk through notice, plan, sort, check, fix.'],
         asks=['What is the first step of our plan?', 'How did we find and fix the mistake?', 'What other rule could we use to sort?']),
    dict(f='AR-Book-3-The-Bot-That-Listens.html', title='The Bot That Listens', emoji='\U0001F442', ac='#1C4E9F', js=B3,
         intro='Meet Echo, a little bot with big ears! Hear high and low sounds, try clear prompts, and see how noise makes listening hard.',
         note='Sound is on, so keep the volume low. This page does not use the microphone.',
         steps=['Press <b>Start AR</b> and allow the camera. Turn the volume down low.',
                'Look ahead to find Echo floating in front of you. Tap Echo to say hello.',
                '<b>High &amp; low</b>: tap each button, listen, and watch the sound waves.',
                '<b>Prompts</b>: compare a fuzzy prompt with a clear prompt.',
                '<b>Noise</b>: switch between a noisy room and a quiet room.',
                'Practice giving Echo a clear prompt out loud together.'],
         asks=['What makes a prompt clear?', 'Why did Echo get confused in the noisy room?', 'What would you ask Echo to do?']),
]

for B in BOOKS:
    css = CSS.replace('__AC__', B['ac'])
    html = (SHELL.replace('__CSS__', css).replace('__TITLE__', B['title']).replace('__EMOJI__', B['emoji'])
            .replace('__INTRO__', B['intro']).replace('__NOTE__', B['note'])
            .replace('__STEPS__', ''.join('<li>%s</li>' % s for s in B['steps']))
            .replace('__ASKS__', ''.join('<li>%s</li>' % s for s in B['asks']))
            .replace('__BOOKJS__', B['js']).replace('__COMMON__', COMMON_JS))
    open(OUT + B['f'], 'w', encoding='utf-8').write(html)
    print(B['f'], len(html.encode()))
