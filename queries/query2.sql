SELECT
  H.HD_ACCT                   AS nr_contrato,
  H.HD_ACCTG                  AS nr_grupo,
  H.HD_CRIT_SELECAO           AS segmento,
  H.HD_ASSESSORIA             AS assessoria,
  H.HD_DIASATRASO             AS dias_atraso,
  H.HD_VL_DIVIDA              AS vl_principal_vencido,
  H.HD_DT_DISPONIBILIZACAO    AS dt_entrada,
  B.U1CT3                     AS u1ct3
FROM RCVRY.TB_HISTORICO_DISPONIBILIZACAO H
JOIN RCVRY.UDA1 B
  ON H.HD_ACCT  = B.U1ACCT
 AND H.HD_ACCTG = B.U1ACCTG
WHERE TRUNC(H.HD_DT_DISPONIBILIZACAO) = TRUNC(SYSDATE)
ORDER BY H.HD_CRIT_SELECAO, H.HD_VL_DIVIDA DESC