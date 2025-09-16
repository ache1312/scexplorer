"""
Plot Theme Management System for scExplorer
============================================

This module provides a comprehensive theming system for all plots generated in scExplorer,
allowing users to customize color palettes, fonts, layouts, and accessibility options.
"""

try:
    import matplotlib.colors as mcolors
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    
try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None
    px = None

import json
import os

class PlotTheme:
    """Base class for plot themes with comprehensive customization options."""
    
    def __init__(self, theme_name="default"):
        self.theme_name = theme_name
        self._setup_default_theme()
    
    def _setup_default_theme(self):
        """Initialize plot-specific theme settings."""
        # Global theme settings
        self.global_settings = {
            "background_color": "#ffffff",
            "text_color": "#333333",
            "font_family": "Arial, sans-serif"
        }
        
        # Plot-specific configurations with extended 20-color palettes
        self.plot_types = {
            "violin_plots": {
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                          "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
                          "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
                          "#c49c94", "#f7b6d3", "#c7c7c7", "#dbdb8d", "#9edae5"],
                "opacity": 0.85,
                "line_width": 2,
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "show_grid": True,
                "title_size": 16,
                "axis_title_size": 14,
                "width": 800,
                "height": 600,
                "template": "plotly_white"
            },
            
            "scatter_plots": {
                "colors": ["#e91e63", "#9c27b0", "#673ab7", "#3f51b5", "#2196f3", 
                          "#00bcd4", "#009688", "#4caf50", "#8bc34a", "#cddc39",
                          "#ffeb3b", "#ffc107", "#ff9800", "#ff5722", "#795548",
                          "#607d8b", "#37474f", "#263238", "#000000", "#424242"],
                "primary_color": "#1f77b4",
                "secondary_color": "#ff7f0e", 
                "marker_size": 4,
                "opacity": 0.6,
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "show_grid": True,
                "title_size": 16,
                "axis_title_size": 14,
                "width": 800,
                "height": 600,
                "template": "plotly_white"
            },
            
            "umap_plots": {
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                          "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
                          "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
                          "#c49c94", "#f7b6d3", "#c7c7c7", "#dbdb8d", "#9edae5"],
                "categorical_palette": "Set3",
                "continuous_palette": "viridis",
                "marker_size": 3,
                "opacity": 0.7,
                "line_width": 0,
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "show_grid": False,
                "title_size": 16,
                "axis_title_size": 14,
                "width": 800,
                "height": 600,
                "template": "plotly_white"
            },
            
            "pca_plots": {
                "categorical_palette": "Set3",
                "continuous_palette": "viridis",  # Blue-green-yellow for default scientific theme
                "marker_size": 3,
                "opacity": 0.7,
                "line_width": 0,
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "show_grid": False,
                "title_size": 16,
                "axis_title_size": 14,
                "width": 800,
                "height": 600,
                "template": "plotly_white"
            },
            
            "elbow_plots": {
                "base_color": "DarkGreen",  # Base color for all markers (from user template)
                "highlight_color": "red",   # Color for the elbow point (from user template)
                "axis_color": "black",      # Color for axis lines (from user template)
                "line_color": "#1f77b4",   # Legacy support
                "marker_color": "#ff7f0e", # Legacy support
                "line_width": 3,
                "marker_size": 15,          # User's preferred marker size
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "show_grid": True,
                "title_size": 16,
                "axis_title_size": 14,
                "width": 600,              # User's preferred dimensions
                "height": 400,             # User's preferred dimensions
                "template": "plotly_white"
            },
            
            "density_plots": {
                "colorscale": "viridis",
                "contour_color": "#333333",
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "title_size": 16,
                "axis_title_size": 14,
                "width": 800,
                "height": 600,
                "template": "plotly_white"
            },
            
            "hvg_plots": {
                "hvg_color": "#d62728",
                "non_hvg_color": "#1f77b4",
                "marker_size": 4,
                "opacity": 0.6,
                "background_color": "#ffffff",
                "grid_color": "#f0f0f0",
                "title_size": 16,
                "axis_title_size": 14,
                "width": 800,
                "height": 600,
                "template": "plotly_white"
            },
            
            "dea_heatmaps": {
                "colorscale": "RdBu_r",
                "background_color": "#ffffff",
                "title_size": 16,
                "axis_title_size": 12,
                "width": 1000,
                "height": 800,
                "template": "plotly_white"
            },
            
            "clustree": {
                "node_colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
                "edge_color": "#666666",
                "background_color": "#ffffff",
                "title_size": 16,
                "width": 1000,
                "height": 800,
                "template": "plotly_white"
            }
        }
        
        # Legacy compatibility (deprecated but maintained for existing code)
        self.colors = {
            "primary_palette": self.plot_types["violin_plots"]["colors"],
            "background_color": self.global_settings["background_color"],
            "text_color": self.global_settings["text_color"],
            "continuous_palette": "viridis",
            "axis_color": "#444444",
            "grid_color": "#e5e5e5"
        }
        self.fonts = {
            "family": self.global_settings["font_family"], 
            "size": 12,
            "title_size": 16,
            "axis_title_size": 14,
            "legend_size": 12
        }
        self.layout = {"template": "plotly_white", "width": 800, "plot_bgcolor": "#ffffff", "paper_bgcolor": "#ffffff"}
        self.markers = {"size": 4, "opacity": 0.7, "line_width": 1}
        self.accessibility = {
            "high_contrast": False,
            "colorblind_friendly": False,
            "large_text": False,
            "simplified_layout": False
        }
    
    def apply_accessibility_options(self):
        """Apply accessibility modifications to the theme."""
        if self.accessibility["high_contrast"]:
            # Ensure high-contrast visuals use black background and white text
            self.colors["background_color"] = "#000000"
            self.colors["text_color"] = "#ffffff"
            # Also reflect in global settings so previews pick it up
            self.global_settings["background_color"] = "#000000"
            self.global_settings["text_color"] = "#ffffff"
            # High-contrast grid lines should be white for clarity on black
            self.colors["grid_color"] = "#ffffff"
            self.layout["plot_bgcolor"] = "#000000"
            self.layout["paper_bgcolor"] = "#000000"
            
            # Apply high contrast to ALL plot types
            # Replace black in the palette with white for UI and plots
            high_contrast_colors = ["#ffffff", "#ff0000", "#00ff00", "#0000ff", "#ff00ff"]
            for plot_type in self.plot_types:
                if "colors" in self.plot_types[plot_type]:
                    self.plot_types[plot_type]["colors"] = high_contrast_colors
        
        if self.accessibility["colorblind_friendly"]:
            # Use colorblind-friendly palettes
            colorblind_colors = ["#0173b2", "#de8f05", "#029e73", "#cc78bc", 
                               "#ca9161", "#fbafe4", "#949494", "#ece133"]
            self.colors["primary_palette"] = colorblind_colors
            self.colors["continuous_palette"] = "cividis"
            
            # Apply colorblind-friendly colors to ALL plot types  
            for plot_type in self.plot_types:
                if "colors" in self.plot_types[plot_type]:
                    self.plot_types[plot_type]["colors"] = colorblind_colors
        
        if self.accessibility["large_text"]:
            self.fonts["size"] = 16
            self.fonts["title_size"] = 22
            self.fonts["axis_title_size"] = 18
            self.fonts["legend_size"] = 15
        
        if self.accessibility["simplified_layout"]:
            self.layout["show_grid"] = False
            self.markers["size"] = 6
            self.markers["line_width"] = 1
    
    def get_plotly_colorscale(self, palette_name=None, n_colors=100):
        """Generate a Plotly-compatible colorscale."""
        if palette_name is None:
            palette_name = self.colors["continuous_palette"]
        
        if isinstance(palette_name, str):
            # Use built-in Plotly colorscales or matplotlib colormaps
            if HAS_MATPLOTLIB:
                try:
                    import numpy as np
                    # Handle matplotlib version compatibility
                    try:
                        # For matplotlib >= 3.5
                        import matplotlib.pyplot as plt
                        cmap = plt.get_cmap(palette_name)
                    except AttributeError:
                        # For older matplotlib versions
                        cmap = mcolors.get_cmap(palette_name)
                    scale = np.linspace(0, 1, n_colors)
                    colors = cmap(scale)
                    return [(s, mcolors.rgb2hex(c)) for s, c in zip(scale, colors)]
                except (ValueError, ImportError):
                    # Fallback to simple colorscale
                    return [(0.0, "#440154"), (0.5, "#21908c"), (1.0, "#fde724")]  # viridis-like
            else:
                # Fallback to simple colorscale without matplotlib
                return [(0.0, "#440154"), (0.5, "#21908c"), (1.0, "#fde724")]  # viridis-like
        else:
            # Custom color list
            n = len(palette_name)
            try:
                import numpy as np
                scale_points = np.linspace(0, 1, n)
                return [(point, color) for point, color in zip(scale_points, palette_name)]
            except ImportError:
                # Simple fallback without numpy
                scale_points = [i / (n-1) if n > 1 else 0 for i in range(n)]
                return [(point, color) for point, color in zip(scale_points, palette_name)]
    
    def get_cluster_colors(self, n_clusters):
        """Generate distinct colors for clustering visualization."""
        if n_clusters <= len(self.colors["primary_palette"]):
            return self.colors["primary_palette"][:n_clusters]
        else:
            # Generate more colors
            if HAS_MATPLOTLIB:
                try:
                    cmap = mcolors.get_cmap('tab20')  # Good for many distinct colors
                    return [mcolors.rgb2hex(cmap(i / n_clusters)) for i in range(n_clusters)]
                except:
                    pass
            # Fallback: repeat primary palette
            base_colors = self.colors["primary_palette"]
            return [base_colors[i % len(base_colors)] for i in range(n_clusters)]
    
    def get_plot_config(self, plot_type):
        """Get configuration for a specific plot type."""
        if plot_type in self.plot_types:
            return self.plot_types[plot_type].copy()
        else:
            # Return default configuration if plot type not found
            return self.plot_types["scatter_plots"].copy()
    
    def update_plot_config(self, plot_type, config):
        """Update configuration for a specific plot type."""
        if plot_type in self.plot_types:
            self.plot_types[plot_type].update(config)
        else:
            raise ValueError("Plot type '{}' not found.".format(plot_type))
    
    def list_plot_types(self):
        """List all available plot types."""
        return list(self.plot_types.keys())
    
    def to_dict(self):
        """Convert theme to dictionary for API serialization."""
        return {
            "theme_name": self.theme_name,
            "global_settings": self.global_settings,
            "plot_types": self.plot_types,
            # Legacy compatibility
            "colors": self.colors,
            "fonts": self.fonts,
            "layout": self.layout,
            "markers": self.markers,
            "accessibility": self.accessibility
        }
    
    @classmethod
    def from_dict(cls, theme_dict):
        """Create theme from dictionary."""
        theme = cls(theme_dict.get("theme_name", "custom"))
        
        # Update plot-specific configurations
        if "global_settings" in theme_dict:
            theme.global_settings.update(theme_dict["global_settings"])
        if "plot_types" in theme_dict:
            theme.plot_types.update(theme_dict["plot_types"])
        
        # Legacy compatibility
        theme.colors.update(theme_dict.get("colors", {}))
        theme.fonts.update(theme_dict.get("fonts", {}))
        theme.layout.update(theme_dict.get("layout", {}))
        theme.markers.update(theme_dict.get("markers", {}))
        theme.accessibility.update(theme_dict.get("accessibility", {}))
        theme.apply_accessibility_options()
        return theme

