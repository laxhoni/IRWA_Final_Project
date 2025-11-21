import re
import math
import collections
from collections import defaultdict
from array import array
import numpy as np

# NLTK imports
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# --- CONFIGURACIÓN NLTK Y STOPWORDS ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))
# Tus stopwords específicas del dominio
stop_words.update({
    'made', 'india', 'proudly', 'use', 'year', 'round', 
    'look', 'design', 'qualiti', 'day', 'make',        
    'feel', 'perfect', 'great', 'wash', 'style',       
})

# --- 1. PRE-PROCESAMIENTO ---

def build_terms(text):
    """Preprocess text: lowercase, tokenize, remove stopwords, stem."""
    if not isinstance(text, str): return []
    text = re.sub(r'\d+', '', text)
    word_tokens = word_tokenize(text.lower())
    textos_limpios = [word for word in word_tokens if word not in stop_words and word.isalnum()]      
    textos_limpios = [stemmer.stem(word) for word in textos_limpios]
    return textos_limpios

# --- 2. INDEXACIÓN ---

def create_index_part3(corpus: dict):
    """
    Crea el índice invertido, DF, y longitudes de documentos.
    Recibe el corpus (diccionario de objetos Document).
    """
    index = defaultdict(list)
    df = defaultdict(int)
    doc_lengths = {}
    
    print("Iniciando indexación en algorithms...")

    for doc_id, doc_obj in corpus.items():
        # Usamos title + description
        content = (doc_obj.title or "") + " " + (doc_obj.description or "")
        terms = build_terms(content)
        
        doc_lengths[doc_id] = len(terms)
        
        # Contamos frecuencia local (Raw TF)
        term_counts = collections.Counter(terms)
        
        for term, count in term_counts.items():
            # Guardamos (doc_id, count) en el índice
            index[term].append((doc_id, count))
            df[term] += 1
            
    return index, df, doc_lengths

# --- 3. FILTRADO (AND) ---

def find_candidate_docs(query, index):
    """Encuentra documentos que contienen TODOS los términos (AND)"""
    query_terms = build_terms(query)
    if not query_terms: return set()
    
    candidate_docs = None
    for term in query_terms:
        # Extraemos solo los doc_ids de la lista de tuplas [(doc_id, count), ...]
        if term not in index:
            return set() # AND estricto: si falta uno, adiós
            
        term_docs = {posting[0] for posting in index[term]}
        
        if candidate_docs is None:
            candidate_docs = term_docs
        else:
            candidate_docs &= term_docs # Intersección
            
        if not candidate_docs: return set()
        
    return candidate_docs if candidate_docs is not None else set()

# --- 4. RANKING (BM25) ---

def rank_documents_bm25(query, docs_to_rank, index, df, N, doc_lengths, avg_doc_length):
    """Calcula el score BM25 para los documentos candidatos"""
    query_terms = build_terms(query)
    
    K1 = 1.2
    B = 0.75
    doc_scores = defaultdict(float)
    idf_cache = {}
    
    # Pre-calcular IDF
    for term in query_terms:
        if term not in df: continue
        n_q = df[term]
        # Fórmula IDF estándar para BM25
        idf_cache[term] = math.log(1 + (N - n_q + 0.5) / (n_q + 0.5))

    for doc_id in docs_to_rank:
        doc_len = doc_lengths.get(doc_id, 0)
        
        for term in query_terms:
            if term not in idf_cache: continue
            
            # Buscar Raw TF en el índice
            raw_tf = 0
            for pid, count in index[term]:
                if pid == doc_id:
                    raw_tf = count
                    break
            
            if raw_tf == 0: continue
            
            # Fórmula BM25
            tf_num = raw_tf * (K1 + 1)
            tf_den = raw_tf + K1 * (1 - B + B * (doc_len / avg_doc_length))
            
            doc_scores[doc_id] += idf_cache[term] * (tf_num / tf_den)

    # Ordenar por score descendente
    ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked_docs # Retorna lista de tuplas (doc_id, score)