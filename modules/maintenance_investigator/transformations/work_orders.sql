-- Development transformation. Adjust column names if the RAW table schema differs.
SELECT
  external_id AS externalId,
  title AS title,
  description AS description,
  work_type AS workType,
  priority AS priority,
  status AS status,
  failure_mode AS failureMode,
  cause AS cause,
  corrective_action AS correctiveAction
FROM
  `maint_inv_demo`.`work_orders`;