class ThemeManager:
    """Manages multiple plot themes and provides theme selection functionality."""
    
    def __init__(self):
        self.themes = {}
        self.current_theme = "default"
        # Use absolute path for theme persistence
        import os
        self.theme_persistence_file = os.path.join(os.path.dirname(__file__), "current_theme.json")
        self._setup_predefined_themes()
        self._load_current_theme()
    
    def _setup_predefined_themes(self):
        """Setup predefined themes for different use cases."""
        
        # Default scientific theme
        default_theme = PlotTheme("default")
        # Use per-plot show_grid defaults (set in plot_types above)
        self.themes["default"] = default_theme
        
        # Dark theme
        dark_theme = PlotTheme("dark")
        # Configure as a light mode: white background, black text
        dark_theme.global_settings.update({
            "background_color": "#ffffff",
            "text_color": "#000000",
            "font_family": "Arial, sans-serif"
        })
        
        # Update all plot types for dark theme
        for plot_type in dark_theme.plot_types:
            dark_theme.plot_types[plot_type].update({
                "background_color": "#ffffff",
                "grid_color": "#e5e5e5",
                "template": "plotly_white"
            })
        
        # Specific elbow plot colors for dark theme
        dark_theme.plot_types["elbow_plots"].update({
            "base_color": "#1f77b4",
            "highlight_color": "#ff7f0e",
            "axis_color": "black",
            "background_color": "#ffffff"
        })
        
        # Specific UMAP discrete colors for dark theme (purple, pink, teal, brown palette)
        dark_theme.plot_types["umap_plots"].update({
            "colors": ["#8b5a96", "#d1729b", "#7a9e9f", "#b8860b", "#9b59b6",
                      "#af7ac5", "#48c9b0", "#cd853f", "#8e44ad", "#5dade2",
                      "#bb8fce", "#85c1e9", "#f8c471", "#d7bde2", "#a9cce3",
                      "#d2b4de", "#76d7c4", "#f4d03f", "#e8daef", "#abebc6"]
        })
        
        # Light (UI 'Light') theme color palettes (using purple, pink, teal, and brown tones)
        dark_violin_colors = [
            "#8b5a96", "#d1729b", "#7a9e9f", "#b8860b", "#9b59b6",
            "#af7ac5", "#48c9b0", "#cd853f", "#8e44ad", "#5dade2",
            "#bb8fce", "#85c1e9", "#f8c471", "#d7bde2", "#a9cce3",
            "#d2b4de", "#76d7c4", "#f4d03f", "#e8daef", "#abebc6"
        ]
        dark_scatter_colors = dark_violin_colors[:]
        dark_theme.plot_types["violin_plots"]["colors"] = dark_violin_colors
        dark_theme.plot_types["scatter_plots"]["colors"] = dark_scatter_colors
        dark_theme.plot_types["scatter_plots"]["primary_color"] = "#8b5a96"
        dark_theme.plot_types["elbow_plots"]["line_color"] = "#8b5a96"
        dark_theme.plot_types["hvg_plots"]["hvg_color"] = "#d1729b"
        
        # Dark theme continuous palettes
        # Keep continuous palettes compatible with light backgrounds
        dark_theme.plot_types["pca_plots"]["continuous_palette"] = "viridis"
        dark_theme.plot_types["umap_plots"]["continuous_palette"] = "viridis"

        # Dark theme (frontend "light") has lower opacity
        dark_theme.plot_types["violin_plots"]["opacity"] = 0.7
        dark_theme.plot_types["scatter_plots"]["opacity"] = 0.6
        dark_theme.plot_types["umap_plots"]["opacity"] = 0.7
        if "pca_plots" in dark_theme.plot_types:
            dark_theme.plot_types["pca_plots"]["opacity"] = 0.7

        self.themes["dark"] = dark_theme
        
        # Colorblind-friendly theme
        colorblind_theme = PlotTheme("colorblind_friendly")
        colorblind_theme.accessibility["colorblind_friendly"] = True
        # Set unique colors before applying accessibility options
        colorblind_violin_colors = ["#0173b2", "#de8f05", "#029e73", "#cc78bc", "#ca9161", 
                                   "#fbafe4", "#949494", "#ece133", "#56b4e9", "#e69f00",
                                   "#009e73", "#f0e442", "#0072b2", "#d55e00", "#cc79a7",
                                   "#000000", "#999999", "#e69f00", "#56b4e9", "#009e73"]
        colorblind_scatter_colors = ["#440154", "#31688e", "#35b779", "#fde725", "#21908c",
                                    "#443983", "#287c8e", "#3e4a89", "#30678d", "#25828e",
                                    "#1e9b8a", "#2bb07f", "#51c56a", "#85d54a", "#c2df23",
                                    "#f8e621", "#fde725", "#c7e020", "#89d548", "#55c667"]
        colorblind_theme.plot_types["violin_plots"]["colors"] = colorblind_violin_colors
        colorblind_theme.plot_types["scatter_plots"]["colors"] = colorblind_scatter_colors
        
        # Colorblind-friendly continuous palettes
        colorblind_theme.plot_types["pca_plots"]["continuous_palette"] = "cividis"  # Colorblind-friendly blue-yellow
        colorblind_theme.plot_types["umap_plots"]["continuous_palette"] = "cividis"  # Same safe palette for both
        
        # Specific elbow plot colors for colorblind-friendly theme
        colorblind_theme.plot_types["elbow_plots"].update({
            "base_color": "#0173b2",      # Safe blue
            "highlight_color": "#de8f05",  # Safe orange for contrast
            "axis_color": "black",         # Keep black axes for consistency
        })
        
        colorblind_theme.apply_accessibility_options()
        # Use per-plot show_grid defaults (no global override)
        self.themes["colorblind_friendly"] = colorblind_theme
        
        # High contrast theme
        high_contrast_theme = PlotTheme("high_contrast")
        high_contrast_theme.accessibility["high_contrast"] = True
        # Set unique colors before applying accessibility options
        high_contrast_violin_colors = ["#ffffff", "#000000", "#ff0000", "#00ff00", "#0000ff",
                                      "#ffff00", "#ff00ff", "#00ffff", "#808080", "#800000",
                                      "#008000", "#000080", "#808000", "#800080", "#008080",
                                      "#c0c0c0", "#404040", "#ff8080", "#80ff80", "#8080ff"]
        high_contrast_scatter_colors = ["#ffffff", "#ff4444", "#44ff44", "#4444ff", "#ffff44", "#ff44ff",
                                       "#44ffff", "#888888", "#cc0000", "#00cc00", "#0000cc",
                                       "#cccc00", "#cc00cc", "#00cccc", "#666666", "#990000",
                                       "#009900", "#000099", "#999900", "#990099", "#009999"]
        high_contrast_theme.plot_types["violin_plots"]["colors"] = high_contrast_violin_colors
        high_contrast_theme.plot_types["scatter_plots"]["colors"] = high_contrast_scatter_colors
        
        # High contrast continuous palettes
        # Use a vivid high-contrast scale for PCA and a diverging one for UMAP
        high_contrast_theme.plot_types["pca_plots"]["continuous_palette"] = "Turbo"   # Vivid, high-contrast
        high_contrast_theme.plot_types["umap_plots"]["continuous_palette"] = "RdBu"   # Red-blue high contrast
        
        # Specific elbow plot colors for high contrast theme
        high_contrast_theme.plot_types["elbow_plots"].update({
            "base_color": "#ffffff",      # White for maximum contrast
            "highlight_color": "#ff0000",  # Bright red for visibility
            "axis_color": "black",         # Keep black axes for consistency
            "background_color": "#000000"  # Black background
        })
        
        # Use per-plot show_grid defaults (no global override)
        high_contrast_theme.apply_accessibility_options()
        self.themes["high_contrast"] = high_contrast_theme
        
        # Publication ready theme
        publication_theme = PlotTheme("publication")
        publication_theme.colors.update({
            "primary_palette": ["#000000", "#666666", "#cccccc"],
            "continuous_palette": "Greys",
        })
        
        # Separate colors for violin and scatter plots in publication theme
        publication_violin_colors = ["#000000", "#333333", "#666666", "#999999", "#cccccc",
                                    "#404040", "#808080", "#a0a0a0", "#c0c0c0", "#e0e0e0",
                                    "#202020", "#505050", "#707070", "#909090", "#b0b0b0",
                                    "#d0d0d0", "#f0f0f0", "#383838", "#585858", "#787878"]
        publication_scatter_colors = ["#1a1a1a", "#4d4d4d", "#737373", "#a6a6a6", "#d9d9d9",
                                     "#2d2d2d", "#5a5a5a", "#868686", "#b3b3b3", "#e6e6e6",
                                     "#0d0d0d", "#404040", "#6d6d6d", "#9a9a9a", "#c7c7c7",
                                     "#f4f4f4", "#262626", "#535353", "#808080", "#adadad"]
        publication_theme.plot_types["violin_plots"]["colors"] = publication_violin_colors
        publication_theme.plot_types["scatter_plots"]["colors"] = publication_scatter_colors
        
        # Publication theme continuous palettes (grayscale for publications)
        publication_theme.plot_types["pca_plots"]["continuous_palette"] = "Greys"  # Professional grayscale
        publication_theme.plot_types["umap_plots"]["continuous_palette"] = "Greys"  # Same professional look
        
        # Specific elbow plot colors for publication theme
        publication_theme.plot_types["elbow_plots"].update({
            "base_color": "#333333",      # Dark gray for professional look
            "highlight_color": "#666666",  # Lighter gray for subtle contrast
            "axis_color": "#000000",       # Black axes for publications
        })
        
        # Specific UMAP discrete colors for publication theme (professional grayscale palette)
        publication_theme.plot_types["umap_plots"].update({
            "colors": ["#333333", "#666666", "#999999", "#4d4d4d", "#737373", 
                      "#a6a6a6", "#1a1a1a", "#808080", "#b3b3b3", "#2d2d2d",
                      "#5a5a5a", "#868686", "#c0c0c0", "#0d0d0d", "#404040",
                      "#6d6d6d", "#9a9a9a", "#d9d9d9", "#262626", "#535353"]
        })
        
        for plot_type in publication_theme.plot_types:
            publication_theme.plot_types[plot_type]["template"] = "plotly_white"
        
        publication_theme.fonts.update({
            "family": "Times New Roman, serif",
            "size": 14,
            "title_size": 18,
        })
        publication_theme.layout.update({
            "width": 1000,
            "height": 800,
            "show_grid": False
        })
        self.themes["publication"] = publication_theme
        
        # Vibrant theme
        vibrant_theme = PlotTheme("vibrant")
        vibrant_theme.colors.update({
            "primary_palette": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57", 
                               "#ff9ff3", "#54a0ff", "#5f27cd", "#00d2d3", "#ff9f43"],
            "continuous_palette": "plasma",
            "background_color": "#f8f9fa",
        })
        # Use per-plot show_grid defaults (no global override)
        
        # Separate color palettes for violin and scatter plots (20-color palette each)
        vibrant_violin_colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57", 
                                "#ff9ff3", "#54a0ff", "#5f27cd", "#00d2d3", "#ff9f43",
                                "#ff6348", "#1dd1a1", "#feca57", "#48dbfb", "#ff9ff3",
                                "#0abde3", "#006ba6", "#f38ba8", "#a8e6cf", "#ffd93d"]
        vibrant_scatter_colors = ["#e55039", "#3c6382", "#f8b500", "#0c2461", "#6c5ce7",
                                 "#a29bfe", "#fd79a8", "#fdcb6e", "#e84393", "#00b894",
                                 "#00cec9", "#6c5ce7", "#a29bfe", "#fd79a8", "#fdcb6e",
                                 "#e17055", "#81ecec", "#74b9ff", "#0984e3", "#fab1a0"]
        vibrant_theme.plot_types["violin_plots"]["colors"] = vibrant_violin_colors
        vibrant_theme.plot_types["scatter_plots"]["colors"] = vibrant_scatter_colors
        
        # Vibrant theme continuous palettes
        vibrant_theme.plot_types["pca_plots"]["continuous_palette"] = "turbo"  # Rainbow-like colorful palette
        vibrant_theme.plot_types["umap_plots"]["continuous_palette"] = "rainbow"  # Bright rainbow colors
        
        # Specific elbow plot colors for vibrant theme
        vibrant_theme.plot_types["elbow_plots"].update({
            "base_color": "#4ecdc4",      # Vibrant teal
            "highlight_color": "#ff6b6b",  # Vibrant coral/red
            "axis_color": "black",         # Keep black axes for consistency
        })
        
        # Specific UMAP discrete colors for vibrant theme (bright, energetic colors)
        vibrant_theme.plot_types["umap_plots"].update({
            "colors": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57", 
                      "#ff9ff3", "#54a0ff", "#5f27cd", "#00d2d3", "#ff9f43",
                      "#ff6348", "#1dd1a1", "#48dbfb", "#a8e6cf", "#ffd93d",
                      "#e55039", "#3c6382", "#f8b500", "#0c2461", "#6c5ce7"]
        })
        
        for plot_type in vibrant_theme.plot_types:
            vibrant_theme.plot_types[plot_type]["template"] = "plotly_white"
        
        self.themes["vibrant"] = vibrant_theme
    
    def get_theme(self, theme_name=None):
        """Get theme by name (or current) ensuring persisted selection is respected."""
        # Always refresh from disk so changes made in another request/worker are seen
        self._load_current_theme()
        if theme_name is None:
            theme_name = self.current_theme
        if theme_name not in self.themes:
            print("Warning: Theme '{}' not found. Using default theme.".format(theme_name))
            theme_name = "default"
            self.current_theme = "default"
        return self.themes[theme_name]
    
    def set_current_theme(self, theme_name):
        """Set the current active theme and persist it."""
        if theme_name in self.themes:
            protected = {"default", "dark", "colorblind_friendly", "high_contrast", "publication", "vibrant"}
            if theme_name in protected:
                # Reinitialize predefined themes to clear any runtime mutations
                self._setup_predefined_themes()
            self.current_theme = theme_name
            self._save_current_theme()
        else:
            raise ValueError("Theme '{}' not found.".format(theme_name))
    
    def add_custom_theme(self, theme):
        """Add a custom theme."""
        self.themes[theme.theme_name] = theme
    
    def remove_theme(self, theme_name):
        """Remove a theme by name if it exists and is not a predefined theme."""
        protected = {"default", "dark", "colorblind_friendly", "high_contrast", "publication", "vibrant"}
        if theme_name in protected:
            raise ValueError(f"Cannot remove predefined theme '{theme_name}'")
        if theme_name not in self.themes:
            raise ValueError(f"Theme '{theme_name}' not found")
        # If removing current theme, fall back to default
        del self.themes[theme_name]
        if self.current_theme == theme_name:
            self.current_theme = "default"
            self._save_current_theme()
    
    def list_themes(self):
        """List all available theme names."""
        return list(self.themes.keys())
    
    def save_theme_to_file(self, theme_name, filepath):
        """Save theme configuration to JSON file."""
        if theme_name not in self.themes:
            raise ValueError("Theme '{}' not found.".format(theme_name))
        
        theme_dict = self.themes[theme_name].to_dict()
        with open(filepath, 'w') as f:
            json.dump(theme_dict, f, indent=2)
    
    def _save_current_theme(self):
        """Persist current theme name and full configuration to disk."""
        try:
            theme_obj = self.themes.get(self.current_theme)
            payload = {"current_theme": self.current_theme}
            # Only persist full config for non-predefined (custom) themes
            protected = {"default", "dark", "colorblind_friendly", "high_contrast", "publication", "vibrant"}
            if theme_obj and getattr(theme_obj, 'theme_name', None) not in protected:
                try:
                    payload["theme_config"] = theme_obj.to_dict()
                except Exception:
                    pass
            with open(self.theme_persistence_file, 'w') as f:
                json.dump(payload, f)
        except Exception as e:
            print("Warning: Could not save current theme: {}".format(e))
    
    def _load_current_theme(self):
        """Load the current theme (and full config if present) from disk."""
        try:
            if os.path.exists(self.theme_persistence_file):
                with open(self.theme_persistence_file, 'r') as f:
                    data = json.load(f)
                theme_name = data.get("current_theme", "default")
                cfg = data.get("theme_config")
                # Only apply persisted config for non-predefined themes to avoid contaminating presets
                protected = {"default", "dark", "colorblind_friendly", "high_contrast", "publication", "vibrant"}
                if cfg and theme_name not in protected:
                    try:
                        loaded = PlotTheme.from_dict(cfg)
                        loaded.theme_name = theme_name
                        self.themes[theme_name] = loaded
                    except Exception:
                        if theme_name not in self.themes:
                            self.themes[theme_name] = PlotTheme(theme_name)
                elif theme_name not in self.themes:
                    self.themes[theme_name] = PlotTheme(theme_name)
                if theme_name in self.themes:
                    self.current_theme = theme_name
        except Exception as e:
            print("Warning: Could not load current theme, using default: {}".format(e))
    
    def load_theme_from_file(self, filepath):
        """Load theme from JSON file."""
        with open(filepath, 'r') as f:
            theme_dict = json.load(f)
        return PlotTheme.from_dict(theme_dict)

