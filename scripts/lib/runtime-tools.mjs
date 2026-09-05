import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';

export const readJSON=file=>JSON.parse(fs.readFileSync(file,'utf8'));

export function cliArgs(required=[]) {
  const args={};
  for(let i=2;i<process.argv.length;i+=2) {
    const key=process.argv[i];
    if(!key.startsWith('--') || process.argv[i+1]===undefined) throw new Error('Expected --name value arguments');
    args[key.slice(2)]=process.argv[i+1];
  }
  for(const key of required) if(!args[key]) throw new Error('Required: --'+key);
  return args;
}

export function attachmentKeys(data) {
  const keys=new Set();
  for(const skin of data.skins||[]) for(const attachments of Object.values(skin.attachments||{}))
    for(const [name,attachment] of Object.entries(attachments)) {
      if(attachment.sequence) throw new Error('Attachment sequences require explicit frame-key expansion');
      if(['region','mesh','linkedmesh'].includes(attachment.type||'region')) keys.add(attachment.path||name);
    }
  return [...keys];
}

export function inspectAtlas(root, required=[]) {
  const pending=[path.resolve(root)], seen=new Set(), imageSizes=new Map(), frames={}, pages=[];
  while(pending.length) {
    const file=pending.pop();
    if(seen.has(file))continue;
    seen.add(file);
    const data=readJSON(file), directory=path.dirname(file);
    const {w,h}=data.meta?.size||{};
    if(!Number.isInteger(w)||!Number.isInteger(h)||w<=0||h<=0)throw new Error('Invalid atlas page size: '+file);
    const image=path.resolve(directory,data.meta.image);
    if(!fs.existsSync(image))throw new Error('Missing atlas image: '+image);
    if(imageSizes.has(image) && imageSizes.get(image)!==w*h*4)throw new Error('Inconsistent atlas image metadata');
    imageSizes.set(image,w*h*4);
    pages.push({file,image,width:w,height:h,data});
    for(const [key,frame] of Object.entries(data.frames||{})) {
      if(frames[key])throw new Error('Duplicate atlas frame: '+key);
      const box=frame.frame;
      if(!box||![box.x,box.y,box.w,box.h].every(Number.isFinite)||box.x<0||box.y<0||box.w<=0||box.h<=0||box.x+box.w>w||box.y+box.h>h)
        throw new Error('Invalid atlas bounds: '+key);
      frames[key]={...frame,image};
    }
    for(const name of data.meta.related_multi_packs||[]) pending.push(path.resolve(directory,name));
  }
  for(const key of required)if(!frames[key])throw new Error('Missing attachment: '+key);
  return {pages,frames,decodedRGBABytes:[...imageSizes.values()].reduce((a,b)=>a+b,0),imagePages:imageSizes.size,maxEdge:Math.max(...pages.flatMap(p=>[p.width,p.height]))};
}

export function checkBudget(atlas,budget) {
  if(!budget||typeof budget!=='object'||!Object.keys(budget).length||Object.keys(budget).some(key=>!['maxDecodedBytes','maxPages','maxEdge'].includes(key)))throw new Error('Supply explicit supported budget limits');
  for(const [limit,value] of [['maxDecodedBytes',atlas.decodedRGBABytes],['maxPages',atlas.imagePages],['maxEdge',atlas.maxEdge]]) {
    if(budget[limit]!==undefined && (!Number.isFinite(budget[limit])||budget[limit]<0))throw new Error('Invalid budget: '+limit);
    if(budget[limit]!==undefined && value>budget[limit])throw new Error('Atlas exceeds budget '+limit+': '+value+' > '+budget[limit]);
  }
}

export function projectModules(project) {
  const require=createRequire(path.resolve(project,'package.json'));
  const roots=[path.resolve(project)];
  try { roots.push(path.dirname(require.resolve('@urso/core/package.json'))); } catch {}
  return {require,resolve:name=>require.resolve(name,{paths:roots})};
}

