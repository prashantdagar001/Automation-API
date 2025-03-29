import os
import inspect
import importlib
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, persist_directory="./vector_db"):
        """Initialize the vector database with FAISS."""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Load the sentence transformer model for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize FAISS index - using L2 distance
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Storage for function metadata
        self.metadata_file = os.path.join(persist_directory, "metadata.pkl")
        self.function_metadata = []
        self.function_ids = []
        self.embeddings = []  # Store embeddings separately for updating
        
        # Load existing data if available
        self._load_data()
    
    def _load_data(self):
        """Load existing index and metadata if available."""
        try:
            # Load metadata
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.function_metadata = data.get('metadata', [])
                    self.function_ids = data.get('ids', [])
                    self.embeddings = data.get('embeddings', [])
                
                # Ensure all lists have the same length
                min_length = min(len(self.function_metadata), len(self.function_ids))
                if len(self.embeddings) != min_length:
                    logger.warning(f"Mismatch in data lengths. Truncating to {min_length} items.")
                    self.function_metadata = self.function_metadata[:min_length]
                    self.function_ids = self.function_ids[:min_length]
                    if len(self.embeddings) < min_length:
                        # If embeddings list is too short, reset everything
                        logger.warning("Embeddings list is too short. Resetting all data.")
                        self.function_metadata = []
                        self.function_ids = []
                        self.embeddings = []
                        min_length = 0
                    else:
                        self.embeddings = self.embeddings[:min_length]
            
            # Rebuild the index from stored embeddings
            if self.embeddings:
                embeddings_array = np.array(self.embeddings).astype('float32')
                self.index = faiss.IndexFlatL2(self.dimension)
                self.index.add(embeddings_array)
                logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
            else:
                logger.info("No existing embeddings found. Starting with empty index.")
        except Exception as e:
            logger.error(f"Error loading vector database: {e}")
            # Initialize with empty data
            self.function_metadata = []
            self.function_ids = []
            self.embeddings = []
            self.index = faiss.IndexFlatL2(self.dimension)
    
    def _save_data(self):
        """Save the index and metadata."""
        try:
            # Ensure all lists have the same length
            assert len(self.function_metadata) == len(self.function_ids) == len(self.embeddings), \
                f"Data length mismatch: metadata({len(self.function_metadata)}), ids({len(self.function_ids)}), embeddings({len(self.embeddings)})"
            
            # Save metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump({
                    'metadata': self.function_metadata,
                    'ids': self.function_ids,
                    'embeddings': self.embeddings
                }, f)
            
            logger.info(f"Saved index with {len(self.function_ids)} functions")
        except Exception as e:
            logger.error(f"Error saving vector database: {e}")
    
    def _get_function_embedding(self, function_info):
        """Generate embedding for function metadata."""
        # Combine function name, docstring, and arguments into a single text
        text = f"{function_info['name']} - {function_info['docstring']}"
        if function_info.get('keywords'):
            text += f" Keywords: {', '.join(function_info['keywords'])}"
        
        # Generate embedding
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def add_function(self, function, keywords=None):
        """Add a function to the vector database."""
        # Extract function metadata
        function_info = {
            'name': function.__name__,
            'docstring': function.__doc__ or "",
            'module': function.__module__,
            'keywords': keywords or []
        }
        
        # Get function signature
        signature = inspect.signature(function)
        function_info['parameters'] = [
            {
                'name': name,
                'default': str(param.default) if param.default is not inspect.Parameter.empty else None,
                'required': param.default is inspect.Parameter.empty and param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.VAR_KEYWORD
            }
            for name, param in signature.parameters.items()
        ]
        
        # Generate function ID
        function_id = f"{function.__module__}.{function.__name__}"
        
        # Generate embedding
        embedding = self._get_function_embedding(function_info)
        
        # Check if function already exists
        if function_id in self.function_ids:
            # Update the function
            idx = self.function_ids.index(function_id)
            logger.info(f"Updating existing function: {function_id} at index {idx}")
            
            # Verify index is valid
            if idx >= len(self.embeddings):
                logger.warning(f"Index {idx} out of range for embeddings list (length {len(self.embeddings)}). Appending instead.")
                self.embeddings.append(embedding.tolist())
            else:
                self.function_metadata[idx] = function_info
                self.embeddings[idx] = embedding.tolist()
        else:
            # Add the new function
            logger.info(f"Adding new function: {function_id}")
            self.function_metadata.append(function_info)
            self.function_ids.append(function_id)
            self.embeddings.append(embedding.tolist())
        
        # Ensure all lists have the same length
        assert len(self.function_metadata) == len(self.function_ids) == len(self.embeddings), \
            f"Data length mismatch after adding {function_id}"
        
        # Rebuild the index from scratch with updated embeddings
        self.index = faiss.IndexFlatL2(self.dimension)
        embeddings_array = np.array(self.embeddings).astype('float32')
        if len(embeddings_array) > 0:
            self.index.add(embeddings_array)
        
        # Save the updated data
        self._save_data()
        
        return function_id
    
    def register_functions_from_module(self, module_path):
        """Register all functions from a Python module."""
        module = importlib.import_module(module_path)
        registered_functions = []
        
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                function_id = self.add_function(obj)
                registered_functions.append(function_id)
        
        return registered_functions
    
    def search_function(self, query, n_results=3):
        """Search for the most relevant function based on the query."""
        if self.index.ntotal == 0:
            return None
        
        # Generate embedding for the query
        query_embedding = self.model.encode(query, normalize_embeddings=True)
        
        # Search the FAISS index
        distances, indices = self.index.search(query_embedding.reshape(1, -1), min(n_results, self.index.ntotal))
        
        if len(indices[0]) == 0:
            return None
        
        # Return search results with metadata
        search_results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.function_metadata):
                metadata = self.function_metadata[idx]
                distance = distances[0][i]
                
                search_results.append({
                    "id": self.function_ids[idx],
                    "name": metadata["name"],
                    "module": metadata["module"],
                    "docstring": metadata["docstring"],
                    "parameters": metadata.get("parameters", []),
                    "relevance_score": 1 / (1 + distance)  # Convert distance to similarity score
                })
        
        return search_results
    
    def count(self):
        """Return the number of functions in the database."""
        return self.index.ntotal 