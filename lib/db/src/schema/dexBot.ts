import {
  bigint,
  boolean,
  index,
  integer,
  numeric,
  pgTable,
  serial,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

const timestamps = {
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
};

export const walletsTable = pgTable(
  "wallets",
  {
    id: serial("id").primaryKey(),
    blockchain: text("blockchain").notNull(),
    currency: text("currency").notNull(),
    address: text("address").notNull(),
    rotationOrder: integer("rotation_order").default(0).notNull(),
    active: boolean("active").default(true).notNull(),
    lastAssignedAt: timestamp("last_assigned_at", { withTimezone: true }),
    createdAt: timestamps.createdAt,
  },
  (table) => [
    uniqueIndex("wallets_blockchain_address_idx").on(
      table.blockchain,
      table.address,
    ),
    index("wallets_blockchain_active_idx").on(table.blockchain, table.active),
  ],
);

export const walletAssignmentsTable = pgTable(
  "wallet_assignments",
  {
    id: serial("id").primaryKey(),
    telegramUserId: bigint("telegram_user_id", { mode: "number" }).notNull(),
    blockchain: text("blockchain").notNull(),
    walletId: integer("wallet_id")
      .notNull()
      .references(() => walletsTable.id),
    assignedAt: timestamp("assigned_at", { withTimezone: true })
      .defaultNow()
      .notNull(),
  },
  (table) => [
    index("wallet_assignments_user_idx").on(table.telegramUserId),
    index("wallet_assignments_wallet_idx").on(table.walletId),
  ],
);

export const paymentsTable = pgTable(
  "payments",
  {
    id: serial("id").primaryKey(),
    telegramUserId: bigint("telegram_user_id", { mode: "number" }).notNull(),
    service: text("service").notNull(),
    platform: text("platform").notNull(),
    tier: text("tier").notNull(),
    blockchain: text("blockchain").notNull(),
    currency: text("currency").notNull(),
    tokenAddress: text("token_address").notNull(),
    tokenName: text("token_name"),
    expectedAmount: numeric("expected_amount", {
      precision: 30,
      scale: 18,
    }).notNull(),
    expectedAmountText: text("expected_amount_text").notNull(),
    recipientAddress: text("recipient_address").notNull(),
    transactionHash: text("transaction_hash"),
    status: text("status").default("awaiting_hash").notNull(),
    verificationAttempts: integer("verification_attempts").default(0).notNull(),
    lastCheckedAt: timestamp("last_checked_at", { withTimezone: true }),
    confirmedAt: timestamp("confirmed_at", { withTimezone: true }),
    failureReason: text("failure_reason"),
    fulfillmentStatus: text("fulfillment_status"),
    fulfillmentQueuedAt: timestamp("fulfillment_queued_at", {
      withTimezone: true,
    }),
    ...timestamps,
  },
  (table) => [
    index("payments_telegram_user_idx").on(table.telegramUserId),
    uniqueIndex("payments_transaction_hash_idx").on(table.transactionHash),
  ],
);

export const bannedUsersTable = pgTable(
  "banned_users",
  {
    telegramUserId: bigint("telegram_user_id", { mode: "number" })
      .primaryKey(),
    reason: text("reason"),
    bannedAt: timestamp("banned_at", { withTimezone: true })
      .defaultNow()
      .notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .defaultNow()
      .notNull(),
  },
);

export type Wallet = typeof walletsTable.$inferSelect;
export type WalletAssignment = typeof walletAssignmentsTable.$inferSelect;
export type Payment = typeof paymentsTable.$inferSelect;
export type BannedUser = typeof bannedUsersTable.$inferSelect;