import {Application, Assets} from 'pixi.js';
import {Spine} from '@esotericsoftware/spine-pixi-v8';

const config=__SLOT_PREVIEW_CONFIG__;
async function start() {
  const app=new Application();
  await app.init({width:900,height:800,background:0x182231,antialias:true,resolution:devicePixelRatio,autoDensity:true});
  document.getElementById('preview').appendChild(app.canvas);
  await Assets.load([{alias:'skeleton',src:'skeleton.json'},{alias:'atlas',src:'textures.atlas'}]);
  const spine=Spine.from({skeleton:'skeleton',atlas:'atlas',autoUpdate:true});
  app.stage.addChild(spine);
  const bounds=spine.getLocalBounds();
  const scale=Math.min(750/Math.max(1,bounds.width),650/Math.max(1,bounds.height));
  spine.scale.set(scale);
  spine.position.set(450-(bounds.x+bounds.width/2)*scale,400-(bounds.y+bounds.height/2)*scale);
  const select=document.getElementById('animation');
  for(const animation of spine.skeleton.data.animations) {
    const option=document.createElement('option');option.value=option.textContent=animation.name;select.appendChild(option);
  }
  const play=()=>{spine.autoUpdate=true;spine.state.setAnimation(0,select.value,true);};
  if(select.options.length){select.value=config.animation||select.options[0].value;play();}
  select.onchange=play;
  document.getElementById('background').oninput=event=>{app.renderer.background.color=event.target.value;};
  window.__spinePreview={app,spine,seek(time){
    spine.autoUpdate=false;spine.skeleton.setToSetupPose();
    const entry=spine.state.setAnimation(0,select.value,false);entry.trackTime=time;spine.update(0);
    app.renderer.render({container:app.stage});
  }};
  document.getElementById('status').textContent='Ready — '+config.runtimeVersion+' — asset preview, not wrapper layout evidence';
}
start().catch(error=>{document.getElementById('status').textContent=error.message;console.error(error);});
