const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({headless:true,channel:'msedge',args:['--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:1200,height:1100}});try{
await p.goto('http://localhost:5173/?glb=1#/register');await p.getByRole('button',{name:'Enable accessibility'}).dispatchEvent('click');
for(const [name,value] of [['Imię','Anna'],['Nazwisko','Kowalska'],['Data urodzenia','04.03.1995'],['Numer telefonu','+48123456789'],['E-mail','avatar-test@example.com'],['Hasło','Bardzo dlugie haslo!'],['Powtórz hasło','Bardzo dlugie haslo!']]){const f=p.getByRole('textbox',{name,exact:true});await f.click();await p.waitForTimeout(250);await p.keyboard.press('Control+A');await p.keyboard.insertText(value);await p.waitForTimeout(300);await p.keyboard.press('Tab');await p.waitForTimeout(100);}
await p.getByRole('button',{name:'Płeć',exact:true}).click();await p.waitForTimeout(250);await p.getByRole('button',{name:'Kobieta',exact:true}).click();await p.waitForTimeout(250);await p.getByRole('button',{name:'Dalej',exact:true}).click();await p.waitForTimeout(500);console.log('STEP2',await p.locator('body').ariaSnapshot());for(const [name,value] of [['Imię kota','Luna'],['Data urodzenia','04.03.2023']]){await p.getByRole('textbox',{name,exact:true}).click();await p.waitForTimeout(250);await p.keyboard.press('Control+A');await p.keyboard.insertText(value);await p.waitForTimeout(250);await p.waitForTimeout(150);await p.keyboard.press('Tab');}await p.getByRole('button',{name:'Płeć kota',exact:true}).click();await p.waitForTimeout(200);await p.getByRole('button',{name:'Kotka',exact:true}).click();await p.getByRole('button',{name:'Dalej',exact:true}).click();await p.waitForTimeout(500);console.log('BEFORE MODEL',await p.locator('body').ariaSnapshot());console.log('FRAMES',p.frames().map(f=>f.url()));const f=await p.locator('iframe').elementHandle();const frame=await f.contentFrame();await frame.waitForFunction(()=>window.catViewer?.ready);await p.screenshot({path:'outputs/bmi-cat/glb-in-registration.png'});await p.getByRole('button',{name:'Umaszczenie Biały',exact:true}).click();await p.getByRole('button',{name:'Czarny',exact:true}).click();await frame.waitForFunction(()=>catViewer.settings.coat==='black');console.log('PASS: registration dropdown updates the GLB material');console.log(await p.locator('body').ariaSnapshot());
}finally{await b.close();}})();












