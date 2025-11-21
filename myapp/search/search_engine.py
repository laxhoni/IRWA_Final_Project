from myapp.search.objects import ResultItem
from myapp.search.algorithms import create_index_part3, find_candidate_docs, rank_documents_bm25

class SearchEngine:
    """
    Orchestrator class. Holds the state (index) and calls algorithms.
    """

    def __init__(self):
        self.index = {}
        self.df = {}
        self.doc_lengths = {}
        self.avg_doc_length = 0
        self.N = 0
        self.is_indexed = False

    def create_index(self, corpus: dict):
        print("SearchEngine: Indexing corpus...")
        self.N = len(corpus)
        self.index, self.df, self.doc_lengths = create_index_part3(corpus)
        
        if self.N > 0:
            self.avg_doc_length = sum(self.doc_lengths.values()) / self.N
        else:
            self.avg_doc_length = 0
            
        self.is_indexed = True
        print(f"SearchEngine: Index created for {self.N} documents.")

    def search(self, search_query, search_id, corpus, algorithm="bm25"):
        """
        Main search method.
        :param algorithm: 'bm25' or 'your_score'
        """
        print(f"SearchEngine: Searching for '{search_query}' using [{algorithm}]")

        if not self.is_indexed:
            self.create_index(corpus)

        # 1. Filtrar (AND)
        candidate_docs = find_candidate_docs(search_query, self.index)
        
        if not candidate_docs:
            return []

        # 2. Ranking Base (BM25)
        # Calculamos siempre BM25 primero porque YourScore lo necesita como base
        ranked_tuples = rank_documents_bm25(
            search_query, 
            candidate_docs, 
            self.index, 
            self.df, 
            self.N, 
            self.doc_lengths, 
            self.avg_doc_length
        )

        # 3. Aplicar Algoritmo Seleccionado
        final_ranking = []
        
        if algorithm == "your_score":
            # --- Lógica de Your Score (Híbrido) ---
            # Formula: Score = 0.8 * Norm(BM25) + 0.2 * Norm(Rating)
            
            # Convertir tuplas a dict para acceso rápido
            scores_bm25 = dict(ranked_tuples)
            
            # Encontrar max score para normalizar
            max_bm25 = ranked_tuples[0][1] if ranked_tuples else 1
            if max_bm25 == 0: max_bm25 = 1
            
            hybrid_scores = {}
            
            for doc_id, bm25_score in ranked_tuples:
                # Recuperar rating del corpus (objeto Document)
                doc_obj = corpus[doc_id]
                rating = doc_obj.average_rating if doc_obj.average_rating else 0
                
                # Normalizar
                norm_bm25 = bm25_score / max_bm25
                norm_rating = rating / 5.0 # Rating maximo es 5
                
                # Calcular Score Híbrido
                # Puedes ajustar los pesos aquí (0.8 / 0.2)
                final_score = (0.8 * norm_bm25) + (0.2 * norm_rating)
                hybrid_scores[doc_id] = final_score
            
            # Reordenar por nuevo score
            final_ranking = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
            
        else:
            # Si es BM25, usamos el resultado directo
            final_ranking = ranked_tuples

        # 4. Formatear resultados (ResultItem)
        results = []
        for doc_id, score in final_ranking[:20]: # Top 20
            doc_original = corpus[doc_id]
            
            result = ResultItem(
                pid=doc_original.pid,
                title=doc_original.title,
                description=doc_original.description,
                url=f"doc_details?pid={doc_original.pid}&search_id={search_id}",
                ranking=score,
                actual_price=doc_original.actual_price,
                average_rating=doc_original.average_rating,
                images=doc_original.images
            )
            results.append(result)

        return results