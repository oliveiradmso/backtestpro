import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj

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

# Variável para armazenar o período global
data_min_global = None
data_max_global = None
dfs_processados = []

if uploaded_files:
    st.info(f"✅ {len(uploaded_files)} arquivo(s) carregado(s). Processando...")

    # 2. Pré-processar para obter o período disponível
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
            df['data_sozinha'] = df['data'].dt.date  # só a data, sem hora

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

    # 3. Mostrar período disponível
    if data_min_global and data_max_global:
        st.subheader("📅 Período disponível para análise")
        st.write(f"**Data inicial mais antiga:** {data_min_global.strftime('%d/%m/%Y')}")
        st.write(f"**Data final mais recente:** {data_max_global.strftime('%d/%m/%Y')}")

        # 4. Filtro de período
        st.subheader("🔍 Filtro de período")
        data_inicio = st.date_input("Data inicial", value=data_min_global, min_value=data_min_global, max_value=data_max_global)
        data_fim = st.date_input("Data final", value=data_max_global, min_value=data_min_global, max_value=data_max_global)

        # Validar
        if data_inicio > data_fim:
            st.error("❌ A data inicial não pode ser maior que a final.")
            st.stop()

        # 5. Configurações
        st.header("⚙️ Configure o Backtest")
        tipo_ativo = st.selectbox("Selecione o tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
        qtd = st.number_input("Quantidade", min_value=1, value=1)
        candles_pos_entrada = st.number_input("Número de Candles após entrada", min_value=1, value=3)
        dist_compra = st.number_input("Distorção mínima COMPRA (%)", value=0.3)
        dist_venda = st.number_input("Distorção mínima VENDA (%)", value=0.3)
        hora_inicio = st.time_input("Horário de entrada", value=time_obj(9, 0))
        hora_fim_pregao = st.time_input("Fechamento do pregão", value=time_obj(17, 30))

        # 6. Botão para rodar
        if st.button("🚀 Rodar Backtest"):
            resultados_gerais = []

            for item in dfs_processados:
                df = item['df'].copy()
                ticker_nome = item['ticker']

                # Aplicar filtro de data
                df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]
                if df.empty:
                    continue

                # Identificar tipo do ativo
                tipo_arquivo = identificar_tipo(ticker_nome)

                # Ajustar valor do ponto
                if tipo_ativo == "acoes":
                    valor_ponto = 0.01
                elif tipo_ativo == "mini_indice":
                    valor_ponto = 0.5
                else:
                    valor_ponto = 0.005

                # Calcular preço de entrada
                df['hora'] = df['data'].dt.time
                mask_horario = df['hora'].between(hora_inicio, hora_fim_pregao)
                dias_uteis = df[mask_horario]['data_sozinha'].unique()

                for dia in dias_uteis:
                    df_dia = df[df['data_sozinha'] == dia]
                    if df_dia.empty:
                        continue

                    entrada = df_dia.iloc[0]['open']
                    fechamento = df_dia.iloc[-1]['close']
                    dist_percent = ((entrada - fechamento) / fechamento) * 100

                    if dist_percent <= -dist_venda:
                        sinal = 'VENDA'
                    elif dist_percent >= dist_compra:
                        sinal = 'COMPRA'
                    else:
                        sinal = 'SEM SINAL'

                    resultado = 0
                    if len(df_dia) > candles_pos_entrada:
                        preco_saida = df_dia.iloc[candles_pos_entrada]['close']
                        if sinal == 'COMPRA':
                            resultado = (preco_saida - entrada) / valor_ponto * qtd
                        elif sinal == 'VENDA':
                            resultado = (entrada - preco_saida) / valor_ponto * qtd

                    resultados_gerais.append({
                        'Arquivo': item['file'].name,
                        'Data': dia.strftime('%d/%m/%Y'),
                        'Entrada': f"{entrada:.5f}",
                        'Fechamento Anterior': f"{fechamento:.5f}",
                        'Distorção (%)': f"{dist_percent:.2f}",
                        'Sinal': sinal,
                        'Resultado (pontos)': f"{resultado:.2f}"
                    })

            # Exibir resultados
            if resultados_gerais:
                df_resultados = pd.DataFrame(resultados_gerais)
                st.subheader("📈 Resultados do Backtest")
                st.dataframe(df_resultados)

                # Estatísticas
                df_resultados['Resultado (pontos)'] = pd.to_numeric(df_resultados['Resultado (pontos)'], errors='coerce')
                total_operacoes = len(df_resultados)
                acertos = len(df_resultados[df_resultados['Resultado (pontos)'] > 0])
                taxa_acerto = (acertos / total_operacoes * 100) if total_operacoes > 0 else 0
                lucro_total = df_resultados['Resultado (pontos)'].sum()

                st.write(f"**Total de operações:** {total_operacoes}")
                st.write(f"**Taxa de acerto:** {taxa_acerto:.1f}%")
                st.write(f"**Lucro total (pontos):** {lucro_total:.2f}")
            else:
                st.info("ℹ️ Nenhum dado processado com os filtros atuais.")

    # 7. Detalhamento por ação
    st.header("🔍 Detalhamento por Ação")
    nome_acao = st.text_input("Digite o nome da ação (ex: ITUB4, WINZ25, DOLZ25)")
    if st.button("📥 Mostrar detalhamento") and nome_acao:
        # Buscar o arquivo correspondente
        encontrado = False
        for item in dfs_processados:
            if nome_acao.upper() in item['ticker'].upper():
                df = item['df']
                st.write(f"### Dados da ação: {nome_acao}")
                st.dataframe(df[['data', 'open', 'high', 'low', 'close']].head(20))
                encontrado = True
                break
        if not encontrado:
            st.warning("⚠️ Ação não encontrada nos arquivos carregados.")
else:
    st.info("ℹ️ Aguardando upload de arquivos Excel.")
