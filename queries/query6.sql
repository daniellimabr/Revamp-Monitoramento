SELECT
  A.DMACCT        AS nr_contrato,
  A.DMACCTG       AS nr_grupo,
  A.DMAGENCY      AS assessoria,
  A.DMQUE         AS segmento,
  A.DMDAYS        AS dias_atraso,
  A.DMAMTDLQ      AS vl_principal_vencido,
  CASE 
    WHEN B.AHSTATUS IN ('A','P') THEN 'Com Acordo Ativo'
    ELSE 'Sem Acordo'
  END             AS situacao_acordo,
  B.AHID          AS id_acordo,
  B.AHSTATUS      AS status_acordo
FROM RCVRY.DELQMST A
LEFT JOIN (
  SELECT ADACCT, MAX(ADAHID) AS ADAHID
  FROM RCVRY.AGRDM D
  JOIN RCVRY.AGRHDR H
    ON D.ADAHID = H.AHID
   AND H.AHSTATUS IN ('A','P')
  GROUP BY ADACCT
) D ON A.DMACCT = D.ADACCT
LEFT JOIN RCVRY.AGRHDR B
  ON D.ADAHID = B.AHID
WHERE A.DMSTATUS IS NULL
  AND A.DMDAYS > 0
ORDER BY A.DMAGENCY, A.DMAMTDLQ DESC