import { z } from 'zod';
import { assessAccess, authorizeReview, captureEvidence, decideReview, DomainError, parseCSV, daysBetween, type Actor, type Snapshot, type Review } from './domain';
import { database, statement, insert, insertMany, auditStatement, snapshot } from './repository';

const admin=(a:Actor)=>{if(a.role!=='admin')throw new DomainError('Only the workspace admin can perform this action.',403);};
const operator=(a:Actor)=>{if(!['admin','security'].includes(a.role))throw new DomainError('An admin or security reviewer is required.',403);};
export async function performAction(workspaceId:string,actor:Actor,input:unknown) {
  const body=z.object({action:z.string()}).passthrough().parse(input);
  const data=await snapshot(workspaceId), now=new Date().toISOString();
  if(body.action==='scan') {
    admin(actor);
    const {name,dueDays}=z.object({name:z.string().trim().min(3).max(80).default('Continuous access review'),dueDays:z.number().int().min(1).max(30).default(7)}).parse(body);
    const campaign={id:crypto.randomUUID(),name,startedAt:now,dueAt:new Date(Date.now()+dueDays*86400000).toISOString()};
    const statements=[insert('campaigns',workspaceId,campaign)],createdIndices:number[]=[],newReviews:Review[]=[];let created=0,refreshed=0;
    for(const grant of data.grants){
      const account=data.accounts.find(a=>a.id===grant.accountId)!,entitlement=data.entitlements.find(e=>e.id===grant.entitlementId)!,source=data.sources.find(s=>s.id===account.sourceId)!;
      const person=data.identities.find(i=>i.id===account.identityId);
      const finding=assessAccess(person,account,entitlement,grant,source,data.policies,now),evidence=captureEvidence(person,account,entitlement,grant,source,data.policies);
      const previous=data.reviews.filter(r=>r.grantId===grant.id).sort((a,b)=>b.createdAt.localeCompare(a.createdAt))[0];
      if(!finding){
        if(previous && ['pending','investigation','awaiting_second'].includes(previous.status) && evidence!==previous.evidence){
          statements.push(statement("UPDATE reviews SET score=0,severity='low',reasons=?,codes=?,recommendation='Confirm the current business requirement',evidence=?,snapshotVersion=?,sourceSnapshotAt=?,status='investigation',proposal=NULL,firstActor=NULL,version=version+1 WHERE id=? AND workspaceId=? AND version=?",JSON.stringify(['The evidence or policy changed. Current rules no longer flag this permission; a reviewer must confirm the business requirement.']),JSON.stringify(['REVALIDATE']),evidence,grant.version,source.lastSync,previous.id,workspaceId,previous.version));refreshed++;
        }
        continue;
      }
      if(previous && ['pending','investigation','awaiting_second'].includes(previous.status)){
        if(previous.evidence!==evidence){
          statements.push(statement("UPDATE reviews SET score=?,severity=?,reasons=?,codes=?,recommendation=?,snapshotVersion=?,sourceSnapshotAt=?,evidence=?,status='investigation',proposal=NULL,firstActor=NULL,version=version+1 WHERE id=? AND workspaceId=? AND version=?",finding.score,finding.severity,JSON.stringify(finding.reasons),JSON.stringify(finding.codes),finding.recommendation,grant.version,source.lastSync,evidence,previous.id,workspaceId,previous.version));refreshed++;
        }
        continue;
      }
      if(previous?.status==='exception' && previous.exceptionUntil && Date.parse(previous.exceptionUntil)>Date.now())continue;
      if(previous?.status==='revoke' && previous.snapshotVersion===grant.version && data.remediations.some(r=>r.reviewId===previous.id && r.status!=='verified'))continue;
      if(previous?.status==='keep' && previous.evidence===evidence && previous.decidedAt && daysBetween(previous.decidedAt,now)<30)continue;
      const review:Review={id:crypto.randomUUID(),grantId:grant.id,campaignId:campaign.id,assigneeId:person?.managerId??`${workspaceId}:EMP003`,...finding,status:'pending',note:'',firstActor:null,proposal:null,decisionId:null,snapshotVersion:grant.version,sourceSnapshotAt:source.lastSync,evidence,exceptionUntil:null,dueAt:campaign.dueAt,createdAt:now,decidedAt:null,version:1};
      newReviews.push(review);
    }
    for(const s of insertMany('reviews',workspaceId,newReviews,true)){createdIndices.push(statements.length);statements.push(s);}
    statements.push(auditStatement(workspaceId,actor.name,actor.principal,'Risk scan completed',campaign.name,`Campaign ${campaign.id}. ${data.grants.filter(g=>g.state==='active').length} active permission assignments evaluated. Open-review uniqueness is database enforced. Policy configuration: ${JSON.stringify(data.policies.map(p=>({code:p.code,enabled:p.enabled,threshold:p.threshold})))}`));
    const results=await database().batch(statements);created=createdIndices.reduce((sum,i)=>sum+(results[i].meta.changes??0),0);
    return {message:`Scan complete. ${created} new reviews created; ${refreshed} refreshed.`,created,refreshed};
  }
  if(body.action==='decide') {
    const v=z.object({id:z.string(),version:z.number().int(),decision:z.string(),note:z.string().trim(),exceptionUntil:z.string().nullable().optional()}).parse(body);
    const review=data.reviews.find(r=>r.id===v.id);if(!review)throw new DomainError('Review not found.',404);
    if(review.version!==v.version)throw new DomainError('This review changed. Refresh and review the latest evidence.',409);
    const grant=data.grants.find(g=>g.id===review.grantId)!,account=data.accounts.find(a=>a.id===grant.accountId)!;
    authorizeReview(actor,review,account.identityId,v.decision);
    if(grant.version!==review.snapshotVersion)throw new DomainError('Access changed after the evidence snapshot. Run a new scan before deciding.',409);
    const source=data.sources.find(s=>s.id===account.sourceId)!;
    const identity=data.identities.find(p=>p.id===account.identityId),entitlement=data.entitlements.find(e=>e.id===grant.entitlementId)!;
    if(captureEvidence(identity,account,entitlement,grant,source,data.policies)!==review.evidence)throw new DomainError('The identity, permission, source or policy evidence changed. Run a new scan before deciding.',409);
    if((v.decision==='revoke' || (v.decision==='confirm' && review.proposal==='revoke')) && (daysBetween(source.lastSync,now)>2 || source.status!=='healthy'))throw new DomainError('Refresh the source evidence before approving access removal.',409);
    const next=decideReview(review,actor,v.decision,v.note,v.exceptionUntil??null,now),decisionId=crypto.randomUUID();
    const final=['keep','revoke','exception'].includes(next.status), action=next.status==='awaiting_second'?'Second approval requested':next.status==='revoke'?'Access removal approved':next.status==='keep'?'Access retained':next.status==='exception'?'Exception granted':'Investigation requested';
    const statements=[statement('UPDATE reviews SET status=?,note=?,proposal=?,firstActor=?,exceptionUntil=?,decidedAt=?,decisionId=?,version=version+1 WHERE id=? AND workspaceId=? AND version=?',next.status,next.note,next.proposal,next.firstActor,next.exceptionUntil,final?now:null,decisionId,review.id,workspaceId,v.version)];
    // Conditional inserts bind the outbox and audit to the successful optimistic update.
    if(next.status==='revoke') statements.push(statement("INSERT INTO remediations (id,workspaceId,reviewId,grantId,status,attempts,expectedVersion,createdAt) SELECT ?,?,?,?,'queued',0,?,? WHERE EXISTS (SELECT 1 FROM reviews WHERE id=? AND workspaceId=? AND decisionId=?)",crypto.randomUUID(),workspaceId,review.id,grant.id,review.snapshotVersion,now,review.id,workspaceId,decisionId));
    statements.push(statement('INSERT INTO audits (id,workspaceId,actor,principal,action,target,detail,createdAt) SELECT ?,?,?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM reviews WHERE id=? AND workspaceId=? AND decisionId=?)',crypto.randomUUID(),workspaceId,actor.name,actor.principal,action,review.id,`${next.note} | Evidence version: ${review.snapshotVersion}; source snapshot: ${review.sourceSnapshotAt}; reasons: ${JSON.stringify(review.reasons)}`,now,review.id,workspaceId,decisionId));
    const results=await database().batch(statements);
    if(!results[0].meta.changes)throw new DomainError('Another reviewer updated this record. Refresh to continue.',409);
    return {message:next.status==='awaiting_second'?'Decision recorded. An independent second approval is required.':next.status==='revoke'?'Removal approved. A remediation job is ready to execute.':'Review decision saved.'};
  }
  if(body.action==='execute') {
    operator(actor);
    const {id,simulateFailure}=z.object({id:z.string(),simulateFailure:z.boolean().default(false)}).parse(body);
    const job=data.remediations.find(j=>j.id===id);if(!job)throw new DomainError('Remediation not found.',404);
    if(job.status==='verified')return {message:'Already verified. No duplicate action was performed.'};
    if(!['queued','failed'].includes(job.status) && !(job.status==='running' && job.leaseUntil && Date.parse(job.leaseUntil)<=Date.now()))throw new DomainError('This job is already being processed. An interrupted worker can be retried after its 2-minute lease expires.',409);
    const leaseUntil=new Date(Date.now()+120000).toISOString();
    const claimed=await statement("UPDATE remediations SET status='running',attempts=attempts+1,error=NULL,leaseUntil=? WHERE id=? AND workspaceId=? AND (status IN ('queued','failed') OR (status='running' AND leaseUntil<=?))",leaseUntil,id,workspaceId,now).run();
    if(!claimed.meta.changes)throw new DomainError('Another worker claimed this job. Refresh to see its result.',409);
    try{
      if(simulateFailure)throw new DomainError('Simulated connector timeout. The source permission was not changed.',503);
      const approvedReview=data.reviews.find(r=>r.id===job.reviewId)!,approvedGrant=data.grants.find(g=>g.id===job.grantId)!,approvedAccount=data.accounts.find(a=>a.id===approvedGrant.accountId)!,approvedEntitlement=data.entitlements.find(e=>e.id===approvedGrant.entitlementId)!,approvedSource=data.sources.find(s=>s.id===approvedAccount.sourceId)!;
      if(captureEvidence(data.identities.find(p=>p.id===approvedAccount.identityId),approvedAccount,approvedEntitlement,approvedGrant,approvedSource,data.policies)!==approvedReview.evidence)throw new DomainError('The approved identity, policy or access evidence changed. A fresh review is required before execution.',409);
      if(daysBetween(approvedSource.lastSync,now)>2)throw new DomainError('The source evidence is stale. Refresh and review before execution.',409);
      const source=await statement('SELECT * FROM source_access WHERE grantId=? AND workspaceId=?',job.grantId,workspaceId).first<{state:string;version:number}>();
      if(!source)throw new DomainError('Source evidence unavailable. No change was made.',409);
      if(source.state!=='revoked' && source.version!==job.expectedVersion)throw new DomainError('The source permission changed after approval. A fresh review is required.',409);
      // Mock connector write. Source state is independent of the governance inventory.
      if(source.state!=='revoked'){
        const changed=await statement("UPDATE source_access SET state='revoked',version=version+1,updatedAt=? WHERE grantId=? AND workspaceId=? AND version=?",now,job.grantId,workspaceId,job.expectedVersion).run();
        if(!changed.meta.changes)throw new DomainError('The source changed during execution. Verify it before retrying.',409);
      }
      const verified=await statement('SELECT state,version,updatedAt FROM source_access WHERE grantId=? AND workspaceId=?',job.grantId,workspaceId).first<{state:string;version:number;updatedAt:string}>();
      if(verified?.state!=='revoked')throw new DomainError('Read-back verification failed.',503);
      const evidence=JSON.stringify({connector:'Mock source adapter',observedState:verified.state,sourceVersion:verified.version,observedAt:now,grantId:job.grantId});
      await database().batch([
        statement("UPDATE grants SET state='revoked',version=? WHERE id=? AND workspaceId=?",verified.version,job.grantId,workspaceId),
        statement("UPDATE remediations SET status='verified',evidence=?,verifiedAt=?,error=NULL,leaseUntil=NULL WHERE id=? AND workspaceId=?",evidence,now,id,workspaceId),
        auditStatement(workspaceId,actor.name,actor.principal,'Remediation verified',id,`Mock connector removed the permission and independently read it back. ${evidence}`),
      ]);
      return {message:'Permission removed in the demo source. Read-back verification passed.'};
    }catch(error){
      const message=error instanceof DomainError?error.message:'Connector execution interrupted. Retry after checking source state.';
      await database().batch([statement("UPDATE remediations SET status='failed',error=?,leaseUntil=NULL WHERE id=? AND workspaceId=?",message,id,workspaceId),auditStatement(workspaceId,actor.name,actor.principal,'Remediation failed',id,message)]);
      throw new DomainError(message,error instanceof DomainError?error.status:503);
    }
  }
  if(body.action==='policy') {
    admin(actor);const v=z.object({id:z.string(),enabled:z.boolean(),threshold:z.number().int().min(1).max(365).optional()}).parse(body);
    const policy=data.policies.find(p=>p.id===v.id);if(!policy)throw new DomainError('Policy not found.',404);
    await database().batch([statement('UPDATE policies SET enabled=?,threshold=? WHERE id=? AND workspaceId=?',Number(v.enabled),v.threshold??policy.threshold,v.id,workspaceId),auditStatement(workspaceId,actor.name,actor.principal,'Policy updated',policy.name,JSON.stringify({before:policy,after:{enabled:v.enabled,threshold:v.threshold??policy.threshold}}))]);
    return {message:'Policy saved. Run a risk scan to evaluate the current configuration.'};
  }
  if(body.action==='sync') {
    admin(actor);const {id}=z.object({id:z.string()}).parse(body);const source=data.sources.find(s=>s.id===id);if(!source)throw new DomainError('Source not found.',404);
    if(source.mode==='CSV import')throw new DomainError('Upload a fresh CSV to update this source.');
    const statements=[statement("UPDATE sources SET lastSync=?,status='healthy' WHERE id=? AND workspaceId=?",now,id,workspaceId)];
    for(const grant of data.grants.filter(g=>data.accounts.some(a=>a.id===g.accountId && a.sourceId===id)))statements.push(statement('UPDATE grants SET state=(SELECT state FROM source_access WHERE grantId=grants.id AND workspaceId=?),version=(SELECT version FROM source_access WHERE grantId=grants.id AND workspaceId=?) WHERE id=? AND workspaceId=?',workspaceId,workspaceId,grant.id,workspaceId));
    statements.push(auditStatement(workspaceId,actor.name,actor.principal,'Source synced',source.name,'Synthetic connector inventory reconciled. No live provider API was contacted.'));
    await database().batch(statements);return {message:`${source.name} demo source synced. Run a scan to refresh review evidence.`};
  }
  if(body.action==='import') {
    admin(actor);const v=z.object({kind:z.enum(['hr','access']),csv:z.string().min(10).max(1000000),filename:z.string().max(150)}).parse(body);
    return importData(workspaceId,actor,v,data,now);
  }
  throw new DomainError('Unsupported action.');
}

