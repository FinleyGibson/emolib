import matplotlib.patches as mpatches
import matplotlib.path as mpath
from matplotlib.collections import PatchCollection
import networkx as nx

import community.community_louvain as commlouv
from resources import _valences
import matplotlib.pyplot as plt
from math import cos, sin, radians


def _rotate_point(point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    Required arguments:
    ----------
    *point*:
        A two-values tuple, (x, y), of the point to rotate
        
    *angle*:
        The angle the point is rotated. The angle should be given in radians.
    
    Returns:
    ----------
    *(qx, qy)*:
        A two-values tuple, the new coordinates of the rotated point.     
        
    """
    ox, oy = 0, 0
    px, py = point
    angle = radians(angle)
    qx = ox + cos(angle) * (px - ox) - sin(angle) * (py - oy)
    qy = oy + sin(angle) * (px - ox) + cos(angle) * (py - oy)
    return (qx, qy)


def _label_rot_params(i, N, d):
    if 0 < i < N/4:
        rotation = 270+(d*i)%90
        align1 = 'right'
        align2 = 'bottom'
    elif i < N/2:
        rotation = (d*i)%90
        align1 = 'right'
        align2 = 'top'
    elif i < N*0.75:
        rotation = 270 + (d*i)%90
        align1 = 'left'
        align2 = 'top'
    else:
        rotation = (d*i)%90
        align1 = 'left'
        align2 = 'bottom'
        
    align2 = 'center'
    return rotation, align1, align2


def _draw_edge(s, t, pos, louv):
    
    if louv[s] == louv[t]:
        mx = (pos[s][0] + pos[t][0]/2)*.2
        my = (pos[s][1] + pos[t][1]/2)*.2
        alpha = .3
    else:
        mx, my = (0, 0)
        alpha = .5
    
    
    # Define Bezier curve
    Path = mpath.Path
    path_data = [
        (Path.MOVETO, pos[s]),
        (Path.CURVE3, (mx, my)),
        (Path.CURVE3, pos[t])
        ]
    
    # add the Path to ax
    codes, verts = zip(*path_data)
    path = mpath.Path(verts, codes)
    patch = mpatches.PathPatch(path)
    
    
    return alpha, patch


def _edge_params(w1, w2, _positive, _negative, _ambivalent, colz):
    
    if w1 in _positive and w1 in _positive:
        return colz['positive'], 3, 1
    if w1 in _negative and w2 in _negative:
        return colz['negative'], 3, 1
    
    if w1 in _negative and w2 in _positive:
        return 'purple', 3, 1
    if w1 in _positive and w2 in _negative:
        return 'purple', 3, 1
    
    return 'lightgrey', 1, -1


def _hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    lv = [int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    lv = [l/255 for l in lv] + [1]
    return lv


def draw_formamentis_circle_layout(fmn, highlight = [], language = 'english', ax = None):
    """
    
    """
    
    # Define color-blind palette
    colz = {'positive': (26/256, 133/256, 255/256),
            'negative': (212/256, 17/256, 89/256)}
    
    # Get positive or negative valences
    _positive, _negative, _ambivalent = _valences(language)
    
    if not ax:
        _, ax = plt.subplots(figsize=(16, 16)) 
    
    
    ## Graph and clusters
    G = nx.Graph(fmn.edges)
    louv = commlouv.best_partition(G)
    louv2 = {comm: [key for key, val in louv.items() if val == comm] for comm in set(louv.values())}
    
    # Compute nodes sizes after their degree
    degrees = dict(G.degree())
    mindeg, maxdeg = min(degrees.values()), max(degrees.values())
    if mindeg == maxdeg:
        maxdeg = mindeg + 1
    degrees = {key: 15*(val - mindeg)/(maxdeg - mindeg) for key, val in degrees.items()}
    
    
    ## Draw nodes
    
    N = len(fmn.vertices) + len(louv2) # N nodes require N endpoints + one space per cluster
    d = 360 / N
    
    
    pos = {}
    i = 0
    comm = 0
    counter = 0
    for _ in range(len(louv)):  
    
        # get position and space clusters
        if len(louv2[comm]) == 0:
            comm += 1
            i += 1
            
        v = louv2[comm].pop()
        i += 1
        counter += 1
        
        # compute position and rotation of label
        x, y = _rotate_point((0, 1), d*i)    
        pos[v] = (x, y)
        rotation, align1, align2 = _label_rot_params(i, N, d)
    
        
        # customization of label
        fz = 16/(N**(3/5)) * 10 + degrees[v]
        
        if v in _positive:
            color = colz['positive']
        elif v in _negative:
            color = colz['negative']
        else:
            color = '#030303'
        
        if v in highlight:
            ax.text(x,y, ' {} '.format(v), rotation = rotation, weight = 'bold',
                          bbox=dict(facecolor='none', edgecolor=color, linewidth = 3), 
                          rotation_mode="anchor", ha=align1, va=align2, fontsize = fz, color = color)
        else:
            ax.text(x,y, ' {} '.format(v), rotation = rotation,   
                          rotation_mode="anchor", ha=align1, va=align2, fontsize = fz, color = color)
            
    
    ## DRAW ARCHS
    patches = []
    alphas = []
    colors = []
    lws = []
    zors = []
    
    for s, t in fmn.edges:
        alpha, patch = _draw_edge(s, t, pos, louv)
        alphas.append(alpha)
        patches.append(patch)
        
        color, linewidth, zorder = _edge_params(s, t, _positive, _negative, _ambivalent, colz)
    
        colors.append(color)
        lws.append(linewidth)
        zors.append(zorder)
        
        
    patches = PatchCollection(patches, facecolor = 'none', linewidth = lws, edgecolor = colors, 
                                  match_original=True, alpha = alphas, zorder = 1, linewidths = lws)
    ax.add_collection(patches)
    
    
        
    plt.xlim((-1.5, 1.5))
    plt.ylim((-1.5, 1.5))

    ax.axis('off')
    return ax