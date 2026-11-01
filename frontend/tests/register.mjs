import { registerHooks } from 'node:module';
import { existsSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
registerHooks({resolve(specifier,context,next){
  if(specifier==='cloudflare:workers')return {url:pathToFileURL(path.join(root,'tests/env.ts')).href,shortCircuit:true};
  if(specifier==='@/app/chatgpt-auth')return {url:pathToFileURL(path.join(root,'tests/auth.ts')).href,shortCircuit:true};
  if(specifier.startsWith('@/'))specifier=pathToFileURL(path.join(root,specifier.slice(2))).href;
  if(specifier.startsWith('.')||specifier.startsWith('file:')){
    const url=new URL(specifier,context.parentURL);
    const candidate=fileURLToPath(url);
    if(!path.extname(candidate)&&existsSync(candidate+'.ts'))return {url:pathToFileURL(candidate+'.ts').href,shortCircuit:true};
  }
  return next(specifier,context);
}});
