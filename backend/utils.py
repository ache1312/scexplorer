import rpy2.robjects as robjects

import mygene
import numpy as np
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import scanpy as sc
import scipy.sparse as sp

from fastapi import HTTPException
from dotenv import load_dotenv
import plotly.io as pio
from plotly.offline import plot
from plotly.subplots import make_subplots
from scipy.sparse import issparse
from scanpy import preprocessing
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import matplotlib.colors as mcolors
import numpy as np

# Import the new theme system
from plot_themes import get_current_theme, apply_theme_to_figure, theme_manager, get_plot_theme_config


colors = ["lightgray", "red"]  # Define the transition colors from light gray to red
n_bins = [3]  # Number of bins for each segment
cmap_name = 'custom_lightgray_to_red'

# Create the colormap
cm = mcolors.LinearSegmentedColormap.from_list(cmap_name, colors, N=100)

def create_plotly_colorscale(colormap, N=100):
    # Generate a list of colors from the colormap
    scale = np.linspace(0, 1, N)
    colors = colormap(scale)

    # Convert to Plotly color scale format
    plotly_scale = [(s, mcolors.rgb2hex(c)) for s, c in zip(scale, colors)]
    return plotly_scale

plotly_cm = create_plotly_colorscale(cm)

load_dotenv()

sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
# Allow disabling emails for simple local runs
enable_email = os.getenv("ENABLE_EMAIL", "true").lower() == "true"


def get_dataset_description(adata):
    num_observations = adata.n_obs
    num_variables = adata.n_vars
    mean_n_genes_by_counts = adata.obs['n_genes_by_counts'].mean()
    mean_total_counts = adata.obs['total_counts'].mean()
    mean_pct_counts_mito = adata.obs['pct_counts_mito'].mean()
    std_n_genes_by_counts = adata.obs['n_genes_by_counts'].std()
    std_total_counts = adata.obs['total_counts'].std()
    std_pct_counts_mito = adata.obs['pct_counts_mito'].std()   
    cell_observations = len(adata.obs.columns.to_list())
    gene_observations = len(adata.var.columns.to_list())
    dataset_description = {
    'num_observations': num_observations,
    'num_variables': num_variables,
    'mean_n_genes_by_counts': f"{mean_n_genes_by_counts:0.2f}",
    'mean_total_counts': f"{mean_total_counts:0.2f}",
    'mean_pct_counts_mito': f"{mean_pct_counts_mito:0.2f}",
    'std_n_genes_by_counts': f"{std_n_genes_by_counts:0.2f}",
    'std_total_counts': f"{std_total_counts:0.2f}",
    'std_pct_counts_mito': f"{std_pct_counts_mito:0.2f}",
    'cell_observations' : cell_observations,
    'gene_observations': gene_observations
    }
    return dataset_description

def get_quality_control_plots(file_path,save_path,species,flavor,root_path,unique_id):
    scrna = sc.read_h5ad(file_path)
    scrna.obs.to_csv(f"{root_path}/{unique_id}/{unique_id}_obs.csv")
    scrna.var.to_csv(f"{root_path}/{unique_id}/{unique_id}_var.csv")
    scanpy_adata = mygene_converter(scrna, species,flavor)
    # print(f"qc_check_names_my_gene = {scanpy_adata.var.index}")
    if species == "human":
        if flavor == "symbol":
            scanpy_adata.var["mito"] = scanpy_adata.var_names.str.startswith('MT-')
            sc.pp.calculate_qc_metrics(scanpy_adata, qc_vars=["mito"], inplace=True)
            plot_paths = plot_violin(scanpy_adata,save_path)
            dataset_description = get_dataset_description(scanpy_adata)
            scanpy_adata.write_h5ad(file_path)

            return plot_paths,dataset_description
        else:
            # adata.var["mito"] = adata.var_names.str.startswith('MT-')
            # sc.pp.calculate_qc_metrics(adata, qc_vars=["mito"], inplace=True)
            # plot_paths = plot_violin(adata,save_path)
            # dataset_description = get_dataset_description(adata)
            # return plot_paths,dataset_description
            pass
            #revisar el ensembl id de genes mitocondriales
    else:
        if flavor == "symbol":
            scanpy_adata.var["mito"] = scanpy_adata.var_names.str.startswith('mt-')
            sc.pp.calculate_qc_metrics(scanpy_adata, qc_vars=["mito"], inplace=True)
            plot_paths = plot_violin(scanpy_adata,save_path)
            dataset_description = get_dataset_description(scanpy_adata)
            scanpy_adata.write_h5ad(file_path)

            return plot_paths,dataset_description
        else:
            # adata.var["mito"] = adata.var_names.str.startswith('MT-')
            # sc.pp.calculate_qc_metrics(adata, qc_vars=["mito"], inplace=True)
            # plot_paths = plot_violin(adata,save_path)
            # dataset_description = get_dataset_description(adata)
            # return plot_paths,dataset_description
            pass
            #revisar el ensembl id de genes mitocondriales   

def load_and_preprocess_data(file_path: str,save_path:str, doublet_detection: bool,root_path: str, unique_id:str, min_genes: int = 200, min_cells: int = 3, mito_threshold: int = 5):
    """
    Load and preprocess the data.

    Parameters:
    - file_path: Path to the .h5ad file.
    - min_genes: Minimum number of genes expressed required for a cell to pass filtering.
    - min_cells: Minimum number of cells for a gene to be kept.
    - mito_threshold: Threshold for mitochondrial gene content. Cells with a percentage above this threshold will be filtered out.

    Returns:
    - info_dic: Dictionary with preprocessing information.
    - adata: Processed AnnData object.
    """
    adata = sc.read_h5ad(file_path)
    n_cells_pre = adata.n_obs
    n_genes_pre = adata.n_vars
    
    # Filter cells and genes based on min_genes and min_cells
    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)

    # Identify Mitochondrial Genes
    if len(adata.var_names[adata.var_names.str.startswith('mt-')]) > 0:
        adata.var["mito"] = adata.var_names.str.startswith('mt-')
    elif len(adata.var_names[adata.var_names.str.startswith('MT-')]) > 0:
        adata.var["mito"] = adata.var_names.str.startswith('MT-')    
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mito"], inplace=True)    # Filter cells based on mitochondrial content using the provided threshold
    adata = adata[adata.obs["pct_counts_mito"] < mito_threshold, :]
    
    if doublet_detection:
        sc.external.pp.scrublet(adata)
        adata = adata[adata.obs["predicted_doublet"] == False]
        adata.layers["counts"] = adata.X.copy()
        adata.raw = adata
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
        adata.write_h5ad(file_path)
        sc.pp.highly_variable_genes(adata, n_top_genes=2000)
        adata.obs.to_csv(f"{root_path}/{unique_id}/{unique_id}_obs.csv")
        adata.var.to_csv(f"{root_path}/{unique_id}/{unique_id}_var.csv")
        all_paths = plot_violin(adata,save_path)
        plot_total_counts_n_genes_by_count_path = plot_scatter(adata,save_path,"total_counts_n_genes_by_count","total_counts",["n_genes_by_counts"], x_label="Total Counts",y_label="N° Genes by Counts",color="orange",color_index=0)
        plot_total_counts_mitochondrial_counts_path = plot_scatter(adata,save_path,"total_counts_mitochondrial_counts","total_counts",["pct_counts_mito"], x_label="Total Counts",y_label="% Mitochondrial Counts",color="green",color_index=1)
        plot_hvg_path = plot_scatter_hvg(adata,save_path,"hvg","means",["dispersions_norm"],x_label="Normalized Dispersion",y_label="Mean Expression")
        all_paths.extend([plot_total_counts_n_genes_by_count_path,plot_total_counts_mitochondrial_counts_path,plot_hvg_path])
        n_cells_post_mito_filter = adata.n_obs 
        info_dic = {
            "cells_number_pre_processing": n_cells_pre,
            "genes_number_pre_processing": n_genes_pre,
            "cells_number_post_processing": n_cells_post_mito_filter,
            "genes_number_post_processing": adata.n_vars,
            "processing_plot_paths": all_paths,
            "message": "Data processed successfully."
        }
        return info_dic
    else:
        adata.layers["counts"] = adata.X.copy()
        adata.raw = adata
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
        adata.write_h5ad(file_path)
        sc.pp.highly_variable_genes(adata, n_top_genes=2000)
        adata.obs.to_csv(f"{root_path}/{unique_id}/{unique_id}_obs.csv")
        adata.var.to_csv(f"{root_path}/{unique_id}/{unique_id}_var.csv")
        all_paths = plot_violin(adata,save_path)
        plot_total_counts_n_genes_by_count_path = plot_scatter(adata,save_path,"total_counts_n_genes_by_count","total_counts",["n_genes_by_counts"], x_label="Total Counts",y_label="N° Genes by Counts",color="orange",color_index=0)
        plot_total_counts_mitochondrial_counts_path = plot_scatter(adata,save_path,"total_counts_mitochondrial_counts","total_counts",["pct_counts_mito"], x_label="Total Counts",y_label="% Mitochondrial Counts",color="green",color_index=1)
        plot_hvg_path = plot_scatter_hvg(adata,save_path,"hvg","means",["dispersions_norm"],x_label="Normalized Dispersion",y_label="Mean Expression")
        all_paths.extend([plot_total_counts_n_genes_by_count_path,plot_total_counts_mitochondrial_counts_path,plot_hvg_path])
        n_cells_post_mito_filter = adata.n_obs 
        info_dic = {
            "cells_number_pre_processing": n_cells_pre,
            "genes_number_pre_processing": n_genes_pre,
            "cells_number_post_processing": n_cells_post_mito_filter,
            "genes_number_post_processing": adata.n_vars,
            "processing_plot_paths": all_paths,
            "message": "Data processed successfully."
        }
        return info_dic
    
def run_pca_on_data(file_path,save_path,top_genes,hvg_flavor,root_path,unique_id):
    adata = sc.read_h5ad(file_path)
    adata.var["mito"] = adata.var_names.str.startswith('MT-')
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mito"], inplace=True)    
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=int(top_genes),flavor=hvg_flavor)
    adata_hvg= adata.copy()
    adata_hvg= adata_hvg[:, adata_hvg.var.highly_variable]
    sc.tl.pca(adata_hvg, svd_solver='arpack')
    adata.obsm['X_pca'] = adata_hvg.obsm['X_pca']
    adata.uns["pca"] = adata_hvg.uns["pca"]
    adata.write(file_path)
    adata_hvg.write_h5ad(f"{save_path}/embedding.h5ad")
    adata.obs.to_csv(f"{root_path}/{unique_id}/{unique_id}_obs.csv")
    adata.var.to_csv(f"{root_path}/{unique_id}/{unique_id}_var.csv")
    plot_pca_percentage_mito_path = plot_pca_and_obs(pca_coords=adata.obsm["X_pca"][:, :2],fig_name="pca_percentage_mito",color_column="pct_counts_mito",title=f"% of Mitochondrial Genes",data_df=adata.obs,save_path=save_path,output_format="html")
    plot_pca_total_counts_path  = plot_pca_and_obs(pca_coords=adata.obsm["X_pca"][:, :2],fig_name="pca_total_counts",color_column="total_counts",title="Total Counts",data_df=adata.obs,save_path=save_path,output_format="html")
    plot_pca_n_genes_per_count_path = plot_pca_and_obs(pca_coords=adata.obsm["X_pca"][:, :2],fig_name="pca_n_genes_by_counts",color_column="n_genes_by_counts",title="N° Genes per Counts",data_df=adata.obs,save_path=save_path,output_format="html")
    elbow_plot = plot_elbow(adata=adata,save_path=save_path,fig_name="pca_elbow_plot")
    
    return [plot_pca_percentage_mito_path,plot_pca_total_counts_path,plot_pca_n_genes_per_count_path,elbow_plot]

def run_clustering_on_data(file_path,save_path,n_neighbors,n_pcs,resolution,root_path,unique_id):
    adata_all_genes = sc.read_h5ad(file_path)
    adata = sc.read_h5ad(f"{save_path}/embedding.h5ad")
    # adata.raw = adata
    # adata = adata[:, adata.var.highly_variable]
    # # sc.pp.scale(adata, max_value=10)#ADD AS PARAMETER;FOR THE MOMENT DEFAULT 
    # sc.tl.pca(adata, svd_solver='arpack')
    sc.pp.neighbors(adata, int(n_neighbors), int(n_pcs))
    sc.tl.umap(adata)
    sc.tl.leiden(adata,resolution=resolution)
    adata_all_genes.obs['leiden'] = adata.obs['leiden']
    adata_all_genes.obsm['X_umap'] = adata.obsm['X_umap'] 
    adata_all_genes.uns["umap"] = adata.uns["umap"]
    adata_all_genes.obs.to_csv(f"{root_path}/{unique_id}/{unique_id}_obs.csv")
    adata_all_genes.var.to_csv(f"{root_path}/{unique_id}/{unique_id}_var.csv")
    adata_all_genes.write_h5ad(file_path)
    sc.tl.dendrogram(adata,groupby="leiden")
    sc.tl.rank_genes_groups(adata,groupby="leiden", method='wilcoxon')
    # clustering_info = len(adata.obs['leiden'].unique()) #usar para dar info
    plot_umap_leiden_path = plot_umap_and_obs(umap_coords=adata.obsm["X_umap"],fig_name="umap_leiden",color_column="leiden",title="Leiden Clusters",data_df=adata.obs,save_path=save_path)
    plot_umap_percentage_mito_path = plot_umap_and_obs(umap_coords=adata.obsm["X_umap"],fig_name="umap_percentage_mito",color_column="pct_counts_mito",title=f"% of Mitochondrial Genes",data_df=adata.obs,save_path=save_path)
    plot_umap_total_counts_path = plot_umap_and_obs(umap_coords=adata.obsm["X_umap"],fig_name="umap_total_counts",color_column="total_counts",title="Total Counts",data_df=adata.obs,save_path=save_path)
    plot_umap_n_genes_per_count_path = plot_umap_and_obs(umap_coords=adata.obsm["X_umap"],fig_name="umap_n_genes_by_counts",color_column="n_genes_by_counts",title="N° Genes per Counts",data_df=adata.obs,save_path=save_path)
    plot_embedding_paths = [plot_umap_leiden_path,plot_umap_percentage_mito_path,plot_umap_total_counts_path,plot_umap_n_genes_per_count_path]
    return plot_embedding_paths

