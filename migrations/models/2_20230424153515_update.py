from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "task" DROP COLUMN "position";
        ALTER TABLE "category" DROP CONSTRAINT IF EXISTS "ut_idx_category_owner_i_ff07be";
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_owner_i_47cd8a";
        DROP INDEX IF EXISTS "idx_worklog_owner_i_4e7f9a";
        DROP INDEX IF EXISTS "idx_worklog_task_id_c3e84d";
        DROP INDEX IF EXISTS "ut_idx_task_positio_c2f0de";
        DROP INDEX IF EXISTS "ut_idx_task_name_c03182";
        DROP INDEX IF EXISTS "ut_idx_category_name_c2d674";
        DROP INDEX IF EXISTS "idx_worklog_date_ad0eec";
        DROP INDEX IF EXISTS "idx_worklog_date_c06645";
        ALTER TABLE "category" ADD CONSTRAINT "ut_idx_category_owner_i_ff07be" UNIQUE ("owner_id", "name") DEFERRABLE INITIALLY IMMEDIATE;;
        ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_owner_i_47cd8a" UNIQUE ("owner_id", "name") DEFERRABLE INITIALLY IMMEDIATE;;
        CREATE INDEX "idx_worklog_date_ad0eec" ON "worklog" USING BRIN ("date", "owner_id");;
        CREATE INDEX "idx_worklog_date_c06645" ON "worklog" USING BRIN ("date", "task_id");;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "ut_idx_category_owner_i_ff07be";
        DROP INDEX "idx_worklog_date_c06645";
        DROP INDEX "idx_worklog_date_ad0eec";
        DROP INDEX "ut_idx_task_owner_i_47cd8a";
        ALTER TABLE "task" ADD "position" INT NOT NULL;
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_name_c03182";ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_name_c03182" UNIQUE ("name", "owner_id") DEFERRABLE INITIALLY IMMEDIATE;;
        ALTER TABLE "task" DROP CONSTRAINT IF EXISTS "ut_idx_task_positio_c2f0de";ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_positio_c2f0de" UNIQUE ("position", "owner_id") DEFERRABLE INITIALLY IMMEDIATE;;
        CREATE INDEX "idx_worklog_task_id_c3e84d" ON "worklog" USING BRIN ("task_id", "date");;
        CREATE INDEX "idx_worklog_owner_i_4e7f9a" ON "worklog" USING BRIN ("owner_id", "date");;
        ALTER TABLE "category" DROP CONSTRAINT IF EXISTS "ut_idx_category_name_c2d674";ALTER TABLE "category" ADD CONSTRAINT "ut_idx_category_name_c2d674" UNIQUE ("name", "owner_id") DEFERRABLE INITIALLY IMMEDIATE;;"""
