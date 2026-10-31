import { sqliteTable, text, integer, index, uniqueIndex } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const workspaces = sqliteTable('workspaces', {
  id: text('id').primaryKey(), createdAt: text('createdAt').notNull(), name: text('name').notNull(),
});
const workspaceId = () => text('workspaceId').notNull().references(() => workspaces.id);
export const identities = sqliteTable('identities', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), employeeId: text('employeeId').notNull(),
  name: text('name').notNull(), email: text('email').notNull(), department: text('department').notNull(),
  jobTitle: text('jobTitle').notNull(), managerId: text('managerId'), status: text('status').notNull(), contractEnd: text('contractEnd'),
}, t => [index('identities_workspace').on(t.workspaceId)]);
export const sources = sqliteTable('sources', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), name: text('name').notNull(),
  category: text('category').notNull(), icon: text('icon').notNull(), lastSync: text('lastSync').notNull(), status: text('status').notNull(), mode: text('mode').notNull(),
});
export const accounts = sqliteTable('accounts', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), sourceId: text('sourceId').notNull().references(() => sources.id),
  identityId: text('identityId').references(() => identities.id), externalId: text('externalId').notNull(),
  kind: text('kind').notNull(), status: text('status').notNull(), lastActive: text('lastActive'), createdAt: text('createdAt').notNull(),
}, t => [index('accounts_workspace').on(t.workspaceId)]);
export const entitlements = sqliteTable('entitlements', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), sourceId: text('sourceId').notNull().references(() => sources.id),
  name: text('name').notNull(), privileged: integer('privileged', {mode:'boolean'}).notNull(), allowedDepartments: text('allowedDepartments').notNull(),
});
export const grants = sqliteTable('grants', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), accountId: text('accountId').notNull().references(() => accounts.id),
  entitlementId: text('entitlementId').notNull().references(() => entitlements.id), state: text('state').notNull(), expiresAt: text('expiresAt'), version: integer('version').notNull(),
}, t => [index('grants_workspace_state').on(t.workspaceId, t.state)]);
export const sourceAccess = sqliteTable('source_access', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), grantId: text('grantId').notNull().references(() => grants.id),
  state: text('state').notNull(), version: integer('version').notNull(), updatedAt: text('updatedAt').notNull(),
});
export const campaigns = sqliteTable('campaigns', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), name: text('name').notNull(), startedAt: text('startedAt').notNull(), dueAt: text('dueAt').notNull(),
});
export const reviews = sqliteTable('reviews', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), grantId: text('grantId').notNull().references(() => grants.id),
  campaignId: text('campaignId').notNull().references(() => campaigns.id), assigneeId: text('assigneeId').notNull(),
  score: integer('score').notNull(), severity: text('severity').notNull(), reasons: text('reasons').notNull(), codes: text('codes').notNull(), recommendation: text('recommendation').notNull(), status: text('status').notNull(),
  note: text('note').notNull(), firstActor: text('firstActor'), proposal: text('proposal'), decisionId: text('decisionId'),
  snapshotVersion: integer('snapshotVersion').notNull(), sourceSnapshotAt: text('sourceSnapshotAt').notNull(), evidence: text('evidence').notNull().default('{}'), exceptionUntil: text('exceptionUntil'),
  dueAt: text('dueAt').notNull(), createdAt: text('createdAt').notNull(), decidedAt: text('decidedAt'), version: integer('version').notNull(),
}, t => [index('reviews_workspace_status').on(t.workspaceId, t.status), index('reviews_grant').on(t.grantId), uniqueIndex('reviews_one_open_per_grant').on(t.grantId).where(sql`${t.status} IN ('pending','investigation','awaiting_second')`)]);
export const remediations = sqliteTable('remediations', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), reviewId: text('reviewId').notNull().references(() => reviews.id), grantId: text('grantId').notNull().references(() => grants.id), status: text('status').notNull(),
  attempts: integer('attempts').notNull(), expectedVersion: integer('expectedVersion').notNull(), error: text('error'), evidence: text('evidence'), leaseUntil: text('leaseUntil'), createdAt: text('createdAt').notNull(), verifiedAt: text('verifiedAt'),
});
export const policies = sqliteTable('policies', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), code: text('code').notNull(), name: text('name').notNull(), description: text('description').notNull(), enabled: integer('enabled', {mode:'boolean'}).notNull(), threshold: integer('threshold').notNull(),
});
export const audits = sqliteTable('audits', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), actor: text('actor').notNull(), principal: text('principal').notNull(), action: text('action').notNull(), target: text('target').notNull(), detail: text('detail').notNull(), createdAt: text('createdAt').notNull(),
}, t => [index('audits_workspace_date').on(t.workspaceId, t.createdAt)]);
export const imports = sqliteTable('imports', {
  id: text('id').primaryKey(), workspaceId: workspaceId(), checksum: text('checksum').notNull(), filename: text('filename').notNull(), kind: text('kind').notNull(), rowCount: integer('rowCount').notNull(), createdAt: text('createdAt').notNull(),
});
