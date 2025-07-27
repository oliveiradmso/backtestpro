import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj, timedelta

# Função para identificar o tipo de ativo
def identificar_tipo(ticker):
    ticker = ticker.upper()
    
    # Remover prefixos comuns
    for prefix in ['5-MIN_', 'MINI_', 'WIN', 'WDO', 'DOL', 'IND', 'DOLZ', 'WINZ']:
        ticker = ticker.replace(prefix, '')
    
    nome_original = ticker.upper()

    # Verificar primeiro: Mini Índice (prioridade)
    if 'WIN' in nome_original or 'INDICE' in nome_original or 'IND' in nome_original:
        return 'mini_indice'
    
    # Depois: Mini Dólar (evita falsos positivos com "INDICE")
    if 'DOL' in nome_original or 'USD' in nome_original or 'WDO' in nome_original:
        return 'mini_dolar'
    
    # Ações
    acoes = ['PETR', 'VALE', 'ITUB', 'BBDC', 'BEEF', 'ABEV', 'ITSA', 'JBSS', 'RADL', 'CIEL', 'GOLL', 'AZUL', 'BBAS', 'SANB']
    for acao in acoes:
        if acao in ticker:
            return 'acoes'
    
    # Padrão
    return 'mini_dolar'

# Interface do app
st.title("📊 BacktestPro")
st.subheader("Análise de distorção de preço")
st.markdown("**Precisão, segurança e poder nas suas decisões. Acesse o futuro do mercado.**")

# Verifica a senha
senha = st.text_input("Digite a senha", type="password")
if senha != "seuacesso123":
    st.warning("🔐 Acesso restrito. Digite a senha correta.")
    st.stop()

st.success("✅ Acesso liberado! Bem-vindo ao BacktestPro.")

# 1. Upload
st.header("📤 Faça upload do seu arquivo Excel")
uploaded_files = st.file_uploader("Escolha um ou mais arquivos .xlsx", type=["xlsx"], accept_multiple_files=True)

# Variáveis para armazenar o período
data_min_global = None
data_max_global = None

