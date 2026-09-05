import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {inspectAtlas, checkBudget} from '../scripts/lib/runtime-tools.mjs';

test('multipack pages are counted once, missing keys and over-budget results fail',()=>{
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),'slot-atlas-test-'));
  try {
    for(const [name,other] of [['a','b'],['b','a']]) {
      fs.writeFileSync(path.join(folder,name+'.png'),Buffer.from([1]));
      fs.writeFileSync(path.join(folder,name+'.json'),JSON.stringify({frames:{[name]:{frame:{x:0,y:0,w:2,h:2}}},meta:{image:name+'.png',size:{w:1024,h:1024},related_multi_packs:[other+'.json']}}));
    }
    const atlas=inspectAtlas(path.join(folder,'a.json'),['a','b']);
    assert.equal(atlas.decodedRGBABytes,8388608);
    assert.equal(atlas.pages.length,2);
    assert.throws(()=>inspectAtlas(path.join(folder,'a.json'),['absent']),/Missing/);
    assert.throws(()=>checkBudget(atlas,{maxDecodedBytes:8388607}),/budget/);
    assert.throws(()=>checkBudget(atlas,{}),/budget/);
    checkBudget(atlas,{maxDecodedBytes:8388608,maxPages:2,maxEdge:1024});
  } finally { fs.rmSync(folder,{recursive:true,force:true}); }
});
