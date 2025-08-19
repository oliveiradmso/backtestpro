import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj, timedelta
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import random

# ========================
# 🔗 CONFIGURAÇÃO DE URL
# ========================
GOOGLE_SHEET_CSV = "https://docs.google.com/spreadsheets/d/1wj5qNNuje6U8VJvRd5eclUNuVCZ4Oc_KDs6ezGBBCpg/gviz/tq?tqx=out:csv&sheet=Clientes"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxuOaM6lWlDf8Z87y7PYKfpKsfz1pSFLU8s1y2zaJRlLZVB6KLvlixEqKC1zBH5ehIAMw/exec"

# ========================
# 🔁 FUNÇÃO PARA CARREGAR ASSINANTES (fora do token)
# ========================
@st.cache_data(ttl=600)
def carregar_assinantes():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV)
        if 'expira_em' in df.columns:
            df['expira_em'] = pd.to_datetime(df['expira_em'], errors='coerce')
        return df
    except Exception as e:
        st.error("❌ Erro ao carregar assinantes.")
        return pd.DataFrame()

# ========================
# 🔑 VERIFICAÇÃO DE TOKEN ANTES DE TUDO
# ========================
token = st.query_params.get("token", "")

if token:
    st.markdown("<h1 style='text-align: center;'>🔑 Ativando sua conta</h1>", unsafe_allow_html=True)

    df = carregar_assinantes()
    if df.empty:
        st.error("❌ Falha ao carregar dados.")
        st.stop()

    user = df[df['token_confirmacao'] == token]

    if user.empty:
        st.error("❌ Token inválido ou já utilizado.")
        st.stop()

    if user.iloc[0]['ativo'] == 'SIM':
        st.success("✅ Sua conta já foi ativada.")
        st.info("Você pode fechar esta aba e acessar normalmente.")
        st.stop()

    # Ativa o usuário
    df.loc[df['token_confirmacao'] == token, 'ativo'] = 'SIM'
    df.loc[df['token_confirmacao'] == token, 'data_confirmacao'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        linha = user.iloc[0].to_dict()
        response = requests.post(WEBHOOK_URL, json=linha)
        if response.status_code == 200:
            st.success("✅ Parabéns! Sua conta foi ativada com sucesso.")
            st.balloons()
            st.info("Volte ao app e faça login com seu email e senha.")
        else:
            st.error("❌ Erro ao confirmar. Tente novamente.")
    except Exception as e:
        st.error(f"❌ Falha ao conectar: {e}")

    st.stop()  # Não executa o resto do appimport streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time as time_obj, timedelta
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import random

# ========================
# 🔗 CONFIGURAÇÃO DE URL
# ========================
GOOGLE_SHEET_CSV = "https://docs.google.com/spreadsheets/d/1wj5qNNuje6U8VJvRd5eclUNuVCZ4Oc_KDs6ezGBBCpg/gviz/tq?tqx=out:csv&sheet=Clientes"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxuOaM6lWlDf8Z87y7PYKfpKsfz1pSFLU8s1y2zaJRlLZVB6KLvlixEqKC1zBH5ehIAMw/exec"

# ========================
# 🔁 FUNÇÃO PARA CARREGAR ASSINANTES (fora do token)
# ========================
@st.cache_data(ttl=600)
def carregar_assinantes():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV)
        if 'expira_em' in df.columns:
            df['expira_em'] = pd.to_datetime(df['expira_em'], errors='coerce')
        return df
    except Exception as e:
        st.error("❌ Erro ao carregar assinantes.")
        return pd.DataFrame()

# ========================
# 🔑 VERIFICAÇÃO DE TOKEN ANTES DE TUDO
# ========================
token = st.query_params.get("token", "")

