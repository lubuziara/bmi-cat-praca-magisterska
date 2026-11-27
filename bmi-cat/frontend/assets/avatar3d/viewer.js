import * as THREE from './vendor/three.module.js';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {createCatMaterial, updateCatMaterial} from './cat-material.js';
import {reshapeCat} from './cat-shape.js';
const scene=new THREE.Scene();
scene.background=new THREE.Color('#f1e8f7');
const camera=new THREE.PerspectiveCamera(32,1,.01,50);
camera.position.set(.25,1.2,4.8);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.35;
document.body.prepend(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);
controls.target.set(0,1.05,0);controls.enablePan=false;controls.enableDamping=true;
controls.minDistance=2.8;controls.maxDistance=6;controls.maxPolarAngle=Math.PI*.65;
scene.add(new THREE.HemisphereLight(0xffffff,0xb5a1bd,2.3));
const key=new THREE.DirectionalLight(0xfff4e8,3.1);key.position.set(-3,4,5);scene.add(key);
const fill=new THREE.DirectionalLight(0xe4eaff,1.6);fill.position.set(3,2,-2);scene.add(fill);
const shadowCanvas=document.createElement('canvas');shadowCanvas.width=128;shadowCanvas.height=128;
const ctx=shadowCanvas.getContext('2d'),g=ctx.createRadialGradient(64,64,0,64,64,64);
g.addColorStop(0,'rgba(80,50,90,.24)');g.addColorStop(1,'rgba(80,50,90,0)');ctx.fillStyle=g;ctx.fillRect(0,0,128,128);
const shadow=new THREE.Mesh(new THREE.PlaneGeometry(2,1.5),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(shadowCanvas),transparent:true,depthWrite:false}));
shadow.rotation.x=-Math.PI/2;shadow.position.y=-.015;scene.add(shadow);
const group=new THREE.Group();scene.add(group);
const meshes=[];let settings={fur:'short',coat:'white',eyes:'green',size:'adult',body:'medium'};
let ready=false;
function configure(next){settings={...settings,...next};for(const entry of meshes){reshapeCat(entry.geometry,entry.original,settings);entry.layers.forEach((m,i)=>{updateCatMaterial(m.material,settings);m.visible=i===0||(settings.fur!=='hairless'&&(settings.fur!=='short'||i<=3));});}group.scale.setScalar(settings.size==='kitten'?.83:1);}
window.setCatSettings=configure;
function setMeasurementView(enabled){
 if(enabled){camera.position.set(4.8,1.25,.15);controls.target.set(0,1.0,0);}
 else {camera.position.set(.25,1.2,4.8);controls.target.set(0,1.05,0);}
 controls.update();
}
window.addEventListener('message',e=>{if(e.source!==parent||e.origin!==location.origin)return;if(e.data?.type==='bmi-cat-settings')configure(e.data.settings);if(e.data?.type==='bmi-cat-view')setMeasurementView(e.data.measurement===true);});
try {
 const gltf=await new GLTFLoader().loadAsync('cat.glb');
 gltf.scene.updateMatrixWorld(true);
 const box=new THREE.Box3().setFromObject(gltf.scene),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3());
 const scale=2/size.y;
 gltf.scene.traverse(object=>{if(!object.isMesh)return;const geometry=object.geometry.clone();geometry.applyMatrix4(object.matrixWorld);geometry.translate(-center.x,-box.min.y,-center.z);geometry.scale(scale,scale,scale);geometry.computeVertexNormals();
 const original=geometry.attributes.position.array.slice();const layers=[];
 for(let i=0;i<=8;i++){const material=createCatMaterial(object.material,i/8);const mesh=new THREE.Mesh(geometry,material);group.add(mesh);layers.push(mesh);}
 meshes.push({geometry,original,layers});});
 configure(settings);ready=true;document.querySelector('#status').hidden=true;
 if(parent!==window)parent.postMessage({type:'bmi-cat-ready'},location.origin);
 window.CatBridge?.postMessage('ready');
} catch(error){document.querySelector('#status').textContent='Nie udało się wczytać modelu kota. Odśwież podgląd.';console.error(error);}
function resize(){const height=Math.max(100,innerHeight-80);renderer.setSize(innerWidth,height);camera.aspect=innerWidth/height;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(document.body);resize();
function rotate(angle){const v=camera.position.clone().sub(controls.target);v.applyAxisAngle(new THREE.Vector3(0,1,0),angle);camera.position.copy(controls.target).add(v);controls.update();}
document.querySelector('#left').onclick=()=>rotate(-.4);document.querySelector('#right').onclick=()=>rotate(.4);
document.querySelector('#front').onclick=()=>{camera.position.set(.25,1.2,4.8);controls.target.set(0,1.05,0);controls.update();};
const reduced=matchMedia('(prefers-reduced-motion: reduce)');let last=0;
function frame(ms){requestAnimationFrame(frame);if(document.hidden||ms-last<32)return;last=ms;controls.update();for(const e of meshes)for(const m of e.layers){if(m.material.userData.catUniforms)m.material.userData.catUniforms.catTime.value=reduced.matches?0:ms/1000;}renderer.render(scene,camera);}
requestAnimationFrame(frame);
window.catViewer={get ready(){return ready;},get settings(){return settings;},renderer,scene,camera,configure};