def _theme_to_matplotlib_cmap(palette_name=None, n_colors: int = 256):
    """Build a matplotlib colormap from the current theme's continuous palette."""
    current_theme = get_current_theme()
    colorscale = current_theme.get_plotly_colorscale(palette_name=palette_name, n_colors=n_colors)
    hex_colors = [c for _, c in colorscale]
    return mcolors.LinearSegmentedColormap.from_list('theme_continuous', hex_colors, N=n_colors)

def generate_cell_heatmap_scanpy_style(
    file_path: str,
    outdir: str,
    groupby: str = "leiden",
    gene_list=None,                # list[str] | dict[str, list[str]] for grouped brackets
    top_n: int = 10,
    zscore: bool = True,
    standard_scale: str | None = None,  # None | "var" | "gene" | "obs" | "cell"
    clip_percentiles=(1.0, 99.0),
    cluster_rows: bool = True,     # cluster genes (columns)
    cluster_cols: bool = False,    # reserved; kept for parity
    layer: str | None = None,
    use_raw: bool = False,
    max_genes: int = 100,
    output_filename: str = "cell_heatmap.png",
    dendrogram: bool = False,      # order categories using sc.tl.dendrogram
    swap_axes: bool = False,       # rotate layout like sc.pl.heatmap(swap_axes=True)
    show_gene_labels: bool | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    vcenter: float | None = None,
    norm=None,                     # matplotlib Normalize; if None + vcenter given -> TwoSlopeNorm
):
    """
    Cell-level heatmap (cells x genes) with scanpy-like layout:
    - left/bottom color blocks for `groupby`
    - optional dendrogram of `groupby` categories
    - optional gene-group brackets (if gene_list is a dict)
    - compact colorbar pane
    - swap_axes to place categories on x and genes on y

    Returns: dict(path, genes_used, genes_missing, categories_order)
    """
    import os, warnings
    import numpy as np, pandas as pd
    import scanpy as sc
    import matplotlib.pyplot as plt
    from matplotlib import gridspec
    from matplotlib.colors import BoundaryNorm, ListedColormap, TwoSlopeNorm
    from scipy.sparse import issparse as _issparse
    try:
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import pdist
    except Exception:
        linkage = leaves_list = pdist = None

    # ----------------------------- helpers -----------------------------
    def _theme_cmap(default="viridis"):
        try:
            # use your app's theme if available
            return _theme_to_matplotlib_cmap(get_current_theme().colors.get("continuous_palette", default))
        except Exception:
            return plt.get_cmap(default)

    def _ensure_cat(series):
        s = series.copy()
        if not pd.api.types.is_categorical_dtype(s):
            s = s.astype("category")
        return s

    def _ensure_groupby_colors(adata, key, cmap_name="tab20"):
        if f"{key}_colors" in adata.uns:
            cats = list(adata.obs[key].cat.categories)
            cols = list(adata.uns[f"{key}_colors"])
            # if lengths mismatch, regenerate
            if len(cols) == len(cats):
                return cols
        
        # Use theme system for consistent cluster colors
        num_cats = len(adata.obs[key].cat.categories)
        try:
            from plot_themes import get_current_theme
            current_theme = get_current_theme()
            theme_colors = current_theme.get_cluster_colors(num_cats)
            adata.uns[f"{key}_colors"] = theme_colors
            return theme_colors
        except Exception:
            # fallback palette - fix division by zero bug
            base = plt.colormaps.get(cmap_name)
            if num_cats == 1:
                cols = [base(0.0)]
            else:
                cols = [base(i / (num_cats - 1)) for i in range(num_cats)]
            adata.uns[f"{key}_colors"] = [mplcolor_to_hex(c) for c in cols]
            return adata.uns[f"{key}_colors"]

    def mplcolor_to_hex(c):
        import matplotlib as mpl
        return mpl.colors.to_hex(c)

    def _plot_colorblocks(ax, cat_codes, labels, colors, orientation="left"):
        # cat_codes: length = number of rows (cells) or columns (cells) in current order
        # Compute block order and sizes by run-length encoding to preserve the visual order
        from matplotlib.colors import ListedColormap, BoundaryNorm
        cmap = ListedColormap(colors, "groupby_cmap")
        norm = BoundaryNorm(np.arange(len(colors)+1)-0.5, len(colors))
        ax.grid(False)

        # Run-length encode the category codes to keep the on-plot order
        codes = np.asarray(cat_codes)
        order_codes = []
        order_counts = []
        if codes.size > 0:
            current = codes[0]
            count = 1
            for v in codes[1:]:
                if v == current:
                    count += 1
                else:
                    order_codes.append(current)
                    order_counts.append(count)
                    current = v
                    count = 1
            order_codes.append(current)
            order_counts.append(count)

        if orientation == "left":
            ax.imshow(codes[:, None], aspect="auto", cmap=cmap, norm=norm)
            if len(labels) > 1 and order_counts:
                cumsum = np.cumsum(order_counts)
                ticks = [(cumsum[i-1] if i > 0 else 0) + (n - 1) / 2.0 for i, n in enumerate(order_counts)]
                ax.set_yticks(ticks)
                ax.set_yticklabels([labels[v] for v in order_codes], fontsize="small")
            ax.tick_params(axis="y", left=False)
            ax.tick_params(axis="x", bottom=False, labelbottom=False)
            for spine in ("right","top","left","bottom"):
                ax.spines[spine].set_visible(False)
            ax.set_ylabel(groupby)
        else:
            ax.imshow(codes[None, :], aspect="auto", cmap=cmap, norm=norm)
            if len(labels) > 1 and order_counts:
                cumsum = np.cumsum(order_counts)
                ticks = [(cumsum[i-1] if i > 0 else 0) + (n - 1) / 2.0 for i, n in enumerate(order_counts)]
                ax.set_xticks(ticks)
                ax.set_xticklabels([labels[v] for v in order_codes], fontsize="small", rotation=90 if max(len(str(x)) for x in labels) >= 3 else 0)
            ax.tick_params(axis="x", bottom=False)
            ax.tick_params(axis="y", left=False, labelleft=False)
            for spine in ("right","top","left","bottom"):
                ax.spines[spine].set_visible(False)
            ax.set_xlabel(groupby)

    def _plot_var_group_brackets(ax, labels, positions, orientation="top"):
        # positions: list[(start_idx, end_idx)] over the current gene order
        from matplotlib.path import Path
        from matplotlib import patches
        if not positions:
            ax.axis("off")
            return
        if orientation == "top":
            rotation = 90 if max(len(x) for x in labels) > 4 else 0
            verts, codes = [], []
            left = [p[0]-0.3 for p in positions]
            right = [p[1]+0.3 for p in positions]
            for i in range(len(positions)):
                verts += [(left[i], 0), (left[i], 0.6), (right[i], 0.6), (right[i], 0)]
                codes += [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO]
                xmid = left[i] + (right[i]-left[i])/2
                ax.text(xmid, 1.05, labels[i], ha="center", va="bottom", rotation=rotation, fontsize="small")
            patch = patches.PathPatch(Path(verts, codes), facecolor="none", lw=1.5)
            ax.add_patch(patch)
            ax.grid(False); ax.axis("off")
            ax.tick_params(axis="both", bottom=False, labelbottom=False, left=False, labelleft=False)
        else:
            ax.axis("off")

    def _compute_norm(vmin, vmax, vcenter, norm):
        if norm is not None:
            return norm
        if vcenter is not None:
            return TwoSlopeNorm(vmin=vmin if vmin is not None else None,
                                vcenter=vcenter,
                                vmax=vmax if vmax is not None else None)
        return None

    # ----------------------------- load & checks -----------------------------
    adata = sc.read_h5ad(file_path)
    if groupby not in adata.obs.columns:
        raise HTTPException(status_code=422, detail=f"'{groupby}' not in adata.obs")

    # gene list or ranked/HVG fallback
    genes_missing, genes_used = [], []
    var_names_ref = adata.raw.var_names if (use_raw and adata.raw is not None and layer is None) else adata.var_names

    var_groups_labels = None
    var_groups_positions = None  # filled if gene_list is dict

    if isinstance(gene_list, dict):
        # gene groups provided
        ordered = []
        labels = []
        positions = []
        start = 0
        for lbl, glist in gene_list.items():
            present = [g for g in glist if g in var_names_ref]
            missing = [g for g in glist if g not in var_names_ref]
            genes_missing.extend(missing)
            if not present:
                continue
            take = present[:max(0, max_genes - len(ordered))]
            if not take:
                break
            ordered.extend(take)
            end = start + len(take) - 1
            positions.append((start, end))
            labels.append(lbl)
            start = end + 1
        genes_used = ordered
        var_groups_labels = labels if labels else None
        var_groups_positions = positions if positions else None
    elif gene_list:
        present = [g for g in gene_list if g in var_names_ref]
        genes_missing = [g for g in gene_list if g not in var_names_ref]
        if not present:
            raise HTTPException(status_code=422, detail="None of the provided genes were found")
        genes_used = present[:max_genes]
        if len(present) > max_genes:
            warnings.warn(f"Gene list truncated to {max_genes} genes")
    else:
        # fallback: rank_genes_groups union or HVGs/variance
        try:
            rgg = adata.uns.get("rank_genes_groups")
            if rgg is None:
                raise KeyError
            candidates = []
            groups = list(pd.Categorical(adata.obs[groupby]).categories)
            for g in groups:
                try:
                    names = rgg["names"][g][:top_n].tolist()
                except Exception:
                    names = rgg["names"][0][:top_n].tolist() if hasattr(rgg["names"], "__getitem__") else []
                for n in names:
                    if n in var_names_ref:
                        candidates.append(n)
            seen = set()
            genes_used = [x for x in candidates if not (x in seen or seen.add(x))]
        except Exception:
            if 'highly_variable' in adata.var.columns:
                genes_used = adata.var.sort_values('highly_variable', ascending=False).index.tolist()
            else:
                Xtmp = adata.raw.X if (use_raw and adata.raw is not None and layer is None) else adata.X
                if _issparse(Xtmp):
                    import numpy as _np
                    mu = _np.asarray(Xtmp.mean(axis=0)).ravel()
                    var = _np.asarray(Xtmp.power(2).mean(axis=0)).ravel() - mu**2
                else:
                    var = Xtmp.var(axis=0)
                order = np.argsort(var)[::-1]
                genes_used = var_names_ref[order].tolist()
        genes_used = genes_used[:max_genes]

    if not genes_used:
        raise HTTPException(status_code=500, detail="Failed to determine genes for heatmap")

    # ----------------------------- build X (cells × genes) -----------------------------
    base = adata.raw if (use_raw and adata.raw is not None and layer is None) else adata
    if layer is not None:
        if layer not in adata.layers:
            raise HTTPException(status_code=422, detail=f"Layer '{layer}' not found in adata.layers")
        X = adata[:, genes_used].layers[layer]
    else:
        X = base[:, genes_used].X
    if _issparse(X):
        X = X.toarray()
    X = X.astype(np.float32, copy=False)

    # clip per gene (skip if clip_percentiles is None)
    if clip_percentiles is not None:
        low_p, high_p = clip_percentiles
        if low_p is not None and high_p is not None:
            for j in range(X.shape[1]):
                lo = np.percentile(X[:, j], low_p)
                hi = np.percentile(X[:, j], high_p)
                if hi > lo:
                    X[:, j] = np.clip(X[:, j], lo, hi)

    # scale
    eps = 1e-8
    print(f"DEBUG - Input parameters: vmin={vmin}, vmax={vmax}, vcenter={vcenter}")
    
    if zscore:
        mu = X.mean(axis=0); sd = X.std(axis=0); sd[sd < eps] = 1.0
        X = (X - mu) / sd
        # Debug: print z-score statistics
        print(f"Z-score debug - Min: {X.min():.3f}, Max: {X.max():.3f}, Mean: {X.mean():.3f}, Std: {X.std():.3f}")
        print(f"Z-score debug - Original data range: {X.min():.3f} to {X.max():.3f}")
        print(f"Z-score debug - Negative values: {(X < 0).sum()}, Positive values: {(X > 0).sum()}")
        
        # Auto-adjust colormap range for z-score normalized data only if not manually set
        if vmin is None and vmax is None:
            # Use symmetric range around 0 for z-score data
            data_max = max(abs(X.min()), abs(X.max()))
            vmin = -data_max
            vmax = data_max
            vcenter = 0.0
            print(f"Z-score debug - Auto-adjusted colormap: vmin={vmin:.3f}, vmax={vmax:.3f}, vcenter={vcenter}")
        elif vmin is None:
            vmin = X.min()
        elif vmax is None:
            vmax = X.max()
        
        # Set vcenter to 0 for z-score data (whether auto or manual vmin/vmax)
        if vcenter is None:
            vcenter = 0.0
            
        print(f"Z-score debug - Final colormap settings: vmin={vmin}, vmax={vmax}, vcenter={vcenter}")
    elif standard_scale in ("gene", "var"):
        gmin = X.min(axis=0); span = np.maximum(X.max(axis=0) - gmin, eps)
        X = (X - gmin) / span
    elif standard_scale in ("obs", "cell"):
        rmin = X.min(axis=1, keepdims=True); span = np.maximum(X.max(axis=1, keepdims=True) - rmin, eps)
        X = (X - rmin) / span

    # column order (genes) via correlation linkage like scanpy
    col_order = np.arange(X.shape[1])
    if cluster_rows and X.shape[1] > 1 and linkage is not None and pdist is not None:
        try:
            d = pdist(X.T, metric='correlation')
            Z = linkage(d, method='average')
            col_order = leaves_list(Z)
        except Exception:
            pass

    # categories & ordering (using dendrogram if requested)
    obs_groups = _ensure_cat(adata.obs[groupby])
    categories = list(obs_groups.cat.categories)

    categories_idx_ordered = list(range(len(categories)))
    categories_ordered = categories

    if dendrogram:
        key = f"dendrogram_{groupby}"
        try:
            if key not in adata.uns or "dendrogram_info" not in adata.uns[key]:
                sc.tl.dendrogram(adata, groupby, key_added=key)
            categories_idx_ordered = list(adata.uns[key]["categories_idx_ordered"])
            categories_ordered = [categories[i] for i in categories_idx_ordered]
        except Exception:
            # fallback: keep as-is
            pass

    # row order: by ordered categories, within each category by PC1 projection
    try:
        Xc = X - X.mean(axis=0, keepdims=True)
        _, _, vt = np.linalg.svd(Xc, full_matrices=False)
        pc1 = vt[0, :]
    except Exception:
        pc1 = np.ones(X.shape[1], dtype=np.float32)

    row_indices = []
    groups_codes = obs_groups.cat.codes.to_numpy()
    for gi in categories_idx_ordered:
        mask = (groups_codes == gi)
        idx = np.where(mask)[0]
        if idx.size == 0:
            continue
        scores = (X[idx][:, col_order] @ pc1[col_order])
        order = np.argsort(scores)  # ascending
        row_indices.extend(idx[order].tolist())
    if len(row_indices) != X.shape[0]:
        row_indices = list(range(X.shape[0]))

    Xp = X[np.array(row_indices)[:, None], col_order]
    genes_plot = [genes_used[i] for i in col_order]
    group_codes_plot = groups_codes[np.array(row_indices)]
    cat_labels = categories  # for mapping index->label
    
    # ----------------------------- layout (scanpy-style gridspec) -----------------------------
    os.makedirs(outdir, exist_ok=True)

    # size: heatmap width ~ genes, height big (cells)
    dpi = 200
    # show_gene_labels default like scanpy: only when <= 50 genes
    if show_gene_labels is None:
        show_gene_labels = len(genes_plot) <= 50

    # choose colormap
    cmap = _theme_cmap()

    # color norm
    norm = _compute_norm(vmin, vmax, vcenter, norm)

    # groupby colors
    try:
        group_colors = _ensure_groupby_colors(adata, groupby)
    except Exception:
        # last-resort simple palette
        base = plt.colormaps.get("tab20")
        group_colors = [mplcolor_to_hex(base(i / max(1, len(categories)-1))) for i in range(len(categories))]

    # Map group codes to 0..K-1 (already true) in the *ordered* sense for labels
    labels_by_code = cat_labels

    # figure geometry inspired by scanpy.pl.heatmap - reduced sizes
    colorbar_width = 0.125
    # track colorbar axes to adjust height to 50% after layout
    cbar_axes = []
    if not swap_axes:
        dendro_width = 0.7 if dendrogram else 0.0  # reduced from 1.0
        groupby_width = 0.18 if len(categories) > 1 else 0.0  # reduced from 0.25
        heatmap_width = max(4.2, min(12.6, 0.21 * len(genes_plot)))  # reduced by 30%
        width = heatmap_width + dendro_width + groupby_width + colorbar_width
        height = max(4.2, min(14.0, 0.00175 * Xp.shape[0] + 2.8))  # reduced by 30%
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        # rows: [brackets(optional), heatmap row]
        height_ratios = (0 if not (var_groups_labels and var_groups_positions) else 0.15, height)
        axs = gridspec.GridSpec(
            nrows=2, ncols=4,
            width_ratios=(groupby_width, heatmap_width, dendro_width, colorbar_width),
            height_ratios=height_ratios,
            wspace=0.15/width, hspace=0.12/height
        )
        # heatmap
        heat_ax = fig.add_subplot(axs[1, 1])
        im = heat_ax.imshow(Xp, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
        heat_ax.set_ylim(Xp.shape[0]-0.5, -0.5)
        heat_ax.set_xlim(-0.5, Xp.shape[1]-0.5)
        heat_ax.grid(False)
        heat_ax.tick_params(axis="y", left=False, labelleft=False)
        if show_gene_labels:
            heat_ax.set_xticks(np.arange(len(genes_plot)))
            heat_ax.set_xticklabels(genes_plot, rotation=90, fontsize="small")
        else:
            heat_ax.tick_params(axis="x", bottom=False, labelbottom=False)
        heat_ax.set_xlabel("Genes")
        # heat_ax.set_title(f"Cell-level expression heatmap ({groupby})", fontsize=12)  # Title removed

        # color blocks on the left
        if groupby_width > 0:
            grp_ax = fig.add_subplot(axs[1, 0], sharey=heat_ax)
            _plot_colorblocks(grp_ax, group_codes_plot, labels_by_code, group_colors, orientation="left")
            # add horizontal lines separating categories based on run-length (order-preserving)
            _codes = np.asarray(group_codes_plot)
            rle_counts = []
            if _codes.size:
                cur = _codes[0]; cnt = 1
                for v in _codes[1:]:
                    if v == cur: cnt += 1
                    else:
                        rle_counts.append(cnt)
                        cur = v; cnt = 1
                rle_counts.append(cnt)
            if rle_counts:
                line_positions = np.cumsum(rle_counts)[:-1] - 0.5
                heat_ax.hlines(line_positions, -0.5, len(genes_plot)-0.5, lw=1.0, color="black", zorder=10, clip_on=False)

        # dendrogram of categories
        if dendrogram and dendro_width > 0:
            dend_ax = fig.add_subplot(axs[1, 2], sharey=heat_ax)
            # plot precomputed dendrogram lines mapped to ticks at centers of category blocks
            # Build ticks (centers)
            vals, counts = np.unique(group_codes_plot, return_counts=True)
            ticks = np.cumsum(counts) - counts/2.0
            # draw simple lines approximating dendrogram using scanpy data
            try:
                dinfo = adata.uns[f"dendrogram_{groupby}"]["dendrogram_info"]
                icoord = np.array(dinfo["icoord"]); dcoord = np.array(dinfo["dcoord"]); leaves = dinfo["ivl"]
                orig_ticks = np.arange(5, len(leaves)*10+5, 10).astype(float)
                # translate positions
                def _translate(xs, new_ticks, old_ticks):
                    new = []
                    old = list(old_ticks)
                    for x in xs:
                        if x in old:
                            new.append(new_ticks[old.index(x)])
                        else:
                            # interpolate
                            i = np.searchsorted(old, x, side="left")
                            i0 = i-1
                            x0, x1 = old[i0], old[i]
                            y0, y1 = new_ticks[i0], new_ticks[i]
                            new.append((x - x0)/(x1 - x0) * (y1 - y0) + y0)
                    return new
                for xs, ys in zip(icoord, dcoord, strict=True):
                    xs_ = _translate(xs, ticks, orig_ticks)
                    dend_ax.plot(ys, xs_, color="#555555")
                dend_ax.set_ylim(heat_ax.get_ylim())
                dend_ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
                for sp in ("right","top","left","bottom"): dend_ax.spines[sp].set_visible(False)
            except Exception:
                dend_ax.axis("off")

        # gene-group brackets on top of heatmap
        if var_groups_labels and var_groups_positions:
            top_ax = fig.add_subplot(axs[0, 1], sharex=heat_ax)
            # positions were defined before column clustering; remap via col_order:
            # build mapping old_idx->new_pos
            # but since we built from `genes_used` after col_order, rebuild positions now:
            if isinstance(gene_list, dict):
                # recompute positions in current genes_plot
                positions = []
                labels = []
                start_idx = 0
                for lbl, glist in gene_list.items():
                    # collect only those present in genes_plot, in that order
                    sel = [g for g in genes_plot if g in set(glist)]
                    if not sel:
                        continue
                    start = min(genes_plot.index(g) for g in sel)
                    end   = max(genes_plot.index(g) for g in sel)
                    positions.append((start, end))
                    labels.append(lbl)
                _plot_var_group_brackets(top_ax, labels, positions, orientation="top")
            else:
                _plot_var_group_brackets(top_ax, var_groups_labels, var_groups_positions, orientation="top")

        # colorbar (vertical) - reduced height significantly
        cax = fig.add_subplot(axs[1, 3])
        from matplotlib.colorbar import Colorbar
        cb = plt.colorbar(im, cax=cax)
        cb.ax.tick_params(labelsize=6)
        cbar_axes.append(cax)

    else:
        # swap_axes case: categories along x, genes along y (with bottom blocks, top dendrogram) - reduced by 30%
        dendro_height = 0.56 if dendrogram else 0.0  # reduced from 0.8
        groupby_height = 0.14 if len(categories) > 1 else 0.0  # reduced from 0.20
        heatmap_height = max(2.8, min(11.2, 0.126 * len(genes_plot)))  # reduced by 30%
        width = max(5.6, min(15.4, 0.00175 * Xp.shape[0] + 7))  # reduced by 30%
        height = heatmap_height + dendro_height + groupby_height
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        axs = gridspec.GridSpec(
            nrows=3, ncols=3,
            height_ratios=(dendro_height, heatmap_height, groupby_height),
            width_ratios=(width-0.25, 0.0, 0.25),
            wspace=0.25/width, hspace=0.28/height
        )
        heat_ax = fig.add_subplot(axs[1, 0])
        im = heat_ax.imshow(Xp.T, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
        heat_ax.set_xlim(0-0.5, Xp.shape[0]-0.5)
        heat_ax.set_ylim(Xp.shape[1]-0.5, -0.5)
        heat_ax.grid(False)
        heat_ax.tick_params(axis="x", bottom=False, labelbottom=False)
        if show_gene_labels:
            heat_ax.set_yticks(np.arange(len(genes_plot)))
            heat_ax.set_yticklabels(genes_plot, fontsize="small")
        else:
            heat_ax.tick_params(axis="y", left=False, labelleft=False)
        heat_ax.set_ylabel("Genes")
        # heat_ax.set_title(f"Cell-level expression heatmap ({groupby})", fontsize=12)  # Title removed

        # bottom color blocks
        if groupby_height > 0:
            grp_ax = fig.add_subplot(axs[2, 0], sharex=heat_ax)
            _plot_colorblocks(grp_ax, group_codes_plot, labels_by_code, group_colors, orientation="bottom")
            # vertical lines between categories based on run-length (order-preserving)
            _codes = np.asarray(group_codes_plot)
            rle_counts = []
            if _codes.size:
                cur = _codes[0]; cnt = 1
                for v in _codes[1:]:
                    if v == cur: cnt += 1
                    else:
                        rle_counts.append(cnt)
                        cur = v; cnt = 1
                rle_counts.append(cnt)
            if rle_counts:
                line_positions = np.cumsum(rle_counts)[:-1] - 0.5
                heat_ax.vlines(line_positions, -0.5, len(genes_plot)-0.5, lw=1.0, color="black", zorder=10, clip_on=False)

        # top dendrogram
        if dendrogram and dendro_height > 0:
            dend_ax = fig.add_subplot(axs[0, 0], sharex=heat_ax)
            try:
                dinfo = adata.uns[f"dendrogram_{groupby}"]["dendrogram_info"]
                icoord = np.array(dinfo["icoord"]); dcoord = np.array(dinfo["dcoord"]); leaves = dinfo["ivl"]
                orig_ticks = np.arange(5, len(leaves)*10+5, 10).astype(float)
                vals, counts = np.unique(group_codes_plot, return_counts=True)
                ticks = np.cumsum(counts) - counts/2.0
                def _translate(xs, new_ticks, old_ticks):
                    new = []
                    old = list(old_ticks)
                    for x in xs:
                        if x in old:
                            new.append(new_ticks[old.index(x)])
                        else:
                            i = np.searchsorted(old, x, side="left")
                            i0 = i-1
                            x0, x1 = old[i0], old[i]
                            y0, y1 = new_ticks[i0], new_ticks[i]
                            new.append((x - x0)/(x1 - x0) * (y1 - y0) + y0)
                    return new
                for xs, ys in zip(icoord, dcoord, strict=True):
                    xs_ = _translate(xs, ticks, orig_ticks)
                    dend_ax.plot(xs_, ys, color="#555555")
                dend_ax.set_xlim(0, Xp.shape[0])
                dend_ax.tick_params(bottom=False, labelbottom=False, left=False, labelleft=False)
                for sp in ("right","top","left","bottom"): dend_ax.spines[sp].set_visible(False)
            except Exception:
                dend_ax.axis("off")

        # right colorbar (vertical) - reduced height significantly
        cax = fig.add_subplot(axs[1, 2])
        cb = plt.colorbar(im, cax=cax)
        cb.ax.tick_params(labelsize=6)
        cbar_axes.append(cax)

        # optional gene-group brackets at right are omitted in swap_axes for brevity

    # finalize & save
    plt.tight_layout()
    # After tight_layout, reduce colorbar height to 50% and center alongside heatmap
    try:
        for ax_cbar in cbar_axes:
            pos = ax_cbar.get_position()
            new_h = pos.height * 0.5
            new_y = pos.y0 + (pos.height - new_h) / 2.0
            ax_cbar.set_position([pos.x0, new_y, pos.width, new_h])
    except Exception:
        pass
    out_path = os.path.join(outdir, output_filename)
    fig.savefig(out_path, bbox_inches="tight", dpi=dpi)
    plt.close(fig)

    return {
        "path": out_path,
        "genes_used": genes_used,
        "genes_missing": genes_missing,
        "categories_order": categories_ordered,
    }

# Keep the old function name for backward compatibility
def generate_cell_heatmap(
    file_path: str,
    outdir: str,
    groupby: str = "leiden",
    gene_list=None,
    top_n: int = 10,
    zscore: bool = True,
    standard_scale: str = "none",
    clip_percentiles=(1.0, 99.0),
    cluster_rows: bool = True,
    cluster_cols: bool = False,
    layer=None,
    use_raw: bool = False,
    max_genes: int = 100,
    output_filename: str = "cell_heatmap.png",
):
    """
    Backward compatibility wrapper for the old function signature.
    Calls the new scanpy-style function with compatible parameters.
    """
    # Convert old standard_scale values to new format
    if standard_scale == "gene":
        new_standard_scale = "var"
    elif standard_scale == "none":
        new_standard_scale = None
    else:
        new_standard_scale = standard_scale
    
    return generate_cell_heatmap_scanpy_style(
        file_path=file_path,
        outdir=outdir,
        groupby=groupby,
        gene_list=gene_list,
        top_n=top_n,
        zscore=zscore,
        standard_scale=new_standard_scale,
        clip_percentiles=clip_percentiles,
        cluster_rows=cluster_rows,
        cluster_cols=cluster_cols,
        layer=layer,
        use_raw=use_raw,
        max_genes=max_genes,
        output_filename=output_filename,
    )

def genes_visualization(file_path,save_path,dim_red,gene_list):
    adata = sc.read_h5ad(file_path)
    genes_vis_plots_path = []
    for gene in gene_list:
        gene_expression = adata[:, gene].X.toarray()  
        adata.obs[gene] = gene_expression.ravel() 
        if dim_red =="X_umap":
            template_plot = plot_umap_and_obs(umap_coords=adata.obsm[dim_red],fig_name=f"{dim_red}_{gene}",color_column=gene,title=f"{gene}",data_df=adata.obs,save_path=save_path)
            genes_vis_plots_path.append(template_plot)
        else:
            template_plot = plot_pca_and_obs(pca_coords=adata.obsm[dim_red],fig_name=f"{dim_red}_{gene}",color_column=gene,title=f"{gene}",data_df=adata.obs,save_path=save_path,output_format="svg")
            genes_vis_plots_path.append(template_plot)       
    return genes_vis_plots_path

def var_visualization(file_path, save_path, dim_red, var_keys):
    """
    Create UMAP / PCA plots colored by multiple adata.var columns.
    Returns a list with the relative paths just like genes_visualization.
    """
    adata = sc.read_h5ad(file_path)
    var_vis_plots_path = []
    
    for var_key in var_keys:
        if var_key not in adata.var.columns:
            raise ValueError(f"{var_key} not in adata.var")

        if dim_red == "X_umap":
            plot_path = plot_umap_and_obs(
                umap_coords=adata.obsm[dim_red],
                fig_name=f"{dim_red}_{var_key}",
                color_column=var_key,
                title=var_key,
                data_df=adata.var,           # note: we pass .var for coloring
                save_path=save_path,
            )
        else:
            plot_path = plot_pca_and_obs(
                pca_coords=adata.obsm[dim_red],
                fig_name=f"{dim_red}_{var_key}",
                color_column=var_key,
                title=var_key,
                data_df=adata.var,
                save_path=save_path,
            )
        var_vis_plots_path.append(plot_path)

    return var_vis_plots_path

def obs_visualization(file_path, save_path, dim_red, obs_keys):
    """
    Create UMAP / PCA plots colored by multiple adata.obs columns.
    Returns a list with the relative paths just like genes_visualization.
    """
    adata = sc.read_h5ad(file_path)
    obs_vis_plots_path = []
    
    for obs_key in obs_keys:
        if obs_key not in adata.obs.columns:
            raise ValueError(f"{obs_key} not in adata.obs")

        if dim_red == "X_umap":
            plot_path = plot_umap_and_obs(
                umap_coords=adata.obsm[dim_red],
                fig_name=f"{dim_red}_{obs_key}",
                color_column=obs_key,
                title=obs_key,
                data_df=adata.obs,           # note: we pass .obs for coloring
                save_path=save_path,
            )
        else:
            plot_path = plot_pca_and_obs(
                pca_coords=adata.obsm[dim_red],
                fig_name=f"{dim_red}_{obs_key}",
                color_column=obs_key,
                title=obs_key,
                data_df=adata.obs,
                save_path=save_path,
            )
        obs_vis_plots_path.append(plot_path)

    return obs_vis_plots_path


def perform_batch_correction(file_path,save_path, batch_correction_method, unique_id, preprocess):
    adata_concat = sc.read_h5ad(file_path)
    if preprocess:
        sc.pp.normalize_per_cell(adata_concat, counts_per_cell_after=1e4)
        sc.pp.log1p(adata_concat)
        sc.pp.highly_variable_genes(adata_concat, n_top_genes=2000)
        # sc.pp.regress_out(adata_concat, ['total_counts', 'pct_counts_mt'])
        sc.pp.scale(adata_concat, max_value=10)
        sc.tl.pca(adata_concat, svd_solver='arpack')

    if batch_correction_method == 'combat':
        try:
            print("inside combat")
            sc.pp.combat(adata_concat, key='batch')
            sc.pp.neighbors(adata_concat,use_rep="X_pca")
            sc.tl.umap(adata_concat)
            sc.tl.leiden(adata_concat,resolution=0.5)
            sc.pl.umap(adata_concat,color=["leiden"])
            plot_umap_batch_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="combat_integration_umap_batch",color_column="batch",title="Combat Integration",data_df=adata_concat.obs,save_path=save_path)
            plot_umap_leiden_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="combat_integration_umap_leiden",color_column="leiden",title="Leiden Clusters",data_df=adata_concat.obs,save_path=save_path)
            integration_plots = [plot_umap_batch_path,plot_umap_leiden_path]
        except Exception as e:
            print(f"Error with combat: {e}")
    elif batch_correction_method == 'scanorama':
        sc.external.pp.scanorama_integrate(adata_concat, key='batch')
        sc.pp.neighbors(adata_concat,use_rep="X_scanorama")
        sc.tl.umap(adata_concat)
        sc.tl.leiden(adata_concat,resolution=0.5)
        sc.pl.umap(adata_concat,color=["leiden"])
        plot_umap_batch_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="scanorama_integration_umap_batch",color_column="batch",title="Scanorama Integration",data_df=adata_concat.obs,save_path=save_path)
        plot_umap_leiden_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="scanorama_integration_umap_leiden",color_column="leiden",title="Combat Integration",data_df=adata_concat.obs,save_path=save_path)
        integration_plots = [plot_umap_batch_path,plot_umap_leiden_path]
        
    elif batch_correction_method == 'bbknn':
        sc.external.pp.bbknn(adata_concat, batch_key='batch')
        sc.pp.neighbors(adata_concat,use_rep="X_pca")
        sc.tl.umap(adata_concat)
        sc.tl.leiden(adata_concat,resolution=0.5)
        sc.pl.umap(adata_concat,color=["leiden"])
        plot_umap_batch_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="bbknn_integration_umap_batch",color_column="batch",title="BBKNN Integration",data_df=adata_concat.obs,save_path=save_path)
        plot_umap_leiden_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="bbknn_integration_umap_leiden",color_column="leiden",title="Leiden Clusters",data_df=adata_concat.obs,save_path=save_path)
        integration_plots = [plot_umap_batch_path,plot_umap_leiden_path]

    elif batch_correction_method == 'harmony':
        sc.external.pp.harmony_integrate(adata_concat, key='batch')
        sc.pp.neighbors(adata_concat,use_rep="X_pca_harmony")
        sc.tl.umap(adata_concat)
        sc.tl.leiden(adata_concat,resolution=0.5)
        plot_umap_batch_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="harmony_integration_umap_batch",title="Harmony Integration",color_column="batch",data_df=adata_concat.obs,save_path=save_path)
        plot_umap_leiden_path = plot_umap_and_obs(umap_coords=adata_concat.obsm["X_umap"],fig_name="harmony_integration_umap_leiden",title="Leiden Clusters",color_column="leiden",data_df=adata_concat.obs,save_path=save_path)
        integration_plots = [plot_umap_batch_path,plot_umap_leiden_path]
    else:
        raise HTTPException(status_code=400, detail="Invalid batch correction method")
    
    adata_concat.write_h5ad(os.path.join(save_path, f"{unique_id}.h5ad"))
    
    return integration_plots
    