if token:
    st.markdown("<h1 style='text-align: center;'>🔑 Ativando sua conta</h1>", unsafe_allow_html=True)

    df = carregar_assinantes()
    if df.empty:
        st.error("❌ Falha ao carregar dados.")
        st.stop()

    user = df[df['token_confirmacao'] == token]

    if user.empty:
        st.error("❌ Token inválido ou já utilizado.")
        st.stop()

    if user.iloc[0]['ativo'] == 'SIM':
        st.success("✅ Sua conta já foi ativada.")
        st.info("Você pode fechar esta aba e acessar normalmente.")
        st.stop()

    # Ativa o usuário
    df.loc[df['token_confirmacao'] == token, 'ativo'] = 'SIM'
    df.loc[df['token_confirmacao'] == token, 'data_confirmacao'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        linha = user.iloc[0].to_dict()
        response = requests.post(WEBHOOK_URL, json=linha)
        if response.status_code == 200:
            st.success("✅ Parabéns! Sua conta foi ativada com sucesso.")
            st.balloons()
            st.info("Volte ao app e faça login com seu email e senha.")
        else:
            st.error("❌ Erro ao confirmar. Tente novamente.")
    except Exception as e:
        st.error(f"❌ Falha ao conectar: {e}")

    st.stop()  # Não executa o resto do app                                    
# ========================
# FUNÇÕES AUXILIARES
# ========================
def extrair_nome_completo(file_name):
    return file_name.split(".")[0]

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

# =====================================================
# 🔹 RASTREAMENTO INTRADAY (5min)
# =====================================================
def processar_rastreamento_intraday(
    uploaded_files,
    tipo_ativo,
    qtd,
    candles_pos_entrada,
    dist_compra_contra,
    dist_venda_contra,
    dist_favor,
    referencia,
    horarios_selecionados,
    data_inicio,
    data_fim,
    modo_estrategia
):
    todas_operacoes = []
    dias_com_entrada = set()
    dias_ignorados = []
    todos_dias_com_dados = set()

    def calcular_max_drawdown(df, idx_entrada, idx_saida, direcao):
        try:
            periodo = df.loc[idx_entrada:idx_saida]
            if periodo.empty or len(periodo) < 2:
                return 0.0
            preco_entrada = periodo.iloc[0]["open"]
            if direcao == "Compra":
                min_preco = periodo["low"].min()
                drawdown = ((min_preco - preco_entrada) / preco_entrada) * 100
            else:
                max_preco = periodo["high"].max()
                drawdown = ((max_preco - preco_entrada) / preco_entrada) * 100
            return round(drawdown, 2)
        except:
            return 0.0

    for horario_str in horarios_selecionados:
        hora, minuto = map(int, horario_str.split(":"))
        hora_inicio = time_obj(hora, minuto)

        for file in uploaded_files:
            try:
                ticker_nome = extrair_nome_completo(file.name)
                tipo_arquivo = identificar_tipo(ticker_nome)
                if tipo_ativo != "todos" and tipo_arquivo != tipo_ativo:
                    continue

                df = pd.read_excel(file)
                df.columns = [str(col).strip().capitalize() for col in df.columns]
                df.rename(columns={'Data': 'data', 'Abertura': 'open', 'Máxima': 'high', 'Mínima': 'low', 'Fechamento': 'close'}, inplace=True)
                df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
                df = df.dropna(subset=['data'])
                df['data_limpa'] = df['data'].dt.floor('min')
                df = df.set_index('data_limpa').sort_index()
                df = df[~df.index.duplicated(keep='first')]
                df['data_sozinha'] = df.index.date
                df = df[(df['data_sozinha'] >= data_inicio) & (df['data_sozinha'] <= data_fim)]

                if df.empty:
                    continue

                dias_no_arquivo = df['data_sozinha'].unique()
                todos_dias_com_dados.update(dias_no_arquivo)
                dias_unicos = pd.unique(df['data_sozinha'])

                for i in range(1, len(dias_unicos)):
                    dia_atual = dias_unicos[i]
                    dia_anterior = dias_unicos[i - 1]
                    df_dia_atual = df[df['data_sozinha'] == dia_atual].copy()

                    if tipo_ativo in ['mini_indice', 'mini_dolar']:
                        mascara_pregao = (df_dia_atual.index.time >= time_obj(9, 0)) & (df_dia_atual.index.time <= time_obj(18, 20))
                    else:
                        mascara_pregao = (df_dia_atual.index.time >= time_obj(10, 0)) & (df_dia_atual.index.time <= time_obj(17, 0))
                    df_pregao = df_dia_atual[mascara_pregao]
                    if df_pregao.empty:
                        dias_ignorados.append((dia_atual, "Sem pregão válido"))
                        continue

                    def time_to_minutes(t):
                        return t.hour * 60 + t.minute

                    minutos_desejado = time_to_minutes(hora_inicio)
                    minutos_candles = [time_to_minutes(t) for t in df_pregao.index.time]
                    diferencas = [abs(m - minutos_desejado) for m in minutos_candles]
                    melhor_idx = np.argmin(diferencas)
                    idx_entrada = df_pregao.index[melhor_idx]
                    preco_entrada = df_pregao.loc[idx_entrada]["open"]
                    idx_saida = idx_entrada + timedelta(minutes=5 * int(candles_pos_entrada))

                    if idx_saida not in df.index or idx_saida.date() != idx_entrada.date():
                        dias_ignorados.append((dia_atual, "Sem candle de saída"))
                        continue

                    if tipo_ativo in ['mini_indice', 'mini_dolar'] and idx_saida.time() > time_obj(18, 20):
                        dias_ignorados.append((dia_atual, "Candle de saída após 18:20"))
                        continue
                    elif tipo_ativo == 'acoes' and idx_saida.time() > time_obj(17, 0):
                        dias_ignorados.append((dia_atual, "Candle de saída após 17:00"))
                        continue

                    preco_saida = df.loc[idx_saida]["open"]
                    referencia_valor = None
                    referencia_label = ""

                    if referencia == "Fechamento do dia anterior":
                        ref_series = df[df.index.date == dia_anterior]["close"]
                        if not ref_series.empty:
                            referencia_valor = ref_series.iloc[-1]
                            referencia_label = f"Fechamento {dia_anterior.strftime('%d/%m')}: {referencia_valor:.2f}"
                        else:
                            dias_ignorados.append((dia_atual, "Sem fechamento do dia anterior"))
                            continue
                    elif referencia == "Mínima do dia anterior":
                        ref_series = df[df.index.date == dia_anterior]["low"]
                        if not ref_series.empty:
                            referencia_valor = ref_series.min()
                            referencia_label = f"Mínima {dia_anterior.strftime('%d/%m')}: {referencia_valor:.2f}"
                        else:
                            dias_ignorados.append((dia_atual, "Sem mínima do dia anterior"))
                            continue
                    elif referencia == "Abertura do dia atual":
                        if not df_dia_atual["open"].empty:
                            referencia_valor = df_dia_atual["open"].iloc[0]
                            referencia_label = f"Abertura {dia_atual.strftime('%d/%m')}: {referencia_valor:.2f}"
                        else:
                            dias_ignorados.append((dia_atual, "Sem abertura do dia atual"))
                            continue

                    if referencia_valor is None or referencia_valor <= 0:
                        dias_ignorados.append((dia_atual, "Referência inválida"))
                        continue

                    distorcao_percentual = ((preco_entrada - referencia_valor) / referencia_valor) * 100

                    horario_entrada_str = idx_entrada.strftime("%H:%M")

                    if horario_entrada_str not in horarios_selecionados:
                        continue

                    if tipo_ativo == "acoes":
                        valor_ponto = 1.0
                    else:
                        valor_ponto = 0.20 if tipo_ativo == "mini_indice" else 10.00

                    if modo_estrategia in ["Contra Tendência", "Ambos"]:
                        if distorcao_percentual < -dist_compra_contra:
                            lucro_reais = (preco_saida - preco_entrada) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Compra")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Compra (Contra)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)
                        elif distorcao_percentual > dist_venda_contra:
                            lucro_reais = (preco_entrada - preco_saida) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Venda")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Venda (Contra)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)

                    if modo_estrategia in ["A Favor da Tendência", "Ambos"]:
                        if distorcao_percentual > dist_favor:
                            lucro_reais = (preco_saida - preco_entrada) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Compra")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Compra (Favor)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)
                        elif distorcao_percentual < -dist_favor:
                            lucro_reais = (preco_entrada - preco_saida) * valor_ponto * qtd
                            max_dd = calcular_max_drawdown(df, idx_entrada, idx_saida, "Venda")
                            todas_operacoes.append({
                                "Ação": ticker_nome,
                                "Direção": "Venda (Favor)",
                                "Horário": horario_entrada_str,
                                "Data Entrada": idx_entrada.strftime("%d/%m/%Y %H:%M"),
                                "Data Saída": idx_saida.strftime("%d/%m/%Y %H:%M"),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"{distorcao_percentual:.2f}%",
                                "Quantidade": qtd,
                                "Referência": referencia_label,
                                "Max Drawdown %": max_dd
                            })
                            dias_com_entrada.add(dia_atual)

            except Exception as e:
                st.write(f"❌ Erro ao processar {file.name}: {e}")
                continue

    df_ops = pd.DataFrame(todas_operacoes)
    return df_ops, list(dias_com_entrada), dias_ignorados, sorted(todos_dias_com_dados)
# ========================
# 🔐 CONFIGURAÇÃO DE ASSINATURA
# ========================
GOOGLE_SHEET_CSV = "https://docs.google.com/spreadsheets/d/1wj5qNNuje6U8VJvRd5eclUNuVCZ4Oc_KDs6ezGBBCpg/gviz/tq?tqx=out:csv&sheet=Clientes"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxuOaM6lWlDf8Z87y7PYKfpKsfz1pSFLU8s1y2zaJRlLZVB6KLvlixEqKC1zBH5ehIAMw/exec"

@st.cache_data(ttl=600)
def carregar_assinantes():
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV)
        if 'expira_em' in df.columns:
            df['expira_em'] = pd.to_datetime(df['expira_em'], errors='coerce')
        return df
    except Exception as e:
        st.error("❌ Erro ao carregar assinantes.")
        return pd.DataFrame()

