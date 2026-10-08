const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');
(async()=>{
  const mode=process.argv[2]||'preview';
  const b=await chromium.launch();
  const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+__dirname+'/scene.html');
  await p.evaluate(()=>document.fonts.ready);
  await p.waitForTimeout(800);
  if(mode==='preview'){
    for(const t of [2.5,5.5,8.3,9.5,16,24.5,28.9,31.8,35,39]){await p.evaluate(t=>render(t),t);await p.screenshot({path:`prev_${t}.png`});}
  } else {
    fs.mkdirSync('frames',{recursive:true});
    const fps=30,dur=await p.evaluate(()=>DUR);
    for(let i=0;i<dur*fps;i++){await p.evaluate(t=>render(t),i/fps);await p.screenshot({path:`frames/f${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:92});}
  }
  await b.close();
})();
