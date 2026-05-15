import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['text.usetex'] = False
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from datetime import datetime
from matplotlib.gridspec import GridSpec
import os
import json
import traceback
from log_execucao import registrar
from imagens_utils import expurgar, garantir_pastas, IMG_DIR as _IMG_DIR

# ── Configurações ──────────────────────────────────────────────────────────────
CSV_PATH  = r"C:\Revamp Monitoramento\Query 7 (RCVRY)_Consulta do SQL personalizado.csv"
IMG_DIR   = _IMG_DIR
TS_FILE   = r"C:\Revamp Monitoramento\ultimo_timestamp_q7.txt"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── Expurgo dos PNGs anteriores ───────────────────────────────────────────────
expurgar("grafico_q7_")
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
GRUPOS = {
    'Collections':['TRC','Bulgarelli','Meet Call','Novaquest','Paschoallotto',
                   'Cobrança Interna','Portal QuintoAndar','QA Salesforce Esp.','Serasa','Monest'],
    'Evictions':  ['Pellon','Gondim','PLC','VZL','SLN','ASL','Bulgarelli Evictions'],
    'Inibidas':   ['Não Cobrar','Suspensão Cobrança'],
}
COR_GRUPO={'Collections':'#1F3864','Evictions':'#843C0C','Inibidas':'#595959'}
ORDEM_PLOT=['Inibidas','Evictions','Collections']

audiencias_producao = {
    'act-fpd-ctr','act-fpd-prd','act-ongoing-deal-ctr','act-new-mob3-e-ctr',
    'act-new-mob3-e-prd','act-new-mob3-lt-ctr','act-new-l-low-ctr','act-new-l-low-prd',
    'act-stock-ctr','act-good-payers-ctr','act-good-payers-prd','act-new-high-ctr',
    'act-new-high-prd','act-new-m-ctr','act-new-m-prd','act-new-e-low-ctr',
    'stock-risk-d-l-ctr','stock-risk-d-h-ctr','stock-risk-d-h-pd','stock-risk-nod-l-ctr',
    'stock-risk-nod-h-ctr','evictions-ctr','end-ongoing-deal-ctr','end-forgiveness-ctr',
    'end-new-h-ctr','end-new-h-prd','end-new-l-ctr','end-31-90-h-ctr','end-31-90-h-pd',
    'end-31-90-l-ctr','end-31-90-l-pd','end-31-90-r-ctr','end-31-90-r-pd',
    'end-91-180-h-ctr','end-91-180-h-pd','end-91-180-l-ctr','end-91-180-l-pd',
    'end-91-180-r-ctr','end-91-180-r-pd','end-181-360-h-ctr','end-181-360-h-pd',
    'end-181-360-h-prd','end-181-360-l-ctr','end-181-360-l-pd','end-181-360-l-prd',
    'end-181-360-r-ctr','end-181-360-r-pd','end-181-360-r-prd','end-361-1440-ctr',
    'end-361-1440-pd','end-1441-ctr'
}

# ── Grupos de PNGs: chave → (título, nome_arquivo) ───────────────────────────
GRUPOS_PNG = {
    'act-fpd':    ('Contratos Ativos - FPD (act-fpd-*)',                         f'grafico_q7_act_fpd_{TIMESTAMP}.png'),
    'act-new':    ('Contratos Ativos - Novos e Ongoing Deal (act-new-* / act-ongoing-deal-*)', f'grafico_q7_act_new_{TIMESTAMP}.png'),
    'act-stock':  ('Contratos Ativos - Stock (act-stock-* / stock-risk-*)',       f'grafico_q7_act_stock_{TIMESTAMP}.png'),
    'evictions':  ('Contratos Evictions',                                         f'grafico_q7_evictions_{TIMESTAMP}.png'),
    'end-new':    ('Contratos Encerrados - Novos e Especiais',                    f'grafico_q7_end_new_{TIMESTAMP}.png'),
    'end-31-90':  ('Contratos Encerrados - 31 a 90 dias',                        f'grafico_q7_end_31_90_{TIMESTAMP}.png'),
    'end-91-180': ('Contratos Encerrados - 91 a 180 dias',                       f'grafico_q7_end_91_180_{TIMESTAMP}.png'),
    'end-181-360':('Contratos Encerrados - 181 a 360 dias',                      f'grafico_q7_end_181_360_{TIMESTAMP}.png'),
    'end-360+':   ('Contratos Encerrados - 360+ dias',                           f'grafico_q7_end_360+_{TIMESTAMP}.png'),
    'outros':     ('Audiencias Residuais (Outros)',                               f'grafico_q7_outros_{TIMESTAMP}.png'),
}

