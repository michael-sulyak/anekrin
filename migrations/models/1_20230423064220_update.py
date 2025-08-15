from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_worklog_task_id_c3e84d";
        DROP INDEX "idx_worklog_owner_i_4e7f9a";
        
        
        CREATE TABLE IF NOT EXISTS "category" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "owner_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_category_owner_i_7711ac" ON "category" ("owner_id");
ALTER TABLE "category" DROP CONSTRAINT IF EXISTS "ut_idx_category_owner_i_ff07be";ALTER TABLE "category" ADD CONSTRAINT "ut_idx_category_owner_i_ff07be" UNIQUE ("owner_id", "name") DEFERRABLE INITIALLY IMMEDIATE;;
        ALTER TABLE "task" ADD "category_id" BIGINT;
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_owner_i_47cd8a";ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_owner_i_47cd8a" UNIQUE ("owner_id", "name") DEFERRABLE INITIALLY IMMEDIATE;;
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_positio_c2f0de";ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_positio_c2f0de" UNIQUE ("position", "owner_id") DEFERRABLE INITIALLY IMMEDIATE;;
        CREATE INDEX "idx_task_categor_a04949" ON "task" ("category_id");
        ALTER TABLE "task" ADD CONSTRAINT "fk_task_category_1e9bf928" FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON DELETE SET NULL;
        CREATE INDEX "idx_task_owner_i_460aaa" ON "task" ("owner_id");
        CREATE INDEX "idx_worklog_date_ad0eec" ON "worklog" USING BRIN ("date", "owner_id");;
        CREATE INDEX "idx_worklog_date_c06645" ON "worklog" USING BRIN ("date", "task_id");;
        CREATE INDEX "idx_worklog_task_id_413e77" ON "worklog" ("task_id");
        CREATE INDEX "idx_worklog_owner_i_01cddc" ON "worklog" ("owner_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_worklog_owner_i_01cddc";
        DROP INDEX "idx_worklog_task_id_413e77";
        DROP INDEX "idx_worklog_date_c06645";
        DROP INDEX "idx_worklog_date_ad0eec";
        DROP INDEX "idx_task_owner_i_460aaa";
        ALTER TABLE "task" DROP CONSTRAINT "fk_task_category_1e9bf928";
        DROP INDEX "idx_task_categor_a04949";
        DROP INDEX "ut_idx_task_positio_c2f0de";
        DROP INDEX "ut_idx_task_owner_i_47cd8a";
        ALTER TABLE "task" DROP COLUMN "category_id";
        DROP TABLE IF EXISTS "category";
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_owner_i_63c12d";ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_owner_i_63c12d" UNIQUE ("owner_id", "position") DEFERRABLE INITIALLY IMMEDIATE;;
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_owner_i_47cd8a";ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_owner_i_47cd8a" UNIQUE ("owner_id", "name") DEFERRABLE INITIALLY IMMEDIATE;;
        CREATE INDEX "idx_worklog_owner_i_4e7f9a" ON "worklog" USING BRIN ("owner_id", "date");;
        CREATE INDEX "idx_worklog_task_id_c3e84d" ON "worklog" USING BRIN ("task_id", "date");;"""
