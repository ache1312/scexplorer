from pydantic import BaseModel, validator
from typing import Optional, List, Literal, Dict, Any
from fastapi import Form, File, UploadFile

class UploadData(BaseModel):
    file: Optional[UploadFile] = File(None)
    species: str
    email: Optional[str] = None
    analysisName: str

class ProcessDataParams(BaseModel):
    min_genes: int = 200
    min_cells: int = 3
    mito_threshold: int = 5  
    doublet_detection: bool = True
    
class EmbeddingParams(BaseModel):
    n_neighbors: int = 15
    n_pcs: int = 18
    resolution: float = 0.5

class PcaParams(BaseModel):
    n_genes : int = 2000
    flavor : str 
    
class VisualizationInput(BaseModel):
    file_uuid: str
    dim_red: str
    gene_list: List[str]

class VarVisualizationInput(BaseModel):
    file_uuid: str
    dim_red: Literal["X_umap", "X_pca"] = "X_umap"
    var_keys: List[str]   # multiple column names in adata.var

class ObsVisualizationInput(BaseModel):
    file_uuid: str
    dim_red: Literal["X_umap", "X_pca"] = "X_umap"
    obs_keys: List[str]   # multiple column names in adata.obs

# ============================================================================
# THEME SYSTEM VALIDATION MODELS
# ============================================================================

class PlotColors(BaseModel):
    primary_palette: List[str] = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    categorical_palette: str = "Set3"
    continuous_palette: str = "viridis"
    diverging_palette: str = "RdBu"
    background_color: str = "#ffffff"
    grid_color: str = "#f0f0f0"
    text_color: str = "#333333"
    axis_color: str = "#666666"
    highlight_color: str = "#ff6b6b"
    qc_pass_color: str = "#2ecc71"
    qc_fail_color: str = "#e74c3c"
    qc_warning_color: str = "#f39c12"
    
    @validator('primary_palette')
    def validate_primary_palette(cls, v):
        if len(v) < 3:
            raise ValueError('Primary palette must have at least 3 colors')
        for color in v:
            if not color.startswith('#') or len(color) != 7:
                raise ValueError(f'Invalid hex color: {color}')
        return v

class PlotFonts(BaseModel):
    family: str = "Arial, sans-serif"
    size: int = 12
    title_size: int = 16
    axis_title_size: int = 14
    legend_size: int = 11
    annotation_size: int = 10
    
    @validator('size', 'title_size', 'axis_title_size', 'legend_size', 'annotation_size')
    def validate_font_sizes(cls, v):
        if v < 8 or v > 36:
            raise ValueError('Font size must be between 8 and 36')
        return v

class PlotLayout(BaseModel):
    width: int = 800
    height: int = 600
    margin: Dict[str, int] = {"l": 60, "r": 60, "t": 80, "b": 60}
    plot_bgcolor: str = "#ffffff"
    paper_bgcolor: str = "#ffffff"
    grid_alpha: float = 0.3
    show_grid: bool = True
    show_legend: bool = True
    legend_position: Literal["right", "left", "top", "bottom"] = "right"
    template: Literal["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white"] = "plotly_white"
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        if v < 200 or v > 2000:
            raise ValueError('Plot dimensions must be between 200 and 2000 pixels')
        return v
    
    @validator('grid_alpha')
    def validate_alpha(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Alpha value must be between 0 and 1')
        return v

class PlotMarkers(BaseModel):
    size: int = 4
    opacity: float = 0.7
    line_width: int = 0
    symbol: Literal["circle", "square", "diamond", "triangle-up", "triangle-down", "cross", "x"] = "circle"
    
    @validator('size')
    def validate_size(cls, v):
        if v < 1 or v > 20:
            raise ValueError('Marker size must be between 1 and 20')
        return v
    
    @validator('opacity')
    def validate_opacity(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Opacity must be between 0 and 1')
        return v

class AccessibilityOptions(BaseModel):
    high_contrast: bool = False
    colorblind_friendly: bool = False
    large_text: bool = False
    simplified_layout: bool = False

class PlotThemeRequest(BaseModel):
    theme_name: str
    colors: Optional[PlotColors] = None
    fonts: Optional[PlotFonts] = None
    layout: Optional[PlotLayout] = None
    markers: Optional[PlotMarkers] = None
    accessibility: Optional[AccessibilityOptions] = None
    
    @validator('theme_name')
    def validate_theme_name(cls, v):
        if len(v) < 1 or len(v) > 50:
            raise ValueError('Theme name must be between 1 and 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Theme name must contain only alphanumeric characters, hyphens, and underscores')
        return v

class VisualizationWithTheme(BaseModel):
    file_uuid: str
    dim_red: str
    gene_list: List[str]
    theme_name: Optional[str] = "default"
    custom_theme: Optional[PlotThemeRequest] = None

# ============================================================================
# CELL-LEVEL HEATMAP INPUT
# ============================================================================
class CellHeatmapInput(BaseModel):
    file_uuid: str
    groupby: str = "leiden"
    gene_list: Optional[List[str]] = None
    top_n: int = 10  # used if gene_list is None
    zscore: bool = True
    standard_scale: Literal["gene", "var", "obs", "cell", "none"] = "none"
    clip_percentiles: List[float] = [1.0, 99.0]
    cluster_rows: bool = True     # cluster genes
    cluster_cols: bool = False    # full column clustering disabled by default
    layer: Optional[str] = None
    use_raw: bool = False
    max_genes: int = 100
    output_format: Literal["png"] = "png"
    dendrogram: bool = False      # order categories using sc.tl.dendrogram
    swap_axes: bool = False       # rotate layout like sc.pl.heatmap(swap_axes=True)
    show_gene_labels: Optional[bool] = None  # auto-decide based on gene count
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    vcenter: Optional[float] = None

    @validator('clip_percentiles')
    def validate_clip_percentiles(cls, v):
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError('clip_percentiles must be a list of two numbers [low, high]')
        low, high = v
        if low < 0 or high > 100 or low >= high:
            raise ValueError('clip_percentiles must satisfy 0 <= low < high <= 100')
        return v

    @validator('top_n')
    def validate_top_n(cls, v):
        if v < 1 or v > 100:
            raise ValueError('top_n must be between 1 and 100')
        return v

    @validator('max_genes')
    def validate_max_genes(cls, v):
        if v < 1 or v > 100:
            raise ValueError('max_genes must be between 1 and 100')
        return v