def dea(file_path,save_path,n_genes,flavor,gene_list,method,root_path,unique_id):
    # Clean up any previous DEA CSV results before starting new analysis
    cleanup_previous_dea_results(unique_id)
    
    adata = sc.read_h5ad(file_path)
    sc.tl.dendrogram(adata,groupby="leiden")
    sc.tl.rank_genes_groups(adata,groupby="leiden", method=method)
    adata.obs.to_csv(f"{root_path}/{unique_id}/{unique_id}_obs.csv")
    adata.var.to_csv(f"{root_path}/{unique_id}/{unique_id}_var.csv")
    save_rank_genes_groups(uuid=unique_id,adata=adata)
    adata = adata.raw.to_adata()
    if isinstance(gene_list, list) and len(gene_list) > 0:        
        if flavor == "mean_expression":##FIX LATER
            plot_mean_expression_list = plotly_dotplot_unified(adata,save_path,"mean_expression_list",n_genes,gene_list=gene_list,group_by="leiden",flavor="mean_expression")
            plot_fold_change_list = plotly_dotplot_unified(adata,save_path,"fold_change_list",n_genes,gene_list=gene_list,group_by="leiden",flavor="fold_change")
            plot_mean_expression = plotly_dotplot_unified(adata,save_path,"mean_expression",n_genes,group_by="leiden",flavor="mean_expression")
            plot_fold_change_expression = plotly_dotplot_unified(adata,save_path,"fold_change",n_genes,group_by="leiden",flavor="fold_change")
            dea_plots = [plot_mean_expression_list,plot_fold_change_list,plot_mean_expression,plot_fold_change_expression]
            return dea_plots
        else:
            plot_fold_change_expression_list = plotly_dotplot_unified(adata,save_path,"fold_change_list",n_genes,gene_list=gene_list,group_by="leiden",flavor="fold_change")
            plot_fold_change_list = plotly_dotplot_unified(adata,save_path,"fold_change_list",n_genes,gene_list=gene_list,group_by="leiden",flavor="fold_change")
            plot_mean_expression = plotly_dotplot_unified(adata,save_path,"mean_expression",n_genes,group_by="leiden",flavor="mean_expression")
            plot_fold_change_expression = plotly_dotplot_unified(adata,save_path,"fold_change",n_genes,group_by="leiden",flavor="fold_change")
            dea_plots = [plot_fold_change_expression_list,plot_fold_change_list,plot_mean_expression_list,plot_mean_expression,plot_fold_change_expression]
            return dea_plots 
    else:
        plot_mean_expression = plotly_dotplot_unified(adata,save_path,"mean_expression",n_genes,group_by="leiden",flavor="mean_expression")
        plot_fold_change_expression = plotly_dotplot_unified(adata,save_path,"fold_change",n_genes,group_by="leiden",flavor="fold_change")
        dea_plots = [plot_mean_expression,plot_fold_change_expression]
        return dea_plots
    
