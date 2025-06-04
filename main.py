from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml # Presumo que este arquivo exista
import json, os

app = FastAPI()

MAPEAMENTO_CATEGORIAS = {
    # Hatch
    "gol": "Hatch", "uno": "Hatch", "palio": "Hatch", "celta": "Hatch", "ka": "Hatch",
    "fiesta": "Hatch", "march": "Hatch", "sandero": "Hatch", "onix": "Hatch", "hb20": "Hatch",
    "i30": "Hatch", "golf": "Hatch", "polo": "Hatch", "fox": "Hatch", "up": "Hatch",
    "fit": "Hatch", "city": "Hatch", "yaris": "Hatch", "etios": "Hatch", "clio": "Hatch",
    "corsa": "Hatch", "bravo": "Hatch", "punto": "Hatch", "208": "Hatch", "argo": "Hatch",
    "mobi": "Hatch", "c3": "Hatch", "picanto": "Hatch", "astra hatch": "Hatch", "stilo": "Hatch",
    "focus hatch": "Hatch", "206": "Hatch", "c4 vtr": "Hatch", "kwid": "Hatch", "soul": "Hatch",
    "agile": "Hatch", "sonic hatch": "Hatch", "fusca": "Hatch",

    # Sedan
    "civic": "Sedan", "corolla": "Sedan", "sentra": "Sedan", "versa": "Sedan", "jetta": "Sedan",
    "prisma": "Sedan", "voyage": "Sedan", "siena": "Sedan", "grand siena": "Sedan", "cruze": "Sedan",
    "cobalt": "Sedan", "logan": "Sedan", "fluence": "Sedan", "cerato": "Sedan", "elantra": "Sedan",
    "virtus": "Sedan", "accord": "Sedan", "altima": "Sedan", "fusion": "Sedan", "mazda3": "Sedan",
    "mazda6": "Sedan", "passat": "Sedan", "city sedan": "Sedan", "astra sedan": "Sedan", "vectra sedan": "Sedan",
    "classic": "Sedan", "cronos": "Sedan", "linea": "Sedan", "focus sedan": "Sedan", "ka sedan": "Sedan",
    "408": "Sedan", "c4 pallas": "Sedan", "polo sedan": "Sedan", "bora": "Sedan", "hb20s": "Sedan",
    "lancer": "Sedan", "camry": "Sedan", "onix plus": "Sedan",

    # SUV
    "duster": "SUV", "ecosport": "SUV", "hrv": "SUV", "compass": "SUV", "renegade": "SUV",
    "tracker": "SUV", "kicks": "SUV", "captur": "SUV", "creta": "SUV", "tucson": "SUV",
    "santa fe": "SUV", "sorento": "SUV", "sportage": "SUV", "outlander": "SUV", "asx": "SUV",
    "pajero": "SUV", "tr4": "SUV", "aircross": "SUV", "tiguan": "SUV", "t-cross": "SUV",
    "rav4": "SUV", "cx5": "SUV", "forester": "SUV", "wrx": "SUV", "land cruiser": "SUV", # land cruiser also off-road
    "cherokee": "SUV", "grand cherokee": "SUV", "xtrail": "SUV", "murano": "SUV", "cx9": "SUV",
    "edge": "SUV", "trailblazer": "SUV", "pulse": "SUV", "fastback": "SUV", "territory": "SUV",
    "bronco sport": "SUV", "2008": "SUV", "3008": "SUV", "c4 cactus": "SUV", "taos": "SUV",
    "cr-v": "SUV", "corolla cross": "SUV", "sw4": "SUV", "pajero sport": "SUV", "commander": "SUV",
    "xv": "SUV", "xc60": "SUV", "tiggo 5x": "SUV", "haval h6": "SUV", "nivus": "SUV",

    # Caminhonete
    "hilux": "Caminhonete", "ranger": "Caminhonete", "s10": "Caminhonete", "l200": "Caminhonete", "triton": "Caminhonete",
    "saveiro": "Utilitário", "strada": "Utilitário", "montana": "Utilitário", "oroch": "Utilitário", # Montana e Oroch as Utilitário
    "toro": "Caminhonete", # Toro como Caminhonete
    "frontier": "Caminhonete", "amarok": "Caminhonete", "gladiator": "Caminhonete", "maverick": "Caminhonete", "colorado": "Caminhonete",
    "dakota": "Caminhonete", "montana (nova)": "Caminhonete", "f-250": "Caminhonete", "courier (pickup)": "Caminhonete", "hoggar": "Caminhonete",
    "ram 1500": "Caminhonete",

    # Utilitário
    "kangoo": "Utilitário", "partner": "Utilitário", "doblo": "Utilitário", "fiorino": "Utilitário", "berlingo": "Utilitário",
    "express": "Utilitário", "combo": "Utilitário", "kombi": "Utilitário", "doblo cargo": "Utilitário", "kangoo express": "Utilitário",

    # Furgão
    "master": "Furgão", "sprinter": "Furgão", "ducato": "Furgão", "daily": "Furgão", "jumper": "Furgão",
    "boxer": "Furgão", "trafic": "Furgão", "transit": "Furgão", "vito": "Furgão", "expert (furgão)": "Furgão",
    "jumpy (furgão)": "Furgão", "scudo (furgão)": "Furgão",

    # Coupe
    "camaro": "Coupe", "mustang": "Coupe", "tt": "Coupe", "supra": "Coupe", "370z": "Coupe",
    "rx8": "Coupe", "challenger": "Coupe", "corvette": "Coupe", "veloster": "Coupe", "cerato koup": "Coupe",
    "clk coupe": "Coupe", "a5 coupe": "Coupe", "gt86": "Coupe", "rcz": "Coupe", "brz": "Coupe",

    # Conversível
    "z4": "Conversível", "boxster": "Conversível", "miata": "Conversível", "beetle cabriolet": "Conversível", "slk": "Conversível",
    "911 cabrio": "Conversível", "tt roadster": "Conversível", "a5 cabrio": "Conversível", "mini cabrio": "Conversível", "206 cc": "Conversível",
    "eos": "Conversível",

    # Minivan / Station Wagon
    "spin": "Minivan", "livina": "Minivan", "caravan": "Minivan", "touran": "Minivan", "parati": "Station Wagon",
    "quantum": "Station Wagon", "sharan": "Minivan", "zafira": "Minivan", "picasso": "Minivan", "grand c4": "Minivan",
    "meriva": "Minivan", "scenic": "Minivan", "xsara picasso": "Minivan", "carnival": "Minivan", "idea": "Minivan",
    "spacefox": "Station Wagon", "golf variant": "Station Wagon", "palio weekend": "Station Wagon", "astra sw": "Station Wagon", "206 sw": "Station Wagon",
    "a4 avant": "Station Wagon", "fielder": "Station Wagon",

    # Off-road
    "wrangler": "Off-road", "troller": "Off-road", "defender": "Off-road", "bronco": "Off-road", "samurai": "Off-road",
    "jimny": "Off-road", "land cruiser": "Off-road", "grand vitara": "Off-road", "jimny sierra": "Off-road", "bandeirante (ate 2001)": "Off-road"
}

