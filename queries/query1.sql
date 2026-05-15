SELECT

  A.DMACCT       AS nr_contrato,

  A.DMACCTG      AS nr_grupo,

  A.DMQUE        AS segmento,

  A.DMDAYS       AS dias_atraso,

  A.DMAMTDLQ     AS vl_principal_vencido,

  A.DMAGENCY     AS assessoria,

  B.U1CT3        AS audiencia

FROM RCVRY.DELQMST A

JOIN RCVRY.UDA1 B

  ON A.DMACCT  = B.U1ACCT

 AND A.DMACCTG = B.U1ACCTG

WHERE A.DMSTATUS IS NULL

  AND A.DMDAYS > 0

ORDER BY A.DMQUE, A.DMAMTDLQ DESC