import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
import os
import traceback
from log_execucao import registrar
from imagens_utils import expurgar, garantir_pastas

# ── Configurações ──────────────────────────────────────────────────────────────
CSV_PATH  = r"C:\Revamp Monitoramento\Query 6 (RCVRY)_Consulta do SQL personalizado.csv"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── Expurgo dos PNGs anteriores ───────────────────────────────────────────────
expurgar("grafico_q6_")
garantir_pastas()

PNG_PATH  = rf"C:\Revamp Monitoramento\imagens\grafico_q6_{TIMESTAMP}.png"
TS_FILE   = r"C:\Revamp Monitoramento\ultimo_timestamp_q6.txt"

# ── De-para de assessorias ─────────────────────────────────────────────────────
DE_PARA = {
    '009': 'Cobrança Interna', '010': 'Paschoallotto', '013': 'PLC',
    '015': 'Portal QuintoAndar', '016': 'QA Salesforce Esp.', '017': 'TRC',
    '018': 'Bulgarelli', '019': 'Meet Call', '020': 'Pellon', '021': 'Monest',
    '022': 'Gondim', '023': 'Novaquest', '024': 'VZL', '025': 'ASL',
    '026': 'SLN', '124': 'Bulgarelli Evictions',
    '997': 'Suspensão Cobrança', '998': 'Não Cobrar', 'SERASA': 'Serasa',
}

GRUPOS = {
    'Collections': ['TRC', 'Bulgarelli', 'Meet Call', 'Novaquest', 'Paschoallotto',
                    'Cobrança Interna', 'Portal QuintoAndar', 'QA Salesforce Esp.', 'Serasa', 'Monest'],
    'Evictions':   ['Pellon', 'Gondim', 'PLC', 'VZL', 'SLN', 'ASL', 'Bulgarelli Evictions'],
    'Inibidas':    ['Não Cobrar', 'Suspensão Cobrança'],
}

COR_GRUPO  = {'Collections': '#1F3864', 'Evictions': '#843C0C', 'Inibidas': '#595959'}
ORDEM_PLOT = ['Inibidas', 'Evictions', 'Collections']  # invertido p/ barh (0 = baixo)
GAP        = 1.5

COR_SEM    = '#4472C4'
COR_ACORDO = '#ED7D31'
COR_SEP    = '#555555'

# ── Funções auxiliares ─────────────────────────────────────────────────────────
def normalizar_agency(cod):
    cod = str(cod).strip()
    base_num = cod.lstrip('G')
    for t in [base_num.zfill(3), base_num, base_num.lstrip('0') or '0']:
        if t in DE_PARA:
            return DE_PARA[t]
    return base_num.lstrip('0') or base_num

def get_grupo(nome):
    for g, membros in GRUPOS.items():
        if nome in membros:
            return g
    return 'Collections'

def fmt_valor(v):
    if v >= 1_000_000: return f'R${v/1_000_000:.1f}M'
    elif v >= 1_000:   return f'R${v/1_000:.0f}K'
    return f'R${v:.0f}'

def fmt_qtd(q): return f'{int(q):,}'.replace(',', '.')
def fmt_pct(p): return f'{p:.1f}%'

def montar_posicoes(pivot_q, pivot_v, sort_col, ordem_grupos, gap):
    rows_q, rows_v, labels, grupos, posicoes = [], [], [], [], []
    cur_y = 0
    for gi, g in enumerate(ordem_grupos):
        mask  = pivot_q.index.get_level_values('GRUPO') == g
        sub_q = pivot_q[mask].sort_values(sort_col, ascending=True)
        sub_v = pivot_v[mask].reindex(sub_q.index)
        for (grp, nome) in sub_q.index:
            labels.append(nome)
            grupos.append(grp)
            posicoes.append(cur_y)
            rows_q.append(sub_q.loc[(grp, nome)])
            rows_v.append(sub_v.loc[(grp, nome)])
            cur_y += 1
        if gi < len(ordem_grupos) - 1:
            cur_y += gap
    return labels, grupos, posicoes, rows_q, rows_v

