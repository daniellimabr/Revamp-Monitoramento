SELECT
  A.DMACCT        AS nr_contrato,
  A.DMACCTG       AS nr_grupo,
  A.DMAGENCY      AS assessoria,
  A.DMQUE         AS segmento,
  A.DMDAYS        AS dias_atraso,
  A.DMAMTDLQ      AS vl_principal_vencido,
  B.U1CT3         AS audiencia,
  CASE
    WHEN C.AHSTATUS IN ('A','P') THEN 'Com Acordo Ativo'
    ELSE 'Sem Acordo'
  END             AS situacao_acordo,
  C.AHID          AS id_acordo,
  C.AHSTATUS      AS status_acordo
FROM RCVRY.DELQMST A
JOIN RCVRY.UDA1 B
  ON A.DMACCT  = B.U1ACCT
 AND A.DMACCTG = B.U1ACCTG
LEFT JOIN (
  SELECT ADACCT, MAX(ADAHID) AS ADAHID
  FROM RCVRY.AGRDM D
  JOIN RCVRY.AGRHDR H
    ON D.ADAHID = H.AHID
   AND H.AHSTATUS IN ('A','P')
  GROUP BY ADACCT
) D ON A.DMACCT = D.ADACCT
LEFT JOIN RCVRY.AGRHDR C
  ON D.ADAHID = C.AHID
WHERE A.DMSTATUS IS NULL
  AND A.DMDAYS > 0
ORDER BY B.U1CT3, A.DMAGENCY, A.DMAMTDLQ DESC