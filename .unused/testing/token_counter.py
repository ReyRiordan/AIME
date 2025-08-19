import tiktoken

def num_tokens_used(listOfMessages,encoding_name = "cl100k_base"):
    """Counts number of tokens from list of input

    Args:
        listOfMessages (list of str): List of all messages passed to API
        encoding_name (str): Preferred encoding type. Defaults to "cl100k_base".

    Returns:
        int: Number of tokens used
    """
    toReturn = 0
    for message in listOfMessages:
        encoding = tiktoken.get_encoding(encoding_name)
        toReturn=toReturn+len(encoding.encode(message))
    return toReturn
