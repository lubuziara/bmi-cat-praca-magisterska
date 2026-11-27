import * as THREE from './vendor/three.module.js';
const coats={white:'#efede8',black:'#24232a',ginger:'#c88443',tabby:'#81776e',tricolor:'#efede8',ginger_white:'#efede8',ginger_black_white:'#efede8',purple:'#a48ace',yellow:'#e8c652',red:'#cd5552'};
const eyes={green:'#90b969',amber:'#dbb04e',blue:'#7bb6e1',brown:'#96643f',gray:'#a1b2bc',heterochromia:'#7bb6e1',purple:'#aa75d5',pink:'#dc87b7',turquoise:'#56c5c4',red:'#c95a50'};
export function updateCatMaterial(material,s){
 const u=material.userData.catUniforms;
 u.catCoat.value.set(coats[s.coat]??coats.white);u.catEye.value.set(eyes[s.eyes]??eyes.green);
 u.catPattern.value=({tricolor:1,ginger_white:2,ginger_black_white:3,tabby:4})[s.coat]??0;
 u.catHetero.value=s.eyes==='heterochromia'?1:0;
 u.catLength.value=({hairless:0,short:.006,long:.025,extra_long:.043})[s.fur]??.006;
 material.normalScale.setScalar(s.fur==='hairless'?.12:.8);
}
export function createCatMaterial(source,layer){
 const material=source.clone();material.side=THREE.FrontSide;material.roughness=.93;material.metalness=0;
 material.userData.catUniforms={catTime:{value:0},catLayer:{value:layer},catLength:{value:.006},catCoat:{value:new THREE.Color(coats.white)},catEye:{value:new THREE.Color(eyes.green)},catPattern:{value:0},catHetero:{value:0}};
 material.onBeforeCompile=shader=>{
 Object.assign(shader.uniforms,material.userData.catUniforms);
 const defs='uniform float catTime,catLayer,catLength; varying vec3 catPosition; varying vec2 catUv;';
 shader.vertexShader=defs+'\n'+shader.vertexShader;
 shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
 catPosition=position;catUv=uv;
 float face=smoothstep(1.25,1.55,position.y);
 float furSize=catLength*(1.-face*.8);
 transformed+=normal*furSize*catLayer;
 transformed.y-=furSize*.3*catLayer*catLayer;
 transformed.x+=sin(catTime*1.5+position.y*5.)*furSize*.13*catLayer*catLayer;
 `);
 shader.fragmentShader=defs+'uniform vec3 catCoat,catEye;uniform float catPattern,catHetero;\n'+shader.fragmentShader;
 shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
 vec3 original=diffuseColor.rgb;
 float lum=dot(original,vec3(.2126,.7152,.0722));
 float eyeMask=step(1.36,catPosition.y)*smoothstep(.025,.10,original.r-original.b)*smoothstep(.01,.07,original.g-original.b);
 float darkFeature=1.-smoothstep(.015,.065,lum);
 vec3 coat=catCoat;
 float patches=sin(catPosition.x*8.+catPosition.y*2.)*cos(catPosition.z*6.-catPosition.y*4.);
 if(catPattern==1.) {coat=mix(coat,vec3(.53,.24,.065),smoothstep(.12,.4,patches));coat=mix(coat,vec3(.035),1.-smoothstep(-.45,-.2,patches));}
 if(catPattern==2.)coat=mix(coat,vec3(.53,.24,.065),smoothstep(-.1,.1,catPosition.x));
 if(catPattern==3.){coat=mix(coat,vec3(.53,.24,.065),smoothstep(.0,.15,catPosition.x));coat=mix(coat,vec3(.035),smoothstep(.1,.3,patches)*step(catPosition.x,0.));}
 if(catPattern==4.)coat*=.62+.38*smoothstep(-.4,.2,sin(catPosition.y*38.+catPosition.x*9.));
 vec3 iris=catEye;if(catHetero==1.&&catPosition.x<0.)iris=vec3(.72,.43,.08);
 diffuseColor.rgb=mix(coat*clamp(lum*3.2,.24,1.1),original,darkFeature);
 diffuseColor.rgb=mix(diffuseColor.rgb,iris*clamp(lum*3.,.25,1.1),eyeMask);
 if(catLayer>0.){
   if(eyeMask>.15||darkFeature>.6)discard;
   vec2 grid=catUv*1500.;vec2 cell=floor(grid);
   float random=fract(sin(dot(cell,vec2(127.1,311.7)))*43758.5453);
   float fiber=length(fract(grid)-vec2(.5));
   if(random<catLayer*.82||fiber>(.42-catLayer*.22))discard;
   diffuseColor.rgb*=1.-catLayer*.08;
 }
 `);
 };
 material.customProgramCacheKey=()=>`bmi-cat-fur-v1-${layer===0?'base':'shell'}`;
 return material;
}

