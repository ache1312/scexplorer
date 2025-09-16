import sys, os, json
script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from utils import var_visualization

def main(h5ad_path, outdir, dim_red, var_keys):
    var_keys_list = eval(var_keys)  # Convert string representation back to list
    paths = var_visualization(h5ad_path, outdir, dim_red, var_keys_list)
    # print a JSON list so main.py can ast.literal_eval it
    print(json.dumps(paths))

if __name__ == "__main__":
    main(*sys.argv[1:])
