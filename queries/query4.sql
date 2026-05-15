SELECT
  A.AHID        AS id_acordo,
  A.AHDT        AS dt_criacao,
  A.AHSTATUS    AS status,
  A.AHCOLLID    AS assessoria,
  A.AHFORMAPAG  AS meio_pagamento,
  A.AHTOTPMT    AS vl_total_acordo,
  A.AHACCT      AS nr_contrato,
  A.AHACCTG     AS nr_grupo
FROM RCVRY.AGRHDR A
WHERE TRUNC(A.AHDT) >= TRUNC(SYSDATE) - 45
ORDER BY A.AHDT DESC