import {existsSync,readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import path from 'node:path';

const root=process.cwd(),built=path.join(root,'dist/server/wrangler.json');
if(!existsSync(built))throw new Error('Run pnpm build before applying local migrations.');
const config=JSON.parse(readFileSync(built,'utf8'));
config.main=path.join(root,'dist/server/index.js');
if(config.assets)config.assets.directory=path.join(root,'dist/client');
for(const db of config.d1_databases??[])db.migrations_dir=path.join(root,'drizzle');
mkdirSync(path.join(root,'.sites-runtime'),{recursive:true});
const file=path.join(root,'.sites-runtime/local-migrations.json');
writeFileSync(file,JSON.stringify(config,null,2));
const argIndex=process.argv.indexOf('--persist-to');
const persistTo=argIndex>=0?path.resolve(root,process.argv[argIndex+1]):path.join(root,'.wrangler/state');
const args=['--import',path.join(root,'scripts/sites-env.mjs'),path.join(root,'node_modules/wrangler/bin/wrangler.js'),'d1','migrations','apply','DB','--local','--config',file,'--persist-to',persistTo];
const result=spawnSync(process.execPath,args,{stdio:'inherit',env:{...process.env,CI:'1'}});
if(result.error)throw result.error;
process.exit(result.status??1);
