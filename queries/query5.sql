SELECT
  A.AHID          AS id_acordo,
  A.AHSTATUS      AS status,
  CASE
    WHEN A.AHDTCANC IS NOT NULL THEN 'CANCELADO'
    WHEN A.AHDTQB   IS NOT NULL THEN 'QUEBRADO'
    ELSE 'INDEFINIDO'
  END             AS tipo_encerramento,
  COALESCE(A.AHDTCANC, A.AHDTQB) AS dt_encerramento,
  A.AHDSCQB       AS motivo_quebra,
  A.AHCOLLID      AS assessoria,
  A.AHFORMAPAG    AS meio_pagamento,
  A.AHTOTPMT      AS vl_total_acordo,
  A.AHACCT        AS nr_contrato,
  A.AHACCTG       AS nr_grupo
FROM RCVRY.AGRHDR A
WHERE A.AHSTATUS = 'C'
  AND TRUNC(COALESCE(A.AHDTCANC, A.AHDTQB)) >= TRUNC(SYSDATE) - 45
ORDER BY dt_encerramento DESC