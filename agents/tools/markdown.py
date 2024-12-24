import re

def convert_to_markdown(content: str) -> str:
    """
    Convert a raw text content to properly formatted markdown.
    
    Args:
        content (str): The input content with potential escaped newlines.
    
    Returns:
        str: A properly formatted markdown string.
    """
    # Replace literal newline escapes with actual newlines
    formatted_content = content.replace('\\n', '\n')
    
    # Optional: Additional markdown cleanup and formatting
    # Remove any excessive whitespace
    formatted_content = re.sub(r'\n{3,}', '\n\n', formatted_content)
    
    # Ensure consistent list formatting
    formatted_content = re.sub(r'^(\s*)\*\s*', r'\1- ', formatted_content, flags=re.MULTILINE)
    
    return formatted_content