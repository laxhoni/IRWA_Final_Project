import os
from json import JSONEncoder

import httpagentparser  # for getting the user agent as json
from flask import Flask, render_template, session, request, redirect, url_for

# Importamos tus clases (asegúrate de que los archivos existen en las carpetas correctas)
from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument
from myapp.search.search_engine import SearchEngine
from myapp.generation.rag import RAGGenerator
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
_default.default = JSONEncoder().default
JSONEncoder.default = _default
# end lines ***for using method to_json in objects ***


# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key_default") # Added default for safety
# open browser dev tool to see the cookies
app.session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "irwa_session")

# instantiate our search engine
search_engine = SearchEngine()
# instantiate our in memory persistence (ahora con persistencia JSON gracias a tu código)
analytics_data = AnalyticsData()
# instantiate RAG generator
rag_generator = RAGGenerator()

# load documents corpus into memory.
# CAMBIO: Gestión más robusta de la ruta del archivo
try:
    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    # Si DATA_FILE_PATH es relativo desde la raíz, ajústalo aquí si falla
    data_file = os.getenv("DATA_FILE_PATH", "data/fashion_products_dataset.json") 
    file_path = os.path.join(path, data_file) if not os.path.isabs(data_file) else data_file
    
    # Si no encuentra el archivo, intentamos buscarlo en la carpeta data relativa a webapp.py
    if not os.path.exists(file_path):
        file_path = os.path.join(path, "..", "data", "fashion_products_dataset.json") # Ajuste común

    corpus = load_corpus(file_path)
    print(f"\nCorpus loaded successfully: {len(corpus)} documents.")
    
    # CAMBIO IMPORTANTE: Crear el índice al arrancar la aplicación
    # Esto prepara BM25 y las estructuras de datos.
    print("Building Search Index... Please wait.")
    search_engine.create_index(corpus)
    print("Index ready!")

except Exception as e:
    print(f"CRITICAL ERROR loading corpus: {e}")
    corpus = {} # Fallback vacío para no romper la app


# Home URL "/"
@app.route('/')
def index():
    print("starting home url /...")

    session['some_var'] = "Some value that is kept in session"

    user_agent = request.headers.get('User-Agent')
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))
    return render_template('index.html', page_title="Welcome")


@app.route('/search', methods=['GET', 'POST'])
def search_form_post():
    search_query = request.args.get('search-query') or request.form.get('search-query')
    
    if not search_query:
        return redirect(url_for('index'))

    session['last_search_query'] = search_query

    # 1. Analytics
    search_id = analytics_data.save_query_terms(search_query)

    # 2. Search Engine
    # ---> CAMBIO CLAVE AQUÍ: Leer el algoritmo <---
    algorithm = request.args.get('algorithm') or request.form.get('algorithm')
    
    # Si no viene nada, por defecto 'bm25'
    if not algorithm: algorithm = 'bm25'

    # Pasamos el algoritmo a la función search
    results = search_engine.search(search_query, search_id, corpus, algorithm=algorithm)

    # 3. RAG
    rag_response = rag_generator.generate_response(search_query, results)

    found_count = len(results)
    session['last_found_count'] = found_count

    # Pasamos 'algorithm' al template también para mostrarlo en el título
    # Pasamos 'query=search_query' para que se vea en el título HTML
    return render_template(
        'results.html', 
        query=search_query,          
        results_list=results, 
        page_title=f"Results for {search_query}", 
        found_counter=found_count, 
        rag_response=rag_response, 
        algorithm=algorithm
    )
@app.route('/doc_details', methods=['GET'])
def doc_details():
    """
    Show document details page
    """
    # get the query string parameters from request
    clicked_doc_id = request.args.get("pid") # Usar .get es más seguro
    
    if not clicked_doc_id:
        return "Error: No document ID provided", 400

    print("click in id={}".format(clicked_doc_id))

    # CAMBIO IMPORTANTE: Usar tu método update_click
    # El código original modificaba analytics_data.fact_clicks directamente.
    # Tu nueva clase tiene lógica para guardar en JSON, así que usamos su método.
    analytics_data.update_click(clicked_doc_id)

    # CAMBIO IMPORTANTE: Recuperar el documento real para mostrarlo
    # El código original solo renderizaba el template vacío.
    # Ahora pasamos el objeto 'document' a la plantilla.
    
    # Manejo de tipos de ID (str vs int)
    doc = corpus.get(clicked_doc_id)
    if not doc:
        try: doc = corpus.get(int(clicked_doc_id))
        except: pass
    
    if not doc:
        return "Document not found", 404

    return render_template('doc_details.html', product=doc)


@app.route('/stats', methods=['GET'])
def stats():
    """
    Show simple statistics example.
    """
    docs = []
    # Iteramos sobre los clicks registrados
    for doc_id, count in analytics_data.fact_clicks.items():
        # Buscar el doc en el corpus. Si el ID es string/int, intentar ambos
        doc_obj = corpus.get(doc_id)
        if not doc_obj:
            try: doc_obj = corpus.get(int(doc_id))
            except: pass
            
        if doc_obj:
            # Crear objeto StatsDocument para la vista
            doc = StatsDocument(
                pid=str(doc_obj.pid),
                title=doc_obj.title,
                description=doc_obj.description,
                url=doc_obj.url,
                count=count
            )
            docs.append(doc)
    
    # Sort by click count descending
    docs.sort(key=lambda doc: doc.count, reverse=True)
    return render_template('stats.html', clicks_data=docs)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Muestra el dashboard con la tabla de visitados y el gráfico
    """
    # 1. Generar lista de documentos visitados
    visited_docs = []
    for doc_id, count in analytics_data.fact_clicks.items():
        doc_obj = corpus.get(doc_id)
        if not doc_obj:
            try: doc_obj = corpus.get(int(doc_id))
            except: pass
            
        if doc_obj:
            # Usamos ClickedDoc para la tabla del dashboard
            doc = ClickedDoc(doc_id, doc_obj.description, count)
            visited_docs.append(doc)

    # Ordenar por visitas
    visited_docs.sort(key=lambda doc: doc.counter, reverse=True)

    # 2. Generar el gráfico (ESTO FALTABA)
    chart_json = analytics_data.plot_number_of_views()

    # 3. Renderizar pasando AMBAS variables
    return render_template(
        'dashboard.html', 
        visited_docs=visited_docs, 
        chart_json=chart_json  # <--- ¡Esta es la clave del error!
    )


# New route added for generating an examples of basic Altair plot (used for dashboard)
@app.route('/plot_number_of_views', methods=['GET'])
def plot_number_of_views():
    # Llama a tu función de analytics_data que devuelve el JSON de Altair
    return analytics_data.plot_number_of_views()


if __name__ == "__main__":
    # Ejecutar en puerto 8088 como pide el código original
    app.run(port=8088, host="0.0.0.0", threaded=False, debug=os.getenv("DEBUG", True))