def draw_subplot(fig, ax, labels, grupos, posicoes, rows_q, rows_v,
                 fmt_bar_sem, fmt_bar_ac, fmt_total, total_grupo_dict, xlabel, title):

    sem_vals       = np.array([r['Sem Acordo']       for r in rows_q])
    acordo_vals    = np.array([r['Com Acordo Ativo'] for r in rows_q])
    vl_sem_vals    = np.array([r['Sem Acordo']       for r in rows_v])
    vl_acordo_vals = np.array([r['Com Acordo Ativo'] for r in rows_v])
    pos = np.array(posicoes)

    ax.barh(pos, sem_vals,    height=0.6, color=COR_SEM,    zorder=2)
    ax.barh(pos, acordo_vals, left=sem_vals, height=0.6, color=COR_ACORDO, zorder=2)

    ax.set_yticks(pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_title(title, fontsize=10, fontweight='bold', pad=10)

    total_max = (sem_vals + acordo_vals).max()
    ax.set_xlim(0, total_max * 1.8)
    ax.set_ylim(-0.8, max(posicoes) + 0.8)

    grupo_atual = None
    grupo_inicio, grupo_fim = {}, {}
    for i, g in enumerate(grupos):
        if g != grupo_atual:
            if grupo_atual is not None:
                sep_y = (posicoes[i] + posicoes[i-1]) / 2
                ax.axhline(sep_y, color='#BBBBBB', linewidth=1.2, linestyle='--', zorder=1)
            grupo_inicio[g] = posicoes[i]
            grupo_atual = g
        grupo_fim[g] = posicoes[i]
    ax._grupo_info = {'inicio': grupo_inicio, 'fim': grupo_fim}

    fig.canvas.draw()
    renderer    = fig.canvas.get_renderer()
    scale       = ax.get_xlim()[1] - ax.get_xlim()[0]
    ax_width_px = ax.get_window_extent(renderer).width

    for i in range(len(labels)):
        g        = grupos[i]
        v_sem    = sem_vals[i]
        v_acordo = acordo_vals[i]
        vl_sem   = vl_sem_vals[i]
        vl_ac    = vl_acordo_vals[i]
        total    = v_sem + v_acordo
        vl_total = vl_sem + vl_ac
        pct      = (total / total_grupo_dict.get(g, 1) * 100)

        x0 = total + total_max * 0.015
        partes = [
            (fmt_bar_sem(v_sem),         COR_SEM,    True),
            (' / ',                      COR_SEP,    False),
            (fmt_bar_ac(v_acordo),       COR_ACORDO, True),
            (' / ',                      COR_SEP,    False),
            (fmt_pct(pct),               COR_SEP,    True),
            (' / ',                      COR_SEP,    False),
            (f'({fmt_total(vl_total)})', COR_SEP,    False),
        ]
        cur_x = x0
        for txt, cor, bold in partes:
            t = ax.text(cur_x, posicoes[i], txt, va='center', ha='left', fontsize=6.5,
                        color=cor, fontweight='bold' if bold else 'normal', zorder=3)
            fig.canvas.draw()
            bb = t.get_window_extent(renderer=renderer)
            cur_x += bb.width / ax_width_px * scale

# ── Leitura e preparação ───────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH, sep=None, engine='python')
df.columns = df.columns.str.replace('\ufeff', '').str.strip()
df['ASSESSORIA'] = df['ASSESSORIA'].astype(str).str.strip()
df['ASSESSORIA_NOME'] = df['ASSESSORIA'].apply(normalizar_agency)
df = df[df['ASSESSORIA_NOME'].notna() & (df['ASSESSORIA_NOME'] != 'nan')]
df['GRUPO'] = df['ASSESSORIA_NOME'].apply(get_grupo)

agg = df.groupby(['GRUPO', 'ASSESSORIA_NOME', 'SITUACAO_ACORDO']).agg(
    qtd=('NR_CONTRATO', 'count'),
    vl=('VL_PRINCIPAL_VENCIDO', 'sum')
).reset_index()

pivot_qtd = agg.pivot_table(index=['GRUPO','ASSESSORIA_NOME'], columns='SITUACAO_ACORDO',
                             values='qtd', aggfunc='sum').fillna(0)
pivot_vl  = agg.pivot_table(index=['GRUPO','ASSESSORIA_NOME'], columns='SITUACAO_ACORDO',
                             values='vl', aggfunc='sum').fillna(0)

for col in ['Sem Acordo', 'Com Acordo Ativo']:
    if col not in pivot_qtd.columns: pivot_qtd[col] = 0
    if col not in pivot_vl.columns:  pivot_vl[col]  = 0

total_qtd_grupo = (pivot_qtd['Sem Acordo'] + pivot_qtd['Com Acordo Ativo']).groupby(level='GRUPO').sum()
total_vl_grupo  = (pivot_vl['Sem Acordo']  + pivot_vl['Com Acordo Ativo']).groupby(level='GRUPO').sum()

labels1, grupos1, pos1, rows_q1, rows_v1 = montar_posicoes(pivot_qtd, pivot_vl, 'Sem Acordo', ORDEM_PLOT, GAP)
labels2, grupos2, pos2, rows_q2, rows_v2 = montar_posicoes(pivot_vl,  pivot_vl, 'Sem Acordo', ORDEM_PLOT, GAP)

# ── Figura ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(22, 11))
fig.patch.set_facecolor('#F5F5F5')
DATA_HOJE = datetime.now().strftime('%d/%m/%Y')

for ax in axes:
    ax.set_facecolor('#FFFFFF')
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.grid(axis='x', color='#E0E0E0', linewidth=0.5, zorder=0)

draw_subplot(fig, axes[0], labels1, grupos1, pos1, rows_q1, rows_v1,
             fmt_qtd, fmt_qtd, fmt_valor,
             {g: total_qtd_grupo.get(g, 1) for g in ORDEM_PLOT},
             'Quantidade de Contratos', 'Qtd. de Contratos por Assessoria')

draw_subplot(fig, axes[1], labels2, grupos2, pos2, rows_q2, rows_v2,
             fmt_valor, fmt_valor, fmt_valor,
             {g: total_vl_grupo.get(g, 1) for g in ORDEM_PLOT},
             'Saldo em Atraso (R$)', 'Saldo em Atraso por Assessoria')

axes[1].xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, _: f'R${x/1_000_000:.0f}M' if x >= 1_000_000 else f'R${x/1_000:.0f}K'
))