def inferir_categoria_por_modelo(modelo_buscado):
    modelo_norm = normalizar(modelo_buscado) # Mantém a normalização original para esta função específica
    return MAPEAMENTO_CATEGORIAS.get(modelo_norm)

def normalizar(texto: str) -> str:
    return unidecode(texto).lower().replace("-", "").replace(" ", "").strip()

def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except (ValueError, TypeError): # Adicionado TypeError para None ou outros tipos inesperados
        return None

def filtrar_veiculos(vehicles, filtros, valormax=None):
    campos_fuzzy = ["modelo", "titulo"]
    vehicles_processados = list(vehicles) # Começa com uma cópia da lista de veículos

    for chave_filtro, valor_filtro in filtros.items():
        if not valor_filtro: # Se o valor do filtro for vazio, pula este filtro
            continue

        veiculos_que_passaram_nesta_chave = []

        if chave_filtro in campos_fuzzy:
            palavras_query_originais = valor_filtro.split()
            palavras_query_normalizadas = [normalizar(p) for p in palavras_query_originais if p.strip()]
            
            # Remove palavras vazias que podem ter surgido da normalização de p. ex. "-"
            palavras_query_normalizadas = [p for p in palavras_query_normalizadas if p]

            if not palavras_query_normalizadas:
                # Se o valor_filtro foi fornecido mas resultou em nenhuma palavra válida para busca,
                # então nenhum veículo deve corresponder a este filtro específico.
                vehicles_processados = []
                break 

            for v in vehicles_processados:
                todas_palavras_query_encontradas_no_veiculo = True
                for palavra_q_norm in palavras_query_normalizadas:
                    match_para_esta_palavra_q = False
                    for nome_campo_fuzzy_veiculo in campos_fuzzy: 
                        conteudo_original_campo_veiculo = v.get(nome_campo_fuzzy_veiculo, "")
                        if not conteudo_original_campo_veiculo:
                            continue
                        
                        texto_normalizado_campo_veiculo = normalizar(str(conteudo_original_campo_veiculo))

                        if not texto_normalizado_campo_veiculo: # Segurança extra
                            continue

                        # 1. Checagem de substring
                        if palavra_q_norm in texto_normalizado_campo_veiculo:
                            match_para_esta_palavra_q = True
                            break 
                        
                        # 2. Checagem Fuzzy (somente se a palavra da query tiver um tamanho razoável)
                        if len(palavra_q_norm) >= 3: # Ajustado para palavras menores
                            # partial_ratio é bom para encontrar uma palavra menor dentro de um texto maior
                            score_partial = fuzz.partial_ratio(texto_normalizado_campo_veiculo, palavra_q_norm)
                            # ratio é bom se o texto do veículo for similar em tamanho à palavra da query
                            score_ratio = fuzz.ratio(texto_normalizado_campo_veiculo, palavra_q_norm)
                            
                            # Mantenha o limiar original de 70 ou ajuste conforme necessário
                            if score_partial >= 70 or score_ratio >= 70:
                                match_para_esta_palavra_q = True
                                break 
                    
                    if not match_para_esta_palavra_q:
                        todas_palavras_query_encontradas_no_veiculo = False
                        break 
                
                if todas_palavras_query_encontradas_no_veiculo:
                    veiculos_que_passaram_nesta_chave.append(v)
        
        else: # Lógica para campos de correspondência exata (ex: "marca", "categoria")
            termo_normalizado_para_comparacao = normalizar(valor_filtro) # Normaliza o valor do filtro inteiro
            for v in vehicles_processados:
                valor_campo_veiculo = v.get(chave_filtro, "")
                if normalizar(str(valor_campo_veiculo)) == termo_normalizado_para_comparacao:
                    veiculos_que_passaram_nesta_chave.append(v)
        
        vehicles_processados = veiculos_que_passaram_nesta_chave
        if not vehicles_processados: # Otimização: se nenhum veículo passar, não há necessidade de continuar
            break

    # Aplicar filtro de valormax
    if valormax:
        try:
            teto = float(valormax)
            maximo = teto * 1.3 
            vehicles_processados = [
                v for v in vehicles_processados
                if "preco" in v and converter_preco(v["preco"]) is not None and converter_preco(v["preco"]) <= maximo
            ]
        except ValueError:
             # Se valormax for inválido, retorna lista vazia como no código original
            return []

    # Ordenar resultados
    vehicles_processados.sort(
        key=lambda v: converter_preco(v["preco"]) if "preco" in v and v["preco"] is not None else float('inf'),
        reverse=True
    )
    return vehicles_processados


