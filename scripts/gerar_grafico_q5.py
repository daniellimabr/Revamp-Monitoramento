import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import traceback
from log_execucao import registrar
from imagens_utils import expurgar, garantir_pastas, IMG_DIR

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE_DIR, "Query 5 (RCVRY)_Consulta do SQL personalizado.csv")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
TS_FILE   = os.path.join(BASE_DIR, "ultimo_timestamp_q5.txt")

# ── Expurgo dos PNGs anteriores ───────────────────────────────────────────────
expurgar("grafico_q5_cancelados_")
expurgar("grafico_q5_quebrados_")
garantir_pastas()

OUTPUT_CANC = os.path.join(IMG_DIR, f"grafico_q5_cancelados_{TIMESTAMP}.png")
OUTPUT_QUEB = os.path.join(IMG_DIR, f"grafico_q5_quebrados_{TIMESTAMP}.png")

# --- Métricas para log ---
_df_log = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
_qtd_log = len(_df_log)
_vl_log  = float(_df_log['VL_TOTAL_ACORDO'].sum()) if 'VL_TOTAL_ACORDO' in _df_log.columns else 0.0

ASSESSORIA_MAP = {
    'PortalQA': 'Portal QuintoAndar', 'QA_PASCH': 'Paschoallotto',
    'QA_TRC': 'TRC', 'QA_GRB': 'Bulgarelli', 'QA_Meetc': 'Meet Call',
    'QA_BGREV': 'Bulgarelli Evictions', 'QA_GODIM': 'Gondim',
    'QA_Pell': 'Pellon', 'QA_NovaQ': 'Novaquest', 'QA_PLC': 'PLC',
    'QA_PASEV': 'Paschoallotto Evictions', 'SERASA': 'Serasa', 'SISTEMA': 'Sistema',
}
PORTAL = 'Portal QuintoAndar'
CORES = {
    'Portal QuintoAndar': '#185FA5', 'Paschoallotto': '#0F6E56',
    'TRC': '#993C1D', 'Bulgarelli': '#BA7517', 'Meet Call': '#534AB7',
    'Bulgarelli Evictions': '#1D7A8A', 'Gondim': '#0F6E6E',
    'Pellon': '#A32D2D', 'Novaquest': '#3B6D11', 'PLC': '#6B3A9E',
    'Paschoallotto Evictions': '#8A6D0F', 'Serasa': '#993556',
    'Sistema': '#555555', 'Time Interno': '#888780',
}

def fmt_M(v):
    if v >= 1_000_000: return f'R${v/1_000_000:.1f}M'
    if v >= 1_000:     return f'R${v/1_000:.0f}K'
    return f'R${v:.0f}'

def fmt_num(v):
    return f'{int(v):,}'.replace(',', '.')

def eixo_x_todas_datas(ax, datas):
    ax.set_xticks(datas)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.tick_params(axis='x', rotation=90, labelsize=6.5)

def destacar_fds(ax, datas):
    for dt in datas:
        if dt.weekday() >= 5:
            ax.axvspan(dt - timedelta(hours=12), dt + timedelta(hours=12),
                       color='#CCCCCC', alpha=0.25, zorder=0, linewidth=0)

def anotar_ponto(ax, dt, qtd, saldo):
    ax.annotate(f'{fmt_num(int(qtd))}\n{fmt_M(saldo)}',
                xy=(dt, qtd), xytext=(0, 7), textcoords='offset points',
                ha='center', va='bottom', fontsize=5.5, color='#444441', linespacing=1.4)

def reindexar_45d(pivot, data_min, data_max):
    idx_completo = pd.date_range(data_min, data_max, freq='D')
    pivot.index = pd.to_datetime(pivot.index)
    return pivot.reindex(idx_completo, fill_value=0)

