from pathlib import Path

# list of available layers for the optimisation based on the layer_list in data 
layer_list = Path(__file__).parents[2].joinpath('utils', 'layer_list.csv')
#layer_list = pd.read_csv().fillna('')