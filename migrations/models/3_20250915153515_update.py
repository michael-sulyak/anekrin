from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
           DROP INDEX "idx_worklog_date_c06645";
           DROP INDEX "idx_worklog_date_ad0eec";
           CREATE INDEX "idx_worklog_date_ad0eec" ON "worklog" USING BRIN ("date", "owner_id");
           CREATE INDEX "idx_worklog_date_c06645" ON "worklog" USING BRIN ("date", "task_id");
           """
