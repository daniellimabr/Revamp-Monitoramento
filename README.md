# Revamp Monitoramento - Cyber / QuintoAndar

Automacao do batimento diario de cobranca. Scripts Python que leem CSVs exportados do CyberVision, geram graficos e enviam cards para o Google Chat via webhook.

## Estrutura

```
scripts/   - Scripts Python de geracao de graficos e envio ao Google Chat
queries/   - Queries SQL validadas por monitoramento
```

## Como usar

```bash
cd "C:\Revamp Monitoramento"
python rodar_monitoramento.py
```

## Monitoramentos

| # | Nome | Status |
|---|------|--------|
| M1 | Contratos por Segmento (foto atual) | OK |
| M2 | Entradas no Dia por Segmento | OK |
| M3 | Pagamentos por Meio (45 dias) | OK |
| M4 | Acordos Criados por Assessoria (45 dias) | OK |
| M5 | Acordos Cancelados e Quebrados (45 dias) | OK |
| M6 | Distribuicao para Assessorias (foto atual) | OK |
| M7 | Distribuicao por Assessoria x Audiencia (foto atual) | OK |
| M8 | Novas Distribuicoes do Dia por Audiencia | Em desenvolvimento |

## Convencoes

- CSVs: exportados manualmente do CyberVision, nao versionados
- Imagens: geradas localmente em `imagens/`, nao versionadas
- Expurgo: PNGs anteriores movidos automaticamente para `imagens/expurgo/`
- Timestamps: gravados como JSON em `ultimo_timestamp_qN.txt`
