import sys, os, json
script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from utils import generate_cell_heatmap_scanpy_style

def main(h5ad_path, outdir, groupby, options_json):
    opts = json.loads(options_json)
    
    # Convert old standard_scale values to new format for backward compatibility
    standard_scale = opts.get('standard_scale', 'none')
    if standard_scale == 'none':
        standard_scale = None
    elif standard_scale == 'gene':
        standard_scale = 'var'
    
    res = generate_cell_heatmap_scanpy_style(
        file_path=h5ad_path,
        outdir=outdir,
        groupby=groupby,
        gene_list=opts.get('gene_list'),
        top_n=int(opts.get('top_n', 10)),
        zscore=bool(opts.get('zscore', True)),
        standard_scale=standard_scale,
        clip_percentiles=None,
        cluster_rows=bool(opts.get('cluster_rows', True)),
        cluster_cols=bool(opts.get('cluster_cols', False)),
        layer=opts.get('layer'),
        use_raw=bool(opts.get('use_raw', False)),
        max_genes=int(opts.get('max_genes', 100)),
        output_filename=opts.get('output_filename', 'cell_heatmap.png'),
        dendrogram=bool(opts.get('dendrogram', False)),
        swap_axes=bool(opts.get('swap_axes', False)),
        show_gene_labels=opts.get('show_gene_labels'),
        vmin=opts.get('vmin'),
        vmax=opts.get('vmax'),
        vcenter=opts.get('vcenter'),
    )
    print(json.dumps(res))

if __name__ == "__main__":
    main(*sys.argv[1:])

