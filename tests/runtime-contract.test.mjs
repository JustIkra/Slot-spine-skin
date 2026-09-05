import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import test from 'node:test';

const here=path.dirname(fileURLToPath(import.meta.url));
const project=process.env.SLOT_TEST_PROJECT;
if (!project) throw new Error('Set SLOT_TEST_PROJECT to the target game for runtime contract tests');
const require=createRequire(path.join(project,'package.json'));
const corePath=require.resolve('@esotericsoftware/spine-core',{paths:[path.dirname(require.resolve('@urso/core/package.json'))]});
const core=await import(pathToFileURL(corePath).href);
for (const owner of ['slot-spine-skin','slot-gen']) {
  const data=JSON.parse(execFileSync(process.env.PYTHON || 'python3',['-B',path.join(here,'generate-fixtures.py'),path.join(here,'../../',owner,'scripts/build_spine_json.py')],{encoding:'utf8'}));
  const parsed=new core.SkeletonJson({}).readSkeletonData(data);
  function pose(time, name='probe') {
    const skeleton=new core.Skeleton(parsed);
    parsed.findAnimation(name).apply(skeleton,0,time,false,[],1,core.MixBlend.replace,core.MixDirection.mixIn);
    return skeleton;
  }
  test(owner+': generated rotation and fixed channels match actual runtime',()=>{
    const bone=pose(4).bones[0];
    assert.equal(bone.rotation,30);
    const halfway=pose(3).bones[0];
    assert.ok(Math.abs(halfway.rotation-15)<0.05);
    assert.equal(halfway.x,0);
    assert.ok(Math.abs(halfway.y-15)<0.05);
    assert.equal(halfway.scaleX,1);
    assert.equal(halfway.scaleY,1);
  });
  test(owner+': all six presets remain finite throughout playback',()=>{
    for (const animation of parsed.animations) {
      for (const timeline of animation.timelines) for (const field of ['frames','curves'])
        if(timeline[field]) assert.ok([...timeline[field]].every(Number.isFinite),animation.name);
      for(let i=0;i<=24;i++) for(const bone of pose(animation.duration*i/24,animation.name).bones)
        assert.ok([bone.x,bone.y,bone.rotation,bone.scaleX,bone.scaleY].every(Number.isFinite),animation.name);
    }
  });
}
