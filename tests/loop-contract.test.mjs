import assert from 'node:assert/strict';
import test from 'node:test';
import {validateSpine} from '../scripts/lib/runtime-tools.mjs';

const project=process.env.SLOT_TEST_PROJECT;
if(!project)throw new Error('Set SLOT_TEST_PROJECT');
const fixture=last=>({skeleton:{spine:'4.2.0'},bones:[{name:'root'}],animations:{idle:{bones:{root:{translate:[{time:0,x:0,y:0},{time:.5,x:1,y:2},{time:1,x:last,y:0}]}}}}});
test('loop contract rejects a different end pose and measures the join',async()=>{
  const accepted=await validateSpine(project,fixture(0),{loop:'idle'});
  assert.equal(accepted.loop.endPoseMaxDelta,0);
  assert.ok(accepted.loop.joinMaxDelta<=accepted.loop.maxStepDelta*2);
  await assert.rejects(validateSpine(project,fixture(2),{loop:'idle'}),/loop/i);
});
