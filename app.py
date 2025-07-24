# app.py
# BacktestPro - Versão Final Online
# Sistema Funcional, com Filtro, Detalhamento e Estabilidade

import streamlit as st
import pandas as pd
from datetime import time as time_obj
from datetime import timedelta
import numpy as np

# Configuração da página
st.set_page_config(page_title="BacktestPro", page_icon="📈", layout="centered")

st.title("📊 BacktestPro")
st.subheader("Análise de distorção de abertura")
st.markdown("---")

# ======= TELA DE SENHA SIMPLES =======
senha = st.text_input("🔐 Digite a senha de acesso", type="password")
if senha != "seuacesso123":  # ← Mude depois
    st.warning("🔒 Acesso restrito. Digite a senha correta.")
    st.info("Dica: a senha padrão é 'seuacesso123'")
    st.stop()

st.success("✅ Acesso liberado! Bem-vindo ao BacktestPro.")

# ======= FUNÇÃO PARA IDENTIFICAR TIPO DO ARQUIVO =======
def identificar_tipo(nome):
    nome_lower = nome.lower()
    if "mini_indice" in nome_lower or "win" in nome_lower:
        return "mini_indice"
    elif "mini_dolar" in nome_lower or "dol" in nome_lower or "wdo" in nome_lower:
        return "mini_dolar"
    else:
        return "acoes"

