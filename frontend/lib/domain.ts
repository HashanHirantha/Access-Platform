export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type ReviewStatus = 'pending' | 'investigation' | 'awaiting_second' | 'keep' | 'revoke' | 'exception';
export interface Identity { id:string; employeeId:string; name:string; email:string; department:string; jobTitle:string; managerId:string|null; status:string; contractEnd:string|null; }
export interface Source { id:string; name:string; category:string; icon:string; lastSync:string; status:string; mode:string; }
export interface Account { id:string; sourceId:string; identityId:string|null; externalId:string; kind:string; status:string; lastActive:string|null; createdAt:string; }
export interface Entitlement { id:string; sourceId:string; name:string; privileged:boolean; allowedDepartments:string[]; }
export interface Grant { id:string; accountId:string; entitlementId:string; state:string; expiresAt:string|null; version:number; }
export interface Policy { id:string; code:string; name:string; description:string; enabled:boolean; threshold:number; }
export interface Review { id:string; grantId:string; campaignId:string; assigneeId:string; score:number; severity:Severity; reasons:string[]; codes:string[]; recommendation:string; status:ReviewStatus; note:string; firstActor:string|null; proposal:string|null; decisionId:string|null; snapshotVersion:number; sourceSnapshotAt:string; evidence:string; exceptionUntil:string|null; dueAt:string; createdAt:string; decidedAt:string|null; version:number; }
export interface Remediation { id:string; reviewId:string; grantId:string; status:string; attempts:number; expectedVersion:number; error:string|null; evidence:string|null; leaseUntil:string|null; createdAt:string; verifiedAt:string|null; }
export interface Audit { id:string; actor:string; principal:string; action:string; target:string; detail:string; createdAt:string; }
export interface Campaign {id:string;name:string;startedAt:string;dueAt:string;}
export interface Snapshot { identities:Identity[]; sources:Source[]; accounts:Account[]; entitlements:Entitlement[]; grants:Grant[]; reviews:Review[]; remediations:Remediation[]; policies:Policy[]; audits:Audit[]; campaigns:Campaign[]; }
export const PERSONAS = {
  admin: { name:'Hashan Hirantha', label:'Workspace admin', role:'admin', employeeKey:'EMP001', initials:'HH' },
  reviewer: { name:'Maya Perera', label:'Department reviewer', role:'reviewer', employeeKey:'EMP002', initials:'MP' },
  security: { name:'Daniel Silva', label:'Security reviewer', role:'security', employeeKey:'EMP003', initials:'DS' },
  auditor: { name:'Alex Morgan', label:'Read-only auditor', role:'auditor', employeeKey:'EMP004', initials:'AM' },
} as const;
export type PersonaKey = keyof typeof PERSONAS;
export interface Actor { key:PersonaKey; name:string; role:string; employeeId:string; principal:string; }
export class DomainError extends Error { constructor(message:string, public status=400) {super(message);} }
export const daysBetween = (earlier:string, later:string) => Math.floor((Date.parse(later)-Date.parse(earlier))/86400000);
export const isoDaysAgo = (days:number, now=new Date()) => new Date(now.getTime()-days*86400000).toISOString();
export const actionable = (s:ReviewStatus) => ['pending','investigation','awaiting_second'].includes(s);

export function captureEvidence(identity:Identity|undefined,account:Account,entitlement:Entitlement,grant:Grant,source:Source,policies:Policy[]) {
  return JSON.stringify({identity:identity??null,account,entitlement,grant,source:{id:source.id,lastSync:source.lastSync,status:source.status},policies:[...policies].sort((a,b)=>a.code.localeCompare(b.code)).map(p=>({code:p.code,enabled:p.enabled,threshold:p.threshold}))});
}

export function assessAccess(identity:Identity|undefined, account:Account, entitlement:Entitlement, grant:Grant, source:Source, policies:Policy[], now:string) {
  const reasons:string[]=[], codes:string[]=[], scores:number[]=[];
  const active = (code:string) => policies.find(p=>p.code===code && p.enabled);
  const flag = (code:string,score:number,reason:string) => {codes.push(code);scores.push(score);reasons.push(reason);};
  if (grant.state!=='active' || account.status!=='enabled') return null;
  const stale = daysBetween(source.lastSync,now)>2 || source.status!=='healthy';
  if(stale) flag('DATA_QUALITY',45,'Source evidence is stale or unavailable. Refresh the source before deciding.');
  if(!identity && account.kind==='user' && active('ORPHANED')) flag('ORPHANED',78,'No verified employee owner is linked to this human account. Investigate the identity mapping.');
  if(identity?.status==='terminated' && active('LEAVER')) flag('LEAVER',100,'The employee has left the organization, but this account is still enabled.');
  if(identity?.contractEnd && Date.parse(identity.contractEnd)<Date.parse(now) && active('CONTRACT')) flag('CONTRACT',90,'The contractor end date has passed while access remains active.');
  if(grant.expiresAt && Date.parse(grant.expiresAt)<Date.parse(now) && active('EXPIRED')) flag('EXPIRED',88,'This temporary permission has passed its approved expiry date.');
  const inactive=active('INACTIVE');
  if(inactive && account.kind==='user' && identity?.status!=='leave' && daysBetween(account.createdAt,now)>=inactive.threshold){
    if(account.lastActive && daysBetween(account.lastActive,now)>=inactive.threshold) flag('INACTIVE',entitlement.privileged?85:56,`No successful application activity for ${daysBetween(account.lastActive,now)} days (policy: ${inactive.threshold} days).`);
    else if(!account.lastActive) flag('DATA_QUALITY',40,'Successful activity data is missing. Confirm usage before removing access.');
  }
  if(identity && entitlement.privileged && active('ROLE_MISMATCH') && !entitlement.allowedDepartments.includes('*') && !entitlement.allowedDepartments.includes(identity.department)) flag('ROLE_MISMATCH',82,`This privileged permission is outside the approved access baseline for ${identity.department}.`);
  if(!scores.length) return null;
  const score=Math.max(...scores),severity:Severity=score>=90?'critical':score>=70?'high':score>=40?'medium':'low';
  const uncertain=stale || codes.includes('ORPHANED') || (codes.length===1 && codes[0]==='DATA_QUALITY');
  return {score,severity,reasons,codes,recommendation:uncertain?'Investigate ownership or evidence':'Review for removal'};
}

