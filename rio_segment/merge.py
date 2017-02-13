'''
Functions for merging adjacent segments using skimage.future.graph.RAG
'''
import numpy as np
from skimage import segmentation
from skimage.future import graph
import click


def update_edge_weights(graph, src, dst, n):
    '''
    update the edge weight between dst and n to include any edge pixels
    from between src and n.
    '''
    # if either src or dst have no edge with n, no weight is added.
    no_edge = {'count': 0, 'weight': 0}
    d = graph.edge[dst].get(n, no_edge)
    s = graph.edge[src].get(n, no_edge)

    # new pixel count is sum of both edges
    count = d['count'] + s['count']
    assert count != 0

    # new weight is mean of union of src and dst edge pixels.
    weight = (d['count'] * d['weight'] + s['count'] * s['weight']) / count

    # weight by the overall size of the two segments
    # (as segments become increasingly larger they are less likly to be merged)
    weight += graph.node[dst]['pixels'] + graph.node[n]['pixels']

    return {'count': count, 'weight': weight}


def merge_nodes(graph, src, dst):
    '''
    merge two nodes of the RAG
    '''
    # merge the pixel counts of the nodes
    graph.node[dst]['pixels'] += graph.node[src]['pixels']


def rag_merge_threshold(edges, labels, threshold, size_pen):
    '''
    Merge adjacent segments using region adjacency graph based on strength of
    edge between them.
    '''

    # create region adjacency graph using the edge info to produce
    # edge weights between the nodes.
    click.echo('creating Region Adjacency Graph')
    rag = graph.rag_boundary(labels, edges)

    # calculate pixel counts for each node
    lab, counts = np.unique(labels.ravel(), return_counts=True)
    click.echo('starting with {} segments'.format(lab.max()))
    counts = (counts / counts.max()) * size_pen
    for i, n in enumerate(lab):
        rag.node[n].update({'pixels': counts[i]})

    # update initial edge weights to weight by mean size of nodes
    for n1, n2 in rag.edges_iter():
        total_pix = rag.node[n1]['pixels'] + rag.node[n2]['pixels']
        rag.edge[n1][n2]['weight'] += total_pix
        rag.edge[n2][n1]['weight'] += total_pix

    # calculate a value from the threshold percentile of edge weights.
    edge_weights = [x[2]['weight'] for x in rag.edges(data=True)]
    t = np.percentile(edge_weights, threshold)

    # merge adjacent labels iteratively if their edge weight is below the
    # required threshold.
    click.echo('merging segments with edge weights below {} percentile'.format(
            threshold))
    refined_labels = graph.merge_hierarchical(
            labels, rag, t, rag_copy=True, in_place_merge=True,
            merge_func=merge_nodes, weight_func=update_edge_weights)
    refined_labels, *_ = segmentation.relabel_sequential(refined_labels + 1,
                                                         offset=1)
    click.echo('merged into {} segments'.format(refined_labels.max()))
    return refined_labels