def gerar_grafico(pivot_qtd, pivot_saldo, datas, cols_s2_ord,
                  titulo_tipo, cor_total, output_path):
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.size': 9,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.grid': True, 'grid.alpha': 0.25, 'grid.linestyle': '--',
        'figure.facecolor': 'white', 'axes.facecolor': 'white',
    })
    fig, axes = plt.subplots(3, 1, figsize=(16, 18), sharex=False)
    fig.subplots_adjust(hspace=0.65, top=0.94, bottom=0.05, left=0.07, right=0.95)
    titulo_data = datetime.today().strftime('%d/%m/%Y')
    fig.suptitle(f'M5 — Acordos {titulo_tipo} por Assessoria  |  45 dias  |  gerado em {titulo_data}',
                 fontsize=12, fontweight='bold', y=0.97)

    ax1 = axes[0]
    qtd_total, saldo_total = pivot_qtd['TOTAL'].values, pivot_saldo['TOTAL'].values
    destacar_fds(ax1, datas)
    ax1.plot(datas, qtd_total, color=cor_total, linewidth=2.0, marker='o', markersize=3, zorder=5)
    for i, (dt, qtd, saldo) in enumerate(zip(datas, qtd_total, saldo_total)):
        if qtd == 0 or i % 2 != 0: continue
        anotar_ponto(ax1, dt, qtd, saldo)
    ax1.set_title(f'Total de acordos {titulo_tipo.lower()} (todas as assessorias)',
                  fontsize=10, fontweight='bold', loc='left', pad=6)
    ax1.set_ylabel('Qtd. acordos', fontsize=8)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_num(x)))
    eixo_x_todas_datas(ax1, datas)

    ax2 = axes[1]
    destacar_fds(ax2, datas)
    for ass in cols_s2_ord:
        if ass not in pivot_qtd.columns: continue
        serie_qtd = pivot_qtd[ass].values
        cor = CORES.get(ass, '#888888')
        ax2.plot(datas, serie_qtd, color=cor, linewidth=1.4, alpha=0.9, label=ass, zorder=4)
        qtd_max = serie_qtd.max()
        if qtd_max > 0:
            idx_pico = serie_qtd.argmax()
            ax2.annotate(fmt_num(int(qtd_max)),
                         xy=(datas[idx_pico], qtd_max), xytext=(0, 5),
                         textcoords='offset points', ha='center', va='bottom',
                         fontsize=5.5, color=cor, fontweight='bold')
    ax2.set_title('Assessorias e Time Interno (excl. Portal QuintoAndar)',
                  fontsize=10, fontweight='bold', loc='left', pad=6)
    ax2.set_ylabel('Qtd. acordos', fontsize=8)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_num(x)))
    eixo_x_todas_datas(ax2, datas)
    ax2.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=7.5,
               frameon=True, framealpha=0.9, edgecolor='#cccccc', ncol=1, handlelength=1.2)

    ax3 = axes[2]
    destacar_fds(ax3, datas)
    if PORTAL in pivot_qtd.columns:
        qtd_portal, saldo_portal = pivot_qtd[PORTAL].values, pivot_saldo[PORTAL].values
        ax3.plot(datas, qtd_portal, color=CORES[PORTAL], linewidth=2.0, marker='o', markersize=3, zorder=5)
        for i, (dt, qtd, saldo) in enumerate(zip(datas, qtd_portal, saldo_portal)):
            if qtd == 0 or i % 2 != 0: continue
            anotar_ponto(ax3, dt, qtd, saldo)
    ax3.set_title('Portal QuintoAndar', fontsize=10, fontweight='bold', loc='left', pad=6)
    ax3.set_ylabel('Qtd. acordos', fontsize=8)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: fmt_num(x)))
    eixo_x_todas_datas(ax3, datas)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"OK: {output_path}")

# --- LEITURA ---
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
df.columns = df.columns.str.strip()
df['ASSESSORIA']        = df['ASSESSORIA'].str.strip()
df['TIPO_ENCERRAMENTO'] = df['TIPO_ENCERRAMENTO'].str.strip()
df['DT_ENCERRAMENTO']   = pd.to_datetime(df['DT_ENCERRAMENTO'], format='%m/%d/%Y %I:%M:%S %p')
df['DATA']              = df['DT_ENCERRAMENTO'].dt.date
df['LABEL']             = df['ASSESSORIA'].apply(lambda r: ASSESSORIA_MAP.get(r, 'Time Interno'))

data_min = pd.to_datetime(df['DATA'].min())
data_max = pd.to_datetime(df['DATA'].max())

pngs_gerados = {}

for tipo, titulo, cor_total, output, chave in [
    ('CANCELADO', 'Cancelados', '#993C1D', OUTPUT_CANC, 'cancelados'),
    ('QUEBRADO',  'Quebrados',  '#534AB7', OUTPUT_QUEB, 'quebrados'),
]:
    df_tipo = df[df['TIPO_ENCERRAMENTO'] == tipo].copy()
    if df_tipo.empty:
        print(f"Sem dados para {tipo}, pulando.")
        continue

    agg = df_tipo.groupby(['DATA', 'LABEL']).agg(
        QTD=('ID_ACORDO', 'count'),
        SALDO=('VL_TOTAL_ACORDO', 'sum')
    ).reset_index()

    pivot_qtd   = agg.pivot_table(index='DATA', columns='LABEL', values='QTD',   fill_value=0)
    pivot_saldo = agg.pivot_table(index='DATA', columns='LABEL', values='SALDO', fill_value=0)

    pivot_qtd   = reindexar_45d(pivot_qtd,   data_min, data_max)
    pivot_saldo = reindexar_45d(pivot_saldo, data_min, data_max)

    pivot_qtd['TOTAL']   = pivot_qtd.sum(axis=1)
    pivot_saldo['TOTAL'] = pivot_saldo.sum(axis=1)

    datas = pivot_qtd.index
    cols_s2 = [c for c in pivot_qtd.columns if c not in ['TOTAL', PORTAL]]
    totais_s2 = {c: int(pivot_qtd[c].sum()) for c in cols_s2 if c in pivot_qtd.columns}
    cols_s2_ord = sorted(totais_s2.keys(), key=lambda c: -totais_s2[c])

    try:
        gerar_grafico(pivot_qtd, pivot_saldo, datas, cols_s2_ord, titulo, cor_total, output)
        pngs_gerados[chave] = os.path.basename(output)
    except Exception:
        registrar(
            monitoramento = "M5",
            timestamp     = TIMESTAMP,
            status        = "erro",
            qtd_contratos = _qtd_log,
            vl_total      = _vl_log,
            erro          = traceback.format_exc(),
        )
        raise

# ── Gravar timestamp como JSON (padrão do projeto) ────────────────────────────
meta = {'timestamp': TIMESTAMP, 'pngs': pngs_gerados}
with open(TS_FILE, 'w') as f:
    json.dump(meta, f)

registrar(
    monitoramento = "M5",
    timestamp     = TIMESTAMP,
    status        = "ok",
    qtd_contratos = _qtd_log,
    vl_total      = _vl_log,
    pngs          = pngs_gerados,
)