# ── Funções auxiliares ─────────────────────────────────────────────────────────
def normalizar_agency(cod):
    cod=str(cod).strip(); b=cod.lstrip('G')
    for t in [b.zfill(3),b,b.lstrip('0') or '0']:
        if t in DE_PARA: return DE_PARA[t]
    return b.lstrip('0') or b

def get_grupo(nome):
    for g,m in GRUPOS.items():
        if nome in m: return g
    return 'Collections'

def mapear_png(row):
    aud=row['AUDIENCIA']; seg=row.get('SEGMENTO','')
    if pd.isna(aud): return 'outros'
    if aud in ('act-fpd-ctr','act-fpd-prd'): return 'act-fpd'
    if aud.startswith('act-new') or aud in ('act-ongoing-deal','act-ongoing-deal-ctr'): return 'act-new'
    if aud in ('act-stock-ctr','act-good-payers-ctr','act-good-payers-prd') or aud.startswith('stock-risk'): return 'act-stock'
    if aud in ('evictions-ctr','evictions'): return 'evictions'
    if aud in ('end-ongoing-deal','end-forgiveness'): return 'end-new'
    if aud not in audiencias_producao: return 'outros'
    if any(x in aud for x in ['end-new','end-ongoing','end-forgiveness']): return 'end-new'
    if 'end-31-90'   in aud: return 'end-31-90'
    if 'end-91-180'  in aud: return 'end-91-180'
    if 'end-181-360' in aud: return 'end-181-360'
    if any(x in aud for x in ['end-361-1440','end-1441']): return 'end-360+'
    return 'outros'

def fmt_valor(v):
    if v>=1_000_000: return f'R${v/1_000_000:.1f}M'
    elif v>=1_000:   return f'R${v/1_000:.0f}K'
    return f'R${v:.0f}'
def fmt_qtd(q): return f'{int(q):,}'.replace(',','.')
def fmt_pct(p): return f'{p:.1f}%'
def txt(ax,x,y,s,**kw): return ax.text(x,y,s,parse_math=False,**kw)

GAP=1.2; COR_SEM='#4472C4'; COR_ACORDO='#ED7D31'; COR_SEP='#555555'
COR_TOTAL='#AAAAAA'; HSPACE=0.7

