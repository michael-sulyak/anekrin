-- upgrade --
ALTER TABLE "task" ADD CONSTRAINT "ut_idx_task_owner_i_47cd8a" UNIQUE ("owner_id", "name") DEFERRABLE INITIALLY IMMEDIATE;;
