import os
from turtle import width
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
import time
import numpy as np

from skimage import io
# import dash_daq as daq
# import dash_bio as dbio
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',dbc.themes.BOOTSTRAP]

app = DjangoDash('RateApp', external_stylesheets=external_stylesheets)

DEFAULT_COLORSCALE = [[0, 'rgb(12,51,131)'], [0.25, 'rgb(10,136,186)'],\
        [0.5, 'rgb(242,211,56)'], [0.75, 'rgb(242,143,56)'], \
        [1, 'rgb(217,30,30)']]

DEFAULT_COLORSCALE_NO_INDEX = [ea[1] for ea in DEFAULT_COLORSCALE]

def read_mniobj(file):
    ''' function to read a MNI obj file '''

    def triangulate_polygons(list_vertex_indices):
        ''' triangulate a list of n indices  n=len(list_vertex_indices) '''

        for k in range(0, len(list_vertex_indices), 3):
                yield list_vertex_indices[k: k+3]

    fp = open(os.path.join(os.getcwd(),'home','dash_apps', file), 'r')
    n_vert=[]
    n_poly=[]
    k=0
    list_indices=[]
    # Find number of vertices and number of polygons, stored in .obj file.
    # Then extract list of all vertices in polygons
    for i, line in enumerate(fp):
        if i==0:
        #Number of vertices
             n_vert=int(line.split()[6])
             vertices=np.zeros([n_vert,3])
        elif i<=n_vert:
             vertices[i-1]=list(map(float, line.split()))
        elif i>2*n_vert+5:
            if not line.strip():
                k=1
            elif k==1:
                list_indices.extend(line.split())
    #at this point list_indices is a list of strings, and each string is a vertex index, like this '23'
    #maps in Python 3.6 returns a generator, hence we convert it to a list
    list_indices=list(map(int, list_indices))#conver the list of string indices to int indices
    faces=np.array(list(triangulate_polygons(np.array(list_indices))))
    return vertices, faces

def standard_intensity(x,y,z):
    ''' color the mesh with a colorscale according to the values
                              of the vertices z-coordinates '''
    return z

def plotly_triangular_mesh(vertices, faces, intensities=None, colorscale="Viridis",
                           flatshading=False, showscale=False, reversescale=False, plot_edges=False):
    ''' vertices = a numpy array of shape (n_vertices, 3)
        faces = a numpy array of shape (n_faces, 3)
        intensities can be either a function of (x,y,z) or a list of values '''

    x,y,z=vertices.T
    I,J,K=faces.T

    if intensities is None:
        intensities = standard_intensity(x,y,z)

    if hasattr(intensities, '__call__'):
        intensity=intensities(x,y,z)#the intensities are computed  via a function,
                                    #that returns the list of vertices intensities
    elif  isinstance(intensities, (list, np.ndarray)):
        intensity=intensities#intensities are given in a list
    else:
        raise ValueError("intensities can be either a function or a list, np.array")

    mesh=dict(
        type='mesh3d',
        x=x, y=y, z=z,
        colorscale=colorscale,
        intensity= intensities,
        flatshading=flatshading,
        i=I, j=J, k=K,
        name='',
        showscale=showscale
    )

    mesh.update(lighting=dict( ambient= 0.18,
                                  diffuse= 1,
                                  fresnel=  0.1,
                                  specular= 1,
                                  roughness= 0.1,
                                  facenormalsepsilon=1e-6,
                                  vertexnormalsepsilon= 1e-12))

    mesh.update(lightposition=dict(x=100,
                                      y=200,
                                      z= 0))

    if  showscale is True:
            mesh.update(colorbar=dict(thickness=20, ticklen=4, len=0.75))

    if plot_edges is False: # the triangle sides are not plotted
        return  [mesh]
    else:#plot edges
        #define the lists Xe, Ye, Ze, of x, y, resp z coordinates of edge end points for each triangle
        #None separates data corresponding to two consecutive triangles
        tri_vertices= vertices[faces]
        Xe=[]
        Ye=[]
        Ze=[]
        for T in tri_vertices:
            Xe+=[T[k%3][0] for k in range(4)]+[ None]
            Ye+=[T[k%3][1] for k in range(4)]+[ None]
            Ze+=[T[k%3][2] for k in range(4)]+[ None]
        #define the lines to be plotted
        lines=dict(type='scatter3d',
                   x=Xe,
                   y=Ye,
                   z=Ze,
                   mode='lines',
                   name='',
                   line=dict(color= 'rgb(70,70,70)', width=1)
               )
        return [mesh, lines]


