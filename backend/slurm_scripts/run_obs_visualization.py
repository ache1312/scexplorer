import sys, os, json
script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from utils import obs_visualization

def main(h5ad_path, outdir, dim_red, obs_keys):
    obs_keys_list = eval(obs_keys)  # Convert string representation back to list
    paths = obs_visualization(h5ad_path, outdir, dim_red, obs_keys_list)
    # print a JSON list so main.py can ast.literal_eval it
    print(json.dumps(paths))

if __name__ == "__main__":
    main(*sys.argv[1:])