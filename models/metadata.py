class Metadata(dict):
    """
    Metadata is a dictionary-like class for storing arbitrary metadata.
    """
    
    def __get_pydantic_core_schema__(self, handler):
        # Define a custom schema for RequestConfig
        return handler.generate_schema(dict)
