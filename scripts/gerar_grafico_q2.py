import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['text.usetex'] = False
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import glob
import json
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from matplotlib.gridspec import GridSpec
from log_execucao import registrar
from imagens_utils import expurgar, garantir_pastas, IMG_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

arquivos = glob.glob(os.path.join(BASE_DIR, 'Query 2*.csv')) + \
           glob.glob(os.path.join(BASE_DIR, 'Query_2*.csv'))
if not arquivos:
    raise FileNotFoundError('Nenhum arquivo CSV com "Query 2" encontrado na pasta.')
CSV_PATH = max(arquivos, key=os.path.getmtime)
print(f'Lendo: {os.path.basename(CSV_PATH)}')

TIMESTAMP       = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S")
TIMESTAMP_LABEL = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
TS_FILE         = os.path.join(BASE_DIR, 'ultimo_timestamp_q2.txt')

# ── Expurgo dos PNGs anteriores ───────────────────────────────────────────────
expurgar("grafico_q2_")
garantir_pastas()

# ── De-para e grupos de assessorias ───────────────────────────────────────────
DE_PARA = {
    '009':'Cobrança Interna','010':'Paschoallotto','013':'PLC',
    '015':'Portal QuintoAndar','016':'QA Salesforce Esp.','017':'TRC',
    '018':'Bulgarelli','019':'Meet Call','020':'Pellon','021':'Monest',
    '022':'Gondim','023':'Novaquest','024':'VZL','025':'ASL',
    '026':'SLN','124':'Bulgarelli Evictions',
    '997':'Suspensão Cobrança','998':'Não Cobrar','SERASA':'Serasa',
}
GRUPOS_ASSESS = {
    'Collections':['TRC','Bulgarelli','Meet Call','Novaquest','Paschoallotto',
                   'Cobrança Interna','Portal QuintoAndar','QA Salesforce Esp.','Serasa','Monest'],
    'Evictions':  ['Pellon','Gondim','PLC','VZL','SLN','ASL','Bulgarelli Evictions'],
    'Inibidas':   ['Não Cobrar','Suspensão Cobrança'],
}
COR_GRUPO  = {'Collections':'#1F3864','Evictions':'#843C0C','Inibidas':'#595959'}
ORDEM_PLOT = ['Inibidas','Evictions','Collections']

# ── Grupos de segmentos -> PNGs ────────────────────────────────────────────────
GRUPOS_SEG = {
    'a': ['ATFX','ATEQ','ATPJ','AONB','XONB','OV15'],
    'b': ['EVIC'],
    'c': ['FINA'],
    'd': ['ADD','CVIP','NCOB','PADM','PAFR','PALE','SFAT','SSEG','XMUL'],
}

GAP=1.2; COR_BAR='#4472C4'; COR_TOTAL='#AAAAAA'; COR_SEP='#555555'; HSPACE=0.7

def normalizar_agency(cod):
    cod=str(cod).strip(); b=cod.lstrip('G')
    for t in [b.zfill(3),b,b.lstrip('0') or '0']:
        if t in DE_PARA: return DE_PARA[t]
    return b.lstrip('0') or b

def get_grupo(nome):
    for g,m in GRUPOS_ASSESS.items():
        if nome in m: return g
    return 'Collections'

def fmt_valor(v):
    if v>=1_000_000: return f'R${v/1_000_000:.1f}M'
    elif v>=1_000:   return f'R${v/1_000:.0f}K'
    return f'R${v:.0f}'
def fmt_qtd(q): return f'{int(q):,}'.replace(',','.')
def fmt_pct(p): return f'{p:.1f}%'
def txt(ax,x,y,s,**kw): return ax.text(x,y,s,parse_math=False,**kw)