# ========================
# 🔑 GERA TOKEN ÚNICO
# ========================
def gerar_token():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32))

# ========================
# 📨 ENVIA E-MAIL DE BOAS-VINDAS
# ========================
def enviar_email_boas_vindas(email, token):
    try:
        link = f"https://radar-b3.streamlit.app/?token={token}"
        corpo = f"""
        Olá,

        Seja muito bem-vindo ao <strong>Radar B3</strong> — a sua nova ferramenta para identificar oportunidades reais de lucro com base em distorções estatísticas de preço.

        Para ativar sua conta e começar a usar o sistema, é só clicar no botão abaixo:

        <div style='text-align: center; margin: 20px 0;'>
            <a href='{link}' style='background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;'>
                CONFIRMAR MEU E-MAIL AGORA
            </a>
        </div>

        Após a confirmação, você poderá acessar com seu email e senha, sem complicações.

        Atenciosamente,  
        Equipe Radar B3  
        contatoradarb3@gmail.com
        """
        data = {
            "email": email,
            "assunto": "🎉 Bem-vindo ao Radar B3! Confirme seu e-mail para ativar sua conta",
            "corpo": corpo
        }
        response = requests.post(WEBHOOK_URL, json=data)
        return response.status_code == 200
    except:
        return False

# ========================
# ✅ PÁGINA DE CONFIRMAÇÃO
# ========================
def pagina_confirmacao():
    token = st.query_params.get("token", "")
    if not token:
        st.error("❌ Link inválido ou expirado.")
        return

    df = carregar_assinantes()
    user = df[df['token_confirmacao'] == token]

    if user.empty:
        st.error("❌ Token inválido ou já utilizado.")
        return

    if user.iloc[0]['ativo'] == 'SIM':
        st.success("✅ Sua conta já foi ativada.")
        st.info("Você pode fechar esta aba e acessar normalmente.")
        return

    df.loc[df['token_confirmacao'] == token, 'ativo'] = 'SIM'
    df.loc[df['token_confirmacao'] == token, 'data_confirmacao'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        linha = df[df['token_confirmacao'] == token].iloc[0].to_dict()
        response = requests.post(WEBHOOK_URL, json=linha)
        if response.status_code == 200:
            st.success("✅ Parabéns! Sua conta foi ativada com sucesso.")
            st.balloons()
            st.info("Volte ao app e faça login com seu email e senha.")
        else:
            st.error("❌ Erro ao confirmar. Tente novamente.")
    except:
        st.error("❌ Falha ao conectar. Tente novamente.")

# ========================
# 🔗 CADASTRO COM CONFIRMAÇÃO
# ========================
def adicionar_assinante(email, senha, plano="gratuito"):
    try:
        # 1. Carrega a planilha para verificar duplicidade
        df = pd.read_csv(GOOGLE_SHEET_CSV)
        if 'email' in df.columns and email.strip().lower() in df['email'].str.strip().str.lower().tolist():
            st.error("❌ Cliente já cadastrado.")
            return False

        # 2. Gera token de confirmação
        token = gerar_token()
        expira_em = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

        # 3. Dados que serão enviados
        data = {
            "email": email.strip(),
            "senha": senha,
            "plano": plano,
            "expira_em": expira_em,
            "ativo": "NÃO",
            "token_confirmacao": token,
            "data_confirmacao": "",
            "ip_atual": "",
            "cidade_atual": "",
            "timestamp_sessao": ""
        }

        # 4. Exibe os dados que estão sendo enviados (para depuração)
        with st.expander("🔍 Dados enviados para o Google Sheets", expanded=False):
            st.json(data)

        # 5. Envia para o Google Sheets
        response = requests.post(WEBHOOK_URL, json=data)

        # 6. Mostra a resposta do servidor (ESSE É O SEGREDO!)
        st.write("📡 **Status Code:**", response.status_code)
        st.write("📦 **Resposta do servidor:**")
        try:
            st.json(response.json())  # Tenta mostrar como JSON
        except:
            st.text(response.text)  # Se não for JSON, mostra como texto

        # 7. Verifica se deu certo
        if response.status_code == 200:
            try:
                resposta = response.json()
                if resposta.get("result") == "success":
                    # ✅ Sucesso: manda e-mail
                    if enviar_email_boas_vindas(email, token):
                        st.success("✅ Cadastro realizado! Verifique seu e-mail para ativar sua conta.")
                    else:
                        st.warning("⚠️ Cadastro feito, mas falha no envio do e-mail.")
                    return True
                else:
                    st.error(f"❌ Erro no servidor: {resposta.get('message', 'Sem mensagem')}")
                    return False
            except:
                st.error("❌ Resposta inesperada do servidor (não é JSON válido)")
                return False
        else:
            st.error(f"❌ Falha na conexão. Status: {response.status_code}")
            return False

    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")
        return False
# ========================
# 🔐 LOGIN
# ========================
def verificar_login(email, senha):
    df = carregar_assinantes()
    if 'email' not in df.columns:
        st.error("❌ Erro ao carregar dados.")
        return False

    user = df[df['email'] == email.strip()]
    if user.empty:
        st.error("❌ Email não encontrado.")
        return False

    user = user.iloc[0]
    if user['senha'] != senha:
        st.error("❌ Senha incorreta.")
        return False

    if user['ativo'] != 'SIM':
        st.warning("⚠️ Sua conta ainda não foi ativada. Verifique seu e-mail.")
        return False

    expira_em = user['expira_em']
    if pd.isna(expira_em) or datetime.now() > expira_em:
        st.warning("⚠️ Sua assinatura expirou. Renove para continuar.")
        return False

    st.session_state.acesso = True
    st.session_state.email = email.strip()
    st.session_state.plano = user['plano']
    st.session_state.expira = expira_em.date()
    return True

# ========================
# 🚪 VERIFICAÇÃO INICIAL
# ========================
if "acesso" not in st.session_state:
    st.session_state.acesso = False

# Verifica token de confirmação
token = st.query_params.get("token", "")
if token and not st.session_state.acesso:
    st.markdown("<h1 style='text-align: center;'>🔑 Ativando sua conta</h1>", unsafe_allow_html=True)
    pagina_confirmacao()
    st.stop()

# ========================
# 🔐 INTERFACE DE ACESSO
# ========================
# ========================
# 🔐 INTERFACE DE ACESSO
# ========================
if not st.session_state.acesso:
    with st.sidebar:
        st.markdown("<h3 style='text-align: center;'>🔐 Acesso</h3>", unsafe_allow_html=True)

        # 🚀 Escolha do Plano
        st.markdown("#### 🚀 Escolha seu plano")
        plano_escolhido = st.selectbox(
            "Plano",
            ["gratuito", "diario", "acoes_pro", "total_pro"],
            format_func=lambda x: {
                "gratuito": "Plano Bronze (Teste Grátis)",
                "diario": "Plano Prata (Diário)",
                "acoes_pro": "Plano Ouro (Ações PRO)",
                "total_pro": "Plano Diamante (Completo)"
            }[x]
        )

        st.markdown("#### 📝 Cadastre-se")
        email_teste = st.text_input("Email", key="teste_email", help="Seu melhor email")
        senha_teste = st.text_input("Senha", type="password", key="teste_senha", help="Escolha uma senha segura")
        
        if st.button("Iniciar Assinatura", key="btn_teste", use_container_width=True):
            if "@" not in email_teste or len(senha_teste) < 4:
                st.error("❌ Email ou senha inválidos.")
            else:
                with st.spinner("Processando cadastro..."):
                    sucesso = adicionar_assinante(email_teste, senha_teste, plano_escolhido)
                if sucesso:
                    st.info("📧 Verifique seu e-mail para ativar sua conta. O acesso será liberado após a confirmação.")

        st.markdown("<br>", unsafe_allow_html=True)

        # ✅ Login de Cliente
        st.markdown("#### 🔐 Já é Cliente?")
        email_login = st.text_input("Email", key="login_email")
        senha_login = st.text_input("Senha", type="password", key="login_senha")
        
        if st.button("Entrar", key="btn_entrar", use_container_width=True):
            with st.spinner("Verificando credenciais..."):
                verificar_login(email_login, senha_login)

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # ✅ Login de Cliente
        st.markdown("#### 🔐 Já é Cliente?")
        email_login = st.text_input("Email",  key="acesso_email")
        senha_login = st.text_input("Senha", type="password", key="acesso_senha")
        
        if st.button("Entrar", key="btn_acesso", use_container_width=True):
            with st.spinner("Verificando credenciais..."):
                verificar_login(email_login, senha_login)

        st.markdown("<br><br><br>", unsafe_allow_html=True)

    # ========================
    # PÁGINA INICIAL
    # ========================
    st.markdown("""
    <h1 style="font-size: 32px; font-weight: 700; text-align: center; margin-bottom: 10px; color: #007bff;">
        📡📈 RADAR B3
    </h1>
    <p style="font-size: 18px; color: #444; text-align: center; max-width: 800px; margin: 0 auto 30px; line-height: 1.6;">
        Descubra oportunidades reais de lucro com base em distorções estatísticas de preço.<br>
        <strong>Entradas precisas, fundamentadas em dados — não em palpite.</strong>
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Tabela de Planos
    st.markdown("""
    <h2 style="text-align: center; font-size: 24px;">📊 Compare os Planos</h2>
    <p style="text-align: center; color: #555;">Escolha o plano ideal para suas estratégias</p>

    <style>
    .comparacao-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 16px;
    }
    .comparacao-table th, .comparacao-table td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: center;
        vertical-align: middle;
        height: 40px;
        line-height: 1;
    }
    .comparacao-table th {
        background-color: #f2f2f2;
        font-weight: 600;
    }
    .comparacao-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .comparacao-table td.check {
        font-family: "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
        font-size: 18px;
        line-height: 1;
    }
    </style>

    <table class="comparacao-table">
        <tr>
            <th>Recurso</th>
            <th>Plano Bronze</th>
            <th>Plano Prata</th>
            <th>Plano Ouro</th>
            <th>Plano Diamante</th>
        </tr>
        <tr>
            <td>Preço</td>
            <td>Gratis</td>
            <td>R$ 49,90/Mês</td>
            <td>R$ 59,90/mês</td>
            <td>R$ 79,90/Mês</td>
        </tr>
        <tr>
            <td>Análise Contra Tendência - Rastreamento</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Análise A Favor da Tendência - Rastreamento</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Qtd de ações para análise por vez</td>
            <td>2</td>
            <td>10</td>
            <td>20</td>
            <td>50</td>
        </tr>
        <tr>
            <td>Entrada e fechamento mesmo dia</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Entrada no dia e fechamento no dia seguinte</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Distorções do preço com vários tipos de referência do dia anterior</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Distorção de preço customizável</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Mini Índice - Análise Diária</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Mini Dólar - Análise Diária</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Mini Índice - Análise Intraday</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Mini Dólar - Análise Intraday</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Distorção do preço em relação ao preço de abertura do mercado do dia atual</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Análise Intraday - 5min</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">❌</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Tempo Gráfico Diário</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Taxa de acerto</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Máximo Drawdown / Pior situação</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Ganho Médio por Trade</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Relatório Resumo de todos ativos</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
        <tr>
            <td>Relatório detalhado - para validação e verificação dos traders encontrados</td>
            <td class="check">❌</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
            <td class="check">✅</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🌟 Como funciona?")
    st.write("O Radar B3 identifica distorções estatísticas no preço de abertura, fechamento, mínima e máxima, gerando entradas com vantagem matemática comprovada.")

    st.markdown("### 📞 Dúvidas?")
    st.write("Entre em contato: contatoradarb3@gmail.com")

    st.stop()

