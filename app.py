import streamlit as st
import pandas as pd
import numpy as np
from datetime import time as time_obj

# Função para identificar o tipo de ativo
def identificar_tipo(ticker):
    ticker = ticker.upper()
    if ticker.startswith('WIN') or ticker.startswith('WDO'):
        return 'mini_indice'
    elif ticker.startswith('PETR') or ticker.startswith('VALE') or ticker.startswith('ITUB') or ticker.startswith('BBDC'):
        return 'acoes'
    else:
        return 'mini_dolar'

# Interface do app
st.title("📊 BacktestPro")
st.subheader("Análise de distorção de abertura")

# Verifica a senha
senha = st.text_input("Digite a senha", type="password")
if senha != "seuacesso123":
    st.warning("🔐 Acesso restrito. Digite a senha correta.")
    st.stop()

st.success("✅ Acesso liberado! Bem-vindo ao BacktestPro.")

# 1. Upload
st.header("📤 Faça upload do seu arquivo Excel")
uploaded_files = st.file_uploader("Escolha um ou mais arquivos .xlsx", type=["xlsx"], accept_multiple_files=True)

# Limpar session_state se novos arquivos forem enviados
if uploaded_files:
    arquivos_nomes = [f.name for f in uploaded_files]
    if "arquivos_carregados" not in st.session_state or st.session_state.arquivos_carregados != arquivos_nomes:
        st.session_state.clear()
        st.session_state.arquivos_carregados = arquivos_nomes

# Processar dados se ainda não estiverem no session_state
if uploaded_files and "dfs_processados" not in st.session_state:
    st.info(f"✅ {len(uploaded_files)} arquivo(s) carregado(s). Processando...")

    data_min_global = None
    data_max_global = None
    dfs_processados = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
            df.columns = [str(col).strip().capitalize() for col in df.columns]
            df.rename(columns={
                'Data': 'data', 'Abertura': 'open', 'Máxima': 'high',
                'Mínima': 'low', 'Fechamento': 'close'
            }, inplace=True)

            # Converter data
            df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['data'])

            # Definir índice com data/hora
            df['data_limpa'] = df['data'].dt.floor('min')
            df = df.set_index('data_limpa').sort_index()
            df['data_sozinha'] = df.index.date  # só a data

            # Atualizar min e max
            min_data = df['data_sozinha'].min()
            max_data = df['data_sozinha'].max()

            if data_min_global is None or min_data < data_min_global:
                data_min_global = min_data
            if data_max_global is None or max_data > data_max_global:
                data_max_global = max_data

            # Guardar o df processado
            dfs_processados.append({
                'file': file,
                'df': df,
                'ticker': file.name.split(".")[0]
            })

        except Exception as e:
            st.warning(f"⚠️ Erro ao ler {file.name}: {e}")

    # Salvar no session_state
    st.session_state.dfs_processados = dfs_processados
    st.session_state.data_min_global = data_min_global
    st.session_state.data_max_global = data_max_global

