        # Botão para rodar
        if st.button("🚀 Rodar Backtest"):
            with st.expander("ℹ️ Ver detalhes do processamento", expanded=False):
                st.write("🔄 Iniciando processamento...")

                # Armazenar todas as operações (para detalhamento)
                todas_operacoes = []

                for horario_str in horarios_selecionados:
                    hora, minuto = map(int, horario_str.split(":"))
                    hora_inicio = time_obj(hora, minuto)
                    st.write(f"⏰ Processando horário: {horario_str}")

                    for file in uploaded_files:
                        try:
                            # Extrair nome completo do arquivo
                            ticker_nome = extrair_nome_completo(file.name)
                            # Identificar o tipo do ativo
                            tipo_arquivo = identificar_tipo(ticker_nome)

                            # ✅ FILTRO RÍGIDO: só processa se for do tipo selecionado
                            if tipo_arquivo != tipo_ativo:
                                continue  # Pula arquivos de outros tipos

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

                                # Calcular referência
                                try:
                                    idx_dia_atual_idx = list(dias_unicos).index(dia_atual)
                                    if idx_dia_atual_idx == 0:
                                        continue
                                    dia_anterior = dias_unicos[idx_dia_atual_idx - 1]
                                    referencia_valor = df[df.index.date == dia_anterior]["close"].iloc[-1]
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

                # ✅ Gerar ranking final
                if todas_operacoes:
                    df_ops = pd.DataFrame(todas_operacoes)

                    # 🏆 Ranking de Compras
                    df_compras = df_ops[df_ops['Direção'] == 'Compra']
                    if not df_compras.empty:
                        resumo_compras = df_compras.groupby(['Ação', 'Horário']).agg(
                            Total_Eventos=('Lucro (R$)', 'count'),
                            Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                            Lucro_Total=('Lucro (R$)', 'sum')
                        ).reset_index()

                        resumo_compras = resumo_compras.sort_values('Lucro_Total', ascending=False).copy()

                        resumo_compras['Taxa de Acerto'] = (resumo_compras['Acertos'] / resumo_compras['Total_Eventos']).map("{:.2%}".format)
                        resumo_compras['Lucro Total (R$)'] = "R$ " + resumo_compras['Lucro_Total'].map("{:.2f}".format)

                        resumo_compras = resumo_compras[[
                            'Ação', 'Horário', 'Total_Eventos', 'Acertos', 'Taxa de Acerto', 'Lucro Total (R$)'
                        ]]

                        st.header("🏆 Ranking de Compras")
                        st.dataframe(resumo_compras, use_container_width=True)

                    # 📉 Ranking de Vendas
                    df_vendas = df_ops[df_ops['Direção'] == 'Venda']
                    if not df_vendas.empty:
                        resumo_vendas = df_vendas.groupby(['Ação', 'Horário']).agg(
                            Total_Eventos=('Lucro (R$)', 'count'),
                            Acertos=('Lucro (R$)', lambda x: (x > 0).sum()),
                            Lucro_Total=('Lucro (R$)', 'sum')
                        ).reset_index()

                        resumo_vendas = resumo_vendas.sort_values('Lucro_Total', ascending=False).copy()

                        resumo_vendas['Taxa de Acerto'] = (resumo_vendas['Acertos'] / resumo_vendas['Total_Eventos']).map("{:.2%}".format)
                        resumo_vendas['Lucro Total (R$)'] = "R$ " + resumo_vendas['Lucro_Total'].map("{:.2f}".format)

                        resumo_vendas = resumo_vendas[[
                            'Ação', 'Horário', 'Total_Eventos', 'Acertos', 'Taxa de Acerto', 'Lucro Total (R$)'
                        ]]

                        st.header("📉 Ranking de Vendas")
                        st.dataframe(resumo_vendas, use_container_width=True)

                    # ✅ Salvar para detalhamento
                    st.session_state.todas_operacoes = df_ops

                else:
                    st.warning("❌ Nenhuma operação foi registrada.")
