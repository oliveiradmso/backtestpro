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

# Configurações
st.header("⚙️ Configure o Backtest")
tipo_ativo = st.selectbox("Selecione o tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
qtd = st.number_input("Quantidade", min_value=1, value=1)
candles_pos_entrada = st.number_input("Número de Candles após entrada", min_value=1, value=3)
dist_compra = st.number_input("Distorção mínima COMPRA (%)", value=0.3)
dist_venda = st.number_input("Distorção mínima VENDA (%)", value=0.3)
hora_inicio = st.time_input("Horário de entrada", value=time_obj(9, 0))
hora_fim_pregao = st.time_input("Fechamento do pregão", value=time_obj(17, 30))

# Filtro de data
st.subheader("📅 Filtro de período")
data_inicio = st.date_input("Data inicial", value=None)
data_fim = st.date_input("Data final", value=None)

# Upload
st.header("📤 Faça upload do seu arquivo Excel")
uploaded_files = st.file_uploader("Escolha um ou mais arquivos .xlsx", type=["xlsx"], accept_multiple_files=True)

# Processamento
if uploaded_files:
    resultados_gerais = []

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

            # Aplicar filtro de data, se definido
            if data_inicio:
                df = df[df['data'] >= pd.Timestamp(data_inicio)]
            if data_fim:
                df = df[df['data'] <= pd.Timestamp(data_fim)]

            # Verifica se ainda há dados
            if df.empty:
                st.warning(f"⚠️ Nenhum dado encontrado entre {data_inicio} e {data_fim}")
                continue

            # Identificar tipo do ativo
            ticker_nome = file.name.split(".")[0]
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

                # Preço de entrada
                entrada = df_dia.iloc[0]['open']
                fechamento = df_dia.iloc[-1]['close']

                # Distorção
                dist_percent = ((entrada - fechamento) / fechamento) * 100

                # Sinal
                if dist_percent <= -dist_venda:
                    sinal = 'VENDA'
                elif dist_percent >= dist_compra:
                    sinal = 'COMPRA'
                else:
                    sinal = 'SEM SINAL'

                # Resultado
                resultado = 0
                if len(df_dia) > candles_pos_entrada:
                    preco_saida = df_dia.iloc[candles_pos_entrada]['close']
                    if sinal == 'COMPRA':
                        resultado = (preco_saida - entrada) / valor_ponto * qtd
                    elif sinal == 'VENDA':
                        resultado = (entrada - preco_saida) / valor_ponto * qtd

                # Armazenar
                resultados_gerais.append({
                    'Arquivo': file.name,
                    'Data': dia.strftime('%d/%m/%Y'),
                    'Entrada': f"{entrada:.5f}",
                    'Fechamento Anterior': f"{fechamento:.5f}",
                    'Distorção (%)': f"{dist_percent:.2f}",
                    'Sinal': sinal,
                    'Resultado (pontos)': f"{resultado:.2f}"
                })

        except Exception as e:
            st.error(f"Erro ao processar {file.name}: {e}")
            continue

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
        st.info("ℹ️ Nenhum dado processado. Verifique os arquivos e filtros.")
else:
    st.info("ℹ️ Aguardando upload de arquivos Excel.")
