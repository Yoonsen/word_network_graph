import sqlite3
import networkx as nx
from collections import Counter, OrderedDict
import json

NEWS = "news_word_pairs.db"
BOOKS  = "book_word_pairs.db"
BOOKS_AND_NEWS = "book_news_word_pairs.db"

DB_DICT = {
    'bok': BOOKS,
    'avis': NEWS,
    'both': BOOKS_AND_NEWS
}


def export_to_json(entries):
    """ Exports results as a JSON object """
    return json.dumps(entries, indent=4, separators=(', ', ': '))



def query(db, sql, param=()):
    """ Query a sqlitedatabase with sql and param"""
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute(sql, param)
    return cur.fetchall()

def check_graph_first(db, x, top = 20):
    return query(db, "select * from word_graph where first = ? order by pmi desc limit ?", (x, top))
def check_graph_second(db, x, top = 20):
    return query(db, "select * from word_graph where second = ? order by pmi desc limit ?", (x, top))


def expand(db, x, top = 30):
    a = check_graph_first(db, x, top)
    b = check_graph_second(db, x, top)
    words = {x[1] for x in a} | {x[0] for x in b} - {x}
    G = a + b
    for word in words:
        G += check_graph_first(db, word, top) + check_graph_second(db, word, top)
    return G

def graph_query(db, words, top = 16, add_leaves = False):
    edges = [edge for w in words for edge in [tuple(x[:3]) for x in expand(db, w, top = top)]]
    g = nx.DiGraph()
    g.add_weighted_edges_from(edges)
    if not add_leaves:
        g = g.subgraph([n for n,d in g.out_degree() if d > 0])
    return g 

# create nodes and links used in force layout
# make a set of nodes and the links between them
def graph2force(graph, leaves = True):

    if leaves:
        nodes = [{"name": x, "size": graph.degree(x)} for x in graph.nodes()]
        links = [
            {"source": nodes.index({'name':n, 'size': graph.degree(n)}),
            "target": nodes.index({'name':m, 'size': graph.degree(m)}),
            "value": round(graph[n][m]['weight'])}
            for (n, m) in graph.edges()
        ]
    else:
        nodes = [{"name": x, "size": graph.degree(x)} for x in graph.nodes() if graph.degree(x) > 1]
        links = [
            {"source": nodes.index({'name': n, 'size': graph.degree(n)}),
             "target": nodes.index({'name': m, 'size': graph.degree(m)}),
             "value": round(graph[n][m]['weight'])}
            for (n, m) in graph.edges() if graph.degree(n) > 1 and graph.degree(m) > 1
        ]
    return {"nodes": nodes, "links":links}

#Generate a parataxis graph from a word


def word2graph_x(word, leaves = False, source=None, limit=10):
    graph =  graph_query(source, word, top = limit, add_leaves = True)
    return graph2force(graph, leaves = leaves), graph

def klikk2html(Graph):
    entry = "Tom graf"
    if Graph.__len__() > 0:
        cliques = k_cliques(Graph)
        sentral = sentrale(Graph)
        entry = "<h3 class= 'fheader'>The most central nodes</h3><div class='flist'>%s</div>" % (', '.join(["%s &ndash; <i style='font-size:0.8em'>%s</i>" % (x, round(y,3)) for (x,y) in sentral]))
        for clq in cliques:
            li = ""
            li += """<h4 class= 'fheader'>Cluster from %s-cliques</h4>
            <div class='flist'>
            <span class='fheader'>central words: </span>
            <i>%s</i></div>""" % ( clq['size'], ", ".join([str(x)+'-'+str(round(clq['centers'][x],2)) for x in clq['centers']]))
            li += """<div class='fheader'>factor
                    <span class='flist'>%s</span></div> """ % (round(clq['coeff'],3),)
            li += "<div class='flist' style='font-size:1.2em'><span class='fheader flist'>word: </span><span>%s</span></div>" % ( ", ".join(clq['cluster']),)
            entry += "<li>%s</li>" % li
    return "<div class = 'summary'><ul>%s</ul></div>" % entry

def graph_summary(Graph):
    if Graph.__len__() > 0:
        cliques = k_cliques(Graph)
        sentral = sentrale(Graph)
    return dict({'sentral': sentral, 'klikk':cliques})

def k_cliques(Graph, mc=2):
    """Generate all k-clique communities for Graph. Graf må ikke være tom"""
    alle = []
    mx = nx.graph_clique_number(Graph.to_undirected())+1
    for n in range(3, mx):
        alle += n_klikk(Graph, n, mc=mc)
    return alle

def n_klikk(Graph, n = 3, mc=2):
    """Generate a k-clique community for cliques of size n
       output is a dict of the form
        kcdict = {
            "size": n,
            "coeff": clustering,
            "centers": centers,
            "cluster": cliq
            }
      where size is the n-clique number, coeff is the clustering coefficient, centers are computed as the intersection between
      the clique and nx.closeness_centrality(Graph), and cluster is the result from nx.k_clique_communities(Graph.to_undirected(), n), where
      n is the same as size.
    """
    klikk = []
    kc_cliques = nx.algorithms.community.kclique.k_clique_communities(Graph.to_undirected(), n)
    ev = nx.closeness_centrality(Graph)
    for kc in kc_cliques:
        kcdict = dict()
        cliq = [x for x in kc]
        #centers = dict(Counter(nx.center(Graph.to_undirected().subgraph(cliq))).most_common(2))
        r = { x:ev[x] for x in ev if x in cliq}
        centers = OrderedDict(Counter(r).most_common(mc))
        clustering = nx.average_clustering(Graph.to_undirected(), list(cliq))
        kcdict = {
            "size": n,
            "coeff": clustering,
            "centers": centers,
            "cluster": cliq
            }
        klikk += [kcdict]
    return klikk

def sentrale(Graph, top = 10):
    #mc = Counter([('ord',0)])
    #SubGraph = nx.Graph()
    #SubGraph.add_edges_from([(x,y) for (x,y) in Graph.edges() if Graph.degree(x)>1 and Graph.degree(y)>1])
    #if Graph.__len__() > 0:
    mc = Counter(nx.closeness_centrality(Graph)).most_common(top)
    return mc


