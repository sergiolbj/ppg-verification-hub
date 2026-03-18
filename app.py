import streamlit as st
import pandas as pd
import json
import os
import re
import io
import gc 
from datetime import datetime
from PIL import Image

# --- CONFIGURAÇÕES DE INTERFACE ---
st.set_page_config(page_title="Verification Hub | Propeg", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #212529; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #dee2e6; }
    .manage-card { background-color: #ffffff; border-left: 5px solid #e30613; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stProgress > div > div > div > div { background-color: #e30613; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    div.stDownloadButton { display: inline-block; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
DB_FILE = "modulos_config.json"
NOME_ARQUIVO_LOGO = "propeg_logo.jpg"

def carregar_modulos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                return json.loads(content) if content else {}
        except: return {}
    return {}

def salvar_modulo(nome, config):
    modulos = carregar_modulos()
    modulos[nome] = config
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(modulos, f, indent=4, ensure_ascii=False)
    return True

def analisar_brand_safety(df, col_url, termos):
    if not termos or col_url not in df.columns:
        df['URL Sensível'] = 0
        return df, pd.DataFrame()
    lista_termos = [t.strip().lower() for t in re.split(r'[,\n]', termos) if t.strip()]
    if not lista_termos:
        df['URL Sensível'] = 0
        return df, pd.DataFrame()
    regex_pattern = '|'.join([re.escape(t) for t in lista_termos])
    mask = df[col_url].astype(str).str.lower().str.contains(regex_pattern, na=False, regex=True)
    df['URL Sensível'] = 0
    df.loc[mask, 'URL Sensível'] = df.loc[mask, 'Impressões']
    df_detalhe = df[mask][[col_url, 'Veiculos', 'Impressões']].copy()
    if not df_detalhe.empty:
        df_detalhe['Termo Encontrado'] = df_detalhe[col_url].str.extract(f'({regex_pattern})', flags=re.IGNORECASE)
        df_detalhe.rename(columns={col_url: 'URL Analisada'}, inplace=True)
    return df, df_detalhe

# --- ESTADOS DO SISTEMA ---
modulos = carregar_modulos()
if 'pagina' not in st.session_state: st.session_state.pagina = "🚀 Executar Módulo"
if 'modulo_para_editar' not in st.session_state: st.session_state.modulo_para_editar = None
if 'processando' not in st.session_state: st.session_state.processando = False
if 'interromper' not in st.session_state: st.session_state.interromper = False
if 'concluido' not in st.session_state: st.session_state.concluido = False

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(NOME_ARQUIVO_LOGO):
        st.image(Image.open(NOME_ARQUIVO_LOGO), width='stretch')
    st.title("Verification Hub")
    st.markdown("---")
    opcoes_menu = ["🚀 Executar Módulo", "✨ Criar Novo Módulo", "⚙️ Gerenciar"]
    menu = st.radio("Menu", opcoes_menu, index=opcoes_menu.index(st.session_state.pagina))
    if menu != st.session_state.pagina:
        st.session_state.pagina = menu
        st.session_state.modulo_para_editar = None if menu == "✨ Criar Novo Módulo" else st.session_state.modulo_para_editar
        st.rerun()

# --- PÁGINAS: CRIAR / GERENCIAR (Mantidas as lógicas anteriores) ---
if st.session_state.pagina == "✨ Criar Novo Módulo":
    st.title(f"📝 Editando: {st.session_state.modulo_para_editar}" if st.session_state.modulo_para_editar else "✨ Criar Novo Módulo")
    config_alvo = modulos.get(st.session_state.modulo_para_editar, {}) if st.session_state.modulo_para_editar else {}
    with st.container(border=True):
        with st.form("form_modulo"):
            nome = st.text_input("Nome do Adserver", value=st.session_state.modulo_para_editar if st.session_state.modulo_para_editar else "")
            c1, c2 = st.columns(2)
            with c1:
                h_idx = st.number_input("Header (Linha)", value=config_alvo.get('header_index', 4) + 1, min_value=1) - 1
                c_imp = st.text_input("Coluna Impressões", value=config_alvo.get('col_impressoes', 'Impressões'))
                c_veic = st.text_input("Coluna Veículo", value=config_alvo.get('col_veiculo', 'Veículo'))
            with c2:
                c_cat = st.text_input("Coluna Categoria", value=config_alvo.get('col_categoria', 'Categoria'))
                n_total = st.text_input("Nome Coluna Total", value=config_alvo.get('nome_total', 'Impressões entregues'))
                cats = st.text_area("Categorias", value="\n".join(config_alvo.get('categorias_alvo', ["Conteúdo Sensível"])))
            st.divider()
            u_bs = st.checkbox("BS por padrão", value=config_alvo.get('usar_bs', False))
            c_url = st.text_input("Coluna URL", value=config_alvo.get('col_url', 'Página URL'))
            t_bs = st.text_area("Dicionário", value=config_alvo.get('termos_bs', ''))
            if st.form_submit_button("💾 Salvar"):
                if nome:
                    salvar_modulo(nome, {"header_index": int(h_idx), "col_impressoes": c_imp, "col_veiculo": c_veic, "col_categoria": c_cat, "nome_total": n_total, "usar_bs": u_bs, "col_url": c_url, "termos_bs": t_bs, "categorias_alvo": [x.strip() for x in cats.split('\n') if x.strip()]})
                    st.session_state.modulo_para_editar = None
                    st.rerun()

elif st.session_state.pagina == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciar Adservers")
    for m_nome, m_cfg in modulos.items():
        st.markdown(f'<div class="manage-card"><strong>📦 {m_nome}</strong></div>', unsafe_allow_html=True)
        c_inf, c_ed, c_del = st.columns([6, 1, 1])
        with c_inf: st.caption(f"Header: {m_cfg['header_index']+1} | Impressões: {m_cfg['col_impressoes']}")
        with c_ed:
            if st.button("✏️", key=f"ed_{m_nome}"):
                st.session_state.modulo_para_editar, st.session_state.pagina = m_nome, "✨ Criar Novo Módulo"
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_{m_nome}"):
                del modulos[m_nome]
                with open(DB_FILE, "w") as f: json.dump(modulos, f)
                st.rerun()

# --- PÁGINA: EXECUTAR ---
elif st.session_state.pagina == "🚀 Executar Módulo":
    st.title("🚀 Processamento de Lote Propeg")
    if not modulos: st.warning("Configure um adserver.")
    else:
        escolha = st.selectbox("Selecione o Adserver:", list(modulos.keys()))
        conf = modulos[escolha]
        usar_bs_agora = st.toggle("🔥 Brand Safety Ativo", value=conf.get('usar_bs', False))
        
        # O file_uploader é resetado se pedirmos um novo processo
        files = st.file_uploader("📂 Suba os arquivos XLSX", type="xlsx", accept_multiple_files=True, key="uploader_lote")
        
        if files:
            total_arquivos = len(files)
            p_btn_placeholder = st.empty()
            
            # 1. ESTADO INICIAL: Botão Iniciar
            if not st.session_state.processando and not st.session_state.concluido:
                if p_btn_placeholder.button("📊 Iniciar Consolidação"):
                    st.session_state.processando, st.session_state.interromper, st.session_state.concluido = True, False, False
                    st.rerun()
            
            # 2. ESTADO PROCESSANDO: Botão Interromper
            elif st.session_state.processando:
                if p_btn_placeholder.button("🛑 Interromper"): 
                    st.session_state.interromper = True
                
                res_resumo, det_bs_lista = [], []
                with st.status(f"🛠️ Processando em Lote (0/{total_arquivos})...", expanded=True) as status:
                    pbar = st.progress(0)
                    stxt = st.empty()
                    for i, arq in enumerate(files):
                        if st.session_state.interromper: break
                        status.update(label=f"🛠️ Processando ({i+1}/{total_arquivos})...")
                        stxt.markdown(f"📖 **Lendo:** `{arq.name}`")
                        pbar.progress(int(((i+1)/total_arquivos)*100))
                        try:
                            df = pd.read_excel(arq, header=conf['header_index'])
                            df.columns = df.columns.str.strip()
                            df.rename(columns={conf['col_veiculo']: 'Veiculos', conf['col_impressoes']: 'Impressões'}, inplace=True)
                            df['Impressões'] = pd.to_numeric(df['Impressões'], errors='coerce').fillna(0)
                            if usar_bs_agora:
                                df, df_det = analisar_brand_safety(df, conf['col_url'], conf['termos_bs'])
                                if not df_det.empty:
                                    df_det['Arquivo'] = arq.name
                                    det_bs_lista.append(df_det)
                            df_total = df.groupby('Veiculos')['Impressões'].sum().reset_index()
                            df_total.rename(columns={'Impressões': conf['nome_total']}, inplace=True)
                            df_f = df_total.copy()
                            if conf['col_categoria'] in df.columns:
                                df_cat = df[df[conf['col_categoria']].isin(conf['categorias_alvo'])].copy()
                                if not df_cat.empty:
                                    df_piv = df_cat.pivot_table(index='Veiculos', columns=conf['col_categoria'], values='Impressões', aggfunc='sum', fill_value=0).reset_index()
                                    df_f = pd.merge(df_f, df_piv, on='Veiculos', how='left').fillna(0)
                            if usar_bs_agora:
                                bs_sum = df.groupby('Veiculos')['URL Sensível'].sum().reset_index()
                                df_f = pd.merge(df_f, bs_sum, on='Veiculos', how='left').fillna(0)
                            for c in conf['categorias_alvo'] + (['URL Sensível'] if usar_bs_agora else []):
                                if c not in df_f.columns: df_f[c] = 0
                            df_f['Soma (categorias)'] = df_f[[c for c in df_f.columns if c in conf['categorias_alvo'] or c == 'URL Sensível']].sum(axis=1)
                            res_resumo.append(df_f)
                            del df; gc.collect() 
                        except Exception as e:
                            st.error(f"Erro em {arq.name}: {e}")
                    status.update(label="✅ Concluído!", state="complete", expanded=False)
                
                # Fim do loop: muda para estado concluído
                st.session_state.processando = False
                st.session_state.concluido = True
                st.session_state.resultado_cache = (res_resumo, det_bs_lista) # Guarda pra exibir
                st.rerun()

            # 3. ESTADO CONCLUÍDO: Botão Novo Processo
            elif st.session_state.concluido:
                if p_btn_placeholder.button("🔄 Iniciar Novo Lote"):
                    st.session_state.concluido = False
                    st.session_state.resultado_cache = None
                    st.rerun()
                
                # Exibe os resultados que foram guardados no cache
                res_resumo, det_bs_lista = st.session_state.resultado_cache
                if res_resumo and not st.session_state.interromper:
                    df_final = pd.concat(res_resumo, ignore_index=True).groupby('Veiculos').sum(numeric_only=True).reset_index()
                    df_final['% do Total'] = (df_final['Soma (categorias)'] / df_final[conf['nome_total']] * 100).fillna(0)
                    st.dataframe(df_final.style.format({"% do Total": "{:.2f}%"}), width='stretch')
                    st.markdown("### 📥 Exportação")
                    col_b1, col_b2, _ = st.columns([1.5, 2, 5])
                    with col_b1:
                        b1 = io.BytesIO()
                        df_final.to_excel(b1, index=False)
                        st.download_button("🟢 Resumo Excel", b1.getvalue(), f"resumo_{escolha}.xlsx")
                    if det_bs_lista:
                        df_det_f = pd.concat(det_bs_lista, ignore_index=True)
                        with col_b2:
                            b2 = io.BytesIO()
                            df_det_f.to_excel(b2, index=False)
                            st.download_button(f"🔴 Brand Safety ({len(df_det_f)})", b2.getvalue(), "detalhes_bs.xlsx")