@app.on_event("startup")
def agendar_tarefas():
    scheduler = BackgroundScheduler()
    # Ajuste o 'hour' conforme necessário para o fuso horário do seu servidor.
    # Se o servidor estiver em UTC, 0 (meia-noite) e 12 (meio-dia) UTC.
    scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
    scheduler.start()
    # Considerar rodar fetch_and_convert_xml() em uma thread separada na inicialização
    # para não bloquear o startup, se for uma operação demorada.
    # Por enquanto, mantendo como está no código original.
    fetch_and_convert_xml()

@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return JSONResponse(content={"error": "Nenhum dado disponível", "resultados": [], "total_encontrado": 0}, status_code=404)

    with open("data.json", "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return JSONResponse(content={"error": "Erro ao ler os dados (JSON inválido)", "resultados": [], "total_encontrado": 0}, status_code=500)


    try:
        vehicles = data["veiculos"]
        if not isinstance(vehicles, list): # Validação adicional
             return JSONResponse(content={"error": "Formato de dados inválido (veiculos não é uma lista)", "resultados": [], "total_encontrado": 0}, status_code=500)
    except KeyError:
        return JSONResponse(content={"error": "Formato de dados inválido (chave 'veiculos' não encontrada)", "resultados": [], "total_encontrado": 0}, status_code=500)
    except Exception: # Captura genérica para outros problemas com 'data'
        return JSONResponse(content={"error": "Formato de dados inválido", "resultados": [], "total_encontrado": 0}, status_code=500)


    query_params = dict(request.query_params)
    valormax = query_params.pop("ValorMax", None)

    filtros = {
        "modelo": query_params.get("modelo"),
        "marca": query_params.get("marca"),
        "categoria": query_params.get("categoria")
        # Adicione outros filtros aqui se necessário
    }
    # Remover filtros com valores None ou vazios para não processá-los desnecessariamente
    filtros = {k: v for k, v in filtros.items() if v}


    resultado = filtrar_veiculos(vehicles, filtros, valormax)

    if resultado:
        return JSONResponse(content={
            "resultados": resultado,
            "total_encontrado": len(resultado)
        })

    # Lógica de busca alternativa (se nenhum resultado encontrado com filtros + ValorMax)
    # Esta parte permanece a mesma, mas agora usará a nova lógica de filtrar_veiculos
    
    alternativas = []
    # 1. Tenta sem o ValorMax
    filtros_sem_valormax = filtros.copy() # Reutiliza os filtros originais de modelo, marca, categoria
    alternativa1 = filtrar_veiculos(vehicles, filtros_sem_valormax) # Sem valormax
    if alternativa1:
        alternativas = alternativa1
    else:
        # 2. Tenta apenas por modelo (com ValorMax, se houver)
        if "modelo" in filtros:
            filtros_so_modelo = {"modelo": filtros["modelo"]}
            alternativa2 = filtrar_veiculos(vehicles, filtros_so_modelo, valormax)
            if alternativa2:
                alternativas = alternativa2
            else:
                # 3. Tenta por categoria inferida (com ValorMax, se houver)
                modelo_para_inferencia = filtros.get("modelo")
                if modelo_para_inferencia:
                    categoria_inferida = inferir_categoria_por_modelo(modelo_para_inferencia)
                    if categoria_inferida:
                        filtros_categoria_inferida = {"categoria": categoria_inferida}
                        alternativa3 = filtrar_veiculos(vehicles, filtros_categoria_inferida, valormax)
                        if alternativa3:
                            alternativas = alternativa3
                        else:
                            # 4. Tenta por categoria inferida (sem ValorMax)
                            alternativa4 = filtrar_veiculos(vehicles, filtros_categoria_inferida) # Sem valormax
                            if alternativa4:
                                alternativas = alternativa4
    
    if alternativas:
        # Limita a quantidade de alternativas para não sobrecarregar a resposta
        alternativas_formatadas = [
            {"titulo": v.get("titulo", ""), "preco": v.get("preco", "")}
            for v in alternativas[:10] # Pega até 10 alternativas
        ]
        return JSONResponse(content={
            "resultados": [],
            "total_encontrado": 0,
            "instrucao_ia": "Não encontramos veículos com os parâmetros informados dentro do valor desejado. Seguem as opções mais próximas.",
            "alternativa": {
                "resultados": alternativas_formatadas,
                "total_encontrado": len(alternativas_formatadas) # Ou len(alternativas) se quiser mostrar o total real antes de limitar
            }
        })

    return JSONResponse(content={
        "resultados": [],
        "total_encontrado": 0,
        "instrucao_ia": "Não encontramos veículos com os parâmetros informados e também não encontramos opções próximas."
    })