# ========================
# ✅ ACESSO LIBERADO
# ========================
st.success("✅ Acesso liberado.")
st.write(f"📆 Expira em: **{st.session_state.expira.strftime('%d/%m/%Y')}**")
st.markdown(f"Olá, **{st.session_state.email}**! Bem-vindo ao Radar B3.")

# ========================
# SELETOR DE MODO POR PLANO
# ========================
plano = st.session_state.plano

if plano == "gratuito":
    st.markdown("### ⚠️ Versão de Teste (15 dias)")
    modo_sistema = st.selectbox("", ["Plano Bronze"])
    modo_analise = st.radio("Modo de Análise", ["Contra Tendência"])

elif plano == "diario":
    st.markdown("### 🟨 Plano Prata")
    modo_sistema = st.selectbox("", ["Plano Prata"])
    modo_analise = st.radio("Modo de Análise", ["Contra Tendência"])

elif plano == "acoes_pro":
    st.markdown("### 🟨 Plano Ouro")
    modo_sistema = st.selectbox("", ["Plano Ouro"])
    modo_analise = st.radio("Modo de Análise", ["Contra Tendência", "A Favor da Tendência", "Ambos"])

elif plano == "total_pro":
    st.markdown("### 💎 Plano Diamante")
    modo_sistema = st.selectbox("", ["Diamante - Diário", "Diamante - Intraday"])
    modo_analise = st.radio("Modo de Análise", ["Contra Tendência", "A Favor da Tendência", "Ambos"])