# ======= UPLOAD DE ARQUIVO =======
st.header("📤 Faça upload do seu arquivo Excel")
uploaded_files = st.file_uploader(
    "Escolha um ou mais arquivos .xlsx",
    type=["xlsx"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("⚠️ Aguardando upload dos arquivos Excel...")
else:
    st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)!")

# ======= CONFIGURAÇÕES DO BACKTEST =======
st.header("⚙️ Configure o Backtest")

tipo_ativo = st.selectbox(
    "Selecione o tipo de ativo",
    ["acoes", "mini_indice", "mini_dolar"]
)

qtd = st.number_input("Quantidade", min_value=1, value=1)

candles_pos_entrada = st.number_input(
    "Número de Candles após entrada",
    min_value=1,
    value=3
)

dist_compra = st.number_input("Distorção mínima COMPRA (%)", value=0.3)
dist_venda = st.number_input("Distorção mínima VENDA (%)", value=0.3)

hora_inicio = st.time_input("Horário de entrada", value=time_obj(9, 0))
hora_fim_pregao = st.time_input("Fechamento do pregão", value=time_obj(17, 30))

# Botão para rodar
if st.button("🚀 Rodar Backtest"):
    with st.spinner("Processando..."):

        # ✅ ZERAR LISTAS E DATAFRAMES
        resultados_compra = []
        resultados_venda = []
        df_compra_geral = pd.DataFrame()
        df_venda_geral = pd.DataFrame()

        if uploaded_files:
            for file in uploaded_files:
                try:
                    # Ler o arquivo
                    df = pd.read_excel(file)
                    df.columns = [str(col).strip().capitalize() for col in df.columns]
                    df.rename(columns={
                        'Data': 'data', 'Abertura': 'open', 'Máxima': 'high',
                        'Mínima': 'low', 'Fechamento': 'close'
                    }, inplace=True)

                    # Converter data
                    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
                    df = df.dropna(subset=['data'])
                    df['data_limpa'] = df['data'].dt.floor('min')
                    df = df.set_index('data_limpa').sort_index()
                    df['data_sozinha'] = df.index.normalize()

                    ticker_nome = file.name.split(".")[0]
                    tipo_arquivo = identificar_tipo(ticker_nome)

                    # Filtrar por tipo selecionado
                    if tipo_arquivo != tipo_ativo:
                        continue  # Pula arquivos que não são do tipo escolhido

                    dias_unicos = df['data_sozinha'].unique()
                    dfs_compra = []
                    dfs_venda = []

                    for i in range(len(dias_unicos)):
                        dia_atual = dias_unicos[i]
                        df_dia_atual = df[df['data_sozinha'] == dia_atual].copy()

                        mascara_pregao = (
                            (df_dia_atual.index.time >= time_obj(9, 0)) &
                            (df_dia_atual.index.time <= time_obj(17, 30))
                        )
                        df_pregao = df_dia_atual[mascara_pregao]

                        if df_pregao.empty:
                            continue

                        # Horário de entrada
                        idx_entrada = df_pregao.index[df_pregao.index.time == hora_inicio]
                        if len(idx_entrada) == 0:
                            continue
                        idx_entrada = idx_entrada[0]
                        preco_entrada = df_pregao.loc[idx_entrada]["open"]

                        # Saída no N-ésimo candle
                        idx_saida = idx_entrada + timedelta(minutes=5 * int(candles_pos_entrada))
                        if idx_saida not in df.index or idx_saida.date() != idx_entrada.date():
                            continue
                        preco_saida = df.loc[idx_saida]["open"]

                        # Fechamento do dia anterior
                        try:
                            idx_dia_atual_idx = list(dias_unicos).index(dia_atual)
                            if idx_dia_atual_idx == 0:
                                fechamento_anterior = 0
                            else:
                                dia_anterior = dias_unicos[idx_dia_atual_idx - 1]
                                fechamento_anterior = df[df.index.normalize() == dia_anterior]["close"].iloc[-1]
                        except:
                            fechamento_anterior = 0

                        distorcao_percentual = 0
                        if fechamento_anterior != 0:
                            distorcao = preco_entrada - fechamento_anterior
                            distorcao_percentual = (distorcao / fechamento_anterior) * 100

                        # Valor por ponto
                        valor_ponto = 1.00
                        if tipo_ativo == "mini_indice":
                            valor_ponto = 0.20
                        elif tipo_ativo == "mini_dolar":
                            valor_ponto = 0.50

                        # Compra: mercado caiu
                        if distorcao_percentual < -dist_compra:
                            lucro_reais = qtd * (preco_saida - preco_entrada) * valor_ponto
                            retorno = (preco_saida - preco_entrada) / preco_entrada * 100
                            dfs_compra.append({
                                "Data Entrada": idx_entrada.strftime("%Y-%m-%d %H:%M"),
                                "Data Saída": idx_saida.strftime("%Y-%m-%d %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Retorno (%)": f"{retorno:.2f}%",
                                "Ação": ticker_nome,
                                "Distorção (%)": f"{distorcao_percentual:.2f}%"
                            })

                        # Venda: mercado subiu
                        if distorcao_percentual > dist_venda:
                            lucro_reais = qtd * (preco_entrada - preco_saida) * valor_ponto
                            retorno = (preco_entrada - preco_saida) / preco_entrada * 100
                            dfs_venda.append({
                                "Data Entrada": idx_entrada.strftime("%Y-%m-%d %H:%M"),
                                "Data Saída": idx_saida.strftime("%Y-%m-%d %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Retorno (%)": f"{retorno:.2f}%",
                                "Ação": ticker_nome,
                                "Distorção (%)": f"{distorcao_percentual:.2f}%"
                            })

                    # Adicionar ao dataframe geral
                    if dfs_compra:
                        df_compra_geral = pd.concat([df_compra_geral, pd.DataFrame(dfs_compra)], ignore_index=True)

                    if dfs_venda:
                        df_venda_geral = pd.concat([df_venda_geral, pd.DataFrame(dfs_venda)], ignore_index=True)

                    # Resultados finais por ativo
                    if dfs_compra:
                        acertos = len([op for op in dfs_compra if op["Lucro (R$)"] > 0])
                        total = len(dfs_compra)
                        taxa_acerto = acertos / total if total > 0 else 0
                        resultados_compra.append({
                            "Ação": ticker_nome,
                            "Total Eventos": total,
                            "Acertos": acertos,
                            "Taxa de Acerto": f"{taxa_acerto:.2%}",
                            "Retorno Médio (R$)": f"R$ {np.mean([op['Lucro (R$)'] for op in dfs_compra]):.2f}",
                            "Lucro Total (R$)": f"R$ {sum(op['Lucro (R$)'] for op in dfs_compra):.2f}"
                        })
                    else:
                        resultados_compra.append({
                            "Ação": ticker_nome,
                            "Total Eventos": 0,
                            "Acertos": 0,
                            "Taxa de Acerto": "0.00%",
                            "Retorno Médio (R$)": "R$ 0.00",
                            "Lucro Total (R$)": "R$ 0.00"
                        })

                    if dfs_venda:
                        acertos = len([op for op in dfs_venda if op["Lucro (R$)"] > 0])
                        total = len(dfs_venda)
                        taxa_acerto = acertos / total if total > 0 else 0
                        resultados_venda.append({
                            "Ação": ticker_nome,
                            "Total Eventos": total,
                            "Acertos": acertos,
                            "Taxa de Acerto": f"{taxa_acerto:.2%}",
                            "Retorno Médio (R$)": f"R$ {np.mean([op['Lucro (R$)'] for op in dfs_venda]):.2f}",
                            "Lucro Total (R$)": f"R$ {sum(op['Lucro (R$)'] for op in dfs_venda):.2f}"
                        })
                    else:
                        resultados_venda.append({
                            "Ação": ticker_nome,
                            "Total Eventos": 0,
                            "Acertos": 0,
                            "Taxa de Acerto": "0.00%",
                            "Retorno Médio (R$)": "R$ 0.00",
                            "Lucro Total (R$)": "R$ 0.00"
                        })

                except Exception as e:
                    st.error(f"Erro ao processar {file.name}: {e}")

            # Mostrar resultados
            if resultados_compra:
                st.header("🟢 Resumo de Compras - Mercado Caiu")
                df_res_comp = pd.DataFrame(resultados_compra)
                st.dataframe(df_res_comp, use_container_width=True)

            if resultados_venda:
                st.header("🔴 Resumo de Vendas - Mercado Subiu")
                df_res_vend = pd.DataFrame(resultados_venda)
                st.dataframe(df_res_vend, use_container_width=True)

            # ✅ SALVAR OS DATAFRAMES NO SESSION STATE
            st.session_state.df_compra_geral = df_compra_geral.copy()
            st.session_state.df_venda_geral = df_venda_geral.copy()

        else:
            st.warning("Nenhum arquivo carregado.")

# ======= DETALHAMENTO POR AÇÃO (com botão para evitar recarga) =======
st.markdown("---")
st.subheader("🔍 Detalhamento por Ação")

acao_input = st.text_input(
    "Digite o nome da ação (ex: ITUB4, WINZ25, DOLZ25)",
    key="acao_input_detalhe"
)

if st.button("🔍 Mostrar Detalhamento"):
    if 'df_compra_geral' in st.session_state and 'df_venda_geral' in st.session_state:
        detalhe_comp = st.session_state.df_compra_geral[
            st.session_state.df_compra_geral["Ação"].str.contains(acao_input, case=False)
        ]
        detalhe_vend = st.session_state.df_venda_geral[
            st.session_state.df_venda_geral["Ação"].str.contains(acao_input, case=False)
        ]

        if detalhe_comp.empty and detalhe_vend.empty:
            st.info(f"⚠️ Nenhuma operação encontrada para '{acao_input}'")
        else:
            if not detalhe_comp.empty:
                st.write(f"🛒 **Compras em {acao_input.upper()}:**")
                st.dataframe(
                    detalhe_comp[["Data Entrada", "Data Saída", "Preço Entrada", "Preço Saída", "Lucro (R$)", "Retorno (%)"]],
                    use_container_width=True
                )

            if not detalhe_vend.empty:
                st.write(f"🛒 **Vendas em {acao_input.upper()}:**")
                st.dataframe(
                    detalhe_vend[["Data Entrada", "Data Saída", "Preço Entrada", "Preço Saída", "Lucro (R$)", "Retorno (%)"]],
                    use_container_width=True
                )
    else:
        st.warning("⚠️ Execute o backtest primeiro!")

# Rodapé
st.markdown("---")
st.caption("💬 BacktestPro — Seu edge, agora online.")