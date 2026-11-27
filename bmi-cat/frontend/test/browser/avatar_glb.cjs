// Run with Node and Playwright installed, after BuildWeb and starting the local web server.
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge',args:['--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:600,height:650}});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error'&&/shader|WebGLProgram|TypeError/i.test(m.text()))errors.push(m.text());});
 try{
 await page.goto((process.env.BMI_TEST_URL??'http://localhost:5173')+'/assets/assets/avatar3d/index.html');
 await page.waitForFunction(()=>window.catViewer?.ready,{timeout:45000});
 await page.waitForTimeout(800);
 await page.screenshot({path:'outputs/bmi-cat/glb-preview.png'});
 const base=await page.evaluate(()=>({triangles:catViewer.renderer.info.render.triangles,settings:catViewer.settings}));
 assert(base.triangles>70000);assert.equal(base.settings.coat,'white');
 await page.evaluate(()=>catViewer.configure({fur:'extra_long',coat:'tricolor',eyes:'brown',body:'xxl',size:'kitten'}));
 await page.waitForTimeout(1000);
 await page.screenshot({path:'outputs/bmi-cat/glb-preview-xxl.png'});
 const changed=await page.evaluate(()=>({triangles:catViewer.renderer.info.render.triangles,settings:catViewer.settings}));
 assert(changed.triangles>base.triangles);assert.equal(changed.settings.body,'xxl');
 await page.getByRole('button',{name:'Obróć w prawo'}).click();
 await page.waitForTimeout(400);
 await page.screenshot({path:'outputs/bmi-cat/glb-preview-side.png'});
 await page.setViewportSize({width:320,height:390});
 await page.waitForTimeout(400);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),320);
 await page.screenshot({path:'outputs/bmi-cat/glb-preview-mobile.png'});
 assert.deepEqual(errors,[]);
 console.log('PASS: GLB loaded, material shaders compiled, settings and rotation work, mobile fits.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