else:
    st.error("❌ Plano desconhecido.")
    st.stop()

# ============ MODO DIÁRIO ============
if modo_sistema in ["Plano Bronze", "Plano Prata", "Plano Ouro", "Diamante - Diário"]:
    st.header("📅 Configurações do Rastreamento Diário")

    volume_minimo_opcoes = {
        "25 mil": 25_000,
        "50 mil": 50_000,
        "100 mil": 100_000,
        "200 mil": 200_000,
        "300 mil": 300_000,
        "400 mil": 400_000,
        "500 mil": 500_000,
        "1 milhão": 1_000_000,
        "2 milhões": 2_000_000
    }
    volume_minimo_nome = st.selectbox("Volume médio mínimo diário", list(volume_minimo_opcoes.keys()))
    volume_minimo = volume_minimo_opcoes[volume_minimo_nome]

    limite_ativos = 50
    if plano == "gratuito":
        limite_ativos = 2
    elif plano == "diario":
        limite_ativos = 10
    elif plano == "acoes_pro":
        limite_ativos = 20

    ativos_diarios = st.text_input(f"Ativos (até {limite_ativos})", value="PETR4, VALE3, ITUB4, BBDC4")
    tickers_input = [t.strip() for t in ativos_diarios.split(",") if t.strip()]
    tickers = tickers_input[:limite_ativos]
    num_inseridas = len(tickers)
    st.info(f"📌 {num_inseridas} ações inseridas.")

    col1, col2 = st.columns(2)
    with col1:
        dist_compra = st.number_input("Distorção mínima para COMPRA (%) - Contra", value=3.0, min_value=0.1)
    with col2:
        dist_venda = st.number_input("Distorção mínima para VENDA (%) - Contra", value=3.0, min_value=0.1)

    qtd = st.number_input("Quantidade", min_value=1, value=1, help="Ex: 100 para ações, 1 para mini")

    referencia_tipo = st.selectbox(
        "Referência",
        ["Fechamento do dia anterior", "Abertura do dia anterior", "Mínima do dia anterior", "Máxima do dia anterior"]
    )
    saida_tipo = st.selectbox(
        "Saída",
        ["Fechamento do dia", "Abertura do dia seguinte"]
    )

    data_inicio_diario = st.date_input("Data Início", value=datetime(2020, 1, 1))
    data_fim_diario = st.date_input("Data Fim", value=datetime.today().date())

    dist_favor = st.number_input("Distorção mínima A FAVOR da tendência (%)", value=2.0, min_value=0.1)
