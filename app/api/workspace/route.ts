import type { NextRequest } from 'next/server';
import { z } from 'zod';
import { getChatGPTUser } from '@/app/chatgpt-auth';
import { PERSONAS, DomainError, exportCSV, type PersonaKey } from '@/lib/domain';
import { ensureWorkspace, snapshot, auditStatement, statement } from '@/lib/repository';
import { performAction } from '@/lib/service';

export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
async function context(request:NextRequest) {
  const user=await getChatGPTUser();
  // Development-only identity: replaced by a production constant during the build.
  const principal=user?.userId??(process.env.NODE_ENV==='development'?'local-demo-owner':null);
  if(!principal)throw new DomainError('Sign in with ChatGPT to open your private workspace.',401);
  const key=(request.headers.get('x-demo-persona')??'admin') as PersonaKey;
  if(!Object.hasOwn(PERSONAS,key))throw new DomainError('Unknown demo persona.');
  const persona=PERSONAS[key];
  await ensureWorkspace(principal);
  return {workspace:principal,actor:{key,name:persona.name,role:persona.role,employeeId:`${principal}:${persona.employeeKey}`,principal},displayName:user?.displayName??'Local demo owner'};
}
function failure(error:unknown){
  if(error instanceof DomainError)return Response.json({error:error.message},{status:error.status,headers});
  if(error instanceof z.ZodError)return Response.json({error:error.issues[0]?.message??'Invalid request.'},{status:400,headers});
  console.error('AccessGuard operation failed',error instanceof Error?error.message:'Unknown error');
  return Response.json({error:'The operation could not be completed. Refresh and try again.'},{status:500,headers});
}
export async function GET(request:NextRequest){
  try{
    const ctx=await context(request),data=await snapshot(ctx.workspace);
    const report=request.nextUrl.searchParams.get('export');
    if(report==='audit'||report==='reviews'){
      await auditStatement(ctx.workspace,ctx.actor.name,ctx.actor.principal,'Evidence report exported',report,'CSV evidence report generated from the current workspace snapshot.').run();
      const auditRows=report==='audit'?(await statement('SELECT * FROM audits WHERE workspaceId=? ORDER BY createdAt DESC',ctx.workspace).all<{createdAt:string;actor:string;principal:string;action:string;target:string;detail:string}>()).results:[];
      const csv=report==='audit'?exportCSV(['timestamp','actor','authenticated_principal','action','target','evidence'],auditRows.map(a=>[a.createdAt,a.actor,a.principal,a.action,a.target,a.detail])):exportCSV(
        ['review_id','campaign','identity','application','permission','risk_score','severity','status','reviewer','source_snapshot','grant_version','reasons','decision_reason','exception_expiry','remediation_status','verified_at','captured_evidence'],
        data.reviews.map(r=>{const grant=data.grants.find(g=>g.id===r.grantId)!,account=data.accounts.find(a=>a.id===grant.accountId)!,person=data.identities.find(p=>p.id===account.identityId),ent=data.entitlements.find(e=>e.id===grant.entitlementId),source=data.sources.find(s=>s.id===account.sourceId),job=data.remediations.find(j=>j.reviewId===r.id);return [r.id,data.campaigns.find(c=>c.id===r.campaignId)?.name,person?.name??account.externalId,source?.name,ent?.name,r.score,r.severity,r.status,data.identities.find(p=>p.id===r.assigneeId)?.name,r.sourceSnapshotAt,r.snapshotVersion,r.reasons.join(' | '),r.note,r.exceptionUntil,job?.status??'',job?.verifiedAt??'',r.evidence];})
      );
      return new Response(csv,{headers:{...headers,'Content-Type':'text/csv;charset=utf-8','Content-Disposition':`attachment; filename="accessguard-${report}.csv"`}});
    }
    return Response.json({...data,actor:ctx.actor,ownerName:ctx.displayName,generatedAt:new Date().toISOString(),environment:'demo'},{headers});
  }catch(error){return failure(error);}
}
export async function POST(request:NextRequest){
  try{
    const origin=request.headers.get('origin');
    if((origin && origin!==new URL(request.url).origin) || request.headers.get('sec-fetch-site')==='cross-site')throw new DomainError('Cross-origin writes are not permitted.',403);
    if(!request.headers.get('content-type')?.startsWith('application/json'))throw new DomainError('Send a JSON request.',415);
    const text=await request.text();if(text.length>1100000)throw new DomainError('The request is too large.',413);
    let body:unknown;try{body=JSON.parse(text);}catch{throw new DomainError('Invalid JSON request.');}
    const ctx=await context(request),result=await performAction(ctx.workspace,ctx.actor,body);
    return Response.json(result,{headers});
  }catch(error){return failure(error);}
}