def var_names_adata(file_path):
    adata = sc.read_h5ad(file_path)
    gene_list = adata.var.index.tolist()
    return gene_list

def fetch_analysis_results(adata):
    n_clusters = len(adata.obs['leiden'].unique())
    n_cells = adata.n_obs
    n_genes = adata.n_vars
    return {
        "clusters": n_clusters,
        "cells_number": n_cells,
        "genes_number":n_genes
    }

def plot_elbow(adata,save_path,fig_name):
    """
    Plot elbow plot for PCA variance ratio to identify optimal number of components.
    Adapted from user template to work with theme system while preserving preferred styling.
    """
    # Get plot-specific theme configuration
    elbow_config = get_plot_theme_config("elbow_plots")
    
    variance_ratio = adata.uns["pca"]["variance_ratio"].tolist()
    log_variance_ratio = np.log(variance_ratio[:25])
    percentage_change = np.diff(log_variance_ratio) / log_variance_ratio[:-1] * 100
    pca_labels = ['PCA_{}'.format(i+1) for i in range(len(log_variance_ratio))]
    
    # Use DarkGreen as base color (from your template) but allow theme override
    base_color = elbow_config.get("base_color", "DarkGreen")
    highlight_color = elbow_config.get("highlight_color", "red")
    colors = [base_color] * len(log_variance_ratio)
    
    found = False
    for i, change in enumerate(percentage_change, start=1):
        if abs(change) < 1 and not found:
            colors[i] = highlight_color
            found = True
            break  

    trace = go.Scatter(
        x=list(range(1, len(log_variance_ratio) + 1)),
        y=log_variance_ratio,
        mode='markers',  # Keep markers only as in your template
        marker=dict(
            color=colors,  
            size=elbow_config.get("marker_size", 15)  # Use your preferred size of 15
        ),
        hoverinfo='text',  
        hovertext=pca_labels  
    )

    text_annotations = [
        go.layout.Annotation(
            x=xi,
            y=yi,
            text=text,
            showarrow=False,
            xanchor='center',
            yanchor='bottom',
            textangle=-90,
            font=dict(
                size=9 
            ),
            yshift=10  
        )
        for xi, yi, text in zip(range(1, len(log_variance_ratio) + 1), log_variance_ratio, pca_labels)
    ]

    layout = go.Layout(
        xaxis=dict(
            title='Ranking',
            showline=True,
            linewidth=1,
            linecolor=elbow_config.get("axis_color", "black"),
            mirror=False
        ),
        yaxis=dict(
            title='Log of Variance Ratio',
            showline=True,
            linewidth=1,
            linecolor=elbow_config.get("axis_color", "black"),
            mirror=False
        ),
        annotations=text_annotations,
        paper_bgcolor=elbow_config.get("background_color", "white"), 
        plot_bgcolor=elbow_config.get("background_color", "white"),
        width=550,  # Keep your preferred dimensions
        height=400     
    )

    fig = go.Figure(data=[trace], layout=layout)
    file_path = plot(fig, filename=f"{save_path}/{fig_name}.html", auto_open=False)
    return file_path