# Global theme manager instance
theme_manager = ThemeManager()

def get_current_theme():
    """Get the currently active theme."""
    return theme_manager.get_theme()

def get_plot_theme_config(plot_type):
    """Get current theme configuration for a specific plot type."""
    current_theme = get_current_theme()
    return current_theme.get_plot_config(plot_type)

def set_theme(theme_name):
    """Set the active theme."""
    theme_manager.set_current_theme(theme_name)

def apply_theme_to_figure(fig, theme=None, plot_type="scatter_plots"):
    """Apply plot-specific theme settings to a Plotly figure."""
    if not HAS_PLOTLY:
        return fig  # Return figure unchanged if plotly not available
        
    if theme is None:
        theme = get_current_theme()
    
    # Get plot-specific configuration
    plot_config = theme.get_plot_config(plot_type)
    
    # Update layout with plot-specific theme settings
    # Merge global layout preferences with plot-specific colors
    plot_bg = theme.layout.get("plot_bgcolor", plot_config.get("background_color", "#ffffff"))
    paper_bg = theme.layout.get("paper_bgcolor", plot_config.get("background_color", "#ffffff"))
    fig.update_layout(
        font=dict(
            family=theme.global_settings.get("font_family", "Arial, sans-serif"),
            size=theme.fonts.get("size", 12),
            color=theme.global_settings.get("text_color", "#333333")
        ),
        title_font_size=theme.fonts.get("title_size", plot_config.get("title_size", 16)),
        plot_bgcolor=plot_bg,
        paper_bgcolor=paper_bg,
        width=plot_config.get("width", 800),
        height=plot_config.get("height", 600),
        template=plot_config.get("template", "plotly_white")
    )

    # Apply discrete palette to layout colorway when provided
    try:
        palette = plot_config.get("colors")
        if isinstance(palette, (list, tuple)) and len(palette) > 0:
            fig.update_layout(colorway=list(palette))
    except Exception:
        pass
    
    # Update axes with plot-specific settings
    show_grid = plot_config.get("show_grid", theme.layout.get("show_grid", True))
    grid_color = plot_config.get("grid_color", theme.colors.get("grid_color", "#f0f0f0"))
    fig.update_xaxes(
        title_font_size=theme.fonts.get("axis_title_size", plot_config.get("axis_title_size", 14)),
        tickfont_size=theme.fonts.get("size", 12),
        gridcolor=grid_color,
        gridwidth=1,
        showgrid=show_grid
    )
    
    fig.update_yaxes(
        title_font_size=theme.fonts.get("axis_title_size", plot_config.get("axis_title_size", 14)),
        tickfont_size=theme.fonts.get("size", 12),
        gridcolor=grid_color,
        gridwidth=1,
        showgrid=show_grid
    )
    
    # Update traces based on plot type
    if plot_type in ["scatter_plots", "umap_plots", "pca_plots"]:
        fig.update_traces(
            marker=dict(
                size=plot_config.get("marker_size", 4),
                opacity=plot_config.get("opacity", 0.7),
                line=dict(width=plot_config.get("line_width", 0))
            )
        )
    elif plot_type == "violin_plots":
        fig.update_traces(
            line=dict(width=plot_config.get("line_width", 2)),
            opacity=plot_config.get("opacity", 0.7)
        )
    elif plot_type == "elbow_plots":
        fig.update_traces(
            line=dict(
                width=plot_config.get("line_width", 3),
                color=plot_config.get("line_color", "#1f77b4")
            ),
            marker=dict(
                size=plot_config.get("marker_size", 8),
                color=plot_config.get("marker_color", "#ff7f0e")
            )
        )
    
    return fig