async function stableId(workspace:string,value:string){const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));return workspace+':'+Array.from(new Uint8Array(bytes)).map(x=>x.toString(16).padStart(2,'0')).join('').slice(0,24);}
async function importData(workspace:string,actor:Actor,v:{kind:'hr'|'access';csv:string;filename:string},data:Snapshot,now:string){
  const rows=parseCSV(v.csv),checksum=await stableId(workspace,v.kind+v.csv);
  if(await statement('SELECT id FROM imports WHERE id=? AND workspaceId=?',checksum,workspace).first())return {message:'This exact file was already imported. No duplicate records were created.',rowCount:0};
  const required=v.kind==='hr'?['employee_id','name','email','department','job_title','manager_id','employment_status','contract_end']:['account_id','employee_id','application','permission','privileged','last_active','account_type','expires_at'];
  for(const h of required)if(!(h in rows[0]))throw new DomainError(`Missing required column: ${h}. Download the template for the expected format.`);
  const isDate=(s:string)=>!s || /^\d{4}-\d{2}-\d{2}(T.*)?$/.test(s) && Number.isFinite(Date.parse(s));
  const seen=new Set<string>();
  const accountMetadata=new Map<string,string>(),entitlementMetadata=new Map<string,string>();
  for(const [i,r] of rows.entries()){
    for(const val of Object.values(r))if(val.length>250 || /[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(val))throw new DomainError(`Row ${i+2} has an invalid or overly long field.`);
    if(v.kind==='hr'){
      if(!/^[A-Za-z0-9_-]{1,40}$/.test(r.employee_id) || !r.name || !r.department || !r.job_title || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(r.email))throw new DomainError(`Row ${i+2} has invalid employee details.`);
      if(!['active','terminated','contractor','leave'].includes(r.employment_status) || !isDate(r.contract_end))throw new DomainError(`Row ${i+2} has an invalid employment status or contract date.`);
    }else{
      if(!r.account_id || !r.application || !r.permission || !['true','false'].includes(r.privileged) || !['user','service','breakglass'].includes(r.account_type) || !isDate(r.last_active) || !isDate(r.expires_at))throw new DomainError(`Row ${i+2} has invalid access details. Use true/false and ISO dates.`);
      if(r.last_active && Date.parse(r.last_active)>Date.now()+86400000)throw new DomainError(`Row ${i+2} has activity in the future.`);
      if(r.employee_id && !data.identities.some(p=>p.employeeId===r.employee_id))throw new DomainError(`Row ${i+2}: employee ${r.employee_id} is unknown. Import HR data first, or leave employee_id blank for an unverified owner.`);
      const accountKey=r.application.toLowerCase()+'|'+r.account_id,metadata=JSON.stringify([r.employee_id,r.account_type,r.last_active]);
      if(accountMetadata.has(accountKey)&&accountMetadata.get(accountKey)!==metadata)throw new DomainError(`Row ${i+2} conflicts with another row for the same account.`);accountMetadata.set(accountKey,metadata);
      const entitlementKey=r.application.toLowerCase()+'|'+r.permission;
      if(entitlementMetadata.has(entitlementKey)&&entitlementMetadata.get(entitlementKey)!==r.privileged)throw new DomainError(`Row ${i+2} has conflicting privileged flags for the same permission.`);entitlementMetadata.set(entitlementKey,r.privileged);
    }
    const key=v.kind==='hr'?r.employee_id:[r.application.toLowerCase(),r.account_id,r.permission].join('|');
    if(seen.has(key))throw new DomainError(`Row ${i+2} repeats a record in this file.`);seen.add(key);
  }
  if(v.kind==='hr')for(const [i,r]of rows.entries())if(r.manager_id && !rows.some(x=>x.employee_id===r.manager_id) && !data.identities.some(x=>x.employeeId===r.manager_id))throw new DomainError(`Row ${i+2} references an unknown manager.`);
  const statements:D1PreparedStatement[]=[],groups=new Map<string,unknown[][]>(),syncedSourceIds=new Set<string>();
  const queue=(sql:string,...params:unknown[])=>{const group=groups.get(sql)??[];group.push(params);groups.set(sql,group);};
  if(v.kind==='hr'){
    for(const r of rows){
      const id=data.identities.find(i=>i.employeeId===r.employee_id)?.id??`${workspace}:${r.employee_id}`;
      const managerId=r.manager_id?(data.identities.find(i=>i.employeeId===r.manager_id)?.id??`${workspace}:${r.manager_id}`):null;
      queue('INSERT INTO identities (id,workspaceId,employeeId,name,email,department,jobTitle,managerId,status,contractEnd) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,email=excluded.email,department=excluded.department,jobTitle=excluded.jobTitle,managerId=excluded.managerId,status=excluded.status,contractEnd=excluded.contractEnd',id,workspace,r.employee_id,r.name,r.email,r.department,r.job_title,managerId,r.employment_status,r.contract_end?new Date(r.contract_end).toISOString():null);
    }
    statements.push(statement('UPDATE sources SET lastSync=? WHERE workspaceId=? AND icon=?',now,workspace,'people'));
  }else{
    const sources=new Map(data.sources.map(s=>[s.name.toLowerCase(),s]));
    const accountIds=new Map<string,string>(),entIds=new Map<string,string>();
    for(const r of rows){
      let source=sources.get(r.application.toLowerCase());
      if(source && source.mode!=='CSV import')throw new DomainError(`Use a distinct application name for imported data; ${source.name} is a seeded mock source.`);
      if(!source){source={id:await stableId(workspace,'source:'+r.application.toLowerCase()),name:r.application,category:'Imported application',icon:'app',lastSync:now,status:'healthy',mode:'CSV import'};sources.set(r.application.toLowerCase(),source);queue('INSERT OR IGNORE INTO sources (id,workspaceId,name,category,icon,lastSync,status,mode) VALUES (?,?,?,?,?,?,?,?)',source.id,workspace,source.name,source.category,source.icon,source.lastSync,source.status,source.mode);}
      const accountKey=source.id+'|'+r.account_id;
      let accountId=accountIds.get(accountKey);
      if(!accountId){accountId=data.accounts.find(a=>a.sourceId===source!.id && a.externalId===r.account_id)?.id??await stableId(workspace,'account:'+accountKey);accountIds.set(accountKey,accountId);
        const person=data.identities.find(p=>p.employeeId===r.employee_id);
        queue("INSERT INTO accounts (id,workspaceId,sourceId,identityId,externalId,kind,status,lastActive,createdAt) VALUES (?,?,?,?,?,?,'enabled',?,?) ON CONFLICT(id) DO UPDATE SET identityId=excluded.identityId,kind=excluded.kind,lastActive=excluded.lastActive",accountId,workspace,source.id,person?.id??null,r.account_id,r.account_type,r.last_active?new Date(r.last_active).toISOString():null,r.last_active?new Date(r.last_active).toISOString():now);
      }
      const entKey=source.id+'|'+r.permission;let entId=entIds.get(entKey);
      if(!entId){entId=data.entitlements.find(e=>e.sourceId===source!.id && e.name===r.permission)?.id??await stableId(workspace,'ent:'+entKey);entIds.set(entKey,entId);queue("INSERT INTO entitlements (id,workspaceId,sourceId,name,privileged,allowedDepartments) VALUES (?,?,?,?,?,'[\"*\"]') ON CONFLICT(id) DO UPDATE SET privileged=excluded.privileged",entId,workspace,source.id,r.permission,Number(r.privileged==='true'));}
      const existing=data.grants.find(g=>g.accountId===accountId && g.entitlementId===entId),grantId=existing?.id??await stableId(workspace,'grant:'+accountId+'|'+entId),version=(existing?.version??0)+1;
      queue("INSERT INTO grants (id,workspaceId,accountId,entitlementId,state,expiresAt,version) VALUES (?,?,?,?,'active',?,?) ON CONFLICT(id) DO UPDATE SET state='active',expiresAt=excluded.expiresAt,version=excluded.version",grantId,workspace,accountId,entId,r.expires_at?new Date(r.expires_at).toISOString():null,version);
      queue("INSERT INTO source_access (id,workspaceId,grantId,state,version,updatedAt) VALUES (?,?,?,'active',?,?) ON CONFLICT(id) DO UPDATE SET state='active',version=excluded.version,updatedAt=excluded.updatedAt",grantId,workspace,grantId,version,now);
      syncedSourceIds.add(source.id);
    }
  }
  // Batch inserts stay below D1's 100-bound-parameter limit and preserve FK order.
  const order=['sources','identities','accounts','entitlements','grants','source_access'];
  const grouped:D1PreparedStatement[]=[];
  for(const [sql,values] of [...groups.entries()].sort((a,b)=>order.indexOf(a[0].match(/INTO (\w+)/)![1])-order.indexOf(b[0].match(/INTO (\w+)/)![1]))){
    const match=sql.match(/^(.+? VALUES )(\([^)]*\))([\s\S]*)$/)!;
    const size=Math.max(1,Math.floor(100/values[0].length));
    for(let start=0;start<values.length;start+=size){const chunk=values.slice(start,start+size);grouped.push(statement(match[1]+chunk.map(()=>match[2]).join(',')+match[3],...chunk.flat()));}
  }
  statements.unshift(...grouped);
  const synced=[...syncedSourceIds];for(let start=0;start<synced.length;start+=98){const chunk=synced.slice(start,start+98);statements.push(statement(`UPDATE sources SET lastSync=? WHERE workspaceId=? AND id IN (${chunk.map(()=>'?').join(',')})`,now,workspace,...chunk));}
  statements.push(insert('imports',workspace,{id:checksum,checksum,filename:v.filename,kind:v.kind,rowCount:rows.length,createdAt:now}),auditStatement(workspace,actor.name,actor.principal,'CSV imported',v.filename,`${rows.length} ${v.kind} rows validated and imported atomically. This is an additive/upsert import; omitted records are not deleted. Checksum: ${checksum}`));
  try{await database().batch(statements);}catch{throw new DomainError('The import could not be committed. No partial import was saved. Refresh before retrying.',409);}
  return {message:`${rows.length} rows imported successfully. Run a risk scan to evaluate the new evidence.`,rowCount:rows.length};
}