def plot_density_contour(adata, save_path=None, fig_name="density_contour", 
                         template=None, 
                         x_hist_color=None, 
                         y_hist_color=None, 
                         contour_line_color=None):
    """
    Generate a density contour plot using Plotly with plot-specific theme system.
    Now uses the plot-specific theme system for consistent styling.
    
    Parameters:
    - adata: the data to plot
    - save_path: Path to save the plot (optional)
    - fig_name: Name for the saved plot file
    - template: string for the plotly template (deprecated, uses theme system now)
    - x_hist_color: color for the x-axis histogram (deprecated, uses theme system now)
    - y_hist_color: color for the y-axis histogram (deprecated, uses theme system now)
    - contour_line_color: color for the contour lines (deprecated, uses theme system now)
    
    Returns:
    - file_path if save_path provided, otherwise displays the plot
    """
    # Get plot-specific theme configuration
    density_config = get_plot_theme_config("density_plots")
    
    fig = px.density_contour(adata.obs, 
                             x="log1p_total_counts", 
                             y="log1p_n_genes_by_counts", 
                             marginal_x="histogram", 
                             marginal_y="histogram", 
                             template=density_config.get("template", "plotly_white"))

    # Use theme colors for histograms
    if len(fig.data) >= 2:
        fig.data[-2]['marker']['color'] = density_config.get("background_color", "#1f77b4")  # x-axis histogram
        fig.data[-1]['marker']['color'] = density_config.get("background_color", "#1f77b4")  # y-axis histogram

    # Update contour colors with theme
    for data in fig.data:
        if data['type'] == 'contour':
            data['line']['color'] = density_config.get("contour_color", "#333333")
            data['line']['width'] = 0.5

    # Apply plot-specific theme
    fig = apply_theme_to_figure(fig, plot_type="density_plots")
    
    # Override specific settings for density plots
    fig.update_layout(
        xaxis_title='log(1 + Total counts)',
        yaxis_title='log(1 + N° Genes by counts)',
        title="Density Contour Plot - Gene Counts vs Total Counts"
    )

    if save_path:
        output_format = "png" if len(adata.obs) > 15000 else "html"
        file_path = f"{save_path}/{fig_name}.{output_format}"
        if output_format == "html":
            pio.write_html(fig, file=file_path, auto_open=False)
        else:
            fig.write_image(file_path, scale=10)
        return file_path
    else:
        fig.show()

def plot_violin(adata, save_path, template=None, features=['n_genes_by_counts', 'total_counts', 'pct_counts_mito'], y_labels=["N° genes by counts", "Total counts", f"% of Mitochondrial Genes"]):
    """
    Plot violin plots for the specified features using Plotly and save them as HTML files.
    Now uses the theme system for consistent styling.
    
    Parameters:
    - adata: Data object, usually from anndata library.
    - save_path: Path where to save the HTML plots.
    - template: Plotly template for styling the plot (deprecated, uses theme system now).
    - features: List of features (columns) in adata.obs to plot.
    - y_labels: List of y-axis labels corresponding to each feature.
    
    Note:
    - Ensure that the length of 'features' and 'y_labels' are the same.
    """
    paths_plots = []
    
    # Get plot-specific theme configuration
    violin_config = get_plot_theme_config("violin_plots")
    
    output_format = "png" if len(adata.obs) > 15000 else "html"

    # Iterate through each feature and its corresponding y-axis label
    for idx, (feature, y_label) in enumerate(zip(features, y_labels)):
        # Use plot-specific theme colors
        colors = violin_config.get("colors", ["#1f77b4", "#ff7f0e", "#2ca02c"])
        color = colors[idx % len(colors)]
        
        # Create violin plot for the current feature
        fig = px.violin(
            adata.obs, 
            y=feature, 
            box=True, 
            points="all", 
            template=violin_config.get("template", "plotly_white"),
            color_discrete_sequence=[color]
        )
        
        # Apply plot-specific theme to the figure
        fig = apply_theme_to_figure(fig, plot_type="violin_plots")
        
        # Apply violin-specific opacity and line width from theme config
        opacity = violin_config.get("opacity", 0.7)
        line_width = violin_config.get("line_width", 2)
        
        # Update violin traces with theme-specific settings
        fig.update_traces(
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, {opacity})",
            line=dict(width=line_width, color=color),
            box_fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, {opacity * 0.8})"
        )
        
        # Override specific settings for violin plots
        fig.update_layout(
            width=violin_config.get("width", 800) // 3,  # Make violin plots smaller
            height=400,
            yaxis_title=y_label,
            showlegend=False,
            margin=dict(l=80, r=20, b=40, t=20)
        )
        
        # Save the plot as an HTML file
        file_path = f"{save_path}/{feature}_violin.{output_format}"
        if output_format == "html":
            plot(fig, filename=file_path, auto_open=False)
        else:
            fig.write_image(file_path, scale=10)  # High definition PNG
        paths_plots.append(file_path)

    return paths_plots

