paths = {
        "intro" : "./streamlit/website_text/intro.txt",
        "selection" : "./streamlit/website_text/selection.txt",
        "interview" : "./streamlit/website_text/interview.txt",
        "post" : "./streamlit/website_text/post.txt",
        "feedback" : "./streamlit/website_text/feedback.txt",
        "final": "./streamlit/website_text/final.txt"
        }

def get(content):
    path = paths[content]
    with open(path, 'r', encoding='utf8') as text:
            description = text.read()
    return description