if st.button("🔍 Iniciar Rastreamento"):
        st.cache_data.clear()
        if "todas_operacoes_diarias" in st.session_state:
            del st.session_state.todas_operacoes_diarias
        if "df_ops" in st.session_state:
            del st.session_state.df_ops

        todas_operacoes = []
        tickers_processados = 0
        tickers_com_erro = []
        status_placeholder = st.empty()
        progress_bar = st.progress(0)

        for ticker in tickers:
            try:
                ticker_clean = ticker.strip().upper().replace(".SA", "")
                if not ticker_clean:
                    tickers_com_erro.append(f"{ticker} (vazio)")
                    continue

                ticker_yf = ticker_clean + ".SA"
                data = pd.DataFrame()
                for _ in range(3):
                    try:
                        data = yf.download(ticker_yf, start=data_inicio_diario, end=data_fim_diario + timedelta(days=1), progress=False)
                        if not data.empty: break
                    except: pass
                    try:
                        ticker_obj = yf.Ticker(ticker_yf)
                        data = ticker_obj.history(start=data_inicio_diario, end=data_fim_diario)
                        if not data.empty: break
                    except: pass

                if data.empty:
                    tickers_com_erro.append(f"{ticker_clean} (sem dados)")
                    continue

                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [col[0] for col in data.columns]
                data.columns = [col.capitalize() for col in data.columns]

                required = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required:
                    if col not in data.columns:
                        tickers_com_erro.append(f"{ticker_clean} (falta {col})")
                        continue

                for col in required:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
                data.dropna(subset=required, inplace=True)
                if len(data) < 2:
                    tickers_com_erro.append(f"{ticker_clean} (poucos dados)")
                    continue

                data['Volume_Reais'] = data['Volume'] * data['Close']
                volume_medio = data['Volume_Reais'].tail(21).mean()
                if pd.isna(volume_medio) or volume_medio < volume_minimo:
                    tickers_com_erro.append(f"{ticker_clean} (volume baixo: R$ {volume_medio:,.0f})")
                    continue

                data = data.loc[str(data_inicio_diario):str(data_fim_diario)]
                if len(data) < 2:
                    tickers_com_erro.append(f"{ticker_clean} (sem dados no período)")
                    continue

                operacoes = []
                for i in range(1, len(data)):
                    row_atual = data.iloc[i]
                    row_anterior = data.iloc[i-1]

                    try:
                        if referencia_tipo == "Fechamento do dia anterior":
                            ref = float(row_anterior['Close'])
                        elif referencia_tipo == "Abertura do dia anterior":
                            ref = float(row_anterior['Open'])
                        elif referencia_tipo == "Mínima do dia anterior":
                            ref = float(row_anterior['Low'])
                        elif referencia_tipo == "Máxima do dia anterior":
                            ref = float(row_anterior['High'])
                        else:
                            continue
                        if pd.isna(ref) or not np.isfinite(ref):
                            continue
                    except:
                        continue

                    low_atual = float(row_atual['Low'])
                    high_atual = float(row_atual['High'])
                    open_atual = float(row_atual['Open'])

                    preco_alvo_compra = ref * (1 - dist_compra / 100)
                    preco_alvo_venda = ref * (1 + dist_venda / 100)

                    if modo_analise in ["Contra Tendência", "Ambos"]:
                        if low_atual <= preco_alvo_compra and i+1 < len(data):
                            preco_entrada = open_atual if open_atual < preco_alvo_compra else preco_alvo_compra
                            preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                            lucro_reais = (preco_saida - preco_entrada) * qtd
                            max_dd_percent = ((low_atual - preco_entrada) / preco_entrada) * 100

                            operacoes.append({
                                "Ação": ticker_clean,
                                "Direção": "Compra (Contra)",
                                "Data Entrada": str(data.index[i].date()),
                                "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"-{dist_compra:.2f}%",
                                "Quantidade": qtd,
                                "Referência": f"{referencia_tipo}: {ref:.2f}",
                                "Max Drawdown %": round(max_dd_percent, 2)
                            })

                        if high_atual >= preco_alvo_venda and i+1 < len(data):
                            preco_entrada = open_atual if open_atual > preco_alvo_venda else preco_alvo_venda
                            preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                            lucro_reais = (preco_entrada - preco_saida) * qtd
                            max_dd_percent = ((high_atual - preco_entrada) / preco_entrada) * 100

                            operacoes.append({
                                "Ação": ticker_clean,
                                "Direção": "Venda (Contra)",
                                "Data Entrada": str(data.index[i].date()),
                                "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"+{dist_venda:.2f}%",
                                "Quantidade": qtd,
                                "Referência": f"{referencia_tipo}: {ref:.2f}",
                                "Max Drawdown %": round(max_dd_percent, 2)
                            })

                    if modo_analise in ["A Favor da Tendência", "Ambos"]:
                        ref = float(row_anterior['Close'])
                        preco_alvo_compra = ref * (1 - dist_favor / 100)
                        preco_alvo_venda = ref * (1 + dist_favor / 100)

                        if high_atual >= preco_alvo_venda and i+1 < len(data):
                            preco_entrada = open_atual if open_atual > preco_alvo_venda else preco_alvo_venda
                            preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                            lucro_reais = (preco_entrada - preco_saida) * qtd

                            close_dia_entrada = row_atual['Close']
                            if close_dia_entrada > preco_entrada:
                                max_dd_percent = ((close_dia_entrada - preco_entrada) / preco_entrada) * 100
                            else:
                                max_dd_percent = 0.0

                            operacoes.append({
                                "Ação": ticker_clean,
                                "Direção": "Venda (Favor)",
                                "Data Entrada": str(data.index[i].date()),
                                "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"+{dist_favor:.2f}%",
                                "Quantidade": qtd,
                                "Referência": f"Alvo +{dist_favor}%: {ref:.2f}",
                                "Max Drawdown %": round(max_dd_percent, 2)
                            })

                        elif low_atual <= preco_alvo_compra and i+1 < len(data):
                            preco_entrada = open_atual if open_atual < preco_alvo_compra else preco_alvo_compra
                            preco_saida = float(data.iloc[i+1]['Open']) if saida_tipo == "Abertura do dia seguinte" else float(row_atual['Close'])
                            lucro_reais = (preco_saida - preco_entrada) * qtd

                            close_dia_entrada = row_atual['Close']
                            if close_dia_entrada < preco_entrada:
                                max_dd_percent = ((close_dia_entrada - preco_entrada) / preco_entrada) * 100
                            else:
                                max_dd_percent = 0.0

                            operacoes.append({
                                "Ação": ticker_clean,
                                "Direção": "Compra (Favor)",
                                "Data Entrada": str(data.index[i].date()),
                                "Data Saída": str(data.index[i+1].date()) if saida_tipo == "Abertura do dia seguinte" else str(data.index[i].date()),
                                "Preço Entrada": round(preco_entrada, 2),
                                "Preço Saída": round(preco_saida, 2),
                                "Lucro (R$)": round(lucro_reais, 2),
                                "Distorção (%)": f"-{dist_favor:.2f}%",
                                "Quantidade": qtd,
                                "Referência": f"Alvo -{dist_favor}%: {ref:.2f}",
                                "Max Drawdown %": round(max_dd_percent, 2)
                            })

                todas_operacoes.extend(operacoes)
                tickers_processados += 1
                progress = tickers_processados / len(tickers)
                progress_bar.progress(progress)
                status_placeholder.info(f"✅ {tickers_processados} / {len(tickers)} ações processadas...")

            except Exception as e:
                tickers_com_erro.append(f"{ticker} ({str(e)})")
                continue

        progress_bar.empty()
        status_placeholder.empty()

        if tickers_com_erro:
            st.info(f"📊 {len(tickers_com_erro)} ações não foram analisadas porque não têm volume ou dados suficientes.")
            with st.expander("📋 Ver ações excluídas"):
                for erro in tickers_com_erro:
                    st.write(f"🔹 {erro}")

        try:
            df_ops = pd.DataFrame(todas_operacoes)
        except Exception as e:
            st.error(f"❌ Erro ao criar DataFrame: {e}")
            st.stop()

        st.success(f"✅ {tickers_processados} ações processadas com sucesso.")

        if df_ops.empty:
            st.warning("❌ Nenhuma oportunidade foi detectada.")
        else:
            for col in ['Preço Entrada', 'Preço Saída', 'Lucro (R$)', 'Max Drawdown %']:
                if col in df_ops.columns and df_ops[col].dtype == 'object':
                    df_ops[col] = pd.to_numeric(df_ops[col].astype(str).str.replace(',', '.'), errors='coerce')

            resumo = df_ops.groupby(['Ação', 'Direção']).agg(
                Total_Eventos=('Lucro (R$)', 'count'),
                Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                Lucro_Total=('Lucro (R$)', 'sum'),
                Max_DD_Medio_Percent=('Max Drawdown %', 'mean')
            ).reset_index()

            resumo['Taxa de Acerto'] = (resumo['Acertos'] / resumo['Total_Eventos']).map(lambda x: f"{x:.2%}")
            resumo['Lucro Total (R$)'] = "R$ " + resumo['Lucro_Total'].map(lambda x: f"{x:.2f}")
            resumo['Ganho Médio por Trade (R$)'] = (resumo['Lucro_Total'] / resumo['Total_Eventos']).map(lambda x: f"R$ {x:+.2f}")
            resumo['Máx. Drawdown Médio (%)'] = resumo['Max_DD_Medio_Percent'].map(lambda x: f"{x:+.2f}%")

            st.markdown("### 📊 Resumo Consolidado por Ação e Direção")
            st.dataframe(
                resumo[[
                    'Ação', 'Direção', 'Total_Eventos', 'Acertos', 'Taxa de Acerto',
                    'Lucro Total (R$)', 'Ganho Médio por Trade (R$)', 'Máx. Drawdown Médio (%)'
                ]],
                use_container_width=True
            )

            if plano != "gratuito":
                csv_data = df_ops.to_csv(index=False, sep=";", decimal=",", encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Resultados para CSV",
                    data=csv_data,
                    file_name="resultados_radar_b3.csv",
                    mime="text/csv"
                )

            if plano != "gratuito":
                with st.expander("🔍 Ver oportunidades detalhadas"):
                    st.dataframe(df_ops, use_container_width=True)
            else:
                st.info("🔒 Relatório detalhado disponível a partir do Plano Prata. Atualize para ver cada trade encontrado.")

            st.markdown("---")
            st.markdown("""
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 1px solid #bee1ff; text-align: center;">
                <h3>Quer rastrear até 50 ações ao mesmo tempo?</h3>
                <p><strong>Libere todo o poder do Radar B3</strong>: análise intraday, WIN, WDO, múltiplas estratégias e rastreamento em massa.</p>
                <p><strong>Contra Tendência</strong> e <strong>A Favor da Tendência</strong> disponíveis no plano PRO.</p>
            </div>
            """, unsafe_allow_html=True)