def draw_ax(ax, pivot_qtd, pivot_vl, is_qtd, xlabel, total_aud_qtd, total_aud_vl):
    rows_q,rows_v,labels,grupos,posicoes=[],[],[],[],[]
    cur_y=0
    for gi,g in enumerate(ORDEM_PLOT):
        mask=pivot_qtd.index.get_level_values('GRUPO')==g
        sub_q=pivot_qtd[mask].sort_values('Sem Acordo',ascending=True)
        sub_v=pivot_vl[mask].reindex(sub_q.index)
        for (grp,nome) in sub_q.index:
            labels.append(nome); grupos.append(grp); posicoes.append(cur_y)
            rows_q.append(sub_q.loc[(grp,nome)]); rows_v.append(sub_v.loc[(grp,nome)])
            cur_y+=1
        if gi<len(ORDEM_PLOT)-1 and mask.any(): cur_y+=GAP
    if not posicoes: return {}

    sem_vals=np.array([r['Sem Acordo']       for r in rows_q])
    ac_vals =np.array([r['Com Acordo Ativo'] for r in rows_q])
    vl_sem  =np.array([r['Sem Acordo']       for r in rows_v])
    vl_ac   =np.array([r['Com Acordo Ativo'] for r in rows_v])
    pos=np.array(posicoes)

    fmt_bar=fmt_qtd if is_qtd else fmt_valor
    total_bar=total_aud_qtd if is_qtd else total_aud_vl
    assoc_max=max((sem_vals+ac_vals).max() if len(sem_vals)>0 else 0,1)
    total_max=max(total_bar,assoc_max)
    pos_total=max(posicoes)+GAP

    ax.barh(pos_total,total_bar,height=0.55,color=COR_TOTAL,zorder=2)
    ax.axhline(pos_total-GAP/2,color='#BBBBBB',linewidth=0.8,linestyle='--',zorder=1)
    txt(ax,total_bar+total_max*0.015,pos_total,
        f'{fmt_bar(total_bar)}  /  100%  /  ({fmt_valor(total_aud_vl)})',
        va='center',ha='left',fontsize=5.5,color=COR_SEP,zorder=3)
    txt(ax,0,pos_total,'TOTAL ',va='center',ha='right',fontsize=5.5,
        color='#333333',fontweight='bold',zorder=3)

    ax.barh(pos,sem_vals,height=0.55,color=COR_SEM,zorder=2)
    ax.barh(pos,ac_vals,left=sem_vals,height=0.55,color=COR_ACORDO,zorder=2)
    ax.set_yticks(list(pos)+[pos_total]); ax.set_yticklabels(labels+[''],fontsize=7)
    ax.set_xlabel(xlabel,fontsize=7); ax.set_facecolor('#FFFFFF')
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(left=False,bottom=False)
    ax.grid(axis='x',color='#E0E0E0',linewidth=0.4,zorder=0)
    ax.set_xlim(0,total_max*1.85); ax.set_ylim(-0.7,pos_total+0.7)

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
                           color='#BBBBBB',linewidth=0.8,linestyle='--',zorder=1)
            gi_map[g]=posicoes[i]; grupo_atual=g
        gf_map[g]=posicoes[i]

    denom=total_aud_qtd if is_qtd else total_aud_vl
    for i in range(len(labels)):
        vs=sem_vals[i]; va=ac_vals[i]; vls=vl_sem[i]; vla=vl_ac[i]
        total=vs+va; vl_total=vls+vla
        pct=(total/denom*100) if denom>0 else 0
        lbl=f'{fmt_bar(vs)}  /  {fmt_bar(va)}  /  {fmt_pct(pct)}  /  ({fmt_valor(vl_total)})'
        txt(ax,total+total_max*0.015,posicoes[i],lbl,
            va='center',ha='left',fontsize=5.5,color=COR_SEP,zorder=3)
    return {'inicio':gi_map,'fim':gf_map}

