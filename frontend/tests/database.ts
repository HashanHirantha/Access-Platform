import { DatabaseSync } from 'node:sqlite';
import { readFileSync,readdirSync } from 'node:fs';
import path from 'node:path';
export function memoryDatabase(){
  const sqlite=new DatabaseSync(':memory:');sqlite.exec('PRAGMA foreign_keys=ON;');
  for(const f of readdirSync(path.join(process.cwd(),'drizzle')).filter(f=>f.endsWith('.sql')).sort())sqlite.exec(readFileSync(path.join(process.cwd(),'drizzle',f),'utf8'));
  class Prepared{
    constructor(public sql:string,public params:unknown[]=[]){ }
    bind(...params:unknown[]){if(params.length>100)throw new Error('D1 bound parameter limit exceeded.');return new Prepared(this.sql,params);}
    execute(){const q=sqlite.prepare(this.sql);if(/^\s*(SELECT|WITH)/i.test(this.sql))return {results:q.all(...this.params as never[]),success:true,meta:{changes:0}};const out=q.run(...this.params as never[]);return {results:[],success:true,meta:{changes:Number(out.changes)}};}
    async run(){return this.execute();}
    async all(){return this.execute();}
    async first(){return this.execute().results[0]??null;}
  }
  const db={prepare:(sql:string)=>new Prepared(sql),async batch(stmts:Prepared[]){sqlite.exec('BEGIN');try{const result=stmts.map(s=>s.execute());sqlite.exec('COMMIT');return result;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};
  return {db:db as unknown as D1Database,sqlite};
}