def draw_ax(ax, df_seg, is_qtd, xlabel, total_seg_qtd, total_seg_vl):
    agg = df_seg.groupby(['GRUPO','ASSESSORIA_NOME']).agg(
        qtd=('NR_CONTRATO','count'),
        vl=('VL_PRINCIPAL_VENCIDO','sum')
    ).reset_index()

    rows, labels, grupos, posicoes = [], [], [], []
    cur_y = 0
    for gi, g in enumerate(ORDEM_PLOT):
        sub = agg[agg['GRUPO']==g].sort_values('qtd' if is_qtd else 'vl', ascending=True)
        for _, row in sub.iterrows():
            labels.append(row['ASSESSORIA_NOME']); grupos.append(g)
            posicoes.append(cur_y); rows.append(row); cur_y += 1
        if gi < len(ORDEM_PLOT)-1 and len(sub) > 0: cur_y += GAP

    if not posicoes: return {}

    vals = np.array([r['qtd'] if is_qtd else r['vl'] for r in rows])
    vls  = np.array([r['vl'] for r in rows])
    pos  = np.array(posicoes)

    total_bar = total_seg_qtd if is_qtd else total_seg_vl
    total_max = max(total_bar, vals.max() if len(vals) > 0 else 1, 1)
    pos_total = max(posicoes) + GAP

    ax.barh(pos_total, total_bar, height=0.55, color=COR_TOTAL, zorder=2)
    ax.axhline(pos_total-GAP/2, color='#BBBBBB', linewidth=0.8, linestyle='--', zorder=1)
    txt(ax, total_bar+total_max*0.015, pos_total,
        f'{(fmt_qtd if is_qtd else fmt_valor)(total_bar)}  /  100%  /  ({fmt_valor(total_seg_vl)})',
        va='center', ha='left', fontsize=5.5, color=COR_SEP, zorder=3)
    txt(ax, 0, pos_total, 'TOTAL ',
        va='center', ha='right', fontsize=5.5, color='#333333', fontweight='bold', zorder=3)

    ax.barh(pos, vals, height=0.55, color=COR_BAR, zorder=2)
    ax.set_yticks(list(pos)+[pos_total])
    ax.set_yticklabels(labels+[''], fontsize=7)
    ax.set_xlabel(xlabel, fontsize=7)
    ax.set_facecolor('#FFFFFF')
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.grid(axis='x', color='#E0E0E0', linewidth=0.4, zorder=0)
    ax.set_xlim(0, total_max*1.85)
    ax.set_ylim(-0.7, pos_total+0.7)

    if is_qtd:
        ax.xaxis.set_major_formatter(plt.FuncFormatter(
            lambda x,_: f'{int(x):,}'.replace(',','.')))
    else:
        ax.xaxis.set_major_formatter(plt.FuncFormatter(
            lambda x,_: f'R${x/1_000_000:.0f}M' if x>=1_000_000 else f'R${x/1_000:.0f}K'))

    grupo_atual=None; gi_map,gf_map={},{}
    for i,g in enumerate(grupos):
        if g!=grupo_atual:
            if grupo_atual is not None:
                ax.axhline((posicoes[i]+posicoes[i-1])/2,
                           color='#BBBBBB', linewidth=0.8, linestyle='--', zorder=1)
            gi_map[g]=posicoes[i]; grupo_atual=g
        gf_map[g]=posicoes[i]

    denom = total_seg_qtd if is_qtd else total_seg_vl
    for i in range(len(labels)):
        v=vals[i]; vl=vls[i]
        pct=(v/denom*100) if denom>0 else 0
        fmt_v=fmt_qtd if is_qtd else fmt_valor
        lbl=f'{fmt_v(v)}  /  {fmt_pct(pct)}  /  ({fmt_valor(vl)})'
        txt(ax, v+total_max*0.015, posicoes[i], lbl,
            va='center', ha='left', fontsize=5.5, color=COR_SEP, zorder=3)

    return {'inicio':gi_map,'fim':gf_map}

