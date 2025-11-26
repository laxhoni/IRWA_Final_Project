from google import genai
import os
from typing import List


class RAGGenerator:
    """
    RAG (Retrieval-Augmented Generation) module.
    Generates a summary answer based on the retrieved documents.
    """

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

        print("[RAG] GOOGLE_API_KEY:", "OK" if api_key else "NOT FOUND")
        print("[RAG] GEMINI_MODEL:", model)

        self.model = model
        self.client = genai.Client(api_key=api_key) if api_key else None

    def generate_response(self, query, results):
        """
        Generates a natural language response based on the query and top results.
        
        :param query: The user's search query
        :param results: List of ResultItem objects returned by search engine
        :return: A string containing the generated response
        """

        
        if not results:
            return f"I'm sorry, but I couldn't find any products related to '{query}' in our catalog."

        top_results = results[:5]

        good_results = [
            doc for doc in top_results
            if doc.average_rating is not None and doc.average_rating >= 3.0
        ]
        if not good_results:
            return (
                f"No he encontrado productos realmente buenos para "
                f"'<b>{query}</b>' según las valoraciones disponibles. "
                f"Prueba a reformular la búsqueda o usar otros filtros."
            )

        if not self.client:
            print("[RAG] NO hay cliente Gemini, usando resumen manual")
            response = (
                f"Based on your search for '<b>{query}</b>', "
                f"here are the top recommendations:\n<ul>"
            )
            for doc in good_results:
                snippet = (
                    doc.description.split(".")[0]
                    if doc.description else "No description available"
                )
                price = f"{doc.actual_price}€" if doc.actual_price is not None else "unknown price"
                rating = doc.average_rating if doc.average_rating is not None else "N/A"
                response += (
                    f"<li><b>{doc.title}</b>: {snippet}. "
                    f"(Price: {price}, Rating: {rating})</li>"
                )
            response += "</ul>"
            response += (
                f"<br><i>We found {len(results)} items in total. "
                f"Check the list below for more details!</i>"
            )
            return response

        context_lines = []
        for doc in good_results:
            snippet = (
                doc.description[:150].replace("\n", " ")
                if doc.description else "Sin descripción disponible"
            )
            price = f"{doc.actual_price}€" if doc.actual_price is not None else "precio desconocido"
            rating = (
                f"{doc.average_rating}/5"
                if doc.average_rating is not None else "sin rating"
            )
            line = (
                f"- Título: {doc.title}\n"
                f"  Precio: {price}\n"
                f"  Rating: {rating}\n"
                f"  Descripción: {snippet}\n"
            )
            context_lines.append(line)

        context_text = "\n".join(context_lines)

        user_content = f"""
Consulta del usuario:
{query}

Productos candidatos del catálogo:
{context_text}

Tarea:
- En 3-4 frases en español, resume qué tipo de productos encajan mejor con la consulta.
- Recomienda 2 o 3 productos concretos de la lista, mencionando su título.
- Usa la información de precio y rating cuando sea útil.
- No inventes productos nuevos ni características que no estén en la lista .
- Devuelve la respuesta en HTML simple: uno o dos párrafos (<p>) y, si recomiendas productos concretos, una lista <ul><li>...</li></ul>.
"""

        try:
            print("[RAG] Llamando a Gemini para generar resumen...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
            )

            text = getattr(response, "text", None)
            if not text:
                text = str(response)

            print("[RAG] Gemini ha respondido correctamente")
            return f"<p>{text}</p>"

        except Exception as e:
            print("[RAG] ERROR llamando a Gemini:", repr(e))
            response = (
                f"Based on your search for '<b>{query}</b>', "
                f"here are the top recommendations:\n<ul>"
            )
            for doc in good_results:
                snippet = (
                    doc.description.split(".")[0]
                    if doc.description else "No description available"
                )
                price = f"{doc.actual_price}€" if doc.actual_price is not None else "unknown price"
                rating = doc.average_rating if doc.average_rating is not None else "N/A"
                response += (
                    f"<li><b>{doc.title}</b>: {snippet}. "
                    f"(Price: {price}, Rating: {rating})</li>"
                )
            response += "</ul>"
            response += (
                f"<br><i>We found {len(results)} items in total. "
                f"Check the list below for more details!</i>"
            )
            return response