# ── Métricas para log ─────────────────────────────────────────────────────────
_df_log = pd.read_csv(CSV_PATH, sep=None, engine='python')
_df_log.columns = _df_log.columns.str.replace('\ufeff', '').str.strip()
_qtd_log = len(_df_log)
_vl_log  = float(_df_log['VL_PRINCIPAL_VENCIDO'].sum()) if 'VL_PRINCIPAL_VENCIDO' in _df_log.columns else 0.0

try:
    # ── Títulos de grupo no espaço central ────────────────────────────────────
    fig.canvas.draw()
    bbox1 = axes[0].get_position()
    bbox2 = axes[1].get_position()
    x_mid = (bbox1.x1 + bbox2.x0) / 2

    for g in ['Collections', 'Evictions', 'Inibidas']:
        info = axes[0]._grupo_info
        if g not in info['inicio']:
            continue
        y_mid_data = (info['inicio'][g] + info['fim'][g]) / 2
        y_mid_disp = axes[0].transData.transform((0, y_mid_data))[1]
        y_mid_fig  = fig.transFigure.inverted().transform((0, y_mid_disp))[1]
        fig.text(x_mid, y_mid_fig, g,
                 ha='center', va='center', fontsize=9,
                 fontweight='bold', color=COR_GRUPO[g], rotation=90,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5F5F5',
                           edgecolor=COR_GRUPO[g], linewidth=1.2))

    # ── Legenda e título ───────────────────────────────────────────────────────
    patch_sem    = mpatches.Patch(color=COR_SEM,    label='Sem Acordo')
    patch_acordo = mpatches.Patch(color=COR_ACORDO, label='Com Acordo Ativo')
    fig.legend(handles=[patch_sem, patch_acordo], loc='lower center',
               ncol=2, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.005))

    fig.suptitle(f'M6 · Distribuição para Assessorias — Foto Atual ({DATA_HOJE})',
                 fontsize=13, fontweight='bold', y=0.99)

    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    plt.subplots_adjust(wspace=0.35)

    # ── Salvar ─────────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
    plt.savefig(PNG_PATH, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()

    with open(TS_FILE, 'w') as f:
        f.write(TIMESTAMP)

    registrar(
        monitoramento = "M6",
        timestamp     = TIMESTAMP,
        status        = "ok",
        qtd_contratos = _qtd_log,
        vl_total      = _vl_log,
        pngs          = {"m6": os.path.basename(PNG_PATH)},
    )
    print(f"Gráfico salvo em: {PNG_PATH}")

except Exception:
    registrar(
        monitoramento = "M6",
        timestamp     = TIMESTAMP,
        status        = "erro",
        qtd_contratos = _qtd_log,
        vl_total      = _vl_log,
        erro          = traceback.format_exc(),
    )
    raise
