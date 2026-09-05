import fs from 'node:fs';
import {cliArgs,readJSON,attachmentKeys,inspectAtlas,checkBudget} from './lib/runtime-tools.mjs';

try {
  const args=cliArgs(['atlas-root','budget']);
  const atlas=inspectAtlas(args['atlas-root'],args.spine?attachmentKeys(readJSON(args.spine)):[]);
  checkBudget(atlas,readJSON(args.budget));
  const result={pages:atlas.imagePages,decodedRGBABytes:atlas.decodedRGBABytes,maxEdge:atlas.maxEdge,estimate:'RGBA8 base textures; excludes mipmaps and driver overhead'};
  if(args.out)fs.writeFileSync(args.out,JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
}catch(error){console.error(error.message);process.exitCode=1;}
