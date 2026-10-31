import { assessAccess, captureEvidence, isoDaysAgo, type Snapshot, type Review } from './domain';

export function createSeed(workspace:string, now=new Date()):Snapshot & {sourceAccess:Record<string,unknown>[]} {
  const id=(key:string)=>`${workspace}:${key}`, at=(days:number)=>isoDaysAgo(days,now), today=now.toISOString();
  const data:Snapshot & {sourceAccess:Record<string,unknown>[]}={identities:[],sources:[],accounts:[],entitlements:[],grants:[],reviews:[],remediations:[],policies:[],audits:[],campaigns:[],sourceAccess:[]};
  const people=[
    ['Hashan Hirantha','Engineering','Cloud Engineer'],['Maya Perera','Engineering','Engineering Manager'],['Daniel Silva','Security','Security Lead'],['Alex Morgan','Compliance','Internal Auditor'],
    ['Nimal Jayawardena','Finance','Financial Analyst'],['Kavindi Fernando','Marketing','Marketing Executive'],['Chamath Wijesinghe','Engineering','Platform Engineer'],['Sarah Mitchell','Finance','Finance Manager'],
    ['Dinuka Rathnayake','Operations','Operations Analyst'],['Amaya Senanayake','Engineering','Software Engineer'],['Ravindu Madushan','Engineering','DevOps Engineer'],['Emma Wilson','Marketing','Brand Manager'],
    ['Tharushi De Silva','Finance','Accountant'],['Kasun Bandara','Engineering','Backend Engineer'],['Olivia Chen','Security','Security Analyst'],['Isuru Dissanayake','Operations','IT Administrator'],
    ['Nethmi Gunasekara','Marketing','Content Strategist'],['Liam Anderson','Engineering','Frontend Engineer'],['Sahan Kumara','Finance','Payments Specialist'],['Ayesha Hassan','Compliance','Risk Analyst'],
    ['Dulani Peiris','Operations','Service Coordinator'],['Noah Williams','Engineering','QA Engineer'],['Yasith Perera','Engineering','Data Engineer'],['Sophie Taylor','Marketing','Product Designer'],
    ['Malith Karunaratne','Operations','Support Engineer'],['Hiruni Wickramasinghe','Finance','Financial Analyst'],['Ryan Thomas','Engineering','Site Reliability Engineer'],['Anjali Raman','Security','IAM Analyst'],
    ['Pasindu Lakshan','Marketing','Campaign Analyst'],['Zara Ahmed','Operations','Project Coordinator'],['Ashen Silva','Engineering','Software Engineer'],['Emily Brown','Compliance','Compliance Analyst'],
  ];
  people.forEach(([name,department,jobTitle],i)=>data.identities.push({id:id(`EMP${String(i+1).padStart(3,'0')}`),employeeId:`EMP${String(i+1).padStart(3,'0')}`,name,email:name.toLowerCase().replaceAll(' ','.')+'@northstar.example',department,jobTitle,managerId:id(i===1?'EMP003':i===7?'EMP003':department==='Finance'?'EMP008':'EMP002'),status:[4,18].includes(i)?'terminated':i===20?'leave':i===8?'contractor':'active',contractEnd:i===8?at(12):null}));
  data.sources=[
    {id:id('hr'),name:'People directory',category:'Human resources',icon:'people',lastSync:at(0.04),status:'healthy',mode:'Synthetic directory'},
    {id:id('aws'),name:'AWS IAM',category:'Cloud infrastructure',icon:'aws',lastSync:at(0.08),status:'healthy',mode:'Mock connector'},
    {id:id('github'),name:'GitHub Enterprise',category:'Source control',icon:'github',lastSync:at(0.06),status:'healthy',mode:'Mock connector'},
    {id:id('finance'),name:'Finance ERP',category:'Business application',icon:'finance',lastSync:at(0.12),status:'healthy',mode:'Mock connector'},
    {id:id('m365'),name:'Microsoft 365',category:'Productivity',icon:'microsoft',lastSync:at(0.1),status:'healthy',mode:'Mock connector'},
  ];
  const permissions:[string,string,boolean,string[]][]=[
    ['aws','ReadOnlyAccess',false,['*']],['aws','AdministratorAccess',true,['Engineering','Security']],['aws','BillingAdmin',true,['Finance']],
    ['github','Repository read',false,['*']],['github','Organization owner',true,['Engineering','Security']],['github','Repository write',false,['*']],
    ['finance','View reports',false,['*']],['finance','Approve payments',true,['Finance']],['finance','Manage payroll',true,['Finance']],
    ['m365','Standard user',false,['*']],['m365','Global administrator',true,['Operations','Security']],
  ];
  permissions.forEach(([source,name,privileged,allowedDepartments],i)=>data.entitlements.push({id:id(`ent${i}`),sourceId:id(source),name,privileged,allowedDepartments}));
  data.identities.forEach((person,i)=>{
    const appKeys=['m365',i%3===0?'aws':i%3===1?'github':'finance'];
    if(i===5)appKeys.push('finance');
    [...new Set(appKeys)].forEach((app,j)=>{
      const account={id:id(`acc-${i}-${app}`),sourceId:id(app),identityId:person.id,externalId:person.email.split('@')[0],kind:'user',status:'enabled',lastActive:i%7===6?at(124+i):at(i%8+0.2),createdAt:at(240)};
      data.accounts.push(account);
      const available=data.entitlements.filter(e=>e.sourceId===id(app));
      const selected=[available[0]];
      if(i%4===0 || i%7===6 || i===5 || i===8)selected.push(available[1]);
      selected.forEach((ent,k)=>{const grant={id:id(`grant-${i}-${app}-${k}`),accountId:account.id,entitlementId:ent.id,state:'active',expiresAt:i===13 && k===1?at(4):null,version:1};data.grants.push(grant);data.sourceAccess.push({id:grant.id,grantId:grant.id,state:'active',version:1,updatedAt:today});});
    });
  });
  const orphan={id:id('acc-orphan'),sourceId:id('aws'),identityId:null,externalId:'legacy.admin',kind:'user',status:'enabled',lastActive:at(106),createdAt:at(300)};
  const service={id:id('acc-service'),sourceId:id('github'),identityId:null,externalId:'ci-deployment-bot',kind:'service',status:'enabled',lastActive:null,createdAt:at(300)};
  data.accounts.push(orphan,service);
  [orphan,service].forEach((a,i)=>{const g={id:id(`grant-special-${i}`),accountId:a.id,entitlementId:id(i===0?'ent1':'ent5'),state:'active',expiresAt:null,version:1};data.grants.push(g);data.sourceAccess.push({id:g.id,grantId:g.id,state:'active',version:1,updatedAt:today});});
  const policyData=[
    ['LEAVER','Departed employees','Flag enabled accounts belonging to employees who have left.',0],
    ['INACTIVE','Inactive access','Review human accounts with no successful application activity.',90],
    ['ORPHANED','Unverified account owners','Investigate human accounts without a verified employee mapping.',0],
    ['ROLE_MISMATCH','Privileged role mismatch','Compare privileged permissions with approved department baselines.',0],
    ['CONTRACT','Expired contractors','Flag access retained beyond a contractor end date.',0],
    ['EXPIRED','Expired temporary access','Review temporary grants after their approved expiry date.',0],
  ] as const;
  data.policies=policyData.map(([code,name,description,threshold])=>({id:id(`policy-${code}`),code,name,description,threshold,enabled:true}));
  const campaign={id:id('campaign-initial'),name:'Quarterly access certification',startedAt:at(6),dueAt:at(-7)};data.campaigns.push(campaign);
  data.grants.forEach(g=>{
    const a=data.accounts.find(x=>x.id===g.accountId)!,ent=data.entitlements.find(x=>x.id===g.entitlementId)!,source=data.sources.find(x=>x.id===a.sourceId)!;
    const person=data.identities.find(x=>x.id===a.identityId);
    const finding=assessAccess(person,a,ent,g,source,data.policies,today);
    if(!finding)return;
    const review:Review={id:id(`review-${data.reviews.length+1}`),grantId:g.id,campaignId:campaign.id,assigneeId:person?.managerId??id('EMP003'),...finding,status:'pending',note:'',firstActor:null,proposal:null,decisionId:null,snapshotVersion:1,sourceSnapshotAt:source.lastSync,evidence:captureEvidence(person,a,ent,g,source,data.policies),exceptionUntil:null,dueAt:campaign.dueAt,createdAt:at(6-data.reviews.length%5),decidedAt:null,version:1};
    data.reviews.push(review);
  });
  // Historical synthetic decisions are clearly scoped to the demo seed.
  const history=data.reviews.filter(r=>r.severity!=='critical').slice(-6);
  history.forEach((r,i)=>{
    r.status='keep';r.note='Demo historical review: owner confirmed a documented business requirement.';r.decidedAt=at(5-i);r.version=2;
    data.audits.push({id:id(`audit-historical-${i}`),actor:'Maya Perera',principal:'synthetic-seed',action:'Access retained',target:r.id,detail:r.note,createdAt:r.decidedAt});
  });
  data.audits.push({id:id('audit-seed'),actor:'AccessGuard',principal:'synthetic-seed',action:'Workspace initialized',target:'Demo environment',detail:'Synthetic people, source accounts and review evidence loaded. No live enterprise systems are connected.',createdAt:today});
  return data;
}
