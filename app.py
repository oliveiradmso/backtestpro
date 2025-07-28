import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj, timedelta

# Função corrigida para identificar o tipo de ativo
def identificar_tipo(ticker):
    ticker = ticker.upper().strip()
    if '.' in ticker:
        ticker = ticker.split('.')[0]
    for prefix in ['5-MIN_', 'MINI_', 'MIN_']:
        if ticker.startswith(prefix):
            ticker = ticker[len(prefix):]
    
    if 'WIN' in ticker or 'INDICE' in ticker:
        return 'mini_indice'
    if 'WDO' in ticker or 'DOLAR' in ticker or 'DOL' in ticker:
        return 'mini_dolar'
    
    acoes = ['PETR', 'VALE', 'ITUB', 'BBDC', 'BEEF', 'ABEV', 'ITSA', 'JBSS', 'RADL', 'CIEL', 'GOLL', 'AZUL', 'BBAS', 'SANB']
    for acao in acoes:
        if acao in ticker:
            return 'acoes'
    
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

    # Nova opção: Referência para cálculo da distorção
    referencia = st.selectbox(
        "Referência para cálculo da distorção",
        [
            "Fechamento do dia anterior",
            "Mínima do dia anterior",
            "Abertura do dia atual"
        ]
    )
    
    # Definir horários disponíveis por tipo de ativo
    if tipo_ativo == "acoes":
        todos_horarios = [
            "10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30",
            "10:35", "10:40", "10:45", "10:50", "10:55", "11:00", "11:05",
            "11:10", "11:15", "11:20", "11:25", "11:30", "11:35", "11:40",
            "11:45", "11:50", "11:55", "12:00", "12:05", "12:10", "12:15",
            "12:20", "12:25", "12:30", "12:35", "12:40", "12:45", "12:50",
            "12:55", "13:00", "13:05", "13:10", "13:15", "13:20", "13:25",
            "13:30", "13:35", "13:40", "13:45", "13:50", "13:55", "14:00",
            "14:05", "14:10", "14:15", "14:20", "14:25", "14:30", "14:35",
            "14:40", "14:45", "14:50", "14:55", "15:00", "15:05", "15:10",
            "15:15", "15:20", "15:25", "15:30", "15:35", "15:40", "15:45",
            "15:50", "15:55", "16:00", "16:05", "16:10", "16:15", "16:20",
            "16:25", "16:30", "16:35", "16:40", "16:45", "16:50", "16:55",
            "17:00"
        ]
        horario_inicial, horario_final = "10:00", "17:00"
    else:  # mini_indice ou mini_dolar
        todos_horarios = [
            "09:00", "09:05", "09:10", "09:15", "09:20", "09:25", "09:30",
            "09:35", "09:40", "09:45", "09:50", "09:55", "10:00", "10:05",
            "10:10", "10:15", "10:20", "10:25", "10:30", "10:35", "10:40",
            "10:45", "10:50", "10:55", "11:00", "11:05", "11:10", "11:15",
            "11:20", "11:25", "11:30", "11:35", "11:40", "11:45", "11:50",
            "11:55", "12:00", "12:05", "12:10", "12:15", "12:20", "12:25",
            "12:30", "12:35", "12:40", "12:45", "12:50", "12:55", "13:00",
            "13:05", "13:10", "13:15", "13:20", "13:25", "13:30", "13:35",
            "13:40", "13:45", "13:50", "13:55", "14:00", "14:05", "14:10",
            "14:15", "14:20", "14:25", "14:30", "14:35", "14:40", "14:45",
            "14:50", "14:55", "15:00", "15:05", "15:10", "15:15", "15:20",
            "15:25", "15:30", "15:35", "15:40", "15:45", "15:50", "15:55",
            "16:00", "16:05", "16:10", "16:15", "16:20", "16:25", "16:30",
            "16:35", "16:40", "16:45", "16:50", "16:55", "17:00", "17:05",
            "17:10", "17:15", "17:20", "17:25", "17:30", "17:35", "17:40",
            "17:45", "17:50", "17:55", "18:00", "18:05", "18:10", "18:15",
            "18:20", "18:25", "18:30"
        ]
        horario_inicial, horario_final = "09:00", "18:30"

    # Seleção de horários
    horarios_selecionados = st.multiselect(
        f"Selecione os horários de entrada ({horario_inicial} às {horario_final})",
        todos_horarios,
        default=[horario_inicial]
    )

    # Validar horários selecionados
    if horarios_selecionados:
        def horario_para_minutos(h):
            h, m = map(int, h.split(":"))
            return h * 60 + m

        min_inicial = horario_para_minutos(horario_inicial)
        min_final = horario_para_minutos(horario_final)

        invalidos = [
            h for h in horarios_selecionados
            if not (min_inicial <= horario_para_minutos(h) <= min_final)
        ]

        if invalidos:
            st.error(f"❌ Horários inválidos selecionados: {', '.join(invalidos)}. Para **{tipo_ativo}**, o intervalo válido é de **{horario_inicial} às {horario_final}**.")
            st.stop()
    else:
        st.warning(f"⚠️ Selecione pelo menos um horário entre **{horario_inicial} e {horario_final}**.")
        st.stop()

    # Botão para rodar
    if st.button("🚀 Rodar Backtest"):
        with st.expander("ℹ️ Ver detalhes do processamento", expanded=False):
            st.write("🔄 Iniciando processamento...")

            # Armazenar resultados por horário
            resultados_por_horario = []
            todas_operacoes = []  # Para detalhamento por ação

            total_dias_analisados = 0
            dias_com_sinal = 0

            for horario_str in horarios_selecionados:
                hora, minuto = map(int, horario_str.split(":"))
                hora_inicio = time_obj(hora, minuto)
                st.write(f"⏰ Processando horário: {horario_str}")

                # ✅ Listas limpas para CADA horário
                operacoes_horario = []

                for file in uploaded_files:
                    try:
                        ticker_nome = file.name.split(".")[0]
                        tipo_arquivo = identificar_tipo(ticker_nome)

                        if tipo_arquivo != tipo_ativo:
                            continue

                        df = pd.read_excel(file)
                        df.columns = [str(col).strip().capitalize() for col in df.columns]
                        df.rename(columns={'Data': 'data', 'Abertura': 'open', 'Máxima': 'high', 'Mínima': 'low', 'Fechamento': 'close'}, inplace=True)
                        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
                        df = df.dropna(subset=['data'])
                        df['data_limpa'] = df['data'].dt.floor('min')
                        df = df.set_index('data_limpa').sort_index()
                        df['data_sozinha'] = df.index.date
                        df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]

                        if df.empty:
                            continue

                        dias_unicos = pd.unique(df['data_sozinha'])

                        for i in range(len(dias_unicos)):
                            dia_atual = dias_unicos[i]
                            df_dia_atual = df[df['data_sozinha'] == dia_atual].copy()
                            mascara_pregao = (df_dia_atual.index.time >= time_obj(9, 0)) & (df_dia_atual.index.time <= time_obj(17, 30))
                            df_pregao = df_dia_atual[mascara_pregao]

                            if df_pregao.empty:
                                continue

                            # Encontrar o candle mais próximo do horário
                            def time_to_minutes(t):
                                return t.hour * 60 + t.minute

                            minutos_desejado = time_to_minutes(hora_inicio)
                            minutos_candles = [time_to_minutes(t) for t in df_pregao.index.time]
                            diferencas = [abs(m - minutos_desejado) for m in minutos_candles]
                            melhor_idx = np.argmin(diferencas)
                            idx_entrada = df_pregao.index[melhor_idx]
                            preco_entrada = df_pregao.loc[idx_entrada]["open"]

                            # Saída
                            idx_saida = idx_entrada + timedelta(minutes=5 * int(candles_pos_entrada))
                            if idx_saida not in df.index or idx_saida.date() != idx_entrada.date():
                                continue
                            preco_saida = df.loc[idx_saida]["open"]

                            # Calcular referência com base na seleção
                            try:
                                idx_dia_atual_idx = list(dias_unicos).index(dia_atual)
                                if idx_dia_atual_idx == 0:
                                    continue  # Pula o primeiro dia
                                dia_anterior = dias_unicos[idx_dia_atual_idx - 1]
                            except:
                                continue

                            referencia_valor = 0

                            if referencia == "Fechamento do dia anterior":
                                try:
                                    referencia_valor = df[df.index.date == dia_anterior]["close"].iloc[-1]
                                except:
                                    continue
                            elif referencia == "Mínima do dia anterior":
                                try:
                                    referencia_valor = df[df.index.date == dia_anterior]["low"].min()
                                except:
                                    continue
                            elif referencia == "Abertura do dia atual":
                                try:
                                    referencia_valor = df_dia_atual.iloc[0]["open"]
                                except:
                                    continue

                            # Calcular distorção
                            distorcao_percentual = 0
                            if referencia_valor > 0:
                                distorcao = preco_entrada - referencia_valor
                                distorcao_percentual = (distorcao / referencia_valor) * 100

                            # Verificar distorção mínima
                            if distorcao_percentual < -dist_compra:
                                if tipo_ativo == "acoes":
                                    lucro_reais = (preco_saida - preco_entrada) * qtd
                                else:
                                    valor_ponto = 0.20 if tipo_ativo == "mini_indice" else 10.00
                                    lucro_reais = (preco_saida - preco_entrada) * valor_ponto * qtd

                                operacoes_horario.append({
                                    "tipo": "Compra",
                                    "lucro": lucro_reais,
                                    "ticker": ticker_nome,
                                    "data": dia_atual
                                })
                                todas_operacoes.append({
                                    "Ação": ticker_nome,
                                    "Direção": "Compra",
                                    "Horário": idx_entrada.strftime("%H:%M"),
                                    "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                    "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                    "Preço Entrada": round(preco_entrada, 2),
                                    "Preço Saída": round(preco_saida, 2),
                                    "Lucro (R$)": round(lucro_reais, 2),
                                    "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                    "Quantidade": qtd
                                })

                            elif distorcao_percentual > dist_venda:
                                if tipo_ativo == "acoes":
                                    lucro_reais = (preco_entrada - preco_saida) * qtd
                                else:
                                    valor_ponto = 0.20 if tipo_ativo == "mini_indice" else 10.00
                                    lucro_reais = (preco_entrada - preco_saida) * valor_ponto * qtd

                                operacoes_horario.append({
                                    "tipo": "Venda",
                                    "lucro": lucro_reais,
                                    "ticker": ticker_nome,
                                    "data": dia_atual
                                })
                                todas_operacoes.append({
                                    "Ação": ticker_nome,
                                    "Direção": "Venda",
                                    "Horário": idx_entrada.strftime("%H:%M"),
                                    "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                    "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                    "Preço Entrada": round(preco_entrada, 2),
                                    "Preço Saída": round(preco_saida, 2),
                                    "Lucro (R$)": round(lucro_reais, 2),
                                    "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                    "Quantidade": qtd
                                })

                    except Exception as e:
                        st.write(f"❌ Erro ao processar {file.name}: {e}")
                        continue

                # ✅ Calcular resultados para este horário
                compras = [op for op in operacoes_horario if op["tipo"] == "Compra"]
                vendas = [op for op in operacoes_horario if op["tipo"] == "Venda"]

                if compras:
                    total = len(compras)
                    acertos = len([op for op in compras if op["lucro"] > 0])
                    lucro_total = sum(op["lucro"] for op in compras)
                    resultados_por_horario.append({
                        "Horário": horario_str,
                        "Total Eventos": total,
                        "Acertos": acertos,
                        "Taxa de Acerto": f"{acertos/total:.2%}" if total > 0 else "0.00%",
                        "Lucro Total (R$)": f"R$ {lucro_total:.2f}",
                        "Direção": "Compra"
                    })

                if vendas:
                    total = len(vendas)
                    acertos = len([op for op in vendas if op["lucro"] > 0])
                    lucro_total = sum(op["lucro"] for op in vendas)
                    resultados_por_horario.append({
                        "Horário": horario_str,
                        "Total Eventos": total,
                        "Acertos": acertos,
                        "Taxa de Acerto": f"{acertos/total:.2%}" if total > 0 else "0.00%",
                        "Lucro Total (R$)": f"R$ {lucro_total:.2f}",
                        "Direção": "Venda"
                    })

            # ✅ SALVAR NO SESSION STATE (APENAS UMA VEZ)
            if resultados_por_horario:
                st.session_state.resultados_por_horario = pd.DataFrame(resultados_por_horario)
            if todas_operacoes:
                st.session_state.todas_operacoes = pd.DataFrame(todas_operacoes)
                st.write(f"✅ Backtest concluído: {len(todas_operacoes)} operações registradas.")
            else:
                st.write("❌ Nenhuma operação foi registrada.")
                st.session_state.todas_operacoes = pd.DataFrame()

        # ✅ Mostrar rankings na tela principal
        if 'resultados_por_horario' in st.session_state:
            df_rank = st.session_state.resultados_por_horario

            # 🏆 Ranking de Compras
            df_compras = df_rank[df_rank['Direção'] == 'Compra']
            if not df_compras.empty:
                st.header("🏆 Ranking de Compras")
                df_compras['Lucro Num'] = (
                    df_compras['Lucro Total (R$)']
                    .str.replace('R\$', '', regex=True)
                    .str.strip()
                    .str.replace(',', '.')
                    .str.replace(' ', '')
                    .astype(float)
                )
                df_compras = df_compras.sort_values('Lucro Num', ascending=False)
                st.dataframe(df_compras.drop('Lucro Num', axis=1), use_container_width=True)

            # 📉 Ranking de Vendas
            df_vendas = df_rank[df_rank['Direção'] == 'Venda']
            if not df_vendas.empty:
                st.header("📉 Ranking de Vendas")
                df_vendas['Lucro Num'] = (
                    df_vendas['Lucro Total (R$)']
                    .str.replace('R\$', '', regex=True)
                    .str.strip()
                    .str.replace(',', '.')
                    .str.replace(' ', '')
                    .astype(float)
                )
                df_vendas = df_vendas.sort_values('Lucro Num', ascending=False)
                st.dataframe(df_vendas.drop('Lucro Num', axis=1), use_container_width=True)

    # 6. Detalhamento por ação
    st.header("🔍 Detalhamento por Ação")
    nome_acao = st.text_input("Digite o nome da ação (ex: ITUB4, WINZ25, DOLZ25)")
    if st.button("📥 Mostrar detalhamento") and nome_acao:
        if "todas_operacoes" in st.session_state and not st.session_state.todas_operacoes.empty:
            df_ops = st.session_state.todas_operacoes
            mask = df_ops['Ação'].str.contains(nome_acao, case=False, na=False)
            df_filtrado = df_ops[mask]

            if not df_filtrado.empty:
                # Separar em compras e vendas
                df_compras = df_filtrado[df_filtrado['Direção'] == 'Compra']
                df_vendas = df_filtrado[df_filtrado['Direção'] == 'Venda']

                if not df_compras.empty:
                    st.subheader("🛒 Detalhamento de Compras")
                    st.dataframe(df_compras, use_container_width=True)
                else:
                    st.info(f"ℹ️ Nenhuma operação de compra encontrada para {nome_acao}.")

                if not df_vendas.empty:
                    st.subheader("🔻 Detalhamento de Vendas")
                    st.dataframe(df_vendas, use_container_width=True)
                else:
                    st.info(f"ℹ️ Nenhuma operação de venda encontrada para {nome_acao}.")
            else:
                st.info(f"ℹ️ Nenhuma operação encontrada para {nome_acao}.")
        else:
            st.warning("⚠️ Nenhum backtest foi rodado ainda ou nenhuma operação foi registrada.")

else:
    st.info("ℹ️ Aguardando upload de arquivos Excel.")