def gerar_png(df_sub, ordem_auds, label_col, titulo, png_path):
    DATA_HOJE=datetime.now().strftime('%d/%m/%Y')
    n_auds=len(ordem_auds)
    alturas=[]
    for aud in ordem_auds:
        n=df_sub[df_sub[label_col]==aud]['ASSESSORIA_NOME'].nunique()
        alturas.append(max(3,n)*0.45+1.5)

    h_medio=sum(alturas)/len(alturas)
    TITULO_H=HSPACE*h_medio; LEGENDA_H=0.6
    total_h=TITULO_H+sum(alturas)+LEGENDA_H
    fig=plt.figure(figsize=(22,total_h)); fig.patch.set_facecolor('#F5F5F5')
    top_frac=1.0-TITULO_H/total_h; bottom_frac=LEGENDA_H/total_h

    gs=GridSpec(n_auds+1,2,figure=fig,height_ratios=alturas+[LEGENDA_H],
                hspace=HSPACE,wspace=0.35,top=top_frac,bottom=bottom_frac)

    for row_idx,aud in enumerate(ordem_auds):
        df_aud=df_sub[df_sub[label_col]==aud]
        total_aud_qtd=float(len(df_aud)); total_aud_vl=float(df_aud['VL_PRINCIPAL_VENCIDO'].sum())

        agg=df_aud.groupby(['GRUPO','ASSESSORIA_NOME','SITUACAO_ACORDO']).agg(
            qtd=('NR_CONTRATO','count'),vl=('VL_PRINCIPAL_VENCIDO','sum')).reset_index()
        pivot_qtd=agg.pivot_table(index=['GRUPO','ASSESSORIA_NOME'],columns='SITUACAO_ACORDO',
                                  values='qtd',aggfunc='sum').fillna(0)
        pivot_vl =agg.pivot_table(index=['GRUPO','ASSESSORIA_NOME'],columns='SITUACAO_ACORDO',
                                  values='vl',aggfunc='sum').fillna(0)
        for col in ['Sem Acordo','Com Acordo Ativo']:
            if col not in pivot_qtd.columns: pivot_qtd[col]=0
            if col not in pivot_vl.columns:  pivot_vl[col]=0

        ax1=fig.add_subplot(gs[row_idx,0]); ax2=fig.add_subplot(gs[row_idx,1])
        gi1=draw_ax(ax1,pivot_qtd,pivot_vl,True,'Qtd. Contratos',total_aud_qtd,total_aud_vl)
        gi2=draw_ax(ax2,pivot_vl, pivot_vl,False,'Saldo em Atraso',total_aud_qtd,total_aud_vl)
        ax1.set_title(f'{aud}  -  {fmt_qtd(int(total_aud_qtd))} contratos',
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

    ax_leg=fig.add_subplot(gs[n_auds,:]); ax_leg.set_axis_off()
    patch_sem   =mpatches.Patch(color=COR_SEM,   label='Sem Acordo')
    patch_acordo=mpatches.Patch(color=COR_ACORDO,label='Com Acordo Ativo')
    patch_total =mpatches.Patch(color=COR_TOTAL, label='Total da Audiencia')
    ax_leg.legend(handles=[patch_sem,patch_acordo,patch_total],loc='center',ncol=3,fontsize=11,
                  frameon=True,facecolor='#F5F5F5',edgecolor='#CCCCCC',bbox_to_anchor=(0.5,0.5))
    fig.suptitle(f'M7 - {titulo}  |  {fmt_qtd(len(df_sub))} contratos  |  {DATA_HOJE}',
                 fontsize=12,fontweight='bold',y=top_frac+(TITULO_H/total_h)/2,parse_math=False)

    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    plt.savefig(png_path,dpi=120,bbox_inches='tight',facecolor=fig.get_facecolor())
    plt.close()
    print(f'  OK: {os.path.basename(png_path)} ({n_auds} subplots)')

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    df=pd.read_csv(CSV_PATH,sep=None,engine='python')
    df.columns=df.columns.str.replace('\ufeff','').str.strip()
    df['PNG']=df.apply(mapear_png,axis=1)
    df['ASSESSORIA_NOME']=df['ASSESSORIA'].astype(str).apply(normalizar_agency)
    df=df[df['ASSESSORIA_NOME'].notna()&(df['ASSESSORIA_NOME']!='nan')]
    df['GRUPO']=df['ASSESSORIA_NOME'].apply(get_grupo)

    pngs_gerados = {}
    _qtd_log = len(df)
    _vl_log  = float(df['VL_PRINCIPAL_VENCIDO'].sum()) if 'VL_PRINCIPAL_VENCIDO' in df.columns else 0.0

    try:
        for sub,(titulo,fname) in GRUPOS_PNG.items():
            print(f'\nGerando {sub}...')
            df_sub=df[df['PNG']==sub].copy()
            if sub=='outros':
                df_sub['AUDIENCIA_LABEL']=df_sub['AUDIENCIA'].fillna('undefined')
                label_col='AUDIENCIA_LABEL'
                ordem=sorted(df_sub[label_col].unique())
            else:
                label_col='AUDIENCIA'
                ordem=sorted(df_sub[label_col].dropna().unique())

            png_path=os.path.join(IMG_DIR,fname)
            gerar_png(df_sub,ordem,label_col,titulo,png_path)
            pngs_gerados[sub]=fname

        # Salvar mapa de PNGs gerados para o script de envio
        meta = {'timestamp': TIMESTAMP, 'pngs': pngs_gerados}
        with open(TS_FILE,'w') as f:
            json.dump(meta,f)

        registrar(
            monitoramento = "M7",
            timestamp     = TIMESTAMP,
            status        = "ok",
            qtd_contratos = _qtd_log,
            vl_total      = _vl_log,
            pngs          = pngs_gerados,
        )
        print(f'\nConcluído. {len(pngs_gerados)} PNGs gerados.')
        print(f'Metadata salvo em: {TS_FILE}')

    except Exception:
        registrar(
            monitoramento = "M7",
            timestamp     = TIMESTAMP,
            status        = "erro",
            qtd_contratos = _qtd_log,
            vl_total      = _vl_log,
            pngs          = pngs_gerados,
            erro          = traceback.format_exc(),
        )
        raise
