# main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
import json, os

# --- NOVO: Importações para a busca com IA ---
import google.generativeai as genai
from pydantic import BaseModel
from dotenv import load_dotenv

app = FastAPI()

# --- NOVO: Configuração da IA do Gemini ---
# Carrega as variáveis de ambiente do arquivo .env
load_dotenv() 

# Configura a API Key do Gemini a partir das variáveis de ambiente
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"ERRO: Não foi possível configurar a API do Gemini. Verifique sua GEMINI_API_KEY. Detalhes: {e}")

# --- NOVO: Modelo Pydantic para a requisição de busca inteligente ---
class NaturalLanguageQuery(BaseModel):
    query: str

MAPEAMENTO_CATEGORIAS = {
    # (Seu MAPEAMENTO_CATEGORIAS aqui - omitido para brevidade)
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
    "rav4": "SUV", "cx5": "SUV", "forester": "SUV", "wrx": "SUV", "land cruiser": "SUV", 
    "cherokee": "SUV", "grand cherokee": "SUV", "xtrail": "SUV", "murano": "SUV", "cx9": "SUV",
    "edge": "SUV", "trailblazer": "SUV", "pulse": "SUV", "fastback": "SUV", "territory": "SUV",
    "bronco sport": "SUV", "2008": "SUV", "3008": "SUV", "c4 cactus": "SUV", "taos": "SUV",
    "cr-v": "SUV", "corolla cross": "SUV", "sw4": "SUV", "pajero sport": "SUV", "commander": "SUV",
    "xv": "SUV", "xc60": "SUV", "tiggo 5x": "SUV", "haval h6": "SUV", "nivus": "SUV",

    # Caminhonete
    "hilux": "Caminhonete", "ranger": "Caminhonete", "s10": "Caminhonete", "l200": "Caminhonete", "triton": "Caminhonete",
    "saveiro": "Utilitário", "strada": "Utilitário", "montana": "Utilitário", "oroch": "Utilitário", 
    "toro": "Caminhonete", 
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


# --- NOVO: Função que usa o Gemini para interpretar a busca ---
async def parse_query_with_gemini(user_query: str) -> dict:
    """
    Usa um modelo generativo para converter uma query em linguagem natural
    em um dicionário de filtros estruturados.
    """
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    # Prompt detalhado para guiar o modelo
    prompt = f"""
    Você é um assistente especialista em vendas de carros. Sua tarefa é analisar a frase de um cliente
    e extrair os parâmetros de busca em um formato JSON.

    Os campos JSON possíveis são:
    - "modelo": string
    - "marca": string
    - "categoria": string (Valores possíveis: Hatch, Sedan, SUV, Caminhonete, Utilitário, Furgão, Coupe, Conversível, Minivan, Station Wagon, Off-road)
    - "ano_min": integer
    - "ano_max": integer
    - "km_max": integer
    - "ValorMax": float (sem R$ ou pontos, ex: 150000.0)
    - "cambio": string (Valores: "automatico" ou "manual")
    - "combustivel": string (Ex: "gasolina", "flex", "diesel")
    - "cor": string
    - "opcionais": string (palavras-chave separadas por vírgula, ex: "teto solar,banco de couro")

    Regras Importantes:
    1.  Se o cliente disser "de 2020 para frente" ou "a partir de 2020", use "ano_min": 2020.
    2.  Se o cliente disser "até 100 mil reais", use "ValorMax": 100000.
    3.  Se a frase for ambígua, priorize os campos mais claros.
    4.  Se o cliente mencionar características, coloque em "opcionais". Ex: "carro para família" -> "opcionais": "familiar,espaçoso".
    5.  A saída DEVE ser APENAS o objeto JSON, sem nenhum texto adicional.

    Exemplo de frase: "Tô procurando um SUV da Honda, automático, de 2022 em diante, na faixa dos 180 mil."
    JSON esperado:
    {{
      "categoria": "SUV",
      "marca": "honda",
      "cambio": "automatico",
      "ano_min": 2022,
      "ValorMax": 180000.0
    }}

    Agora, analise a seguinte frase do cliente:
    "{user_query}"
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        # Limpa a resposta para garantir que é um JSON válido
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        
        filtros = json.loads(cleaned_response)
        return filtros
    except Exception as e:
        print(f"Erro ao analisar a query com IA: {e}")
        # Retorna um dicionário vazio em caso de falha para não quebrar a busca
        return {}


# Suas funções existentes (sem modificações)
def inferir_categoria_por_modelo(modelo_buscado):
    modelo_norm = normalizar(modelo_buscado)
    return MAPEAMENTO_CATEGORIAS.get(modelo_norm)

def normalizar(texto: str) -> str:
    return unidecode(texto).lower().replace("-", "").replace(" ", "").strip()

def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except (ValueError, TypeError):
        return None

def get_price_for_sort(price_val):
    converted = converter_preco(price_val)
    return converted if converted is not None else float('-inf')

# --- MODIFICADO: Adaptando a função para receber mais filtros da IA ---
def filtrar_veiculos(vehicles, filtros, valormax=None):
    campos_fuzzy = ["modelo", "titulo", "opcionais"] # Adicionando opcionais aqui!
    vehicles_processados = list(vehicles)

    for v in vehicles_processados:
        v['_relevance_score'] = 0.0
        v['_matched_word_count'] = 0

    active_fuzzy_filter_applied = False
    
    # Filtros exatos ou de faixa vindos da IA
    filtros_para_remover = []
    
    # --- NOVO: Lógica para filtros de faixa (ano/km) ---
    ano_min = filtros.get("ano_min")
    ano_max = filtros.get("ano_max")
    km_max = filtros.get("km_max")
    
    veiculos_filtrados_faixa = []
    for v in vehicles_processados:
        passou = True
        if ano_min and int(v.get("ano_fabricacao", 0)) < int(ano_min):
            passou = False
        if ano_max and int(v.get("ano_fabricacao", 0)) > int(ano_max):
            passou = False
        if km_max and int(v.get("km", 0)) > int(km_max):
            passou = False
        
        if passou:
            veiculos_filtrados_faixa.append(v)
    vehicles_processados = veiculos_filtrados_faixa
    # Fim da lógica de faixa

    # Identificar filtros que já foram processados
    if ano_min: filtros_para_remover.append("ano_min")
    if ano_max: filtros_para_remover.append("ano_max")
    if km_max: filtros_para_remover.append("km_max")
    if "ValorMax" in filtros: filtros_para_remover.append("ValorMax") # valormax é tratado separadamente

    for f in filtros_para_remover:
        filtros.pop(f, None)

    # Lógica de filtro fuzzy/exato restante
    for chave_filtro, valor_filtro in filtros.items():
        if not valor_filtro:
            continue

        veiculos_que_passaram_nesta_chave = []

        if chave_filtro in campos_fuzzy:
            active_fuzzy_filter_applied = True
            # ... (Sua lógica fuzzy continua aqui, sem alterações)
            palavras_query_originais = valor_filtro.split()
            palavras_query_normalizadas = [normalizar(p) for p in palavras_query_originais if p.strip()]
            palavras_query_normalizadas = [p for p in palavras_query_normalizadas if p] 

            if not palavras_query_normalizadas:
                vehicles_processados = [] 
                break 

            for v in vehicles_processados:
                vehicle_score_for_this_filter = 0.0
                vehicle_matched_words_for_this_filter = 0

                for palavra_q_norm in palavras_query_normalizadas:
                    if not palavra_q_norm: 
                        continue
                    
                    best_score_for_this_q_word_in_vehicle = 0.0
                    
                    for nome_campo_fuzzy_veiculo in campos_fuzzy: 
                        conteudo_original_campo_veiculo = v.get(nome_campo_fuzzy_veiculo, "")
                        if not conteudo_original_campo_veiculo: 
                            continue
                        texto_normalizado_campo_veiculo = normalizar(str(conteudo_original_campo_veiculo))
                        if not texto_normalizado_campo_veiculo: 
                            continue

                        current_field_match_score = 0.0
                        if palavra_q_norm in texto_normalizado_campo_veiculo:
                            current_field_match_score = 100.0
                        elif len(palavra_q_norm) >= 4:
                            score_partial = fuzz.partial_ratio(texto_normalizado_campo_veiculo, palavra_q_norm)
                            score_ratio = fuzz.ratio(texto_normalizado_campo_veiculo, palavra_q_norm)
                            achieved_score = max(score_partial, score_ratio)
                            if achieved_score >= 75:
                                current_field_match_score = achieved_score
                        
                        if current_field_match_score > best_score_for_this_q_word_in_vehicle:
                            best_score_for_this_q_word_in_vehicle = current_field_match_score
                    
                    if best_score_for_this_q_word_in_vehicle > 0:
                        vehicle_score_for_this_filter += best_score_for_this_q_word_in_vehicle
                        vehicle_matched_words_for_this_filter += 1
                
                if vehicle_matched_words_for_this_filter > 0:
                    v['_relevance_score'] += vehicle_score_for_this_filter
                    v['_matched_word_count'] += vehicle_matched_words_for_this_filter
                    veiculos_que_passaram_nesta_chave.append(v)
        else: # Lógica para campos de correspondência exata
            termo_normalizado_para_comparacao = normalizar(str(valor_filtro))
            for v in vehicles_processados:
                valor_campo_veiculo = v.get(chave_filtro, "")
                if normalizar(str(valor_campo_veiculo)) == termo_normalizado_para_comparacao:
                    veiculos_que_passaram_nesta_chave.append(v)
        
        vehicles_processados = veiculos_que_passaram_nesta_chave
        if not vehicles_processados:
            break

    # ... (O resto da sua função `filtrar_veiculos` continua aqui, com ordenação e filtro de valormax)
    if active_fuzzy_filter_applied:
        vehicles_processados = [v for v in vehicles_processados if v['_matched_word_count'] > 0]

    if active_fuzzy_filter_applied:
        vehicles_processados.sort(
            key=lambda v: (
                v['_matched_word_count'], 
                v['_relevance_score'],
                get_price_for_sort(v.get("preco")) 
            ),
            reverse=True
        )
    else:
        vehicles_processados.sort(
            key=lambda v: get_price_for_sort(v.get("preco")),
            reverse=True
        )
    
    if valormax:
        try:
            teto = float(valormax)
            max_price_limit = teto * 1.3 
            
            vehicles_filtrados_preco = []
            for v_dict in vehicles_processados:
                price = converter_preco(v_dict.get("preco"))
                if price is not None and price <= max_price_limit:
                    vehicles_filtrados_preco.append(v_dict)
            vehicles_processados = vehicles_filtrados_preco
        except ValueError:
            return [] 

    for v in vehicles_processados:
        v.pop('_relevance_score', None)
        v.pop('_matched_word_count', None)

    return vehicles_processados


# Seus endpoints existentes...
# ... @app.on_event("startup") ...
# ... @app.get("/api/data") ...

@app.on_event("startup")
def agendar_tarefas():
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
    scheduler.start()
    fetch_and_convert_xml()

# --- NOVO: Endpoint de Busca Inteligente ---
@app.post("/api/busca-inteligente")
async def intelligent_search(nl_query: NaturalLanguageQuery):
    """
    Recebe uma query em linguagem natural, usa IA para extrair filtros
    e retorna os veículos correspondentes.
    """
    # 1. Usar a IA para extrair filtros
    filtros_ia = await parse_query_with_gemini(nl_query.query)

    if not filtros_ia:
        raise HTTPException(status_code=500, detail="Não foi possível processar a busca com a IA.")

    # 2. Carregar os dados dos veículos
    if not os.path.exists("data.json"):
        return JSONResponse(content={"error": "Nenhum dado disponível", "resultados": []}, status_code=404)
    
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    vehicles = data.get("veiculos", [])

    # 3. Chamar a função de filtragem com os filtros da IA
    valormax = filtros_ia.get("ValorMax")
    resultado = filtrar_veiculos(vehicles, filtros_ia.copy(), valormax)

    # 4. Retornar o resultado
    return JSONResponse(content={
        "filtros_detectados_pela_ia": filtros_ia,
        "resultados": resultado,
        "total_encontrado": len(resultado)
    })
    
@app.get("/api/data")
def get_data(request: Request):
     if not os.path.exists("data.json"):
         return JSONResponse(content={"error": "Nenhum dado disponível", "resultados": [], "total_encontrado": 0}, status_code=404)

     try:
         with open("data.json", "r", encoding="utf-8") as f:
             data = json.load(f)
     except json.JSONDecodeError:
         return JSONResponse(content={"error": "Erro ao ler os dados (JSON inválido)", "resultados": [], "total_encontrado": 0}, status_code=500)

     try:
         vehicles = data["veiculos"]
         if not isinstance(vehicles, list):
              return JSONResponse(content={"error": "Formato de dados inválido (veiculos não é uma lista)", "resultados": [], "total_encontrado": 0}, status_code=500)
     except KeyError:
         return JSONResponse(content={"error": "Formato de dados inválido (chave 'veiculos' não encontrada)", "resultados": [], "total_encontrado": 0}, status_code=500)
     # Removida a captura genérica de Exception para ser mais específico acima

     query_params = dict(request.query_params)
     valormax = query_params.pop("ValorMax", None)

     filtros_originais = {
         "modelo": query_params.get("modelo"),
         "marca": query_params.get("marca"),
         "categoria": query_params.get("categoria")
     }
     filtros_ativos = {k: v for k, v in filtros_originais.items() if v}

     resultado = filtrar_veiculos(vehicles, filtros_ativos, valormax)

     if resultado:
         return JSONResponse(content={
             "resultados": resultado,
             "total_encontrado": len(resultado)
         })

     # Lógica de busca alternativa (mantida, mas agora usará a nova filtrar_veiculos com relevância)
     alternativas = []
     filtros_alternativa1 = {k: v for k, v in filtros_originais.items() if v} # Filtros originais sem ValorMax
    
     # 1. Tenta com filtros originais, sem ValorMax
     alt1 = filtrar_veiculos(vehicles, filtros_alternativa1) # valormax é None por padrão
     if alt1:
         alternativas = alt1
     else:
         # 2. Tenta apenas por modelo (com ValorMax, se houver originalmente)
         if filtros_originais.get("modelo"):
             filtros_so_modelo = {"modelo": filtros_originais["modelo"]}
             alt2 = filtrar_veiculos(vehicles, filtros_so_modelo, valormax)
             if alt2:
                 alternativas = alt2
             else:
                 # 3. Tenta por categoria inferida (com ValorMax, se houver originalmente)
                 modelo_para_inferencia = filtros_originais.get("modelo")
                 if modelo_para_inferencia:
                     categoria_inferida = inferir_categoria_por_modelo(modelo_para_inferencia)
                     if categoria_inferida:
                         filtros_categoria_inferida = {"categoria": categoria_inferida}
                         alt3 = filtrar_veiculos(vehicles, filtros_categoria_inferida, valormax)
                         if alt3:
                             alternativas = alt3
                         else:
                             # 4. Tenta por categoria inferida (sem ValorMax)
                             alt4 = filtrar_veiculos(vehicles, filtros_categoria_inferida)
                             if alt4:
                                 alternativas = alt4
    
     if alternativas:
         alternativas_formatadas = [
             {"titulo": v.get("titulo", ""), "preco": v.get("preco", "")}
             for v in alternativas[:10] 
         ]
         return JSONResponse(content={
             "resultados": [],
             "total_encontrado": 0,
             "instrucao_ia": "Não encontramos veículos com os parâmetros informados dentro do valor desejado. Seguem as opções mais próximas.",
             "alternativa": {
                 "resultados": alternativas_formatadas,
                 "total_encontrado": len(alternativas_formatadas) 
             }
         })

     return JSONResponse(content={
         "resultados": [],
         "total_encontrado": 0,
         "instrucao_ia": "Não encontramos veículos com os parâmetros informados e também não encontramos opções próximas."
     })