pts, tri = read_mniobj("surf_reg_model_both.obj")
intensities = np.loadtxt(os.path.join(os.getcwd(), 'home', 'dash_apps', 'aal_atlas.txt'))
data=plotly_triangular_mesh(pts, tri, intensities,
                            colorscale=DEFAULT_COLORSCALE, flatshading=False,
                            showscale=False, reversescale=False, plot_edges=False)
data[0]['name'] = 'human_atlas'

axis_template = dict(
    showbackground=True,
    backgroundcolor="rgb(10, 10,10)",
    gridcolor="rgb(255, 255, 255)",
    zerolinecolor="rgb(255, 255, 255)")

plot_layout = dict(
    title='3D Repesentation of Brain data for congenital abnormalities',
         margin=dict(t=0,b=0,l=0,r=0),
         font=dict(size=12, color='white'),
         width=700,
         height=700,
         showlegend=False,
         scene=dict(xaxis=axis_template,
                    yaxis=axis_template,
                    zaxis=axis_template,
                    aspectratio=dict(x=1, y=1.2, z=1),
                    camera=dict(eye=dict(x=1.25, y=1.25, z=1.25)),
                    annotations=[]
                )
        )


vol = io.imread("https://s3.amazonaws.com/assets.datacamp.com/blog_assets/attention-mri.tif")
volume = vol.T
r, c = volume[0].shape

# Define frames
import plotly.graph_objects as go
nb_frames = 68

fig = go.Figure(frames=[go.Frame(data=go.Surface(
    z=(6.7 - k * 0.1) * np.ones((r, c)),
    surfacecolor=np.flipud(volume[67 - k]),
    cmin=0, cmax=200
    ),
    name=str(k) # you need to name the frame for the animation to behave properly
    )
    for k in range(nb_frames)])

# Add data to be displayed before animation starts
fig.add_trace(go.Surface(
    z=6.7 * np.ones((r, c)),
    surfacecolor=np.flipud(volume[67]),
    colorscale='Gray',
    cmin=0, cmax=200,
    colorbar=dict(thickness=20, ticklen=4)
    ))


def frame_args(duration):
    return {
            "frame": {"duration": duration},
            "mode": "immediate",
            "fromcurrent": True,
            "transition": {"duration": duration, "easing": "linear"},
        }

sliders = [
            {
                "pad": {"b": 10, "t": 60},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {
                        "args": [[f.name], frame_args(0)],
                        "label": str(k),
                        "method": "animate",
                    }
                    for k, f in enumerate(fig.frames)
                ],
            }
        ]

# Layout
fig.update_layout(
    title='MRI Data for congenital abnormalities',
         width=600,
         height=600,
         scene=dict(
                    zaxis=dict(range=[-0.1, 6.8], autorange=False),
                    aspectratio=dict(x=1, y=1, z=1),
                    ),
         updatemenus = [
            {
                "buttons": [
                    {
                        "args": [None, frame_args(50)],
                        "label": "&#9654;", # play symbol
                        "method": "animate",
                    },
                    {
                        "args": [[None], frame_args(0)],
                        "label": "&#9724;", # pause symbol
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 70},
                "type": "buttons",
                "x": 0.1,
                "y": 0,
            }
         ],
         sliders=sliders
)
app.layout = html.Div([
 dbc.Row(
     [
         dbc.Col(
             [
                 dbc.Container(
                     [dcc.Graph(figure=fig)]
                 ),
                
             ],
             width=5
        
         ),
         dbc.Col(
             [
                 dcc.Graph(
                     id='brain-graph',
                     figure={
                         'data': data,
                         'layout': plot_layout,
                     },
                     config={'editable': True, 'scrollZoom': False},
                 ),
             ],
      

         )
     ]
 )

],)