if uploaded_files:
    st.info(f"✅ {len(uploaded_files)} arquivo(s) carregado(s). Processando...")

    # Pré-processar para obter o período disponível
    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
            df['data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['data'])
            df['data_sozinha'] = df['data'].dt.date

            min_data = df['data_sozinha'].min()
            max_data = df['data_sozinha'].max()

            if data_min_global is None or min_data < data_min_global:
                data_min_global = min_data
            if data_max_global is None or max_data > data_max_global:
                data_max_global = max_data

        except Exception as e:
            st.warning(f"⚠️ Erro ao ler {file.name}: {e}")

# Mostrar período disponível
if data_min_global and data_max_global:
    st.subheader("📅 Período disponível para análise")
    st.write(f"**Data inicial mais antiga:** {data_min_global.strftime('%d/%m/%Y')}")
    st.write(f"**Data final mais recente:** {data_max_global.strftime('%d/%m/%Y')}")

    # Filtro de período
    st.subheader("🔍 Filtro de período")
    data_inicio = st.date_input("Data inicial", value=data_min_global, min_value=data_min_global, max_value=data_max_global)
    data_fim = st.date_input("Data final", value=data_max_global, min_value=data_min_global, max_value=data_max_global)

    # ✅ Correção: garantir que são objetos date
    if isinstance(data_inicio, datetime):
        data_inicio = data_inicio.date()
    if isinstance(data_fim, datetime):
        data_fim = data_fim.date()

    if data_inicio > data_fim:
        st.error("❌ A data inicial não pode ser maior que a final.")
        st.stop()

    # Configurações
    st.header("⚙️ Configure o Backtest")
    tipo_ativo = st.selectbox("Selecione o tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
    qtd = st.number_input("Quantidade", min_value=1, value=1)
    candles_pos_entrada = st.number_input("Número de Candles após entrada", min_value=1, value=3)
    dist_compra = st.number_input("Distorção mínima COMPRA (%)", value=0.3)
    dist_venda = st.number_input("Distorção mínima VENDA (%)", value=0.3)
    hora_inicio = st.time_input("Horário de entrada", value=time_obj(10, 0))
    hora_fim_pregao = st.time_input("Fechamento do pregão", value=time_obj(17, 30))

    # Botão para rodar
    if st.button("🚀 Rodar Backtest"):
        with st.expander("ℹ️ Ver detalhes do processamento", expanded=False):
            st.write("🔄 Iniciando processamento...")

            # ✅ ZERAR LISTAS E DATAFRAMES
            resultados_compra = []
            resultados_venda = []
            df_compra_geral = pd.DataFrame()
            df_venda_geral = pd.DataFrame()

            if not uploaded_files:
                st.write("⚠️ Nenhum arquivo carregado.")
            else:
                for file in uploaded_files:
                    try:
                        st.write(f"📁 Processando: {file.name}")

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
                        df['data_sozinha'] = df.index.date

                        # Aplicar filtro de data
                        df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]
                        if df.empty:
                            st.write(f"🟡 {file.name}: Nenhum dado no período filtrado.")
                            continue

                        ticker_nome = file.name.split(".")[0]
                        tipo_arquivo = identificar_tipo(ticker_nome)
                        st.write(f"🏷️ {ticker_nome} → tipo identificado: {tipo_arquivo}")

                        # Filtrar por tipo selecionado
                        if tipo_arquivo != tipo_ativo:
                            st.write(f"⏭️ {ticker_nome}: Ignorado (não é {tipo_ativo})")
                            continue

                        dias_unicos = pd.unique(df['data_sozinha'])
                        st.write(f"📅 {ticker_nome}: {len(dias_unicos)} dias únicos")

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

                            # ✅ Horário de entrada: encontrar o candle mais próximo
                            def time_to_minutes(t):
                                return t.hour * 60 + t.minute

                            minutos_desejado = time_to_minutes(hora_inicio)
                            minutos_candles = [time_to_minutes(t) for t in df_pregao.index.time]
                            diferencas = [abs(m - minutos_desejado) for m in minutos_candles]
                            melhor_idx = np.argmin(diferencas)
                            idx_entrada = df_pregao.index[melhor_idx]
                            preco_entrada = df_pregao.loc[idx_entrada]["open"]

                            # Saída no N-ésimo candle
                            idx_saida = idx_entrada + timedelta(minutes=5 * int(candles_pos_entrada))
                            if idx_saida not in df.index:
                                st.write(f"❌ Saída não encontrada: {idx_saida}")
                                continue
                            if idx_saida.date() != idx_entrada.date():
                                st.write(f"❌ Saída em dia diferente: {idx_saida.date()}")
                                continue
                            preco_saida = df.loc[idx_saida]["open"]

                            # Fechamento do dia anterior
                            try:
                                idx_dia_atual_idx = list(dias_unicos).index(dia_atual)
                                if idx_dia_atual_idx == 0:
                                    fechamento_anterior = 0
                                else:
                                    dia_anterior = dias_unicos[idx_dia_atual_idx - 1]
                                    fechamento_anterior = df[df.index.date == dia_anterior]["close"].iloc[-1]
                            except Exception as e:
                                st.write(f"⚠️ Erro no fechamento anterior: {e}")
                                fechamento_anterior = 0

                            distorcao_percentual = 0
                            if fechamento_anterior != 0:
                                distorcao = preco_entrada - fechamento_anterior
                                distorcao_percentual = (distorcao / fechamento_anterior) * 100

                            # Valor por ponto (R$ por ponto por contrato)
                            if tipo_ativo == "acoes":
                                valor_ponto = 0.01
                            elif tipo_ativo == "mini_indice":
                                valor_ponto = 0.20
                            elif tipo_ativo == "mini_dolar":
                                valor_ponto = 10.00

                            # Compra: mercado caiu
                            if distorcao_percentual < -dist_compra:
                                lucro_reais = (preco_saida - preco_entrada) * valor_ponto * qtd
                                lucro_formatado = round(lucro_reais, 2)
                                retorno = (preco_saida - preco_entrada) / preco_entrada * 100
                                dfs_compra.append({
                                    "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                    "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                    "Preço Entrada": round(preco_entrada, 2),
                                    "Preço Saída": round(preco_saida, 2),
                                    "Lucro (R$)": lucro_formatado,
                                    "Retorno (%)": f"{retorno:.2f}%",
                                    "Ação": ticker_nome,
                                    "Distorção (%)": f"{distorcao_percentual:.2f}%"
                                })

                            # Venda: mercado subiu
                            if distorcao_percentual > dist_venda:
                                lucro_reais = (preco_entrada - preco_saida) * valor_ponto * qtd
                                lucro_formatado = round(lucro_reais, 2)
                                retorno = (preco_entrada - preco_saida) / preco_entrada * 100
                                dfs_venda.append({
                                    "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                    "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                    "Preço Entrada": round(preco_entrada, 2),
                                    "Preço Saída": round(preco_saida, 2),
                                    "Lucro (R$)": lucro_formatado,
                                    "Retorno (%)": f"{retorno:.2f}%",
                                    "Ação": ticker_nome,
                                    "Distorção (%)": f"{distorcao_percentual:.2f}%"
                                })

                        # Adicionar ao dataframe geral
                        if dfs_compra:
                            df_temp_compra = pd.DataFrame(dfs_compra)
                            df_compra_geral = pd.concat([df_compra_geral, df_temp_compra], ignore_index=True)
                            st.write(f"✅ {ticker_nome}: {len(dfs_compra)} compras")

                        if dfs_venda:
                            df_temp_venda = pd.DataFrame(dfs_venda)
                            df_venda_geral = pd.concat([df_venda_geral, df_temp_venda], ignore_index=True)
                            st.write(f"✅ {ticker_nome}: {len(dfs_venda)} vendas")

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
                        st.write(f"❌ Erro ao processar {file.name}: {e}")
                        continue

            # ✅ SALVAR OS DATAFRAMES NO SESSION STATE
            if not df_compra_geral.empty:
                st.session_state.df_compra_geral = df_compra_geral.copy()
            if not df_venda_geral.empty:
                st.session_state.df_venda_geral = df_venda_geral.copy()

            if df_compra_geral.empty and df_venda_geral.empty:
                st.write("❌ Nenhuma operação foi registrada. Verifique os filtros e os dados.")

        # ✅ FORA DO EXPANDER: Mostrar resumos na tela principal
        if 'resultados_compra' in locals() and resultados_compra:
            st.header("🟢 Resumo de Compras - Mercado Caiu")
            df_res_comp = pd.DataFrame(resultados_compra)
            st.dataframe(df_res_comp, use_container_width=True)

        if 'resultados_venda' in locals() and resultados_venda:
            st.header("🔴 Resumo de Vendas - Mercado Subiu")
            df_res_vend = pd.DataFrame(resultados_venda)
            st.dataframe(df_res_vend, use_container_width=True)

    # 6. Detalhamento por ação
    st.header("🔍 Detalhamento por Ação")
    nome_acao = st.text_input("Digite o nome da ação (ex: ITUB4, WINZ25, DOLZ25)")
    if st.button("📥 Mostrar detalhamento") and nome_acao:
        if "df_compra_geral" in st.session_state or "df_venda_geral" in st.session_state:
            df_compra_geral = st.session_state.get("df_compra_geral", pd.DataFrame())
            df_venda_geral = st.session_state.get("df_venda_geral", pd.DataFrame())

            # Filtrar por ação
            mask_compra = df_compra_geral['Ação'].str.contains(nome_acao, case=False, na=False) if 'Ação' in df_compra_geral.columns else pd.Series(False, index=df_compra_geral.index)
            mask_venda = df_venda_geral['Ação'].str.contains(nome_acao, case=False, na=False) if 'Ação' in df_venda_geral.columns else pd.Series(False, index=df_venda_geral.index)

            df_compra_acao = df_compra_geral[mask_compra]
            df_venda_acao = df_venda_geral[mask_venda]

            if not df_compra_acao.empty:
                st.subheader(f"🛒 Compras em {nome_acao}:")
                st.dataframe(df_compra_acao, use_container_width=True)
            else:
                st.info(f"ℹ️ Nenhuma operação de compra encontrada para {nome_acao}.")

            if not df_venda_acao.empty:
                st.subheader(f"🛒 Vendas em {nome_acao}:")
                st.dataframe(df_venda_acao, use_container_width=True)
            else:
                st.info(f"ℹ️ Nenhuma operação de venda encontrada para {nome_acao}.")
        else:
            st.warning("⚠️ Nenhum backtest foi rodado ainda.")

else:
    st.info("ℹ️ Aguardando upload de arquivos Excel.")