def create_theme_preview(theme):
    """Create a preview of the theme showing key visual elements."""
    import numpy as np
    
    # Create sample data
    np.random.seed(42)
    x = np.random.randn(100)
    y = np.random.randn(100)
    colors = np.random.rand(100)
    
    # Create preview scatter plot
    fig = px.scatter(
        x=x, y=y, 
        color=colors,
        color_continuous_scale=theme.get_plotly_colorscale(),
        title="Theme Preview: {}".format(theme.theme_name)
    )
    
    fig = apply_theme_to_figure(fig, theme, "scatter")
    
    # Convert to HTML
    html_str = fig.to_html(include_plotlyjs='cdn', div_id="theme-preview-{}".format(theme.theme_name))
    
    # Get colors from theme structure
    colors = []
    if hasattr(theme, 'plot_types') and 'violin_plots' in theme.plot_types:
        colors = theme.plot_types['violin_plots'].get('colors', ['#1f77b4', '#ff7f0e', '#2ca02c'])
    elif hasattr(theme, 'colors') and 'primary_palette' in theme.colors:
        colors = theme.colors['primary_palette']
    else:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    background = theme.global_settings.get('background_color', '#ffffff') if hasattr(theme, 'global_settings') else '#ffffff'
    text_color = theme.global_settings.get('text_color', '#333333') if hasattr(theme, 'global_settings') else '#333333'
    
    return {
        "html": html_str,
        "colors": colors[:5],  # Show first 5 colors
        "background": background,
        "text": text_color
    }

# Numpy is imported locally where needed