def plot_scatter(adata,save_path,fig_name, x, y, template=None,x_label=None,y_label=None,color=None,color_index=None):
    """
    Plot scatter plots based on provided x and y columns from adata.obs.
    Now uses the plot-specific theme system for consistent styling.
    
    Parameters:
    - adata: Data object, usually from anndata library.
    - x: Column name in adata.obs for x-axis.
    - y: List of column names in adata.obs for y-axis.
    - template: Plotly template for styling the plot (deprecated, uses theme system now).
    - x_label: Custom label for x-axis.
    - y_label: Custom label for y-axis.
    - color: Custom color for markers (deprecated, uses theme system now).
    """
    # Get plot-specific theme configuration
    scatter_config = get_plot_theme_config("scatter_plots")
    
    output_format = "png" if len(adata.obs) > 15000 else "html"

    for idx, y_col in enumerate(y):
        # Use different colors from the theme palette for each scatter plot
        theme_colors = scatter_config.get("colors", ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"])
        # Use color_index if provided, otherwise use idx
        color_idx = color_index if color_index is not None else idx
        marker_color = theme_colors[color_idx % len(theme_colors)]
            
        fig = go.Figure(data=go.Scatter(x=adata.obs[x], 
                                        y=adata.obs[y_col],
                                        mode='markers',
                                        marker=dict(
                                            color=marker_color,
                                            size=scatter_config.get("marker_size", 4),
                                            opacity=scatter_config.get("opacity", 0.6)
                                        )))
        
        # Apply plot-specific theme
        fig = apply_theme_to_figure(fig, plot_type="scatter_plots")
        
        # Override specific settings for scatter plots
        fig.update_layout(
            xaxis_title=x if x_label is None else x_label,
            yaxis_title=y_col if y_label is None else y_label,
            width=360,  # Better width for scatter plots
            height=350, # Better height for scatter plots
            showlegend=False,
            margin=dict(l=60, r=60, b=40, t=40)  
        )
        
        file_path = f"{save_path}/{fig_name}.{output_format}"
        if output_format == "html":
            plot(fig, filename=file_path, auto_open=False)
        else:
            fig.write_image(file_path, scale=10)  # High definition PNG
    return file_path        

def highest_expr_genes_plotly(
    adata,
    n_top=30,
    gene_symbols=None,
    log=False,
    template="white",
    **kwargs
):
    """
    Display the highest expressed genes in a dataset using a box plot.

    Parameters:
    ----------
    - adata: An AnnData object containing expression data.
    - n_top: Number of top genes to display.
    - gene_symbols: Column name in adata.var that stores gene symbols.
    - log: Boolean indicating whether y-axis should be log-scaled.
    - template: Style template for the plot. Either "white" or "dark".
    - **kwargs: Additional keyword arguments passed to the box plot.

    Returns:
    --------
    A Plotly figure object.
    """

    # Define a color palette for the box plots
    colors = [
        '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', 
        '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', 
        '#ccebc5', '#ffed6f', '#1f78b4', '#33a02c', '#e31a1c'
    ]

    # Normalize the expression data to compute the percentage of each gene per cell
    norm_dict = preprocessing.normalize_total(adata, target_sum=100, inplace=False)

    # Determine the genes with the highest mean expression
    if issparse(norm_dict['X']):
        mean_percent = norm_dict['X'].mean(axis=0).A1
        top_idx = np.argsort(mean_percent)[::-1][:n_top]
        counts_top_genes = norm_dict['X'][:, top_idx].A
    else:
        mean_percent = norm_dict['X'].mean(axis=0)
        top_idx = np.argsort(mean_percent)[::-1][:n_top]
        counts_top_genes = norm_dict['X'][:, top_idx]
    
    # Extract the names of the top genes, using gene symbols if provided
    columns = (
        adata.var_names[top_idx]
        if gene_symbols is None
        else adata.var[gene_symbols][top_idx]
    )
    counts_top_genes = pd.DataFrame(
        counts_top_genes, index=adata.obs_names, columns=columns
    )

    # Initialize a Plotly figure
    fig = go.Figure()

    # Add each gene as a separate trace (box plot) to the figure
    for idx, col in enumerate(counts_top_genes.columns):
        fig.add_trace(go.Box(x=counts_top_genes[col], 
                              name=col, 
                              boxpoints='outliers', 
                              marker_color=colors[idx % len(colors)],
                              hovertemplate='<b>Gene: %{fullData.name}</b><br>' +
                                           'Expression: %{x}<br>' +
                                           '<extra></extra>',
                              **kwargs))

    # Set the template based on the input
    plot_template = "plotly_white" if template == "white" else "plotly_dark"

    # Set the layout and styling details for the figure
    fig.update_layout(
        xaxis_title="% of total counts",
        xaxis=dict(categoryorder='total descending'),
        height=600,
        width=550,
        paper_bgcolor='white' if template == "white" else 'black',
        plot_bgcolor='white' if template == "white" else 'black',
        template=plot_template,
        showlegend=False,
        margin=dict(l=60, r=60, b=40, t=40)  # Padding: left, right, bottom, top
    )

    # If log scale is requested for the y-axis, apply it
    if log:
        fig.update_layout(yaxis_type="log")

    return fig


        
def prepare_data(adata, cell_types, n_genes, gene_list, group_by, flavor, min_logfc=1):
    """
    Prepare gene expression data for plotting. 

    This function processes the AnnData object to extract the mean expression 
    and fraction of cells expressing specific genes, either provided through 
    a gene list or by identifying top expressed genes.

    Parameters:
    ----------
    adata : AnnData
        An object containing gene expression data and potentially 
        differential expression results.
        
    cell_types : list
        List of cell types to consider.
        
    n_genes : int
        Number of top genes to consider if gene_list is not provided.
        
    gene_list : list, optional
        List of specific genes to consider. If provided, n_genes is ignored.
        
    group_by : str
        Column name in adata.obs that contains cell type information.
        
    flavor : str
        Specifies the method for obtaining gene values. Should be one of 
        'mean_expression' or 'fold_change'. If 'mean_expression', the function 
        will retrieve the mean expression of each gene. If 'fold_change', 
        the function will fetch the fold change value from differential 
        expression results stored in adata.uns.
        
    min_logfc : float, optional
        Minimum log fold change to consider when selecting genes based 
        on fold change. Only used if flavor is 'fold_change'.

    Returns:
    -------
    tuple
        A tuple containing three arrays:
        - Mean expression data across cell types for selected genes.
        - Fraction of cells expressing each gene across cell types.
        - List of all genes considered.
    """
    data = []
    fraction_expressing_data = []
    all_genes = []
    
    if gene_list is not None:  # If gene_list is provided, collect data once for each gene in gene_list
        selected_genes = gene_list
        all_genes.extend(selected_genes)
        
        for gene in selected_genes:
            values = []
            fraction_values = []
            
            for ct in cell_types:
                subset = adata[adata.obs[group_by] == ct]
                
                if flavor == "mean_expression":
                    value = subset[:, gene].X.mean()
                elif flavor == "fold_change":
                    value = adata.uns["rank_genes_groups"]["logfoldchanges"][ct][
                        np.where(adata.uns["rank_genes_groups"]["names"][ct] == gene)
                    ][0]
                else:
                    raise ValueError("Invalid flavor. Choose 'mean_expression' or 'fold_change'.")
                
                fraction_value = np.sum(subset[:, gene].X > 0) / subset.shape[0]
                
                values.append(value)
                fraction_values.append(fraction_value)
            
            data.append(values)
            fraction_expressing_data.append(fraction_values)
    
    else:  # Original logic when gene_list is not provided
        for cell_type in cell_types:
            top_genes = adata.uns["rank_genes_groups"]["names"][cell_type][:n_genes * 2].tolist()  # Taking 2x to have a buffer
            selected_genes = []
            
            for gene in top_genes:
                if len(selected_genes) >= n_genes:
                    break  # Stop if we already have enough genes
                
                if flavor == "fold_change":
                    logfc_value = adata.uns["rank_genes_groups"]["logfoldchanges"][cell_type][
                        np.where(adata.uns["rank_genes_groups"]["names"][cell_type] == gene)
                    ][0]
                    
                    if logfc_value >= min_logfc:
                        selected_genes.append(gene)
                else:
                    selected_genes.append(gene)
            
            # Check if we have enough genes; if not, fill with top genes irrespective of fold change
            remaining_genes_needed = n_genes - len(selected_genes)
            for gene in top_genes:
                if gene not in selected_genes:
                    selected_genes.append(gene)
                    remaining_genes_needed -= 1
                
                if remaining_genes_needed <= 0:
                    break
            
            all_genes.extend(selected_genes)
            
            for gene in selected_genes:
                values = []
                fraction_values = []
                
                for ct in cell_types:
                    subset = adata[adata.obs[group_by] == ct]
                    
                    if flavor == "mean_expression":
                        value = subset[:, gene].X.mean()
                    elif flavor == "fold_change":
                        value = adata.uns["rank_genes_groups"]["logfoldchanges"][ct][
                            np.where(adata.uns["rank_genes_groups"]["names"][ct] == gene)
                        ][0]
                    else:
                        raise ValueError("Invalid flavor. Choose 'mean_expression' or 'fold_change'.")
                    
                    fraction_value = np.sum(subset[:, gene].X > 0) / subset.shape[0]
                    
                    values.append(value)
                    fraction_values.append(fraction_value)
                
                data.append(values)
                fraction_expressing_data.append(fraction_values)
    
    return np.array(data), np.array(fraction_expressing_data), all_genes

def add_annotations(fig, cell_types, font_family, n_genes, gene_list=None):
    """
    Annotate the Plotly figure with cell type labels and horizontal bars.

    This function adds text annotations to the figure, representing the cell types. 
    If a gene list is not provided, it also adds horizontal bars with cell type 
    labels above the dot plot, providing a visual summary of the number of top genes 
    for each cell type.

    Parameters:
    ----------
    fig : plotly.graph_objects.Figure
        The Plotly figure to which the annotations will be added.

    cell_types : list
        List of cell types to annotate.

    font_family : str
        Font family to use for the text annotations.

    n_genes : int
        Number of top genes considered. Used to determine the length of the horizontal bars.

    gene_list : list, optional
        List of specific genes considered. If provided, horizontal bars are not added.

    Returns:
    -------
    None
    """
    # Initialize variables for bar plotting
    # We no longer draw y-axis labels via annotations (use real ticks instead)
    bar_y_start = len(cell_types) + 0.1  # The y-position where the bars will start
    bar_x_start = 0  # The x-position where the first bar will start

    if gene_list is None:

        # Add the horizontal bars and vertical lines on top of the scatter plot
        for j, cell_type in enumerate(cell_types):
            bar_x_end = bar_x_start + n_genes - 1  # The x-position where the bar will end
            mid_x = (bar_x_start + bar_x_end) / 2  # Midpoint for text positioning

            # Add the horizontal bar
            fig.add_trace(
                go.Scatter(
                    x=[bar_x_start, bar_x_end],
                    y=[bar_y_start, bar_y_start],
                    mode='lines',
                    line=dict(color="black", width=1),
                    hoverinfo='none'
                ),
                row=1, col=1
            )

            # Add the cell type text at the midpoint of the bar with -45° rotation.
            # Place the annotation INSIDE the y-axis range to avoid any top clipping,
            # using axis coordinates rather than paper coordinates.
            fig.add_annotation(
                x=mid_x,
                y=bar_y_start + 0.5,  # slightly above the bar, within axis range
                text=cell_type,
                showarrow=False,
                textangle=-45,
                font=dict(family=font_family, color="black"),
                xref="x",
                yref="y",  # inside axis -> won't be cut by figure/container
                xanchor="center",
                yanchor="bottom"
            )

            # Add vertical lines (square brackets)
            for x_pos in [bar_x_start, bar_x_end]:
                fig.add_trace(
                    go.Scatter(
                        x=[x_pos, x_pos],
                        y=[bar_y_start - 0.2, bar_y_start + 0.02],
                        mode='lines',
                        line=dict(color="black", width=1),
                        hoverinfo='none'
                    ),
                    row=1, col=1
                )

            bar_x_start = bar_x_end + 1

    # Axis title is now handled via yaxis.title, not a manual annotation
    fig.update_xaxes(fixedrange=True, domain=[0, 0.99], row=1, col=1)
    # Expand the top of the axis range a bit more to fully accommodate
    # the rotated labels drawn just above the bar line
    fig.update_yaxes(fixedrange=True, range=[-1, bar_y_start + 1.5], row=1, col=1)
    fig.update_xaxes(fixedrange=True, domain=[0.95, 0.985], row=1, col=2)
    fig.update_yaxes(fixedrange=True, range=[-5, 105], row=1, col=2)

def set_plot_layout(fig, all_genes, cell_types, font_family, base_height, base_width, scaling_factor):
    """
    Configure the layout and style of a Plotly dot plot figure.

    This function sets the appearance and layout of the figure, such as axis titles, 
    tick values, figure dimensions, and font styling. 
    """
    # Ajuste dinámico de la altura según número de tipos celulares
    base_height = max(base_height, 24 * max(1, len(cell_types)))
    adjusted_width = int(base_width * scaling_factor)

    config = {
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': 'custom_image',
            'height': base_height,
            'width': adjusted_width,
            'scale': 1
        }
    }

    fig.update_layout(
        xaxis1=dict(
            tickvals=list(range(len(all_genes))),
            ticktext=all_genes,
            title="Genes",
            showgrid=False,
            zeroline=False,
            tickangle=270
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=True,
            tickmode='array',
            tickvals=list(range(len(cell_types))),
            ticktext=cell_types,
            automargin=True,  # deja que Plotly ajuste automáticamente
            ticklabelposition="outside left",  # asegura etiquetas a la izquierda
            title=dict(text="Cell Types")
        ),
        yaxis2=dict(showticklabels=False, showgrid=False, zeroline=False),
        xaxis2=dict(showticklabels=False, showgrid=False, zeroline=False),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        # Increase top margin to prevent cropped labels at the top
        margin=dict(l=70, r=30, t=120, b=50),  # controla espacio entre etiquetas y plot
        font=dict(family=font_family, color="black"),
        width=adjusted_width,
        height=base_height+100
    )

    # Ajuste fino de separación entre título del eje y etiquetas
    fig.update_yaxes(title_standoff=1, row=1, col=1, automargin=True)

    return config


def add_scatter_plot(fig, mean_expression_data, fraction_expressing_data, all_genes, cell_types, colorscale, max_size, flavor):
    """
    Add a scatter plot representation of gene expression data to a Plotly figure.

    This function generates and adds to the figure a scatter plot showing gene 
    expression across cell types. The size of each point represents the fraction 
    of cells expressing the gene, while the color indicates the mean expression 
    level or fold change, depending on the flavor.

    Parameters:
    ----------
    fig : plotly.graph_objects.Figure
        The Plotly figure to which the scatter plot will be added.

    mean_expression_data : numpy.ndarray
        2D array containing mean expression data of genes across cell types.

    fraction_expressing_data : numpy.ndarray
        2D array containing the fraction of cells expressing each gene across cell types.

    all_genes : list
        List of all genes considered, used for x-axis positioning.

    cell_types : list
        List of cell types, used for y-axis positioning.

    colorscale : str
        Colorscale for the scatter plot points, representing expression level or fold change.

    max_size : int
        Maximum size for the scatter plot points.

    flavor : str
        Specifies the method for obtaining gene values: 'mean_expression' or 'fold_change'.
        Determines the data visualized by the scatter plot's color.

    Returns:
    -------
    None
    """
    normalized_sizes = (fraction_expressing_data / np.max(fraction_expressing_data)) * max_size
    x_data, y_data, sizes, colors, hover_texts = [], [], [], [], []
    
    for i, gene in enumerate(all_genes):
        for j, cell_type in enumerate(cell_types):
            x_data.append(i)
            y_data.append(j)
            sizes.append(normalized_sizes[i, j])
            colors.append(mean_expression_data[i, j])
            hover_texts.append(f"Gene: {gene}<br>Fraction: {fraction_expressing_data[i, j]*100:.2f}%<br>Value: {mean_expression_data[i, j]:.2f}")
    
    final_colorscale = colorscale if flavor == "mean_expression" else "balance"
    color_range = [0, np.max(mean_expression_data)] if flavor == "mean_expression" else [-4, 4]
    
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                colorscale=final_colorscale,
                showscale=False,
                colorbar=dict(title="", orientation='h'),
                cmin=color_range[0],
                cmax=color_range[1],
                line=dict(width=1, color="Black"),
                sizemode="diameter",
                opacity=1
            ),
            hoverinfo="text",
            hovertext=hover_texts
        ),
        row=1, col=1
    )


def add_dendrogram_to_plot(fig, adata, color_mapping=None, n_genes=10):
    """
    Add a dendrogram to an existing Plotly figure.

    This function extracts dendrogram information from the AnnData object 
    and plots it onto the provided figure. The dendrogram typically represents
    the hierarchical clustering structure of the data.

    Parameters:
    ----------
    fig: plotly.graph_objects.Figure
        The Plotly figure to which the dendrogram will be added.

    adata: AnnData
        An AnnData object, which is expected to contain dendrogram data 
        under the 'dendrogram_leiden' key in its uns attribute.

    color_mapping: dict, optional
        A dictionary mapping the original colors in the dendrogram to desired 
        colors for visualization. If a color is not provided in this mapping,
        it defaults to black.

    n_genes: int, optional
        The number of genes being analyzed, used to adjust scaling if necessary.

    Returns:
    -------
    None
    """
    # Extract dendrogram information from the AnnData object
    icoord = adata.uns["dendrogram_leiden"]['dendrogram_info']['icoord']
    dcoord = adata.uns["dendrogram_leiden"]['dendrogram_info']['dcoord']
    color_list = adata.uns["dendrogram_leiden"]['dendrogram_info']['color_list']

    # Calculate scaling factor for x-axis
    max_x = max(max(xs) for xs in icoord)  # Maximum x-coordinate in dendrogram
    max_y = max(max(d) for d in dcoord)    # Maximum height in dendrogram

    # Normalize y-coordinates (ys)
    normalized_dcoord = [[y / max_y for y in d] for d in dcoord]

    # Normalize x-coordinates (xs) to range [0, 1]
    normalized_icoord = [[x / max_x for x in xs] for xs in icoord]

    # Plot dendrogram lines
    for xs, ys, color in zip(normalized_icoord, normalized_dcoord, color_list):
        line_color = color_mapping.get(color, 'black') if color_mapping else 'black'
        fig.add_trace(
            go.Scatter(
                x=ys,
                y=xs,
                mode='lines',
                line=dict(color=line_color, width=1),
                hoverinfo='none'
            ),
            row=1, col=2
        )

    # Set fixed axis limits
    fig.update_xaxes(range=[0, 1], row=1, col=2)
    fig.update_yaxes(range=[0, 1.2], row=1, col=2)


        
