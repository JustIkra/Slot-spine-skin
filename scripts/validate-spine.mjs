import fs from 'node:fs';
import {cliArgs,readJSON,attachmentKeys,inspectAtlas,validateSpine} from './lib/runtime-tools.mjs';

try {
  const args=cliArgs(['project-root','spine']);
  const data=readJSON(args.spine);
  const result=await validateSpine(args['project-root'],data,{loop:args.loop});
  if(args['atlas-root']) {
    const atlas=inspectAtlas(args['atlas-root'],attachmentKeys(data));
    result.atlas={pages:atlas.imagePages,decodedRGBABytes:atlas.decodedRGBABytes};
  }
  if(args.out)fs.writeFileSync(args.out,JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
} catch(error) {console.error(error.message);process.exitCode=1;}
