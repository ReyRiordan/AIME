paths = {
        "intro" : "./webapp/website_text/intro.txt",
        "selection" : "./webapp/website_text/selection.txt",
        "interview" : "./webapp/website_text/interview.txt",
        "post" : "./webapp/website_text/post.txt",
        "feedback" : "./webapp/website_text/feedback.txt",
        "final": "./webapp/website_text/final.txt"
        }

def get(content):
    path = paths[content]
    with open(path, 'r', encoding='utf8') as text:
            description = text.read()
    return description