def plotly_dotplot_unified(adata,save_path,fig_name, n_genes=10, gene_list=None, group_by="leiden", 
                           max_size=14, show_dendrogram=True, dendrogram_color='black', 
                           font_family='Arial', colorscale="Reds", flavor="mean_expression", min_logfc=1):
    """
    Create a unified dot plot visualization of gene expression using Plotly.

    This function produces a dot plot showcasing gene expression across different cell types.
    Each dot's size represents the fraction of cells expressing the gene, while its color 
    indicates the mean expression level or fold change. Additional annotations and an optional 
    dendrogram can also be added to provide context about the hierarchical structure of the data.

    Parameters:
    ----------
    adata : AnnData
        An object containing gene expression data, differential expression results, and 
        potentially dendrogram data.

    n_genes : int, optional
        Number of top genes to consider if gene_list is not provided. Default is 10.

    gene_list : list, optional
        List of specific genes to consider. If provided, n_genes is ignored.

    group_by : str, optional
        Column name in adata.obs that contains cell type or cluster information. Default is 'leiden'.

    max_size : int, optional
        Maximum size for the scatter plot points. Default is 15.

    show_dendrogram : bool, optional
        Whether to overlay a dendrogram on the plot, indicating hierarchical clustering. Default is True.

    dendrogram_color : str, optional
        Color for the dendrogram lines. Default is 'black'.

    font_family : str, optional
        Font family to use for all text elements in the figure. Default is 'Arial'.

    colorscale : str, optional
        Colorscale for the scatter plot points, representing expression level or fold change. Default is "Reds".

    flavor : str, optional
        Specifies the method for obtaining gene values: 'mean_expression' or 'fold_change'. Default is 'mean_expression'.

    min_logfc : float, optional
        Minimum log fold change to consider when selecting genes based on fold change. Only used if flavor is 'fold_change'. Default is 1.

    Returns:
    -------
    plotly.graph_objects.Figure
        The fully constructed Plotly figure.
    """
    
    cell_types = list(adata.uns["dendrogram_leiden"]['categories_ordered'])
    
    if gene_list is not None:
        n_genes = len(gene_list)  
    
    mean_expression_data, fraction_expressing_data, all_genes = prepare_data(
        adata, cell_types, n_genes, gene_list, group_by, flavor, min_logfc)   # Pass min_logfc here
    
    fig = make_subplots(rows=1, cols=2, shared_yaxes=False, column_widths=[0.98, 0.02])
    
    add_scatter_plot(fig, mean_expression_data, fraction_expressing_data, all_genes, cell_types, colorscale, max_size, flavor)
    
    base_height = 350
    
    if gene_list is not None:
        if len(gene_list) < 20:
            base_width = 75
            scaling_factor = 5
        else:
            base_width = 55
            scaling_factor = 15
    else:
        scaling_factor = max(1, n_genes / 2)
        base_width = 500
    config = set_plot_layout(fig, all_genes, cell_types, font_family, base_height, base_width, scaling_factor)
    
    add_annotations(fig, cell_types, font_family, n_genes, gene_list=gene_list)
    
    if show_dendrogram:
        add_dendrogram_to_plot(fig, adata, color_mapping=None, n_genes=10)
    
    output_format = "png" if len(adata.obs) > 15000 else "html"

    file_path = f"{save_path}/{fig_name}.{output_format}"
    if output_format == "html":
        plot(fig, filename=file_path, auto_open=False, config=config)
    else:
        fig.write_image(file_path, scale=10) 
    
    return file_path


def plot_umap_and_obs(umap_coords, save_path, fig_name, data_df,title, color_column=None, template=None, output_format="html"):
    """
    Plot UMAP scatter plot using Plotly based on colors from a specified column.
    Now uses the theme system for consistent styling.

    Parameters:
    - umap_coords: numpy array containing UMAP coordinates.
    - data_df: DataFrame containing metadata and columns for coloring.
    - color_column: Column name in data_df to color the scatter plot.
    - template: Plotly template for styling the plot (deprecated, uses theme system now).
    """
    
    # Get current theme for consistent styling
    current_theme = get_current_theme()
    
    # Convert UMAP coordinates to DataFrame
    umap_df = pd.DataFrame(umap_coords, columns=['UMAP1', 'UMAP2'])
    
    # Concatenate UMAP DataFrame with data_df side by side
    merged_df = pd.concat([umap_df, data_df.reset_index(drop=True)], axis=1)
    
    # Sort the DataFrame based on the condition
    if color_column:
        merged_df = merged_df.sort_values(by=color_column)
    
    num_unique_classes = merged_df[color_column].nunique() if color_column else 0

    # Determine if we're dealing with discrete or continuous data
    is_discrete = num_unique_classes < 30 and merged_df[color_column].dtype == 'object' if color_column else False
    
    # Choose appropriate color scale
    if is_discrete:
        # Use UMAP-specific discrete colors from current theme instead of legacy primary_palette
        umap_config = get_plot_theme_config("umap_plots")
        umap_discrete_colors = umap_config.get("colors", ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"])
        color_scale = umap_discrete_colors[:num_unique_classes] if num_unique_classes <= len(umap_discrete_colors) else umap_discrete_colors * ((num_unique_classes // len(umap_discrete_colors)) + 1)
        color_discrete_map = {val: color_scale[i % len(color_scale)] for i, val in enumerate(merged_df[color_column].unique())}
    else:
        color_scale = current_theme.get_plotly_colorscale(current_theme.colors["continuous_palette"])

    # Create the scatter plot
    fig = px.scatter(
        merged_df,
        x='UMAP1',
        y='UMAP2',
        color=color_column,
        color_continuous_scale=color_scale if not is_discrete else None,
        color_discrete_map=color_discrete_map if is_discrete else None,
        template=current_theme.layout["template"]
    )

    # Get the label for the color column and set as title
    if title is None:
        title = data_df[color_column].name if color_column else "UMAP Scatter Plot"

    show_legend = True if num_unique_classes < 30 else False

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig, current_theme, "umap_plots")
    
    # Override specific settings for UMAP plots
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font_size=current_theme.fonts["title_size"]
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            linecolor=current_theme.colors["axis_color"],
            linewidth=1.5,
            mirror=True,
            showline=True,
            showspikes=False,
            title_text=""
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            linecolor=current_theme.colors["axis_color"],
            linewidth=1.5,
            mirror=True,
            showline=True,
            showspikes=False,
            title_text=""
        ),
        showlegend=show_legend,
        width=current_theme.layout["width"] // 2,
        height=380,
        annotations=[
            # X-axis label
            dict(
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.1,
                showarrow=False,
                text="UMAP1",
                font=dict(
                    size=current_theme.fonts["axis_title_size"],
                    color=current_theme.colors["text_color"]
                )
            ),
            # Y-axis label
            dict(
                xref="paper",
                yref="paper",
                x=-0.08,
                y=0.5,
                showarrow=False,
                text="UMAP2",
                textangle=-90,
                font=dict(
                    size=current_theme.fonts["axis_title_size"],
                    color=current_theme.colors["text_color"]
                )
            )
        ]
    )
    
    # Remove colorbar title if continuous
    if not is_discrete:
        fig.update_layout(coloraxis_colorbar_title_text="")
    
    # Update marker properties with theme settings
    fig.update_traces(marker=dict(
        size=current_theme.markers["size"],
        opacity=current_theme.markers["opacity"],
        line=dict(width=0)  # Remove contour lines from scatter points
    ))
    output_format = "png" if len(data_df) > 15000 else "html"

    file_path = f"{save_path}/{fig_name}.{output_format}"
    if output_format == "html":
        pio.write_html(fig, file=file_path, auto_open=False)
    elif output_format == "svg":
        fig.write_image(file_path)
    else:
        fig.write_image(file_path, scale=10)  

    return file_path

def plot_pca_and_obs(pca_coords, save_path, fig_name, data_df,title, color_column=None, template=None, output_format="html"):
    """
    Plot PCA scatter plot using Plotly based on colors from a specified column.
    Now uses the theme system for consistent styling.

    Parameters:
    - pca_coords: numpy array containing PCA coordinates.
    - data_df: DataFrame containing metadata and columns for coloring.
    - color_column: Column name in data_df to color the scatter plot.
    - template: Plotly template for styling the plot (deprecated, uses theme system now).
    """
    
    # Get current theme for consistent styling
    current_theme = get_current_theme()
    
    # Convert PCA coordinates to DataFrame
    pca_df = pd.DataFrame(pca_coords[:, :2], columns=['PC1', 'PC2'])
    
    # Concatenate PCA DataFrame with data_df side by side
    merged_df = pd.concat([pca_df, data_df.reset_index(drop=True)], axis=1)
    
    # Sort the DataFrame based on the condition
    if color_column:
        merged_df = merged_df.sort_values(by=color_column)
    
    num_unique_classes = merged_df[color_column].nunique() if color_column else 0

    # Determine if we're dealing with discrete or continuous data
    is_discrete = num_unique_classes < 30 and merged_df[color_column].dtype == 'object' if color_column else False
    
    # Choose appropriate color scale
    if is_discrete:
        color_scale = current_theme.get_cluster_colors(num_unique_classes)
        color_discrete_map = {val: color_scale[i % len(color_scale)] for i, val in enumerate(merged_df[color_column].unique())}
    else:
        color_scale = current_theme.get_plotly_colorscale(current_theme.colors["continuous_palette"])

    # Create the scatter plot
    fig = px.scatter(
        merged_df,
        x='PC1',
        y='PC2',
        color=color_column,
        color_continuous_scale=color_scale if not is_discrete else None,
        color_discrete_map=color_discrete_map if is_discrete else None,
        template=current_theme.layout["template"]
    )

    # Get the label for the color column and set as title
    if title is None:
        title = data_df[color_column].name if color_column else "PCA Scatter Plot"

    show_legend = True if num_unique_classes < 30 else False

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig, current_theme, "pca_plots")

    # Override specific settings for PCA plots
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font_size=current_theme.fonts["title_size"]
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            linecolor=current_theme.colors["axis_color"],
            linewidth=1.5,
            mirror=True,
            showline=True,
            showspikes=False,
            title_text=""
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            linecolor=current_theme.colors["axis_color"],
            linewidth=1.5,
            mirror=True,
            showline=True,
            showspikes=False,
            title_text=""
        ),
        showlegend=show_legend,
        width=current_theme.layout["width"] // 2,
        height=380,
        annotations=[
            # X-axis label
            dict(
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.1,
                showarrow=False,
                text="PC1",
                font=dict(
                    size=current_theme.fonts["axis_title_size"],
                    color=current_theme.colors["text_color"]
                )
            ),
            # Y-axis label
            dict(
                xref="paper",
                yref="paper",
                x=-0.08,
                y=0.5,
                showarrow=False,
                text="PC2",
                textangle=-90,
                font=dict(
                    size=current_theme.fonts["axis_title_size"],
                    color=current_theme.colors["text_color"]
                )
            )
        ]
    )
    
    # Remove colorbar title if continuous
    if not is_discrete:
        fig.update_layout(coloraxis_colorbar_title_text="")
    
    # Update marker properties with theme settings
    fig.update_traces(marker=dict(
        size=current_theme.markers["size"],
        opacity=current_theme.markers["opacity"],
        line=dict(width=0)  # Remove contour lines from scatter points
    ))
    output_format = "png" if len(data_df) > 15000 else "html"

    file_path = f"{save_path}/{fig_name}.{output_format}"
    if output_format == "html":
        pio.write_html(fig, file=file_path, auto_open=False)
    elif output_format == "svg":
        fig.write_image(file_path)
    else:
        fig.write_image(file_path, scale=10)  
        
    return file_path

def plot_scatter_hvg(adata,save_path,fig_name, x, y, template=None, x_label=None, y_label=None):
    """
    Plot scatter plots for highly variable genes based on provided x and y columns from adata.var.
    Now uses the plot-specific theme system for consistent styling.

    Parameters:
    - adata: Data object, usually from anndata library.
    - x: Column name in adata.var for x-axis.
    - y: List of column names in adata.var for y-axis.
    - template: Plotly template for styling the plot (deprecated, uses theme system now).
    - x_label: Custom label for x-axis. If not provided, defaults to column name.
    - y_label: Custom label for y-axis. If not provided, defaults to column name.
    """
    # Get plot-specific theme configuration
    hvg_config = get_plot_theme_config("hvg_plots")
    
    output_format = "png" if len(adata.obs) > 15000 else "html"

    # Determine the source based on the provided parameter
    data_source = adata.var
    
    for idx, y_col in enumerate(y):
        # Extract highly variable and other genes
        hv_indices = adata.var["highly_variable"]
        
        # Create scatter plot for Highly Variable Genes with theme colors
        fig = go.Figure(data=go.Scatter(x=data_source[x][hv_indices], 
                                        y=data_source[y_col][hv_indices],
                                        mode='markers',
                                        marker=dict(
                                            color=hvg_config.get("hvg_color", "#d62728"),
                                            size=hvg_config.get("marker_size", 4),
                                            opacity=hvg_config.get("opacity", 0.6)
                                        ),
                                        text=data_source.index[hv_indices],
                                        hovertemplate='<b>%{text}</b><br>' +
                                                     x + ': %{x}<br>' +
                                                     y_col + ': %{y}<extra></extra>',
                                        name="Highly Variable Genes"))
        
        # Add scatter plot for Other Genes with theme colors
        fig.add_trace(go.Scatter(x=data_source[x][~hv_indices], 
                                 y=data_source[y_col][~hv_indices],
                                 mode='markers',
                                 marker=dict(
                                     color=hvg_config.get("non_hvg_color", "#1f77b4"),
                                     size=hvg_config.get("marker_size", 4),
                                     opacity=hvg_config.get("opacity", 0.6)
                                 ),
                                 text=data_source.index[~hv_indices],
                                 hovertemplate='<b>%{text}</b><br>' +
                                              x + ': %{x}<br>' +
                                              y_col + ': %{y}<extra></extra>',
                                 name="Other Genes"))
        
        # Apply plot-specific theme
        fig = apply_theme_to_figure(fig, plot_type="hvg_plots")
        
        # Override specific settings for HVG plots
        fig.update_layout(
            width=360,  # Better width for scatter plots
            height=350, # Better height for scatter plots
            xaxis_title=x if x_label is None else x_label,
            yaxis_title=y_col if y_label is None else y_label,
            margin=dict(l=60, r=60, b=40, t=40),
            # title="Highly Variable Genes",  # Removed title
            legend=dict(
                x=1,      # 1 is the far right, so this pushes the legend to the right edge
                y=1,      # 1 is the top, so this pushes the legend to the top edge
                xanchor="right",   # Anchor the legend's right edge at x=1
                yanchor="top"      # Anchor the legend's top at y=1
            )
        )
        
        file_path = f"{save_path}/{fig_name}.{output_format}"
        if output_format == "html":
            plot(fig, filename=file_path, auto_open=False)
        else:
            fig.write_image(file_path, scale=10)        
    return file_path
        