export function authorizeReview(actor:Actor, review:Review, identityId:string|null, decision:string) {
  if(actor.role==='auditor') throw new DomainError('Auditors have read-only access.',403);
  if(identityId===actor.employeeId) throw new DomainError('You cannot review your own access.',403);
  if(review.status==='awaiting_second') {
    if(!['admin','security'].includes(actor.role)) throw new DomainError('An independent security reviewer must provide the second approval.',403);
    if(review.firstActor===actor.employeeId) throw new DomainError('The second approval must come from a different person.',403);
    if(!['confirm','return'].includes(decision)) throw new DomainError('Confirm the proposed decision or return it for investigation.');
  } else {
    if(!['pending','investigation'].includes(review.status)) throw new DomainError('This review is already completed.',409);
    if(actor.role==='reviewer' && review.assigneeId!==actor.employeeId) throw new DomainError('This review is assigned to another reviewer.',403);
    if(!['keep','revoke','investigate','exception'].includes(decision)) throw new DomainError('Invalid review decision.');
  }
}

export function decideReview(review:Review, actor:Actor, decision:string, note:string, exceptionUntil:string|null, now:string) {
  if(note.trim().length<8 || note.length>2000) throw new DomainError('Add a reason between 8 and 2,000 characters.');
  if(decision==='exception' || (decision==='confirm' && review.proposal==='exception')){
    const expiry=decision==='confirm'?review.exceptionUntil:exceptionUntil;
    const days=expiry?daysBetween(now,expiry):-1;
    if(!Number.isFinite(days) || days<1 || days>90) throw new DomainError('Exceptions must expire between 1 and 90 days from now.');
  }
  if(decision==='confirm') return {status:review.proposal as ReviewStatus,proposal:review.proposal,firstActor:review.firstActor,note:`${review.note}\nSecond approval: ${note}`,exceptionUntil:review.exceptionUntil};
  if(decision==='return') return {status:'investigation' as ReviewStatus,proposal:null,firstActor:null,note,exceptionUntil:null};
  const finalStatus = decision==='investigate'?'investigation':decision as ReviewStatus;
  const needsSecond=review.severity==='critical' && ['revoke','keep','exception'].includes(decision);
  return {status:needsSecond?'awaiting_second' as ReviewStatus:finalStatus,proposal:needsSecond?finalStatus:null,firstActor:needsSecond?actor.employeeId:null,note,exceptionUntil:decision==='exception'?exceptionUntil:null};
}

export function parseCSV(input:string):Record<string,string>[] {
  const text=input.replace(/^\uFEFF/,'');
  const rows:string[][]=[];let row:string[]=[],field='',quoted=false,closed=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){
      if(quoted && text[i+1]==='"'){field+='"';i++;}
      else if(quoted){quoted=false;closed=true;}
      else if(!field && !closed)quoted=true;
      else throw new DomainError('Malformed CSV quotation.');
    } else if(!quoted && (c===',' || c==='\n' || c==='\r')){
      row.push(field.trim());field='';closed=false;
      if(c!==','){if(row.some(Boolean)) rows.push(row);row=[];if(c==='\r' && text[i+1]==='\n')i++;}
    } else {if(closed && c.trim()) throw new DomainError('Unexpected text after a quoted CSV field.');field+=c;}
  }
  if(quoted) throw new DomainError('CSV contains an unclosed quote.');
  row.push(field.trim());if(row.some(Boolean))rows.push(row);
  if(rows.length<2) throw new DomainError('The CSV must include a header and at least one data row.');
  const headers=rows.shift()!.map(h=>h.toLowerCase());
  if(new Set(headers).size!==headers.length || headers.some(h=>!h)) throw new DomainError('CSV headers must be unique and non-empty.');
  if(rows.length>1000) throw new DomainError('Import up to 1,000 rows at a time.');
  return rows.map((r,i)=>{if(r.length!==headers.length)throw new DomainError(`Row ${i+2} has ${r.length} columns; expected ${headers.length}.`);return Object.fromEntries(headers.map((h,j)=>[h,r[j]]));});
}
export function csvCell(value:unknown):string {
  let s=String(value??''); if(/^[\s]*[=+@\-\t\r]/.test(s))s="'"+s;
  return '"'+s.replaceAll('"','""')+'"';
}
export function exportCSV(headers:string[], rows:unknown[][]) {return '\uFEFF'+[headers,...rows].map(r=>r.map(csvCell).join(',')).join('\r\n');}