export async function validateSpine(project,data,options={}) {
  const modules=projectModules(project);
  const corePath=modules.resolve('@esotericsoftware/spine-core');
  const core=await import(pathToFileURL(corePath).href);
  const version=readJSON(path.resolve(path.dirname(corePath),'../package.json')).version;
  if(data.skeleton?.spine?.split('.').slice(0,2).join('.')!==version.split('.').slice(0,2).join('.'))throw new Error('Spine data/runtime version mismatch');
  for(const animation of Object.values(data.animations||{}))for(const timelines of Object.values(animation.bones||{}))
    for(const key of timelines.rotate||[])if('angle' in key)throw new Error('Spine rotate requires value, not angle');
  const parsed=new core.SkeletonJson({
    newRegionAttachment:(_skin,name,texture)=>new core.RegionAttachment(name,texture),
    newMeshAttachment:(_skin,name,texture)=>new core.MeshAttachment(name,texture),
    newBoundingBoxAttachment:(_skin,name)=>new core.BoundingBoxAttachment(name),
    newClippingAttachment:(_skin,name)=>new core.ClippingAttachment(name),
    newPathAttachment:(_skin,name)=>new core.PathAttachment(name),
    newPointAttachment:(_skin,name)=>new core.PointAttachment(name),
  }).readSkeletonData(data);
  const animations=[];
  for(const animation of parsed.animations) {
    for(const timeline of animation.timelines) for(const field of ['frames','curves'])
      if(timeline[field] && ![...timeline[field]].every(Number.isFinite))throw new Error('Nonfinite timeline: '+animation.name);
    for(let frame=0;frame<=120;frame++) {
      const skeleton=new core.Skeleton(parsed);
      animation.apply(skeleton,0,animation.duration*frame/120,false,[],1,core.MixBlend.replace,core.MixDirection.mixIn);
      skeleton.updateWorldTransform(core.Physics.none);
      for(const bone of skeleton.bones)if(![bone.worldX,bone.worldY,bone.a,bone.b,bone.c,bone.d].every(Number.isFinite))throw new Error('Nonfinite bone pose');
      for(const slot of skeleton.slots)if(slot.attachment instanceof core.MeshAttachment) {
        const mesh=slot.attachment, vertices=new Float32Array(mesh.worldVerticesLength);
        mesh.computeWorldVertices(slot,0,vertices.length,vertices,0,2);
        if(![...vertices].every(Number.isFinite))throw new Error('Nonfinite mesh vertices');
      }
    }
    animations.push({name:animation.name,duration:animation.duration,timelines:animation.timelines.length});
  }
  const result={runtimeVersion:version,bones:parsed.bones.length,slots:parsed.slots.length,animations};
  if(options.loop) {
    const animation=parsed.findAnimation(options.loop);
    if(!animation||animation.duration<=0)throw new Error('Loop animation missing or empty');
    if(data.physics?.length)throw new Error('Physics loops require a simulation-based check');
    const sample=time=>{
      const skeleton=new core.Skeleton(parsed);
      animation.apply(skeleton,0,time,false,[],1,core.MixBlend.replace,core.MixDirection.mixIn);
      skeleton.updateWorldTransform(core.Physics.none);
      const values=skeleton.bones.flatMap(b=>[b.worldX,b.worldY,b.a,b.b,b.c,b.d]);
      for(const slot of skeleton.slots) {
        values.push(slot.color.r,slot.color.g,slot.color.b,slot.color.a);
        if(slot.attachment instanceof core.MeshAttachment) {
          const vertices=new Float32Array(slot.attachment.worldVerticesLength);
          slot.attachment.computeWorldVertices(slot,0,vertices.length,vertices,0,2);
          values.push(...vertices);
        }
      }
      return {values,attachments:skeleton.slots.map(s=>s.attachment?.name||null)};
    };
    const delta=(a,b)=>a.values.length!==b.values.length?Infinity:a.values.reduce((max,v,i)=>Math.max(max,Math.abs(v-b.values[i])),0);
    const steps=120,dt=animation.duration/steps,samples=Array.from({length:steps+1},(_,i)=>sample(dt*i));
    const endPoseMaxDelta=delta(samples[0],samples.at(-1));
    const joinMaxDelta=delta(sample(animation.duration-dt/2),sample(dt/2));
    const maxStepDelta=Math.max(...samples.slice(1).map((s,i)=>delta(samples[i],s)));
    if(endPoseMaxDelta>1e-3||JSON.stringify(samples[0].attachments)!==JSON.stringify(samples.at(-1).attachments)||joinMaxDelta>Math.max(1e-3,maxStepDelta*2))throw new Error('Loop endpoint/join continuity check failed');
    result.loop={name:options.loop,endPoseMaxDelta,joinMaxDelta,maxStepDelta};
  }
  return result;
}
