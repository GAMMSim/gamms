from time import sleep
import gamms, gamms.osm
import pickle
import glob


files = glob.glob('raws/*.osm')
print(files)
for file in files:
    print(f'Processing {file}')
    G = gamms.osm.graph_from_xml(file, resolution=100.0)
    graph_path = file.replace('.osm', '.pkl')
    graph_path = graph_path.replace('raws/', 'processed/')
    with open(graph_path, 'wb') as f:
        pickle.dump(G, f)


graph_vis_config = {
    'width' : 1980,
    'height' : 1080
}

files = glob.glob('processed/*.pkl')


for file in files:
    show = True
    print(f'Processing {file}')
    with open(file, 'rb') as f:
        G = pickle.load(f)

    ctx = gamms.create_context(vis_engine=gamms.visual.Engine.PYGAME)
    ctx.graph.attach_networkx_graph(G)
    ctx.visual.set_graph_visual(**graph_vis_config)

    while show: 
        ctx.visual.simulate()
        # sleep(10)
        # show = False
    
    
