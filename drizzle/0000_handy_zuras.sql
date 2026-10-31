CREATE TABLE `accounts` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`sourceId` text NOT NULL,
	`identityId` text,
	`externalId` text NOT NULL,
	`kind` text NOT NULL,
	`status` text NOT NULL,
	`lastActive` text,
	`createdAt` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`sourceId`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`identityId`) REFERENCES `identities`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `accounts_workspace` ON `accounts` (`workspaceId`);--> statement-breakpoint
CREATE TABLE `audits` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`actor` text NOT NULL,
	`principal` text NOT NULL,
	`action` text NOT NULL,
	`target` text NOT NULL,
	`detail` text NOT NULL,
	`createdAt` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `audits_workspace_date` ON `audits` (`workspaceId`,`createdAt`);--> statement-breakpoint
CREATE TABLE `campaigns` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`name` text NOT NULL,
	`startedAt` text NOT NULL,
	`dueAt` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `entitlements` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`sourceId` text NOT NULL,
	`name` text NOT NULL,
	`privileged` integer NOT NULL,
	`allowedDepartments` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`sourceId`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `grants` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`accountId` text NOT NULL,
	`entitlementId` text NOT NULL,
	`state` text NOT NULL,
	`expiresAt` text,
	`version` integer NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`accountId`) REFERENCES `accounts`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`entitlementId`) REFERENCES `entitlements`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `grants_workspace_state` ON `grants` (`workspaceId`,`state`);--> statement-breakpoint
CREATE TABLE `identities` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`employeeId` text NOT NULL,
	`name` text NOT NULL,
	`email` text NOT NULL,
	`department` text NOT NULL,
	`jobTitle` text NOT NULL,
	`managerId` text,
	`status` text NOT NULL,
	`contractEnd` text,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `identities_workspace` ON `identities` (`workspaceId`);--> statement-breakpoint
CREATE TABLE `imports` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`checksum` text NOT NULL,
	`filename` text NOT NULL,
	`kind` text NOT NULL,
	`rowCount` integer NOT NULL,
	`createdAt` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `policies` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`code` text NOT NULL,
	`name` text NOT NULL,
	`description` text NOT NULL,
	`enabled` integer NOT NULL,
	`threshold` integer NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `remediations` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`reviewId` text NOT NULL,
	`grantId` text NOT NULL,
	`status` text NOT NULL,
	`attempts` integer NOT NULL,
	`expectedVersion` integer NOT NULL,
	`error` text,
	`evidence` text,
	`createdAt` text NOT NULL,
	`verifiedAt` text,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`reviewId`) REFERENCES `reviews`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`grantId`) REFERENCES `grants`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `reviews` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`grantId` text NOT NULL,
	`campaignId` text NOT NULL,
	`assigneeId` text NOT NULL,
	`score` integer NOT NULL,
	`severity` text NOT NULL,
	`reasons` text NOT NULL,
	`codes` text NOT NULL,
	`recommendation` text NOT NULL,
	`status` text NOT NULL,
	`note` text NOT NULL,
	`firstActor` text,
	`proposal` text,
	`decisionId` text,
	`snapshotVersion` integer NOT NULL,
	`sourceSnapshotAt` text NOT NULL,
	`exceptionUntil` text,
	`dueAt` text NOT NULL,
	`createdAt` text NOT NULL,
	`decidedAt` text,
	`version` integer NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`grantId`) REFERENCES `grants`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`campaignId`) REFERENCES `campaigns`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `reviews_workspace_status` ON `reviews` (`workspaceId`,`status`);--> statement-breakpoint
CREATE INDEX `reviews_grant` ON `reviews` (`grantId`);--> statement-breakpoint
CREATE TABLE `source_access` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`grantId` text NOT NULL,
	`state` text NOT NULL,
	`version` integer NOT NULL,
	`updatedAt` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`grantId`) REFERENCES `grants`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `sources` (
	`id` text PRIMARY KEY NOT NULL,
	`workspaceId` text NOT NULL,
	`name` text NOT NULL,
	`category` text NOT NULL,
	`icon` text NOT NULL,
	`lastSync` text NOT NULL,
	`status` text NOT NULL,
	`mode` text NOT NULL,
	FOREIGN KEY (`workspaceId`) REFERENCES `workspaces`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `workspaces` (
	`id` text PRIMARY KEY NOT NULL,
	`createdAt` text NOT NULL,
	`name` text NOT NULL
);
