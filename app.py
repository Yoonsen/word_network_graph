
# coding: utf-8

#--------- Flask modules

from flask import Flask, request, jsonify, Response

#-------- Python modules -------#

from query_graphs_to_html import word2graph_x, klikk2html, export_to_json

#-------- Global databases    

NEWS = "news_word_pairs.db"
BOOKS  = "book_word_pairs.db"
BOOKS_AND_NEWS = "book_news_word_pairs.db"

DB_DICT = {
    'bok': BOOKS,
    'avis': NEWS,
    'both': BOOKS_AND_NEWS
}



#-------- Routes

app = Flask(__name__)

@app.route('/galaxies/query')
def galaxyjson():
    xparams = dict(request.args.items())
    params = validate(xparams)
    if len(params['terms']) == 0:
        params['terms'] = ' '
    else:
        params['terms'] = return_terms(params['terms'])
    if params['corpus'] == 'all':
        galaxy= word2graph_x(
            source = DB_DICT['both'], 
            word = params['terms'], 
            leaves = bool(int(params['leaves'])), 
            limit = int(params['limit'])
        )
    elif params['corpus'] == 'bok' or params['corpus'] == 'avis':
        galaxy= word2graph_x(
            source = DB_DICT[params['corpus']], 
            word = params['terms'], 
            leaves = bool(int(params['leaves'])), 
            limit = int(params['limit'])
        )
            
    values = galaxy[0]
    graph = galaxy[1]
    galaxy_html = klikk2html(graph)
    values["html"] = galaxy_html
    jsonOutput = export_to_json(values)
    return Response(jsonOutput, mimetype='application/json')

def validate(sParams):
    if 'd' in sParams:
        if (int(sParams['d']) > 4):
            sParams['d'] = 4
        elif (int(sParams['d']) <= 0):
            sParams['d'] = 1
        else:
            sParams['d'] = int(sParams['d'])

    if 'mode' in sParams:
        if (int(sParams['mode']) > 4):
            sParams['mode'] = 4
        elif (int(sParams['mode']) <= 0):
            sParams['mode'] = 1
        else:
            sParams['mode'] = int(sParams['mode'])

    if 'limit' in sParams:
        if (int(sParams['limit']) > 20):
            sParams['limit'] = 20
        elif (int(sParams['limit']) <= 0):
            sParams['limit'] = 1
        else:
            sParams['limit'] = int(sParams['limit'])

    return sParams

def return_terms(terms):
    """Gets a string of terms and returns them as a list, with some clean-up"""

    terms =[x.strip() for x in terms.split(',')]

    return terms


# ------ main ----- #

if __name__ == '__main__':
    app.run()
