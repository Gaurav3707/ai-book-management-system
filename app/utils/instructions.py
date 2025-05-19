class LLMInstructions:
    @staticmethod
    def get_recommendation_prompt(books_for_prompt: str) -> str:
        return f"""<Instruction>
            <prompt>
                Based on the user's highly rated books: {books_for_prompt}, provide a list of 5 book recommendations with their titles and authors.
            </prompt>
            <responseFormat>
                <format>JSON</format>
                <guidelines>
                    Ensure the output is in JSON format and follows this structure:
                    {{
                        "recommendations": [
                            {{
                                "title": "string",
                                "author": "string",
                                "genre": "string",
                                "year_published": "string",
                            }}
                        ]
                    }}
                </guidelines>
            </responseFormat>
            </Instruction>"""
    
    @staticmethod
    def get_content_summary_prompt(content: str) -> str:
        return f"Provide a short summary for the following - {content}."
    
    @staticmethod
    def get_summary_book_id_prompt(title: str, author: str) -> str:
        return f"Provide a short summary for book - {title} by {author}."
    
    @staticmethod
    def get_summary_book_name_prompt(book_name: str) -> str:
        return f"Provide a short summary for book - {book_name}."
    

    
            
