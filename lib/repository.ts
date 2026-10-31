import { env } from 'cloudflare:workers';
import type { Snapshot, Audit } from './domain';
import { createSeed } from './seed';

export function database():D1Database {
  if(!env.DB) throw new Error('The persistent SQL database is not available.');
  return env.DB;
}
export function statement(sql:string,...params:unknown[]) {return database().prepare(sql).bind(...params);}
export function insert(table:string,workspaceId:string,record:object,orIgnore=false) {
  return insertMany(table,workspaceId,[record],orIgnore)[0];
}
export function insertMany(table:string,workspaceId:string,records:object[],orIgnore=false) {
  if(!records.length)return [];
  const rows=records.map(record=>({...record,workspaceId}) as Record<string,unknown>),keys=Object.keys(rows[0]),size=Math.max(1,Math.floor(100/keys.length)),statements:D1PreparedStatement[]=[];
  for(let start=0;start<rows.length;start+=size){const chunk=rows.slice(start,start+size),values=chunk.flatMap(row=>keys.map(k=>{const v=row[k];return typeof v==='boolean'?Number(v):Array.isArray(v)?JSON.stringify(v):v;}));statements.push(statement(`INSERT ${orIgnore?'OR IGNORE ':''}INTO ${table} (${keys.map(k=>`"${k}"`).join(',')}) VALUES ${chunk.map(()=>`(${keys.map(()=>'?').join(',')})`).join(',')}`,...values));}
  return statements;
}
export function auditStatement(workspaceId:string, actor:string, principal:string, action:string, target:string, detail:string) {
  const record:Audit={id:crypto.randomUUID(),actor,principal,action,target,detail,createdAt:new Date().toISOString()};
  return insert('audits',workspaceId,record);
}
export async function ensureWorkspace(id:string) {
  if(await statement('SELECT id FROM workspaces WHERE id = ?',id).first())return;
  const seed=createSeed(id);
  const statements=[statement('INSERT OR IGNORE INTO workspaces (id,name,createdAt) VALUES (?,?,?)',id,'Northstar workspace',new Date().toISOString())];
  const order:[string,object[]][]=[['identities',seed.identities],['sources',seed.sources],['accounts',seed.accounts],['entitlements',seed.entitlements],['grants',seed.grants],['source_access',seed.sourceAccess],['policies',seed.policies],['campaigns',seed.campaigns],['reviews',seed.reviews],['audits',seed.audits]];
  for(const [table,records]of order)for(const row of records)statements.push(insert(table,id,row,true));
  await database().batch(statements);
}
const TABLES=['identities','sources','accounts','entitlements','grants','reviews','remediations','policies','audits','campaigns'] as const;
export async function snapshot(workspaceId:string):Promise<Snapshot> {
  const results=await database().batch(TABLES.map(t=>statement(`SELECT * FROM ${t} WHERE workspaceId = ? ${t==='audits'?'ORDER BY createdAt DESC LIMIT 500':''}`,workspaceId)));
  const result=Object.fromEntries(TABLES.map((table,i)=>[table,results[i].results.map(raw=>{
    const r={...(raw as Record<string,unknown>)};delete r.workspaceId;
    for(const key of ['reasons','codes','allowedDepartments'])if(typeof r[key]==='string')r[key]=JSON.parse(r[key] as string);
    for(const key of ['privileged','enabled'])if(key in r)r[key]=Boolean(r[key]);
    return r;
  })])) as unknown as Snapshot;
  result.reviews.sort((a,b)=>b.score-a.score || a.createdAt.localeCompare(b.createdAt));
  return result;
}