# ============ MODO INTRADAY ============
elif modo_sistema == "Diamante - Intraday":
    st.header("📤 Carregue seus Dados (Excel 5min)")
    uploaded_files = st.file_uploader("Escolha um ou mais arquivos .xlsx", type=["xlsx"], accept_multiple_files=True)

    if uploaded_files:
        limites_por_plano = {
            "gratuito": 2,
            "diario": 6,
            "acoes_pro": 12,
            "total_pro": 9999
        }
        limite = limites_por_plano.get(st.session_state.plano, 2)
        if len(uploaded_files) > limite:
            st.error(f"❌ Seu plano permite {limite} arquivos. Você enviou {len(uploaded_files)}.")
            st.stop()
        else:
            st.info(f"📌 Seu plano permite até {limite} arquivos. ({len(uploaded_files)} enviados)")

        st.info(f"✅ {len(uploaded_files)} arquivo(s) carregado(s).")

        data_min_global = None
        data_max_global = None
        for file in uploaded_files:
            try:
                df_temp = pd.read_excel(file)
                df_temp['data'] = pd.to_datetime(df_temp['Data'], dayfirst=True, errors='coerce')
                df_temp = df_temp.dropna(subset=['data'])
                df_temp['data_sozinha'] = df_temp['data'].dt.date
                min_data = df_temp['data_sozinha'].min()
                max_data = df_temp['data_sozinha'].max()
                if data_min_global is None or min_data < data_min_global:
                    data_min_global = min_data
                if data_max_global is None or max_data > data_max_global:
                    data_max_global = max_data
            except Exception as e:
                st.warning(f"⚠️ Erro ao ler {file.name}: {e}")

        if data_min_global and data_max_global:
            st.subheader("📅 Período disponível")
            st.write(f"**Início:** {data_min_global.strftime('%d/%m/%Y')}")
            st.write(f"**Fim:** {data_max_global.strftime('%d/%m/%Y')}")

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

            st.header("⚙️ Configure o Rastreamento")
            with st.form("configuracoes"):
                tipo_ativo = st.selectbox("Tipo de ativo", ["acoes", "mini_indice", "mini_dolar"])
                if plano == "acoes_pro" and tipo_ativo in ["mini_indice", "mini_dolar"]:
                    st.warning("⚠️ No plano Ações PRO, só é permitido analisar ações.")
                    tipo_ativo = "acoes"

                todos_horarios = [f"{h:02d}:{m:02d}" for h in range(9, 19) for m in range(0, 60, 5)]
                horarios_selecionados = st.multiselect(
                    "Horários de análise",
                    todos_horarios,
                    default=["09:00"]
                )

                qtd = st.number_input("Quantidade", min_value=1, value=1)
                candles_pos_entrada = st.number_input("Candles após entrada", min_value=1, value=3)

                modo_estrategia = st.selectbox(
                    "Modo da Estratégia",
                    ["Contra Tendência", "A Favor da Tendência", "Ambos"]
                )

                if modo_estrategia in ["Contra Tendência", "Ambos"]:
                    dist_compra_contra = st.number_input("Distorção mínima COMPRA (%) - Contra", value=0.3)
                    dist_venda_contra = st.number_input("Distorção mínima VENDA (%) - Contra", value=0.3)
                else:
                    dist_compra_contra = dist_venda_contra = 0.0

                if modo_estrategia in ["A Favor da Tendência", "Ambos"]:
                    dist_favor = st.number_input("Distorção mínima A FAVOR da tendência (%)", value=0.5)
                else:
                    dist_favor = 0.0

                referencia = st.selectbox(
                    "Referência da distorção",
                    ["Fechamento do dia anterior", "Mínima do dia anterior", "Abertura do dia atual"]
                )

                submitted = st.form_submit_button("✅ Aplicar Configurações")

            if submitted:
                horarios_validos = []
                horarios_invalidos = []
                for horario in horarios_selecionados:
                    h, m = map(int, horario.split(":"))
                    hora = time_obj(h, m)
                    if tipo_ativo == "acoes":
                        if time_obj(10, 0) <= hora <= time_obj(17, 0):
                            horarios_validos.append(horario)
                        else:
                            horarios_invalidos.append(horario)
                    else:
                        if time_obj(9, 0) <= hora <= time_obj(18, 20):
                            horarios_validos.append(horario)
                        else:
                            horarios_invalidos.append(horario)

                if horarios_invalidos:
                    st.error(f"""
                    ❌ Horários inválidos para {tipo_ativo.replace('_', ' ').title()}:
                    - {', '.join(horarios_invalidos)}
                    """)
                elif not horarios_validos:
                    st.warning("⚠️ Nenhum horário válido foi selecionado.")
                else:
                    st.session_state.configuracoes_salvas = {
                        "tipo_ativo": tipo_ativo,
                        "qtd": qtd,
                        "candles_pos_entrada": candles_pos_entrada,
                        "dist_compra_contra": dist_compra_contra,
                        "dist_venda_contra": dist_venda_contra,
                        "dist_favor": dist_favor,
                        "referencia": referencia,
                        "horarios_selecionados": horarios_validos,
                        "modo_estrategia": modo_estrategia
                    }
                    st.success("✅ Configurações aplicadas!")
            if "configuracoes_salvas" in st.session_state:
                if st.button("🔍 Iniciar Rastreamento"):
                    cfg = st.session_state.configuracoes_salvas
                    with st.spinner("📡 Rastreando padrões de mercado..."):
                        df_ops, dias_com_entrada, dias_ignorados, todos_dias_com_dados = processar_rastreamento_intraday(
                            uploaded_files=uploaded_files,
                            tipo_ativo=cfg["tipo_ativo"],
                            qtd=cfg["qtd"],
                            candles_pos_entrada=cfg["candles_pos_entrada"],
                            dist_compra_contra=cfg["dist_compra_contra"],
                            dist_venda_contra=cfg["dist_venda_contra"],
                            dist_favor=cfg["dist_favor"],
                            referencia=cfg["referencia"],
                            horarios_selecionados=cfg["horarios_selecionados"],
                            data_inicio=data_inicio,
                            data_fim=data_fim,
                            modo_estrategia=cfg["modo_estrategia"]
                        )

                    if not df_ops.empty:
                        df_ops = df_ops[df_ops['Horário'].isin(cfg["horarios_selecionados"])].copy()
                        st.session_state.todas_operacoes = df_ops
                        st.success(f"✅ Rastreamento concluído: {len(df_ops)} oportunidades detectadas.")

                        # Converter colunas para cálculo
                        for col in ['Preço Entrada', 'Preço Saída', 'Lucro (R$)', 'Max Drawdown %']:
                            if col in df_ops.columns and df_ops[col].dtype == 'object':
                                df_ops[col] = pd.to_numeric(df_ops[col].astype(str).str.replace(',', '.'), errors='coerce')

                        # Gerar resumo consolidado
                        resumo = df_ops.groupby(['Ação', 'Direção']).agg(
                            Total_Eventos=('Lucro (R$)', 'count'),
                            Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                            Lucro_Total=('Lucro (R$)', 'sum'),
                            Max_DD_Medio_Percent=('Max Drawdown %', 'mean')
                        ).reset_index()

                        # Formatar resumo
                        resumo['Taxa de Acerto'] = (resumo['Acertos'] / resumo['Total_Eventos']).map(lambda x: f"{x:.2%}")
                        resumo['Lucro Total (R$)'] = "R$ " + resumo['Lucro_Total'].map(lambda x: f"{x:.2f}")
                        resumo['Ganho Médio por Trade (R$)'] = (resumo['Lucro_Total'] / resumo['Total_Eventos']).map(lambda x: f"R$ {x:+.2f}")
                        resumo['Máx. Drawdown Médio (%)'] = resumo['Max_DD_Medio_Percent'].map(lambda x: f"{x:+.2f}%")

                        # Exibir resumo
                        st.markdown("### 📊 Resumo Consolidado por Ação e Direção")
                        st.dataframe(
                            resumo[[
                                'Ação', 'Direção', 'Total_Eventos', 'Acertos', 'Taxa de Acerto',
                                'Lucro Total (R$)', 'Ganho Médio por Trade (R$)', 'Máx. Drawdown Médio (%)'
                            ]],
                            use_container_width=True
                        )

                        # Exportar resultados
                        csv_data = df_ops.to_csv(index=False, sep=";", decimal=",", encoding='utf-8-sig')
                        st.download_button(
                            label="📥 Exportar Resultados para CSV",
                            data=csv_data,
                            file_name="resultados_intraday.csv",
                            mime="text/csv"
                        )

                    else:
                        st.warning("❌ Nenhuma oportunidade foi detectada.")

                    # Análise de dias
                    with st.expander("📊 Análise de Dias"):
                        st.write("Dias com entrada e saída válida:", len(dias_com_entrada))
                        if dias_ignorados:
                            st.write("Dias ignorados:")
                            for dia, motivo in dias_ignorados[:10]:
                                st.write(f"- {dia.strftime('%d/%m')} → {motivo}")

                    # Detalhamento com cores
                    if not df_ops.empty:
                        df_detalhe = df_ops.copy()
                        df_detalhe['Lucro (R$)'] = pd.to_numeric(df_detalhe['Lucro (R$)'], errors='coerce')
                        df_detalhe['Acerto?'] = df_detalhe['Lucro (R$)'].apply(
                            lambda x: '✅ Sim' if x > 0 else '❌ Não' if x < 0 else '➖ Neutro'
                        )
                        cols = df_detalhe.columns.tolist()
                        lucro_idx = cols.index('Lucro (R$)')
                        cols.insert(lucro_idx + 1, cols.pop(cols.index('Acerto?')))
                        df_detalhe = df_detalhe[cols]

                        def colorir_linhas(row):
                            valor = row['Lucro (R$)']
                            if valor > 0:
                                return ['background-color: #d4edda'] * len(row)  # verde claro
                            elif valor < 0:
                                return ['background-color: #f8d7da'] * len(row)  # vermelho claro
                            else:
                                return ['background-color: #fff3cd'] * len(row)  # amarelo claro

                        with st.expander("🔍 Ver oportunidades detalhadas (Intraday)"):
                            st.dataframe(
                                df_detalhe.style.apply(colorir_linhas, axis=1),
                                use_container_width=True
                            )
