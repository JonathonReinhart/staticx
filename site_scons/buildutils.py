def quote(s, q='"'):
    return q + s + q

def cquote(s):
    if isinstance(s, str):
        s = quote(s, '"')
    else:
        s = str(s)
    return quote(s, "'")