def gerar_png(df_sub, ordem_segs, titulo, png_path):
    n = len(ordem_segs)
    alturas = []
    for seg in ordem_segs:
        na = df_sub[df_sub['SEGMENTO']==seg]['ASSESSORIA_NOME'].nunique()
        alturas.append(max(3,na)*0.45+1.5)

    h_medio=sum(alturas)/len(alturas)
    TITULO_H=HSPACE*h_medio; LEGENDA_H=0.6
    total_h=TITULO_H+sum(alturas)+LEGENDA_H

    fig=plt.figure(figsize=(22,total_h))
    fig.patch.set_facecolor('#F5F5F5')
    top_frac=1.0-TITULO_H/total_h; bottom_frac=LEGENDA_H/total_h

    gs=GridSpec(n+1,2,figure=fig,height_ratios=alturas+[LEGENDA_H],
                hspace=HSPACE,wspace=0.35,top=top_frac,bottom=bottom_frac)

    for row_idx,seg in enumerate(ordem_segs):
        df_seg=df_sub[df_sub['SEGMENTO']==seg]
        total_seg_qtd=float(len(df_seg))
        total_seg_vl=float(df_seg['VL_PRINCIPAL_VENCIDO'].sum())

        ax1=fig.add_subplot(gs[row_idx,0]); ax2=fig.add_subplot(gs[row_idx,1])
        gi1=draw_ax(ax1,df_seg,True, 'Qtd. Contratos',       total_seg_qtd,total_seg_vl)
        gi2=draw_ax(ax2,df_seg,False,'Saldo em Atraso (R$)', total_seg_qtd,total_seg_vl)
        ax1.set_title(
            f'{seg}  —  {fmt_qtd(int(total_seg_qtd))} contratos  /  {fmt_valor(total_seg_vl)}',
            fontsize=8,fontweight='bold',loc='left',pad=4,color='#111111')

        if gi1:
            fig.canvas.draw()
            bbox1=ax1.get_position(); bbox2=ax2.get_position()
            x_mid=(bbox1.x1+bbox2.x0)/2
            for g in ['Collections','Evictions','Inibidas']:
                if g not in gi1['inicio']: continue
                y_mid=(gi1['inicio'][g]+gi1['fim'][g])/2
                yd=ax1.transData.transform((0,y_mid))[1]
                yf=fig.transFigure.inverted().transform((0,yd))[1]
                fig.text(x_mid,yf,g[0],ha='center',va='center',fontsize=6,
                         fontweight='bold',color=COR_GRUPO[g],rotation=90,
                         bbox=dict(boxstyle='round,pad=0.2',facecolor='#F5F5F5',
                                   edgecolor=COR_GRUPO[g],linewidth=0.8))

    ax_leg=fig.add_subplot(gs[n,:]); ax_leg.set_axis_off()
    patch_bar  =mpatches.Patch(color=COR_BAR,   label='Assessoria')
    patch_total=mpatches.Patch(color=COR_TOTAL, label='Total do Segmento')
    ax_leg.legend(handles=[patch_bar,patch_total],loc='center',ncol=2,fontsize=11,
                  frameon=True,facecolor='#F5F5F5',edgecolor='#CCCCCC',
                  bbox_to_anchor=(0.5,0.5))

    fig.suptitle(titulo,fontsize=12,fontweight='bold',
                 y=top_frac+(TITULO_H/total_h)/2,parse_math=False)

    os.makedirs(IMG_DIR,exist_ok=True)
    plt.savefig(png_path,dpi=120,bbox_inches='tight',facecolor=fig.get_facecolor())
    plt.close()
    print(f'  OK: {os.path.basename(png_path)} ({n} subplots)')

# ── Main ───────────────────────────────────────────────────────────────────────
df=pd.read_csv(CSV_PATH,sep=None,engine='python')
df.columns=df.columns.str.replace('\ufeff','').str.strip()
df['ASSESSORIA_NOME']=df['ASSESSORIA'].astype(str).apply(normalizar_agency)
df=df[df['ASSESSORIA_NOME'].notna()&(df['ASSESSORIA_NOME']!='nan')]
df['GRUPO']=df['ASSESSORIA_NOME'].apply(get_grupo)

_qtd_log=len(df)
_vl_log=float(df['VL_PRINCIPAL_VENCIDO'].sum()) if 'VL_PRINCIPAL_VENCIDO' in df.columns else 0.0

# Segmentos não mapeados vão para grupo d
segs_mapeados={s for segs in GRUPOS_SEG.values() for s in segs}
segs_novos=set(df['SEGMENTO'].unique())-segs_mapeados
if segs_novos:
    print(f'Segmentos não mapeados adicionados ao grupo d: {segs_novos}')
    GRUPOS_SEG['d']=list(set(GRUPOS_SEG['d'])|segs_novos)

pngs_gerados={}

try:
    for grp,segs in GRUPOS_SEG.items():
        df_sub=df[df['SEGMENTO'].isin(segs)].copy()
        if df_sub.empty:
            print(f'  Grupo {grp}: sem dados, pulando.')
            continue
        ordem=sorted(df_sub['SEGMENTO'].unique())
        fname=f'grafico_q2_{grp}_{TIMESTAMP}.png'
        png_path=os.path.join(IMG_DIR,fname)
        titulo=(f'M2 · Entradas por Segmento — Foto Atual  |  '
                f'Grupo {grp.upper()}  |  {fmt_qtd(len(df_sub))} contratos  |  {TIMESTAMP_LABEL}')
        gerar_png(df_sub,ordem,titulo,png_path)
        pngs_gerados[f'grupo_{grp}']=fname

    meta={'timestamp':TIMESTAMP,'pngs':pngs_gerados}
    with open(TS_FILE,'w') as f:
        json.dump(meta,f)

    registrar(
        monitoramento="M2",timestamp=TIMESTAMP,status="ok",
        qtd_contratos=_qtd_log,vl_total=_vl_log,pngs=pngs_gerados,
    )
    print(f'\nConcluído. {len(pngs_gerados)} PNGs gerados.')

except Exception:
    registrar(
        monitoramento="M2",timestamp=TIMESTAMP,status="erro",
        qtd_contratos=_qtd_log,vl_total=_vl_log,pngs=pngs_gerados,
        erro=traceback.format_exc(),
    )
    raise
