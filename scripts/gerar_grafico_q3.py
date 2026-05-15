import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import pandas as pd
import glob
import json
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from log_execucao import registrar
from imagens_utils import expurgar, garantir_pastas, IMG_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

arquivos = glob.glob(os.path.join(BASE_DIR, 'Query 3*.csv')) + \
           glob.glob(os.path.join(BASE_DIR, 'Query_3*.csv'))
if not arquivos:
    raise FileNotFoundError('Nenhum arquivo CSV com "Query 3" encontrado na pasta.')
CSV_PATH = max(arquivos, key=os.path.getmtime)
print(f'Lendo: {os.path.basename(CSV_PATH)}')

TIMESTAMP       = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S")
TIMESTAMP_LABEL = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
TS_FILE         = os.path.join(BASE_DIR, 'ultimo_timestamp_q3.txt')

# ── Expurgo dos PNGs anteriores ───────────────────────────────────────────────
expurgar("grafico_q3_")
garantir_pastas()

OUTPUT_PATH = os.path.join(IMG_DIR, f'grafico_q3_{TIMESTAMP}.png')

# --- Métricas para log ---
_df_log = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
_qtd_log = len(_df_log)
_vl_log  = float(_df_log['VL_PAGAMENTO'].sum()) if 'VL_PAGAMENTO' in _df_log.columns else 0.0

# --- Leitura e tratamento ---
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
df['DT_PAGAMENTO'] = pd.to_datetime(df['DT_PAGAMENTO'], dayfirst=False)
df['DATA'] = df['DT_PAGAMENTO'].dt.normalize()

meio_map   = {0: 'Não Identificado', 1: 'Boleto', 2: 'Pix', 3: 'Cartão'}
origem_map = {'PC': 'Acordo', 'PE': 'Espontâneo', 'CC': 'Campanha'}

df['MEIO_LABEL']   = pd.to_numeric(df['MEIO_PAGAMENTO'], errors='coerce').map(meio_map).fillna('Outro')
df['ORIGEM_LABEL'] = df['ORIGEM'].map(origem_map).fillna(df['ORIGEM'])

todas_datas = pd.date_range(df['DATA'].min(), df['DATA'].max(), freq='D')

meios   = ['Boleto', 'Pix', 'Cartão', 'Não Identificado']
cores   = {'Boleto': '#378ADD', 'Pix': '#27AE60', 'Cartão': '#E67E22', 'Não Identificado': '#BDC3C7'}
origens_plot = ['Espontâneo', 'Acordo']

text_main  = '#3d3d3a'
text_muted = '#5F5E5A'
grid_color = '#EBEBEB'
fds_color  = '#F5F5F0'

def fmt_vl_eixo(v, _):
    if v >= 1e6: return f'R$ {v/1e6:.1f}M'
    if v >= 1e3: return f'R$ {v/1e3:.0f}K'
    return f'R$ {v:.0f}'

def fmt_vl_label(v):
    if v >= 1e6: return f'{v/1e6:.1f}M'
    if v >= 1e3: return f'{v/1e3:.0f}K'
    return f'{v:.0f}'

fig, axes = plt.subplots(2, 1, figsize=(22, 12), sharex=False)
fig.patch.set_facecolor('#FFFFFF')

fig.text(0.02, 0.98, 'Pagamentos por Meio — Histórico 45 dias',
         fontsize=13, fontweight='bold', color=text_main, va='top', ha='left')
fig.text(0.02, 0.955, f'Gerado em {TIMESTAMP_LABEL}',
         fontsize=9, color=text_muted, va='top', ha='left')

for ax, origem in zip(axes, origens_plot):
    ax.set_facecolor('#FFFFFF')
    ax.set_title(f'Pagamento {origem}', fontsize=11, fontweight='bold',
                 color=text_main, loc='left', pad=8)

    df_orig = df[df['ORIGEM_LABEL'] == origem]
    agg = df_orig.groupby(['DATA', 'MEIO_LABEL'])['VL_PAGAMENTO'].sum().reset_index()
    pivot = agg.pivot(index='DATA', columns='MEIO_LABEL', values='VL_PAGAMENTO')
    pivot = pivot.reindex(todas_datas).fillna(0)
    pivot.index = pd.to_datetime(pivot.index)

    for data in todas_datas:
        if data.weekday() >= 5:
            ax.axvspan(data - timedelta(hours=12), data + timedelta(hours=12),
                       color=fds_color, zorder=0, lw=0)

    for meio in meios:
        if meio not in pivot.columns:
            continue
        linha = pivot[meio]
        ax.plot(pivot.index, linha, label=meio, color=cores[meio],
                linewidth=1.8, marker='o', markersize=4, zorder=3)
        for data, val in linha.items():
            if data.weekday() < 5 and val > 0:
                ax.annotate(fmt_vl_label(val), xy=(data, val), xytext=(0, 6),
                            textcoords='offset points', ha='center', fontsize=6,
                            color=cores[meio], zorder=4)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_vl_eixo))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, ha='right', fontsize=7)
    ax.tick_params(axis='y', labelsize=9, colors=text_main)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#DDDDD5')
    ax.yaxis.grid(True, color=grid_color, linewidth=0.6, zorder=1)
    ax.set_axisbelow(True)
    ax.set_xlim(todas_datas[0] - timedelta(hours=12), todas_datas[-1] + timedelta(hours=12))
    ax.legend(loc='upper right', fontsize=9, framealpha=0.7)

try:
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor='#FFFFFF')
    plt.close()

    # ── Gravar timestamp como JSON (padrão do projeto) ────────────────────────
    meta = {'timestamp': TIMESTAMP, 'pngs': {'m3': f'grafico_q3_{TIMESTAMP}.png'}}
    with open(TS_FILE, 'w') as f:
        json.dump(meta, f)

    registrar(
        monitoramento = "M3",
        timestamp     = TIMESTAMP,
        status        = "ok",
        qtd_contratos = _qtd_log,
        vl_total      = _vl_log,
        pngs          = {"m3": os.path.basename(OUTPUT_PATH)},
    )
    print(f'Gráfico salvo em: {OUTPUT_PATH}')

except Exception:
    registrar(
        monitoramento = "M3",
        timestamp     = TIMESTAMP,
        status        = "erro",
        qtd_contratos = _qtd_log,
        vl_total      = _vl_log,
        erro          = traceback.format_exc(),
    )
    raise