# Mostrar período e filtros (se houver dados)
if "dfs_processados" in st.session_state:
    dfs_processados = st.session_state.dfs_processados
    data_min_global = st.session_state.data_min_global
    data_max_global = st.session_state.data_max_global

    # 2. Mostrar período disponível
    st.subheader("📅 Período disponível para análise")
    st.write(f"**Data inicial mais antiga:** {data_min_global.strftime('%d/%m/%Y')}")
    st.write(f"**Data final mais recente:** {data_max_global.strftime('%d/%m/%Y')}")

    # 3. Filtro de período
    st.subheader("🔍 Filtro de período")
    data_inicio = st.date_input("Data inicial", value=data_min_global, min_value=data_min_global, max_value=data_max_global)
    data_fim = st.date_input("Data final", value=data_max_global, min_value=data_min_global, max_value=data_max_global)

    if data_inicio > data_fim:
        st.error("❌ A data inicial não pode ser maior que a final.")
        st.stop()

    # 4. Configurações
    st.header("⚙️ Configure o Backtest")
    tipo_ativo = st.selectbox("Selecione o tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
    qtd = st.number_input("Quantidade", min_value=1, value=1)
    candles_pos_entrada = st.number_input("Número de Candles após entrada", min_value=1, value=3)
    dist_compra = st.number_input("Distorção mínima COMPRA (%)", value=0.3)
    dist_venda = st.number_input("Distorção mínima VENDA (%)", value=0.3)
    hora_inicio = st.time_input("Horário de entrada", value=time_obj(9, 0))
    hora_fim_pregao = st.time_input("Fechamento do pregão", value=time_obj(17, 30))

    # Ajustar valor do ponto
    if tipo_ativo == "acoes":
        valor_ponto = 0.01
    elif tipo_ativo == "mini_indice":
        valor_ponto = 0.5
    else:
        valor_ponto = 0.005

    # 5. Botão para rodar
    if st.button("🚀 Rodar Backtest"):
        resultados_compras = []
        resultados_vendas = []

        for item in dfs_processados:
            df = item['df'].copy()
            ticker_nome = item['ticker']

            # Identificar tipo do ativo
            tipo_arquivo = identificar_tipo(ticker_nome)

            # Filtrar pelo tipo selecionado
            if tipo_ativo == "acoes" and tipo_arquivo != "acoes":
                continue
            elif tipo_ativo == "mini_indice" and tipo_arquivo != "mini_indice":
                continue
            elif tipo_ativo == "mini_dolar" and tipo_arquivo != "mini_dolar":
                continue

            # Aplicar filtro de data
            df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]
            if df.empty:
                continue

            # Calcular preço de entrada
            df['hora'] = df.index.time
            mask_horario = df['hora'].between(hora_inicio, hora_fim_pregao)
            dias_uteis = pd.unique(df[mask_horario]['data_sozinha'])

            for dia in dias_uteis:
                df_dia = df[df['data_sozinha'] == dia]
                if df_dia.empty or len(df_dia) <= candles_pos_entrada:
                    continue

                entrada = df_dia.iloc[0]['open']
                fechamento = df_dia.iloc[-1]['close']
                dist_percent = ((entrada - fechamento) / fechamento) * 100

                # Sinal
                if dist_percent <= -dist_venda:
                    sinal = 'VENDA'
                elif dist_percent >= dist_compra:
                    sinal = 'COMPRA'
                else:
                    sinal = 'SEM SINAL'

                # Saída
                saida_row = df_dia.iloc[candles_pos_entrada]
                preco_saida = saida_row['close']

                # Lucro em R$
                if sinal == 'COMPRA':
                    lucro_pontos = (preco_saida - entrada)
                    lucro_reais = (lucro_pontos / valor_ponto) * qtd
                elif sinal == 'VENDA':
                    lucro_pontos = (entrada - preco_saida)
                    lucro_reais = (lucro_pontos / valor_ponto) * qtd
                else:
                    lucro_reais = 0

                # Retorno %
                retorno_percent = (lucro_pontos / entrada) * 100 if entrada != 0 else 0

                # Armazenar
                resultado = {
                    'Ação': ticker_nome,
                    'Total Eventos': 1,
                    'Lucro (R$)': lucro_reais,
                    'Retorno (%)': retorno_percent
                }

                if sinal == 'COMPRA':
                    resultados_compras.append(resultado)
                elif sinal == 'VENDA':
                    resultados_vendas.append(resultado)

        # Exibir resumos
        if resultados_compras:
            st.subheader("🟢 Resumo de Compras - Mercado Caiu")
            df_compras = pd.DataFrame(resultados_compras)
            resumo_compras = df_compras.groupby('Ação').agg({
                'Total Eventos': 'sum',
                'Lucro (R$)': 'sum'
            }).reset_index()

            acertos_compras = df_compras[df_compras['Lucro (R$)'] > 0].groupby('Ação').size().reset_index(name='Acertos')
            resumo_compras = resumo_compras.merge(acertos_compras, on='Ação', how='left').fillna(0)
            resumo_compras['Acertos'] = resumo_compras['Acertos'].astype(int)
            resumo_compras['Taxa de Acerto'] = (resumo_compras['Acertos'] / resumo_compras['Total Eventos'] * 100).round(2).astype(str) + '%'

            retorno_medio = df_compras.groupby('Ação')['Lucro (R$)'].mean().round(2)
            resumo_compras['Retorno Médio (R$)'] = resumo_compras['Ação'].map(retorno_medio).apply(lambda x: f'R$ {x:.2f}')
            resumo_compras['Lucro Total (R$)'] = resumo_compras['Lucro (R$)'].round(2).apply(lambda x: f'R$ {x:.2f}')

            resumo_compras = resumo_compras[[
                'Ação', 'Total Eventos', 'Acertos', 'Taxa de Acerto',
                'Retorno Médio (R$)', 'Lucro Total (R$)'
            ]]

            st.table(resumo_compras)
        else:
            st.info("ℹ️ Nenhuma operação de compra foi registrada.")

        if resultados_vendas:
            st.subheader("🔴 Resumo de Vendas - Mercado Subiu")
            df_vendas = pd.DataFrame(resultados_vendas)
            resumo_vendas = df_vendas.groupby('Ação').agg({
                'Total Eventos': 'sum',
                'Lucro (R$)': 'sum'
            }).reset_index()

            acertos_vendas = df_vendas[df_vendas['Lucro (R$)'] > 0].groupby('Ação').size().reset_index(name='Acertos')
            resumo_vendas = resumo_vendas.merge(acertos_vendas, on='Ação', how='left').fillna(0)
            resumo_vendas['Acertos'] = resumo_vendas['Acertos'].astype(int)
            resumo_vendas['Taxa de Acerto'] = (resumo_vendas['Acertos'] / resumo_vendas['Total Eventos'] * 100).round(2).astype(str) + '%'

            retorno_medio_v = df_vendas.groupby('Ação')['Lucro (R$)'].mean().round(2)
            resumo_vendas['Retorno Médio (R$)'] = resumo_vendas['Ação'].map(retorno_medio_v).apply(lambda x: f'R$ {x:.2f}')
            resumo_vendas['Lucro Total (R$)'] = resumo_vendas['Lucro (R$)'].round(2).apply(lambda x: f'R$ {x:.2f}')

            resumo_vendas = resumo_vendas[[
                'Ação', 'Total Eventos', 'Acertos', 'Taxa de Acerto',
                'Retorno Médio (R$)', 'Lucro Total (R$)'
            ]]

            st.table(resumo_vendas)
        else:
            st.info("ℹ️ Nenhuma operação de venda foi registrada.")

    # 6. Detalhamento por ação
    st.header("🔍 Detalhamento por Ação")
    nome_acao = st.text_input("Digite o nome da ação (ex: ITUB4, WINZ25, DOLZ25)")
    if st.button("📥 Mostrar detalhamento") and nome_acao:
        encontrado = False
        detalhes_compras = []
        detalhes_vendas = []

        for item in dfs_processados:
            ticker_nome = item['ticker'].upper()
            nome_acao_upper = nome_acao.upper()

            # Verificar se o nome da ação está no ticker
            if nome_acao_upper in ticker_nome or ticker_nome.replace('5-MIN_', '').replace('_', '') == nome_acao_upper:
                df = item['df'].copy()
                df['hora'] = df.index.time
                df = df[df['hora'].between(hora_inicio, hora_fim_pregao)]
                dias_uteis = pd.unique(df['data_sozinha'])

                for dia in dias_uteis:
                    df_dia = df[df['data_sozinha'] == dia]
                    if df_dia.empty or len(df_dia) <= candles_pos_entrada:
                        continue

                    entrada_row = df_dia.iloc[0]
                    entrada_dt = entrada_row.name  # Timestamp com data e hora
                    preco_entrada = entrada_row['open']

                    saida_row = df_dia.iloc[candles_pos_entrada]
                    saida_dt = saida_row.name  # Timestamp com data e hora
                    preco_saida = saida_row['close']

                    fechamento_anterior = df_dia.iloc[-1]['close']
                    dist_percent = ((preco_entrada - fechamento_anterior) / fechamento_anterior) * 100

                    # Sinal
                    if dist_percent <= -dist_venda:
                        sinal = 'VENDA'
                    elif dist_percent >= dist_compra:
                        sinal = 'COMPRA'
                    else:
                        continue

                    # Lucro e retorno
                    lucro_pontos = (preco_saida - preco_entrada) if sinal == 'COMPRA' else (preco_entrada - preco_saida)
                    lucro_reais = (lucro_pontos / valor_ponto) * qtd
                    retorno_percent = (lucro_pontos / preco_entrada) * 100 if preco_entrada != 0 else 0

                    detalhe = {
                        'Data Entrada': entrada_dt.strftime('%d/%m/%Y %H:%M'),
                        'Data Saída': saida_dt.strftime('%d/%m/%Y %H:%M'),
                        'Preço Entrada': f"{preco_entrada:.2f}",
                        'Preço Saída': f"{preco_saida:.2f}",
                        'Lucro (R$)': f"{lucro_reais:.2f}",
                        'Retorno (%)': f"{retorno_percent:.2f}%"
                    }

                    if sinal == 'COMPRA':
                        detalhes_compras.append(detalhe)
                    elif sinal == 'VENDA':
                        detalhes_vendas.append(detalhe)

                encontrado = True
                break

        if detalhes_compras:
            st.subheader(f"🛒 Compras em {nome_acao}:")
            df_compras = pd.DataFrame(detalhes_compras)
            st.table(df_compras)
        else:
            st.info(f"ℹ️ Nenhuma operação de compra encontrada para {nome_acao}.")

        if detalhes_vendas:
            st.subheader(f"🛒 Vendas em {nome_acao}:")
            df_vendas = pd.DataFrame(detalhes_vendas)
            st.table(df_vendas)
        elif encontrado:
            st.info(f"ℹ️ Nenhuma operação de venda encontrada para {nome_acao}.")
        elif not encontrado:
            st.warning("⚠️ Ação não encontrada nos arquivos carregados.")

else:
    st.info("ℹ️ Aguardando upload de arquivos Excel.")
