-- upgrade --
ALTER TABLE "worklog" ADD "type" VARCHAR(20) NOT NULL DEFAULT 'user_work';

UPDATE worklog
SET name = '', type = 'bonus'
WHERE worklog.name = 'Bonus for good work';
