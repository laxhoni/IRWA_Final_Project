import json
import os
import pandas as pd
import altair as alt
from datetime import datetime

class AnalyticsData:
    """
    An in memory persistence object that saves to a JSON file.
    """
    
    def __init__(self):
        self.db_file = "data/analytics_db.json"
        # Initialize tables
        self.fact_clicks = {} # {doc_id: count}
        self.fact_queries = [] # List of dicts
        self.last_query_id = 0
        
        # Load existing data if file exists
        self.load_data()

    def load_data(self):
        """Load data from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    self.fact_clicks = data.get('fact_clicks', {})
                    self.fact_queries = data.get('fact_queries', [])
                    self.last_query_id = data.get('last_query_id', 0)
                print(f"Analytics loaded: {len(self.fact_clicks)} docs clicked.")
            except Exception as e:
                print(f"Error loading analytics: {e}")

    def save_data(self):
        """Save data to JSON file"""
        data = {
            'fact_clicks': self.fact_clicks,
            'fact_queries': self.fact_queries,
            'last_query_id': self.last_query_id
        }
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving analytics: {e}")

    def save_query_terms(self, terms: str) -> int:
        """
        Saves the user query and returns a unique search_id
        """
        self.last_query_id += 1
        
        new_query = {
            'id': self.last_query_id,
            'terms': terms,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.fact_queries.append(new_query)
        self.save_data() # Persist to disk
        
        return self.last_query_id

    def update_click(self, doc_id):
        """
        Increment click count for a document and save.
        """
        if doc_id in self.fact_clicks:
            self.fact_clicks[doc_id] += 1
        else:
            self.fact_clicks[doc_id] = 1
        
        self.save_data() # Persist to disk

    # --- AQUESTA ÉS LA FUNCIÓ QUE ET FALTAVA ---
    def plot_number_of_views(self):
        """
        Generates a bar chart of document views using Altair.
        Returns JSON spec for Vega-Lite or None if no data.
        """
        if not self.fact_clicks:
            return None

        # Prepare data
        data = [{'Document ID': k, 'Number of Views': v} for k, v in self.fact_clicks.items()]
        df = pd.DataFrame(data)
        
        # Sort by views to make it prettier
        df = df.sort_values(by='Number of Views', ascending=False).head(20) # Show top 20

        # Create Altair chart
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Document ID', sort='-y'),
            y='Number of Views',
            tooltip=['Document ID', 'Number of Views']
        ).properties(
            title='Top Visited Documents',
            width='container', # Responsive width
            height=400
        ).interactive()
        
        return chart.to_json() # Return JSON specification

class ClickedDoc:
    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        return json.dumps(self.to_json())