def send_email(email: str, subject: str, content: str):
    # In local or when disabled, skip sending instead of failing
    if not enable_email:
        print("[email] Skipped (ENABLE_EMAIL=false)")
        return
    if not sendgrid_api_key:
        print("[email] SENDGRID_API_KEY not set; skipping send")
        return

    message = Mail(
        from_email='scrnaexplorer@gmail.com',
        to_emails=email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"sendgrid: {response}")
    except Exception as e:
        # Log but do not break main workflow
        print(f"[email] Error sending email: {e}")
        return
    
def upload_notification(mail, name_analysis, id_for):
    template_path = "mail/templates/upload_notification.html"
    content = read_template(template_path)
    content = content.replace("name_analysis", name_analysis) \
                        .replace("id_for_email", id_for)
    send_email(mail, "scExplorer Upload Confirmation 🧬", content)
    
def read_template(template_path):
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def sanitize_column_names(dataframe):
    """Sanitize column names to have only alphanumeric characters and underscores."""
    dataframe.columns = [re.sub(r'\W+', '', col) for col in dataframe.columns]
    return dataframe

# def run_r_script(uuid):

#     r_script = f"""
#     library(Seurat)
#     library(SeuratDisk)

#     # Specify the path to your h5ad file
#     h5ad_path <- 'uploads/{uuid}/seurat.h5ad'
#     h5seurat_path <- 'uploads/{uuid}/seurat.h5seurat' # This is the corrected part

#     # Specify the path where you want to save the RDS file
#     rds_path <- 'uploads/{uuid}/{uuid}.rds'
#     Convert(h5ad_path, dest = "h5seurat", overwrite = TRUE) # Specify the output format and overwrite if exists

#     # Load the converted h5Seurat file as a Seurat object
#     seuratObject <- LoadH5Seurat(h5seurat_path,assays = "RNA") 

#     # Save the Seurat object as an RDS file
#     saveRDS(seuratObject, file = rds_path)
#     """
    
#     input = sc.read_h5ad(f"uploads/{uuid}/{uuid}.h5ad")
#     adata = input.copy()
#     if "counts" in adata.layers:
#         matrix = adata.layers["counts"]
#         adata.obs.columns = [sub.replace('(', '') for sub in adata.obs.columns]
#         adata.obs.columns = [sub.replace(')', '') for sub in adata.obs.columns]
#         adata.obs.columns = [sub.replace('/', '') for sub in adata.obs.columns]
#         adata.obs.columns = [sub.replace('=', '.') for sub in adata.obs.columns]
#         adata.obs.columns = [sub.replace(' ', '_') for sub in adata.obs.columns]
#         adata.obs.columns = [sub.replace('-', '_') for sub in adata.obs.columns]
#         adata.obs_names = [sub.replace('-', '_') for sub in adata.obs_names]
#         new_adata = sc.AnnData(X=matrix, obs=sanitize_column_names(adata.obs))
#         new_adata.write_h5ad(f"uploads/{uuid}/seurat.h5ad")

#         robjects.r(r_script)
#         os.remove(f"uploads/{uuid}/seurat.h5ad")
#         os.remove(f"uploads/{uuid}/seurat.h5seurat")
#         path = f"uploads/{uuid}/{uuid}.rds"
#         return path
#     else:
#         input = sc.read_h5ad(f"uploads/{uuid}/{uuid}.h5ad")
#         input.write_h5ad(f"uploads/{uuid}/seurat.h5ad")
#         robjects.r(r_script)
#         os.remove(f"uploads/{uuid}/seurat.h5ad")
#         os.remove(f"uploads/{uuid}/seurat.h5seurat")
#         path = f"uploads/{uuid}/{uuid}.rds"
#         return path
def run_r_script(uuid):

    r_script = f"""
    library(Seurat)
    library(anndata)
    library(Matrix)

    h5ad_path <- 'uploads/{uuid}/seurat.h5ad'
    rds_path <- 'uploads/{uuid}/{uuid}.rds'
    data <- read_h5ad(h5ad_path)
    colnames(data$X) <- gsub('_', '-', colnames(data$X))
    if (inherits(data$X, 'sparseMatrix')) data$X <- as.matrix(data$X)
    data <- CreateSeuratObject(counts = t(data$X))
    saveRDS(data, file = rds_path)
    """

    clean_data = sc.read_h5ad(f"uploads/{uuid}/{uuid}.h5ad")
    adata = clean_data.copy()

    # Ensure unique names to avoid Seurat duplicate row/colname errors
    try:
        adata.obs_names_make_unique()
        adata.var_names_make_unique()
    except Exception as e:
        print(f"Failed to make names unique: {e}")

    adata.write_h5ad(f"uploads/{uuid}/seurat.h5ad")

    robjects.r(r_script)
    robjects.r("q(save='no')")
    os.remove(f"uploads/{uuid}/seurat.h5ad")
    path = f"uploads/{uuid}/{uuid}.rds"
    return path

def clustree_seurat(uuid):
    input = sc.read_h5ad(f"uploads/{uuid}/{uuid}.h5ad")
    adata = input.copy()
    if not sp.issparse(adata.X):
        print("matrix to csr for clustree")
        adata.X = sp.csr_matrix(adata.X)
    if "counts" in adata.layers:
        matrix = adata.layers["counts"]
        adata.obs.columns = [sub.replace('(', '') for sub in adata.obs.columns]
        adata.obs.columns = [sub.replace(')', '') for sub in adata.obs.columns]
        adata.obs.columns = [sub.replace('/', '') for sub in adata.obs.columns]
        adata.obs.columns = [sub.replace('=', '.') for sub in adata.obs.columns]
        adata.obs.columns = [sub.replace(' ', '_') for sub in adata.obs.columns]
        adata.obs.columns = [sub.replace('-', '_') for sub in adata.obs.columns]
        adata.obs_names = [sub.replace('-', '_') for sub in adata.obs_names]
        new_adata = sc.AnnData(X=matrix, obs=sanitize_column_names(adata.obs))
        new_adata.write_h5ad(f"uploads/{uuid}/clustree.h5ad")


    r_script = f"""
    library(Seurat)
    library(anndata)
    library(Matrix)
    library(clustree)
    set.seed(1234)

    h5ad_path <- 'uploads/{uuid}/clustree.h5ad'
    data <- read_h5ad(h5ad_path)
    colnames(data$X) <- gsub('_', '-', colnames(data$X))
    if (inherits(data$X, 'sparseMatrix')) data$X <- as.matrix(data$X)
    seuratObject <- CreateSeuratObject(counts = t(data$X))

    seuratObject <- NormalizeData(seuratObject)
    seuratObject <- FindVariableFeatures(seuratObject)
    seuratObject <- ScaleData(seuratObject)
    seuratObject <- RunPCA(seuratObject)
    seuratObject <- FindNeighbors(seuratObject)
    seuratObject <- FindClusters(seuratObject, res = seq(0, 2, by = 0.1))
    clustreePlot <- clustree(seuratObject, prefix = "RNA_snn_res.")

    ggsave("uploads/{uuid}/embedding/clustreePlot.svg", plot = clustreePlot, width = 10, height = 10)
    """

    try:
        try:
            robjects.r(r_script)
        except Exception as e:
            print(f"--- [utils.py] Error during R script execution: {e} ---")

        os.remove(f"uploads/{uuid}/clustree.h5ad")

        path = f"uploads/{uuid}/embedding/clustreePlot.svg"
        return path

    finally:
        robjects.r("q(save='no')")
    

def mygene_converter(adata, species, flavor="symbol"):
    mg = mygene.MyGeneInfo()
    gene_ids = adata.var.index.tolist()
    first_id = gene_ids[0]

    if (flavor == "symbol" and not first_id.startswith(('ENSG', 'ENSM'))) or \
       (flavor == "ensembl" and first_id.startswith(('ENSG', 'ENSM'))):
        return adata

    if flavor == "symbol":
        scopes = 'ensembl.gene'
        fields = 'symbol'
    elif flavor == "ensembl":
        scopes = 'refseq,symbol'
        fields = 'ensembl.gene'
    else:
        return "wrong flavor"
    
    out = mg.querymany(gene_ids, scopes=scopes, fields=fields, species=species, returnall=True,as_dataframe=True)
    out["out"]["symbol"] = out["out"]["symbol"].fillna(pd.Series(out["out"].index, index=out["out"].index)) 
    df_unique = out["out"][~out["out"].index.duplicated(keep='first')]

    # try:
    #     out = mg.querymany(gene_ids, scopes=scopes, fields=fields, species=species, returnall=True)
    # except Exception as e:
    #     print(f"Error querying MyGeneInfo: {e}")
    #     return "Error Mygene"
    
    # output_dict = {}
    # for item in out['out']:
    #     if 'notfound' in item:
    #         output_dict[item['query']] = item['query']
    #     elif 'ensembl' in item:
    #         ensembl = item['ensembl']
    #         if isinstance(ensembl, list):
    #             output_dict[item['query']] = ensembl[0]['gene']
    #         else:
    #             output_dict[item['query']] = ensembl['gene']

    # final_output = [output_dict.get(tid, tid) for tid in gene_ids]
    adata.var.index = df_unique["symbol"].tolist()
    return adata
    


def cleanup_previous_dea_results(uuid):
    """
    Remove all previous DEA CSV files before starting a new DEA analysis.
    
    Parameters:
    ----------
    uuid : str
        The UUID of the analysis
    """
    import glob
    import os
    
    # Define the path where DEA CSV files are stored
    output_dir = f'uploads/{uuid}/dea/results'
    
    if os.path.exists(output_dir):
        # Find all cluster CSV files
        csv_files = glob.glob(f'{output_dir}/cluster_*.csv')
        
        # Remove each CSV file
        for csv_file in csv_files:
            try:
                os.remove(csv_file)
                #print(f"Removed old DEA CSV file: {csv_file}")
            except OSError as e:
                pass
                #print(f"Error removing {csv_file}: {e}")
        
       # print(f"Cleaned up {len(csv_files)} previous DEA CSV files for UUID: {uuid}")
    else:
        pass
    #print(f"No previous DEA results directory found for UUID: {uuid}")

def save_rank_genes_groups(uuid, adata):
    def recarray_to_dict_with_dtype(rec_array):
        data_dict = {}
        for field in rec_array.dtype.names:
            data_dict[field] = rec_array[field].tolist()
        return data_dict

    def flatten_dict_with_dtype(data_dict):
        flat_list = []
        dtype_list = []
        for field, values in data_dict.items():
            flat_list.extend(values)
            dtype_list.extend([field] * len(values))
        return flat_list, dtype_list

    # Ensure the output directory exists
    output_dir = f'uploads/{uuid}/dea/results'
    os.makedirs(output_dir, exist_ok=True)

    adata_uns_rank_genes_groups = {
        'names': adata.uns["rank_genes_groups"]["names"],
        'scores': adata.uns["rank_genes_groups"]["scores"],
        'pvals': adata.uns["rank_genes_groups"]["pvals"],
        'pvals_adj': adata.uns["rank_genes_groups"]["pvals_adj"],
        'logfoldchanges': adata.uns["rank_genes_groups"]["logfoldchanges"]
    }

    names_dict = recarray_to_dict_with_dtype(adata_uns_rank_genes_groups['names'])
    scores_dict = recarray_to_dict_with_dtype(adata_uns_rank_genes_groups['scores'])
    pvals_dict = recarray_to_dict_with_dtype(adata_uns_rank_genes_groups['pvals'])
    pvals_adj_dict = recarray_to_dict_with_dtype(adata_uns_rank_genes_groups['pvals_adj'])
    logfoldchanges_dict = recarray_to_dict_with_dtype(adata_uns_rank_genes_groups['logfoldchanges'])

    # Flatten the lists and add dtype information
    names_list, names_dtype = flatten_dict_with_dtype(names_dict)
    scores_list, scores_dtype = flatten_dict_with_dtype(scores_dict)
    pvals_list, pvals_dtype = flatten_dict_with_dtype(pvals_dict)
    pvals_adj_list, pvals_adj_dtype = flatten_dict_with_dtype(pvals_adj_dict)
    logfoldchanges_list, logfoldchanges_dtype = flatten_dict_with_dtype(logfoldchanges_dict)

    # Creating a DataFrame with dtype column
    df = pd.DataFrame({
        'cluster': names_dtype,
        'names': names_list,
        'scores': scores_list,
        'pvals': pvals_list,
        'pvals_adj': pvals_adj_list,
        'logfoldchanges': logfoldchanges_list,
    })

    combined_dict = {
        'names': names_dict,
        'scores': scores_dict,
        'pvals': pvals_dict,
        'pvals_adj': pvals_adj_dict,
        'logfoldchanges': logfoldchanges_dict
    }

    dataframes = {}
    for dtype_index in names_dict.keys():
        data = {
            'names': combined_dict['names'][dtype_index],
            'scores': combined_dict['scores'][dtype_index],
            'pvals': combined_dict['pvals'][dtype_index],
            'pvals_adj': combined_dict['pvals_adj'][dtype_index],
            'logfoldchanges': combined_dict['logfoldchanges'][dtype_index]
        }
        dataframes[dtype_index] = pd.DataFrame(data)

    for dtype_index, df in dataframes.items():
        df.to_csv(f'{output_dir}/cluster_{dtype_index}.csv', index=False)
