import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {cliArgs,readJSON,attachmentKeys,inspectAtlas,projectModules,validateSpine} from './lib/runtime-tools.mjs';

try {
  const args=cliArgs(['project-root','spine','atlas-root','out']);
  const data=readJSON(args.spine), report=await validateSpine(args['project-root'],data);
  const needed=new Set(attachmentKeys(data)), atlas=inspectAtlas(args['atlas-root'],[...needed]);
  const output=path.resolve(args.out);
  if(fs.existsSync(output)&&fs.readdirSync(output).length)throw new Error('Preview output must be a new or empty directory');
  fs.mkdirSync(output,{recursive:true});
  const pages=[];
  for(const [index,page] of atlas.pages.entries()) {
    const entries=Object.entries(page.data.frames).filter(([key])=>needed.has(key));
    if(!entries.length)continue;
    const name='page-'+index+path.extname(page.image);
    fs.copyFileSync(page.image,path.join(output,name));
    const lines=[name,`size: ${page.width},${page.height}`,'format: RGBA8888','filter: Linear,Linear','repeat: none'];
    for(const [key,entry] of entries) {
      const frame=entry.frame, source=entry.sourceSize||{w:frame.w,h:frame.h};
      const sprite=entry.spriteSourceSize||{x:0,y:0,w:frame.w,h:frame.h};
      lines.push(key,`bounds: ${frame.x},${frame.y},${sprite.w},${sprite.h}`,
        `offsets: ${sprite.x},${source.h-sprite.y-sprite.h},${source.w},${source.h}`,`rotate: ${entry.rotated?90:0}`,'index: -1');
    }
    pages.push(lines.join('\n'));
  }
  fs.writeFileSync(path.join(output,'textures.atlas'),pages.join('\n\n')+'\n');
  fs.copyFileSync(args.spine,path.join(output,'skeleton.json'));
  fs.writeFileSync(path.join(output,'index.html'),'<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,"><title>Spine asset preview</title><style>body{margin:1rem;background:#182231;color:white;font:1rem sans-serif}canvas{max-width:100%;height:auto}label{margin-right:1rem}</style><label>Animation <select id="animation"></select></label><label>Background <input id="background" type="color" value="#182231"></label><p id="status">Loading</p><div id="preview"></div><script src="preview.js"></script>');
  const modules=projectModules(args['project-root']), webpack=modules.require(modules.resolve('webpack'));
  const compiler=webpack({mode:'development',devtool:false,entry:fileURLToPath(new URL('../assets/runtime-preview.js',import.meta.url)),
    output:{path:output,filename:'preview.js'},resolve:{alias:{'pixi.js$':modules.resolve('pixi.js'),'@esotericsoftware/spine-pixi-v8$':modules.resolve('@esotericsoftware/spine-pixi-v8')}},
    plugins:[new webpack.DefinePlugin({__SLOT_PREVIEW_CONFIG__:JSON.stringify({runtimeVersion:report.runtimeVersion,animation:args.animation})})]});
  await new Promise((resolve,reject)=>compiler.run((error,stats)=>compiler.close(closeError=>error||closeError||stats.hasErrors()?reject(error||closeError||new Error(stats.toString({all:false,errors:true}))):resolve())));
  fs.writeFileSync(path.join(output,'preview-report.json'),JSON.stringify(report,null,2));
  console.log('Preview ready: '+path.join(output,'index.html'));
}catch(error){console.error(error.message);process.exitCode=1;}
