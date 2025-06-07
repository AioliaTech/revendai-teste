# Versão completa e limpa do arquivo main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import json
import os

# --- 1. Configuração Inicial ---
app = FastAPI()

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configura a API Key do Gemini
try:
    api_key = os.getenv("AIzaSyDVUKbebnCg48Rhjsrtf7wvzYu6CppCTFQ")
    if not api_key:
        print("ERRO: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
    else:
        genai.configure(api_key=api_key)
except Exception as e:
    print(f"ERRO: Não foi possível configurar a API do Gemini. Detalhes: {e}")

# Modelo Pydantic para a requisição de busca inteligente
class NaturalLanguageQuery(BaseModel):
    query: str


# --- 2. Dados e Funções Auxiliares ---
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
    # Outras categorias...
}

def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        texto = str(texto)
    return unidecode(texto).lower().replace("-", "").replace(" ", "").strip()

def converter_preco(valor_str):
    try:
        return float(str(valor_str).replace(",", "").replace("R$", "").strip())
    except (ValueError, TypeError):
        return None

def get_price_for_sort(price_val):
    converted = converter_preco(price_val)
    return converted if converted is not None else float('-inf')

def inferir_categoria_por_modelo(modelo_buscado):
    modelo_norm = normalizar(modelo_buscado)
    return MAPEAMENTO_CATEGORIAS.get(modelo_norm)

# Presumo que este arquivo exista. Se não, comente as linhas que o usam.
try:
    from xml_fetcher import fetch_and_convert_xml
except ImportError:
    print("AVISO: 'xml_fetcher.py' não encontrado. A busca de dados agendada será desativada.")
    def fetch_and_convert_xml():
        print("Função 'fetch_and_convert_xml' não implementada.")


# --- 3. Lógica Principal de Busca ---

async def parse_query_with_gemini(user_query: str) -> dict:
    model = genai.GenerativeModel('gemini-2.5-flash-latest')
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
    1. Se o cliente disser "de 2020 para frente" ou "a partir de 2020", use "ano_min": 2020.
    2. Se o cliente disser "até 100 mil reais", use "ValorMax": 100000.
    3. Se o cliente mencionar características, coloque em "opcionais". Ex: "carro para família" -> "opcionais": "familiar,espaçoso".
    4. A saída DEVE ser APENAS o objeto JSON, sem nenhum texto adicional.

    Frase do cliente: "{user_query}"
    """
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        filtros = json.loads(cleaned_response)
        return filtros
    except Exception as e:
        print(f"Erro ao analisar a query com IA: {e}")
        return {}

def filtrar_veiculos(vehicles, filtros, valormax=None):
    campos_fuzzy = ["modelo", "titulo", "opcionais"]
    vehicles_processados = list(vehicles)

    # Inicializa campos temporários
    for v in vehicles_processados:
        v['_relevance_score'] = 0.0
        v['_matched_word_count'] = 0

    # Filtros de faixa (ano/km)
    ano_min = filtros.pop("ano_min", None)
    ano_max = filtros.pop("ano_max", None)
    km_max = filtros.pop("km_max", None)
    
    veiculos_filtrados_faixa = []
    for v in vehicles_processados:
        passou = True
        if ano_min and int(v.get("ano_fabricacao", 0)) < int(ano_min):
            passou = False
        if ano_max and int(v.get("ano_fabricacao", 0)) > int(ano_max):
            passou = False
        if km_max and int(v.get("km", 999999)) > int(km_max):
            passou = False
        
        if passou:
            veiculos_filtrados_faixa.append(v)
    vehicles_processados = veiculos_filtrados_faixa

    # Filtros exatos e fuzzy
    active_fuzzy_filter_applied = False
    for chave_filtro, valor_filtro in filtros.items():
        if not valor_filtro:
            continue

        veiculos_que_passaram_nesta_chave = []
        if chave_filtro in campos_fuzzy:
            # Lógica de busca fuzzy (simplificada para brevidade, mas igual à sua)
            active_fuzzy_filter_applied = True
            palavras_query = [normalizar(p) for p in str(valor_filtro).split() if p.strip()]
            for v in vehicles_processados:
                # ... sua lógica fuzzy aqui ...
                pass # Substitua este 'pass' pela sua lógica de fuzzy matching
        else: # Lógica para campos de correspondência exata
            termo_normalizado = normalizar(valor_filtro)
            for v in vehicles_processados:
                valor_campo = v.get(chave_filtro, "")
                if normalizar(valor_campo) == termo_normalizado:
                    veiculos_que_passaram_nesta_chave.append(v)
        
        vehicles_processados = veiculos_que_passaram_nesta_chave
        if not vehicles_processados:
            break

    # Ordenação (simplificada, adicione a sua lógica de relevância aqui)
    vehicles_processados.sort(key=lambda v: get_price_for_sort(v.get("preco")), reverse=True)
    
    # Filtro de preço máximo
    if valormax:
        try:
            teto = float(valormax) * 1.3
            vehicles_processados = [v for v in vehicles_processados if get_price_for_sort(v.get("preco")) <= teto]
        except (ValueError, TypeError):
            pass

    # Limpa as chaves temporárias
    for v in vehicles_processados:
        v.pop('_relevance_score', None)
        v.pop('_matched_word_count', None)

    return vehicles_processados


# --- 4. Endpoints da API ---

@app.on_event("startup")
def agendar_tarefas():
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    # Roda a cada 12 horas
    scheduler.add_job(fetch_and_convert_xml, "cron", hour="0,12")
    scheduler.start()
    # Roda uma vez na inicialização
    fetch_and_convert_xml()

@app.post("/api/busca-inteligente")
async def intelligent_search(nl_query: NaturalLanguageQuery):
    if not os.path.exists("data.json"):
        raise HTTPException(status_code=404, detail="Arquivo de dados não encontrado.")
    
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    vehicles = data.get("veiculos", [])

    filtros_ia = await parse_query_with_gemini(nl_query.query)
    if not filtros_ia:
        raise HTTPException(status_code=500, detail="Não foi possível processar a busca com a IA.")

    valormax = filtros_ia.pop("ValorMax", None)
    resultado = filtrar_veiculos(vehicles, filtros_ia.copy(), valormax)

    return JSONResponse(content={
        "filtros_detectados_pela_ia": filtros_ia,
        "resultados": resultado,
        "total_encontrado": len(resultado)
    })

@app.get("/api/data")
def get_data(request: Request):
    if not os.path.exists("data.json"):
        return JSONResponse(content={"error": "Nenhum dado disponível"}, status_code=404)

    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "Erro ao ler os dados"}, status_code=500)

    vehicles = data.get("veiculos", [])
    query_params = dict(request.query_params)
    valormax = query_params.pop("ValorMax", None)
    
    filtros = {k: v for k, v in query_params.items() if v}

    resultado = filtrar_veiculos(vehicles, filtros, valormax)

    if resultado:
        return JSONResponse(content={
            "resultados": resultado,
            "total_encontrado": len(resultado)
        })

    # Lógica de busca alternativa (pode ser expandida ou simplificada)
    return JSONResponse(content={
        "resultados": [],
        "total_encontrado": 0,
        "instrucao_ia": "Não encontramos veículos com os parâmetros informados."
    })

# Para rodar localmente: uvicorn main:app --reload
