SELECT
  P.PMACCT        AS nr_contrato,
  P.PMACCTG       AS nr_grupo,
  P.PMEDATE       AS dt_pagamento,
  P.PMTCODE       AS origem,
  P.PMBATCH       AS meio_pagamento,
  P.PMTAMT        AS vl_pagamento
FROM RCVRY.PMTFIL P
WHERE P.PMEDATE >= TRUNC(SYSDATE) - 45
  AND P.PMTAMT IS NOT NULL
ORDER BY P.PMEDATE DESC, P.PMACCT