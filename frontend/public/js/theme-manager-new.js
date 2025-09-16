/**
 * Theme Management System - Redesigned as Popup
 * Clean popup interface that appears next to page titles
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'default';
        this.availableThemes = {};
        this.customTheme = null;
        this.initialized = false;
        this._justSwitchedTheme = false; // prevent stale slider pushes after switching
        // Track whether user modified global settings (background, grid, fonts)
        this._globalsDirty = false;
        // Cache for preview points to avoid re-randomizing on opacity-only changes
        this._previewCache = {
            scatter: new Map(), // Map<Element, { width, height, points: Array<{cx, cy, colorIndex}> }>
            umap: new Map(),    // Map<Element, { width, height, points: Array<{cx, cy, colorIndex}> }>
            pca: new Map()      // Map<Element, { width, height, points: Array<{cx, cy, colorIndex}> }>
        };
        
        this.init();
    }
    
    async init() {
        if (this.initialized) return;
        
        try {
            console.log('Initializing Theme Manager...');
            
            // Test backend connectivity first
            await this.testBackendConnectivity();
            
            await this.loadAvailableThemes();
            this.setupThemeIcons();
            this.createThemePopup();
            this.initialized = true;
            console.log('Theme Manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Theme Manager:', error);
            // Initialize with fallback even if backend is not available
            this.setupThemeIcons();
            this.createThemePopup();
            this.initialized = true;
            console.log('Theme Manager initialized with fallback');
        }
    }
    
    async testBackendConnectivity() {
        try {
            const response = await fetch('/backend/');
            console.log('Backend connectivity test:', response.status);
        } catch (error) {
            console.error('Backend connectivity test failed:', error);
            throw error;
        }
    }
    
    async loadAvailableThemes() {
        try {
            console.log('Loading available themes from backend...');
            const response = await fetch('/backend/themes/');
            if (!response.ok) {
                console.error(`Failed to load themes: ${response.status}`);
                throw new Error('Failed to load themes');
            }
            
            const data = await response.json();
            console.log('API Response for available themes:', data);
            
            // Handle different response formats
            if (data.themes && Array.isArray(data.themes)) {
                // Convert array to object keyed by theme name
                this.availableThemes = {};
                data.themes.forEach(theme => {
                    const key = theme.name || theme.theme_name || `theme_${Object.keys(this.availableThemes).length}`;
                    this.availableThemes[key] = theme;
                });
            } else if (data.themes && typeof data.themes === 'object') {
                this.availableThemes = data.themes;
            } else {
                // Fallback structure
                this.availableThemes = data;
            }
            
            this.currentTheme = data.current_theme || 'default';
            console.log('Processed themes:', this.availableThemes); // Debug log
        } catch (error) {
            console.error('Error loading themes:', error);
            console.log('Using fallback themes - theme application will still work');
            // Fallback to default themes
            this.availableThemes = {
                'default': { name: 'default', theme_name: 'Default', description: 'Clean scientific theme', preview_colors: ['#1f77b4', '#ff7f0e', '#2ca02c'] },
                'dark': { name: 'dark', theme_name: 'Dark', description: 'Dark mode theme', preview_colors: ['#8b5a96', '#d1729b', '#7a9e9f'] },
                'colorblind_friendly': { name: 'colorblind_friendly', theme_name: 'Colorblind Friendly', description: 'Accessible colors', preview_colors: ['#0173b2', '#de8f05', '#029e73'] },
                'high_contrast': { name: 'high_contrast', theme_name: 'High Contrast', description: 'Maximum contrast with white foreground', preview_colors: ['#ffffff', '#ff0000', '#00ff00'] },
                'publication': { name: 'publication', theme_name: 'Greys', description: 'Grayscale theme for publications', preview_colors: ['#000000', '#666666', '#cccccc'] },
                'vibrant': { name: 'vibrant', theme_name: 'Vibrant', description: 'Bright and colorful', preview_colors: ['#ff6b6b', '#4ecdc4', '#45b7d1'] }
            };
            this.currentTheme = 'default';
        }
    }
    
    setupThemeIcons() {
        // Add palette icons next to all page titles, except inside tutorial and help modals
        const titles = document.querySelectorAll('h2');
        titles.forEach(title => {
            // Skip titles inside the tutorial popup and help modals
            if (title.closest('#exampleModal') || title.closest('#helpModal') || title.closest('.modal_help')) return;
            if (!title.querySelector('.theme-icon')) {
                const icon = document.createElement('i');
                icon.className = 'fas fa-palette theme-icon';
                icon.title = 'Customize plot themes';
                icon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showThemePopup();
                });
                title.style.display = 'flex';
                title.style.alignItems = 'center';
                title.style.gap = '10px';
                title.appendChild(icon);
            }
        });
    }
    
    createThemePopup() {
        // Remove existing popup
        const existing = document.getElementById('theme-popup');
        if (existing) existing.remove();
        
        const popup = document.createElement('div');
        popup.id = 'theme-popup';
        popup.className = 'theme-popup';
        popup.style.display = 'none';
        
        popup.innerHTML = `
            <div class="theme-popup-overlay" id="theme-popup-overlay"></div>
            <div class="theme-popup-content">
                <div class="theme-popup-header">
                    <h3><i class="fas fa-palette"></i> Plot Theme Customization</h3>
                    <div class="theme-tabs">
                        <button class="tab-btn active" data-tab="predefined">Presets</button>
                        <button class="tab-btn" data-tab="plot-specific">By Plot Type</button>
                        <button class="tab-btn" data-tab="global">Global Settings</button>
                    </div>
                    <button class="theme-popup-close" id="close-theme-popup">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="theme-popup-body">
                    <!-- Predefined Themes Tab -->
                    <div class="tab-content active" id="predefined-tab">
                        <div class="theme-section">
                            <h4>📋 Quick Theme Presets</h4>
                            <div class="theme-cards">
                                ${this.renderThemeCards()}
                            </div>
                            
                            <!-- Presets Live Preview -->
                            <div class="preview-section">
                                <div class="preview-container">
                                    <h5><i class="fas fa-eye"></i> Live Preview</h5>
                                    <div class="preview-plots">
                                        <div class="mini-plot" id="preset-preview-scatter">
                                            <div class="plot-title">Scatter Plot Preview</div>
                                            <div class="preview-dots"></div>
                                        </div>
                                        <div class="mini-plot" id="preset-preview-violin">
                                            <div class="plot-title">Violin Plot Preview</div>
                                            <div class="preview-shapes"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Plot-Specific Tab -->
                    <div class="tab-content" id="plot-specific-tab">
                        <div class="theme-section">
                            <h4>🎯 Plot-Specific Customization</h4>
                            <div class="plot-types-container">
                                <div class="plot-type-section" data-plot-type="violin_plots">
                                    <h5><i class="fas fa-chart-area"></i> Violin Plots</h5>
                                    <div class="plot-controls">
                                        <div class="plot-config">
                                            <div class="color-palette-section">
                                                <label>Colors:</label>
                                                <div class="color-palette">
                                                    <input type="color" class="plot-color" data-index="0" value="#1f77b4" title="Color 1">
                                                    <input type="color" class="plot-color" data-index="1" value="#ff7f0e" title="Color 2">
                                                    <input type="color" class="plot-color" data-index="2" value="#2ca02c" title="Color 3">
                                                    <input type="color" class="plot-color" data-index="3" value="#d62728" title="Color 4">
                                                    <button class="add-color-btn" title="Add Color"><i class="fas fa-plus"></i></button>
                                                </div>
                                            </div>
                                            <div class="plot-settings">
                                                <div class="setting-item">
                                                    <label>Opacity:</label>
                                                    <input type="range" class="opacity-slider" min="0.1" max="1" step="0.1" value="0.7">
                                                    <span class="value-display">0.7</span>
                                                </div>
                                                <div class="setting-item">
                                                    <label>Line Width:</label>
                                                    <input type="range" class="line-width-slider" min="1" max="5" step="0.5" value="2">
                                                    <span class="value-display">2</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="plot-preview-pane">
                                            <div class="mini-plot" id="preview-violin">
                                                <div class="plot-title">Violin Preview</div>
                                                <div class="preview-shapes"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="plot-type-section" data-plot-type="scatter_plots">
                                    <h5><i class="fas fa-braille"></i> Scatter Plots</h5>
                                    <div class="plot-controls">
                                        <div class="plot-config">
                                            <div class="color-palette-section">
                                                <label>Colors:</label>
                                                <div class="color-palette">
                                                    <input type="color" class="plot-color" data-index="0" value="#1f77b4" title="Color 1">
                                                    <input type="color" class="plot-color" data-index="1" value="#ff7f0e" title="Color 2">
                                                    <input type="color" class="plot-color" data-index="2" value="#2ca02c" title="Color 3">
                                                    <input type="color" class="plot-color" data-index="3" value="#d62728" title="Color 4">
                                                    <button class="add-color-btn" title="Add Color"><i class="fas fa-plus"></i></button>
                                                </div>
                                            </div>
                                            <div class="plot-settings">
                                                <div class="setting-item">
                                                    <label>Marker Size:</label>
                                                    <input type="range" class="marker-size-slider" min="1" max="10" step="0.5" value="5">
                                                    <span class="value-display">5</span>
                                                </div>
                                                <div class="setting-item">
                                                    <label>Opacity:</label>
                                                    <input type="range" class="opacity-slider" min="0.1" max="1" step="0.1" value="0.6">
                                                    <span class="value-display">0.6</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="plot-preview-pane">
                                            <div class="mini-plot" id="preview-scatter">
                                                <div class="plot-title">Scatter Preview</div>
                                                <div class="preview-dots"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="plot-type-section" data-plot-type="pca_plots">
                                    <h5><i class="fas fa-border-none"></i> PCA Plots</h5>
                                    <div class="plot-controls">
                                        <div class="plot-config">
                                            <div class="color-palette-section">
                                                <label>Colors:</label>
                                                <div class="color-palette">
                                                    <input type="color" class="plot-color" data-index="0" value="#1f77b4" title="Color 1">
                                                    <input type="color" class="plot-color" data-index="1" value="#ff7f0e" title="Color 2">
                                                    <input type="color" class="plot-color" data-index="2" value="#2ca02c" title="Color 3">
                                                    <input type="color" class="plot-color" data-index="3" value="#d62728" title="Color 4">
                                                    <input type="color" class="plot-color" data-index="4" value="#9467bd" title="Color 5">
                                                    <input type="color" class="plot-color" data-index="5" value="#8c564b" title="Color 6">
                                                    <input type="color" class="plot-color" data-index="6" value="#e377c2" title="Color 7">
                                                    <button class="add-color-btn" title="Add Color"><i class="fas fa-plus"></i></button>
                                                </div>
                                            </div>
                                            <div class="plot-settings">
                                                <div class="setting-item">
                                                    <label>Point Size:</label>
                                                    <input type="range" class="marker-size-slider" min="1" max="8" step="0.5" value="3">
                                                    <span class="value-display">3</span>
                                                </div>
                                                <div class="setting-item">
                                                    <label>Opacity:</label>
                                                    <input type="range" class="opacity-slider" min="0.1" max="1" step="0.1" value="0.7">
                                                    <span class="value-display">0.7</span>
                                                </div>
                                                <div class="setting-item">
                                                    <label>Line Width:</label>
                                                    <input type="range" class="line-width-slider" min="0" max="5" step="0.5" value="0">
                                                    <span class="value-display">0</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="plot-preview-pane">
                                            <div class="mini-plot" id="preview-pca">
                                                <div class="plot-title">PCA Preview</div>
                                                <div class="preview-dots"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="plot-type-section" data-plot-type="umap_plots">
                                    <h5><i class="fas fa-project-diagram"></i> UMAP Plots</h5>
                                    <div class="plot-controls">
                                        <div class="plot-config">
                                            <div class="color-palette-section">
                                                <label>Colors:</label>
                                                <div class="color-palette">
                                                    <input type="color" class="plot-color" data-index="0" value="#1f77b4" title="Color 1">
                                                    <input type="color" class="plot-color" data-index="1" value="#ff7f0e" title="Color 2">
                                                    <input type="color" class="plot-color" data-index="2" value="#2ca02c" title="Color 3">
                                                    <input type="color" class="plot-color" data-index="3" value="#d62728" title="Color 4">
                                                    <input type="color" class="plot-color" data-index="4" value="#9467bd" title="Color 5">
                                                    <input type="color" class="plot-color" data-index="5" value="#8c564b" title="Color 6">
                                                    <button class="add-color-btn" title="Add Color"><i class="fas fa-plus"></i></button>
                                                </div>
                                            </div>
                                            <div class="plot-settings">
                                                <div class="setting-item">
                                                    <label>Point Size:</label>
                                                    <input type="range" class="marker-size-slider" min="1" max="8" step="0.5" value="3">
                                                    <span class="value-display">3</span>
                                                </div>
                                                <div class="setting-item">
                                                    <label>Opacity:</label>
                                                    <input type="range" class="opacity-slider" min="0.1" max="1" step="0.1" value="0.8">
                                                    <span class="value-display">0.8</span>
                                                </div>
                                                <div class="setting-item">
                                                    <label>Line Width:</label>
                                                    <input type="range" class="line-width-slider" min="0" max="5" step="0.5" value="0">
                                                    <span class="value-display">0</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="plot-preview-pane">
                                            <div class="mini-plot" id="preview-umap">
                                                <div class="plot-title">UMAP Preview</div>
                                                <div class="preview-dots"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="plot-type-section" data-plot-type="heatmaps">
                                    <h5><i class="fas fa-th"></i> Heatmaps</h5>
                                    <div class="plot-controls">
                                        <div class="plot-config">
                                            <div class="color-palette-section">
                                                <label>Colorscale:</label>
                                                <select class="colorscale-select">
                                                    <option value="viridis">Viridis</option>
                                                    <option value="plasma">Plasma</option>
                                                    <option value="cividis">Cividis</option>
                                                    <option value="Blues">Blues</option>
                                                    <option value="Reds">Reds</option>
                                                    <option value="RdBu">Red-Blue</option>
                                                </select>
                                            </div>
                                            <div class="plot-settings">
                                                <div class="setting-item">
                                                    <label>Show Scale:</label>
                                                    <input type="checkbox" class="show-colorbar" checked>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="plot-preview-pane">
                                            <div class="mini-plot" id="preview-heatmap">
                                                <div class="plot-title">Heatmap Preview</div>
                                                <div class="preview-grid"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Global Settings Tab -->
                    <div class="tab-content" id="global-tab">
                        <div class="theme-section">
                            <h4>🌐 Global Plot Settings</h4>
                            
                            <div class="setting-group">
                                <h5>Background & Layout</h5>
                                <div class="setting-item">
                                    <label>Plot Background:</label>
                                    <input type="color" id="plot-background" value="#ffffff" class="color-input">
                                </div>
                                <div class="setting-item">
                                    <label>Grid Color:</label>
                                    <input type="color" id="grid-color" value="#e5e5e5" class="color-input">
                                </div>
                                <div class="setting-item">
                                    <label>Show Grid:</label>
                                    <input type="checkbox" id="show-grid">
                                </div>
                            </div>
                            
                            <div class="setting-group">
                                <h5>Typography</h5>
                                <div class="setting-item">
                                    <label>Font Family:</label>
                                    <select id="plot-font-family" class="font-select">
                                        <option value="Arial, sans-serif">Arial</option>
                                        <option value="Times New Roman, serif">Times New Roman</option>
                                        <option value="Helvetica, sans-serif">Helvetica</option>
                                        <option value="Georgia, serif">Georgia</option>
                                    </select>
                                </div>
                                <div class="setting-item">
                                    <label>Title Size:</label>
                                    <input type="range" id="title-size" min="10" max="20" value="14" class="size-slider">
                                    <span class="value-display">14px</span>
                                </div>
                                <div class="setting-item">
                                    <label>Axis Label Size:</label>
                                    <input type="range" id="axis-size" min="8" max="24" value="12" class="size-slider">
                                    <span class="value-display">12px</span>
                                </div>
                                <div class="setting-item">
                                    <label>Font Color:</label>
                                    <input type="color" id="plot-font-color" value="#333333" class="color-input">
                                </div>
                            </div>
                            
                            <!-- Accessibility controls removed per requirements -->
                            <div class="plot-preview-pane" style="margin-top: 8px;">
                                <div class="mini-plot" id="preview-global">
                                    <div class="plot-title">Global Preview</div>
                                    <div class="preview-dots"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    
                    <!-- Actions -->
                    <div class="theme-actions">
                        <button class="theme-btn apply-btn" id="apply-theme">
                            <i class="fas fa-check"></i> Apply Theme
                        </button>
                        <button class="theme-btn save-btn" id="save-theme">
                            <i class="fas fa-save"></i> Save Custom
                        </button>
                        <button class="theme-btn reset-btn" id="reset-theme">
                            <i class="fas fa-undo"></i> Reset
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        this.setupEventListeners();
    }
    
    renderThemeCards() {
        const protectedNames = new Set(['default','dark','colorblind_friendly','high_contrast','publication','vibrant']);
        return Object.entries(this.availableThemes).map(([key, theme]) => {
            const isActive = key === this.currentTheme ? 'active' : '';
            
            // ALWAYS use the specific theme colors from getThemeColors to ensure variety
            const colors = this.getThemeColors(key);
            // Override display names/descriptions for specific themes regardless of backend payload
            let themeName = theme.name || theme.theme_name || key;
            let themeDescription = theme.description || 'Theme for plot customization';
            // UI-only display name mapping (keys remain unchanged for backend calls)
            if (key === 'dark') { themeName = 'Light'; themeDescription = 'Light mode theme'; }
            if (key === 'default') { themeName = 'Default'; }
            if (key === 'colorblind_friendly') { themeName = 'Colorblind'; }
            if (key === 'vibrant') { themeName = 'Vibrant'; }
            if (key === 'publication') { themeName = 'Greys'; themeDescription = 'Grayscale theme for publications'; }
            if (key === 'high_contrast') { themeName = 'High Contrast'; }
            
            console.log(`Rendering theme card for "${key}" with colors:`, colors); // Debug
            
            return `
                <div class="theme-card ${isActive}" data-theme="${key}">
                    <div class="theme-name">${themeName}</div>
                    ${protectedNames.has(key) ? '' : '<button class="theme-delete" title="Delete" data-theme="'+key+'"><i class="fas fa-trash"></i></button>'}
                    <div class="theme-colors-preview">
                        ${colors.slice(0, 4).map(color => `<div class="color-dot" style="background-color: ${color}"></div>`).join('')}
                    </div>
                    <div class="theme-description">${themeDescription}</div>
                </div>
            `;
        }).join('');
    }
    
    getThemeColors(themeKey) {
        const colorSets = {
            'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],        // Blue, Orange, Green, Red
            // Light theme palette (backend key 'dark')
            'dark': ['#8b5a96', '#d1729b', '#7a9e9f', '#b8860b'],           
            'colorblind_friendly': ['#0173b2', '#de8f05', '#029e73', '#cc78bc'], // Blue, Orange, Teal, Pink
            // Start with white (no black) for UI palette dots
            'high_contrast': ['#ffffff', '#ff0000', '#00ff00', '#0000ff', '#ff00ff'],
            'publication': ['#000000', '#4a4a4a', '#7a7a7a', '#aaaaaa'],    // Greyscale
            'vibrant': ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']         // Coral, Teal, Blue, Mint
        };
        
        const colors = colorSets[themeKey] || ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'];
        console.log(`Theme "${themeKey}" colors:`, colors);
        return colors;
    }
    
    setupEventListeners() {
        // Close popup
        document.getElementById('close-theme-popup')?.addEventListener('click', () => this.hideThemePopup());
        document.getElementById('theme-popup-overlay')?.addEventListener('click', () => this.hideThemePopup());
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Theme cards
        document.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('click', () => this.selectTheme(card.dataset.theme));
        });
        // Delete buttons (event delegation fallback)
        document.addEventListener('click', async (e) => {
            const del = e.target.closest('.theme-delete');
            if (del) {
                e.stopPropagation();
                const name = del.dataset.theme;
                if (!name) return;
                if (!confirm(`Delete theme "${name}"?`)) return;
                try {
                    const res = await fetch(`/backend/themes/${encodeURIComponent(name)}/`, { method: 'DELETE' });
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(txt || res.status);
                    }
                    // Refresh available themes list
                    await this.loadAvailableThemes();
                    const cards = document.querySelector('.theme-cards');
                    if (cards) {
                        cards.innerHTML = this.renderThemeCards();
                        cards.querySelectorAll('.theme-card').forEach(card => {
                            card.addEventListener('click', () => this.selectTheme(card.dataset.theme));
                        });
                    }
                    this.showMessage(`Theme "${name}" deleted`, 'success');
                } catch (err) {
                    console.error('Failed to delete theme:', err);
                    this.showMessage('Failed to delete theme', 'error');
                }
            }
        });
        
        // Plot-specific color pickers
        document.querySelectorAll('.plot-color').forEach(input => {
            input.addEventListener('change', (e) => this.updatePlotTypeColors(e));
        });
        
        // Add color buttons
        document.querySelectorAll('.add-color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.addColorToPalette(e));
        });
        
        // Range sliders with live updates
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.addEventListener('input', (e) => this.updateSliderDisplay(e));
            slider.addEventListener('change', (e) => this.updatePlotSettings(e));
        });
        
        // Global color inputs
        document.querySelectorAll('.color-input').forEach(input => {
            input.addEventListener('change', () => this.updateGlobalSettings());
            // Live update while dragging color pickers
            input.addEventListener('input', () => this.updateGlobalSettings());
        });

        // Font controls
        document.getElementById('plot-font-family')?.addEventListener('change', () => this.updateGlobalSettings());

        // Global-only controls: mark globals dirty when changed
        const markGlobalsDirty = () => { this._globalsDirty = true; };
        ['plot-background','grid-color','plot-font-family','title-size','axis-size','plot-font-color','show-grid']
            .forEach(id => document.getElementById(id)?.addEventListener('change', markGlobalsDirty));

        // Live preview for global sliders and toggles
        ;['title-size','axis-size','plot-background','grid-color','plot-font-color']
            .forEach(id => document.getElementById(id)?.addEventListener('input', () => this.updateGlobalSettings()));
        document.getElementById('show-grid')?.addEventListener('change', () => this.updateGlobalSettings());
        
        // Accessibility UI removed; skip handlers
        
        // Colorscale selects
        document.querySelectorAll('.colorscale-select').forEach(select => {
            select.addEventListener('change', (e) => this.updatePlotSettings(e));
        });
        
        // Action buttons
        document.getElementById('apply-theme')?.addEventListener('click', () => this.applyTheme());
        document.getElementById('save-theme')?.addEventListener('click', () => this.saveCustomTheme());
        document.getElementById('reset-theme')?.addEventListener('click', () => this.resetTheme());

        // Initialize actions visibility for default active tab
        this.updateActionButtonsVisibility();
    }
    
    switchTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        document.querySelector(`.tab-btn[data-tab="${tabName}"]`)?.classList.add('active');
        document.getElementById(`${tabName}-tab`)?.classList.add('active');

        // Update actions visibility (hide Save on Presets)
        this.updateActionButtonsVisibility();
    }

    updateActionButtonsVisibility() {
        const activeTabBtn = document.querySelector('.tab-btn.active');
        const activeTab = activeTabBtn ? activeTabBtn.dataset.tab : 'predefined';
        const saveBtn = document.getElementById('save-theme');
        if (saveBtn) {
            if (activeTab === 'predefined') {
                saveBtn.style.display = 'none';
            } else {
                saveBtn.style.display = '';
            }
        }
    }
    
    updateSliderDisplay(event) {
        const slider = event.target;
        const valueDisplay = slider.parentElement.querySelector('.value-display');
        if (valueDisplay) {
            const unit = slider.className.includes('size') ? 'px' : '';
            valueDisplay.textContent = slider.value + unit;
        }
        
        // Re-render only the affected preview for smoother UX
        const section = slider.closest('.plot-type-section');
        if (section && section.dataset.plotType) {
            this.updateLivePreview(section.dataset.plotType);
        }
    }
    
    updatePlotTypeColors(event) {
        const colorInput = event.target;
        const plotSection = colorInput.closest('.plot-type-section');
        const plotType = plotSection.dataset.plotType;
        
        // Collect all colors for this plot type
        const colors = Array.from(plotSection.querySelectorAll('.plot-color')).map(input => input.value);
        
        // Mark explicit color change so we only send colors when user edits them
        try { colorInput.dataset.changed = 'true'; } catch (e) {}
        try { plotSection.dataset.colorsChanged = 'true'; } catch (e) {}

        console.log(`Updated ${plotType} colors:`, colors);
        // Update only the section's preview
        this.updateLivePreview(plotType);
        this.showMessage(`Updated ${plotType.replace('_', ' ')} colors`, 'success');
    }
    
    addColorToPalette(event) {
        const button = event.target.closest('.add-color-btn');
        const colorPalette = button.parentElement;
        
        // Create new color input
        const colorCount = colorPalette.querySelectorAll('.plot-color').length;
        const newColorInput = document.createElement('input');
        newColorInput.type = 'color';
        newColorInput.className = 'plot-color';
        newColorInput.dataset.index = colorCount;
        newColorInput.value = this.generateNewColor(colorCount);
        newColorInput.title = `Color ${colorCount + 1}`;
        
        // Add event listener
        newColorInput.addEventListener('change', (e) => this.updatePlotTypeColors(e));
        
        // Insert before the add button
        colorPalette.insertBefore(newColorInput, button);
        
        // Update colors immediately
        this.updatePlotTypeColors({ target: newColorInput });
    }
    
    generateNewColor(index) {
        const colors = ['#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];
        return colors[index % colors.length];
    }
    
    updatePlotSettings(event) {
        const control = event.target;
        const plotSection = control.closest('.plot-type-section');
        
        if (plotSection) {
            const plotType = plotSection.dataset.plotType;
            console.log(`Updated ${plotType} settings`);
            // Re-render only the affected preview to avoid global/layout thrash
            this.updateLivePreview(plotType);
        }
        // Mark this specific control and its section as changed so we only send deltas
        try { control.dataset.changed = 'true'; } catch (e) {}
        try { plotSection && (plotSection.dataset.settingsChanged = 'true'); } catch (e) {}
        
        this.showMessage('Plot settings updated', 'info');
    }
    
    updateGlobalSettings() {
        console.log('Updated global settings');
        // mark that globals were changed so we only push when needed
        this._globalsDirty = true;
        // Global updates re-render all previews within the By Plot Type tab
        this.updateLivePreview('globals');
        this.showMessage('Global settings updated', 'info');
    }
    
    // Accessibility UI removed per requirements
    
    updateLivePreview(scope = 'all') {
        // scope: 'all' (everything), 'globals' (all plot previews),
        // or a specific plot type key: 'scatter_plots' | 'violin_plots' | 'umap_plots' | 'heatmap_plots' | 'pca_plots'
        const includePresets = scope === 'all';
        const renderByType = (type) => {
            switch (type) {
                case 'scatter_plots': this.renderPreviewScatter(includePresets); break;
                case 'violin_plots': this.renderPreviewViolin(includePresets); break;
                case 'umap_plots': this.renderPreviewUMAP(includePresets); break;
                case 'heatmap_plots': this.renderPreviewHeatmap(includePresets); break;
                case 'pca_plots': this.renderPreviewPCA(includePresets); break;
                default:
                    this.renderPreviewScatter(includePresets);
                    this.renderPreviewUMAP(includePresets);
                    this.renderPreviewPCA(includePresets);
                    this.renderPreviewViolin(includePresets);
                    this.renderPreviewHeatmap(includePresets);
                    this.renderPreviewGlobal();
            }
        };

        if (scope === 'globals') {
            // Global settings affect all plot previews (but not necessarily preset cards)
            this.renderPreviewScatter(false);
            this.renderPreviewUMAP(false);
            this.renderPreviewPCA(false);
            this.renderPreviewViolin(false);
            this.renderPreviewHeatmap(false);
            this.renderPreviewGlobal();
        } else if (scope && scope !== 'all') {
            renderByType(scope);
        } else {
            renderByType('all');
        }
    }

    renderPreviewGlobal() {
        const container = document.querySelector('#preview-global .preview-dots');
        const previewRoot = document.getElementById('preview-global');
        if (!container || !previewRoot) return;

        // Hard-lock preview box dimensions to avoid layout expansion
        try {
            previewRoot.style.height = '140px';
            previewRoot.style.maxHeight = '140px';
            container.style.height = '90px';
            container.style.maxHeight = '90px';
        } catch (_) {}

        const bg = document.getElementById('plot-background')?.value || '#ffffff';
        const gridColor = document.getElementById('grid-color')?.value || '#e5e5e5';
        const showGrid = !!document.getElementById('show-grid')?.checked;
        const fontFamily = document.getElementById('plot-font-family')?.value || 'Arial, sans-serif';
        const titleSize = parseInt(document.getElementById('title-size')?.value || '14', 10);
        const axisSize = parseInt(document.getElementById('axis-size')?.value || '12', 10);

        // Apply background and title font
        previewRoot.style.backgroundColor = bg;
        const titleEl = previewRoot.querySelector('.plot-title');
        if (titleEl) {
            titleEl.style.fontFamily = fontFamily;
            titleEl.style.fontSize = `${titleSize}px`;
            const textColor = document.getElementById('plot-font-color')?.value || '#333333';
            titleEl.style.color = textColor;
        }

        // Rebuild simple grid
        container.innerHTML = '';
        const width = container.clientWidth || container.offsetWidth || 200;
        const height = container.clientHeight || 90;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        // Use explicit pixel dimensions to prevent percentage-height induced stretching
        svg.setAttribute('width', String(width));
        svg.setAttribute('height', String(height));
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.style.display = 'block';

        if (showGrid) {
            const step = 20;
            for (let x = step; x < width; x += step) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', x.toString());
                line.setAttribute('y1', '0');
                line.setAttribute('x2', x.toString());
                line.setAttribute('y2', height.toString());
                line.setAttribute('stroke', gridColor);
                line.setAttribute('stroke-width', '1');
                line.setAttribute('opacity', '0.6');
                svg.appendChild(line);
            }
            for (let y = step; y < height; y += step) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', '0');
                line.setAttribute('y1', y.toString());
                line.setAttribute('x2', width.toString());
                line.setAttribute('y2', y.toString());
                line.setAttribute('stroke', gridColor);
                line.setAttribute('stroke-width', '1');
                line.setAttribute('opacity', '0.6');
                svg.appendChild(line);
            }
        }

        // Axis label samples
        const xLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        xLabel.textContent = 'X';
        xLabel.setAttribute('x', (width - 12).toString());
        xLabel.setAttribute('y', (height - 6).toString());
        xLabel.setAttribute('fill', (document.getElementById('plot-font-color')?.value || '#444'));
        xLabel.setAttribute('font-size', `${axisSize}px`);
        xLabel.setAttribute('font-family', fontFamily);
        svg.appendChild(xLabel);

        const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        yLabel.textContent = 'Y';
        yLabel.setAttribute('x', '6');
        yLabel.setAttribute('y', '14');
        yLabel.setAttribute('fill', (document.getElementById('plot-font-color')?.value || '#444'));
        yLabel.setAttribute('font-size', `${axisSize}px`);
        yLabel.setAttribute('font-family', fontFamily);
        svg.appendChild(yLabel);

        container.appendChild(svg);
    }
    
    renderPreviewScatter(includePresets = false) {
        const selector = includePresets
            ? '#preview-scatter .preview-dots, #preset-preview-scatter .preview-dots'
            : '#preview-scatter .preview-dots';
        const containers = Array.from(document.querySelectorAll(selector));
        if (!containers.length) return;

        // Read current settings from the scatter plot section
        const scatterSection = document.querySelector('[data-plot-type="scatter_plots"]');
        const colors = Array.from(scatterSection?.querySelectorAll('.plot-color') || []).map(input => input.value);
        const opacityVal = parseFloat(scatterSection?.querySelector('.opacity-slider')?.value || '0.8');
        const markerSize = parseFloat(scatterSection?.querySelector('.marker-size-slider')?.value || '3');

        // Fallback colors
        const palette = colors.length ? colors : ['#1f77b4', '#ff7f0e', '#2ca02c'];

        containers.forEach(container => {
            // Adjust preview background for high contrast theme
            const mini = container.closest('.mini-plot');
            if (mini) {
                mini.style.backgroundColor = (this.currentTheme === 'high_contrast') ? '#000000' : '';
            }

            // Clear and create an SVG to draw into (for crisp shapes)
            container.innerHTML = '';
            const width = container.clientWidth || container.offsetWidth || 200;
            const height = container.clientHeight || 80;

            // Get or create cached points for this container
            const cacheMap = this._previewCache.scatter;
            let cached = cacheMap.get(container);
            const nPoints = 45;
            if (!cached || cached.width !== width || cached.height !== height || !Array.isArray(cached.points) || cached.points.length !== nPoints) {
                const points = [];
                for (let i = 0; i < nPoints; i++) {
                    const cx = 8 + Math.random() * (width - 16);
                    const cy = 8 + Math.random() * (height - 16);
                    points.push({ cx, cy, colorIndex: i });
                }
                cached = { width, height, points };
                cacheMap.set(container, cached);
            }

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '100%');
            svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

            // Optional subtle frame/grid for context
            const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            border.setAttribute('x', '0.5');
            border.setAttribute('y', '0.5');
            border.setAttribute('width', (width - 1).toString());
            border.setAttribute('height', (height - 1).toString());
            border.setAttribute('fill', 'none');
            border.setAttribute('stroke', this.currentTheme === 'high_contrast' ? '#999999' : '#e5e7eb');
            border.setAttribute('stroke-width', '1');
            svg.appendChild(border);

            // Map slider value to a sensible radius in px
            const r = Math.max(1.5, Math.min(8, markerSize)) * 1.2; // default ~3.6px at value=3

            // Draw from cached positions to keep layout stable
            cached.points.forEach((p, i) => {
                const color = palette[p.colorIndex % palette.length];
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', p.cx.toString());
                circle.setAttribute('cy', p.cy.toString());
                circle.setAttribute('r', r.toString());
                circle.setAttribute('fill', color);
                circle.setAttribute('fill-opacity', opacityVal.toString());
                svg.appendChild(circle);
            });

            container.appendChild(svg);
        });
    }

    renderPreviewUMAP(includePresets = false) {
        // Currently only a single UMAP preview exists in By Plot Type
        const container = document.querySelector('#preview-umap .preview-dots');
        if (!container) return;

        const umapSection = document.querySelector('[data-plot-type="umap_plots"]');
        const colors = Array.from(umapSection?.querySelectorAll('.plot-color') || []).map(input => input.value);
        const opacityVal = parseFloat(umapSection?.querySelector('.opacity-slider')?.value || '0.8');
        const lineWidthVal = parseFloat(umapSection?.querySelector('.line-width-slider')?.value || '0');
        const markerSize = parseFloat(umapSection?.querySelector('.marker-size-slider')?.value || '3');
        const palette = colors.length ? colors : ['#1f77b4', '#ff7f0e', '#2ca02c'];

        container.innerHTML = '';
        const width = container.clientWidth || container.offsetWidth || 200;
        const height = container.clientHeight || 80;

        // Get or create cached points for UMAP preview
        const cacheMap = this._previewCache.umap;
        let cached = cacheMap.get(container);
        if (!cached || cached.width !== width || cached.height !== height || !Array.isArray(cached.points)) {
            const points = [];
            // Four clusters (simple approximation of UMAP structure)
            const clusters = [
                { cx: width * 0.35, cy: height * 0.55, sigma: Math.min(width, height) * 0.09, colorIndex: 0 },
                { cx: width * 0.65, cy: height * 0.40, sigma: Math.min(width, height) * 0.08, colorIndex: 1 },
                { cx: width * 0.20, cy: height * 0.25, sigma: Math.min(width, height) * 0.07, colorIndex: 2 },
                { cx: width * 0.75, cy: height * 0.70, sigma: Math.min(width, height) * 0.06, colorIndex: 3 }
            ];
            const nPer = 18;
            clusters.forEach((c) => {
                for (let i = 0; i < nPer; i++) {
                    // Box-Muller transform for Gaussian spread
                    const u1 = Math.random();
                    const u2 = Math.random();
                    const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
                    const z1 = Math.sqrt(-2.0 * Math.log(u1)) * Math.sin(2 * Math.PI * u2);
                    const x = Math.max(6, Math.min(width - 6, c.cx + z0 * c.sigma));
                    const y = Math.max(6, Math.min(height - 6, c.cy + z1 * c.sigma));
                    points.push({ cx: x, cy: y, colorIndex: c.colorIndex });
                }
            });
            cached = { width, height, points };
            cacheMap.set(container, cached);
        }

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        border.setAttribute('x', '0.5');
        border.setAttribute('y', '0.5');
        border.setAttribute('width', (width - 1).toString());
        border.setAttribute('height', (height - 1).toString());
        border.setAttribute('fill', 'none');
        border.setAttribute('stroke', '#e5e7eb');
        border.setAttribute('stroke-width', '1');
        svg.appendChild(border);

        const r = Math.max(1.5, Math.min(8, markerSize)) * 1.1;
        cached.points.forEach(p => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', p.cx.toString());
            circle.setAttribute('cy', p.cy.toString());
            circle.setAttribute('r', r.toString());
            circle.setAttribute('fill', palette[p.colorIndex % palette.length]);
            circle.setAttribute('fill-opacity', opacityVal.toString());
            const strokeColor = (this.currentTheme === 'high_contrast') ? '#ffffff' : '#000000';
            circle.setAttribute('stroke', strokeColor);
            circle.setAttribute('stroke-width', lineWidthVal.toString());
            svg.appendChild(circle);
        });

        container.appendChild(svg);
    }

    renderPreviewHeatmap(includePresets = false) {
        const container = document.querySelector('#preview-heatmap .preview-grid');
        if (!container) return;

        const heatmapSection = document.querySelector('[data-plot-type="heatmaps"]');
        const colorscaleName = heatmapSection?.querySelector('.colorscale-select')?.value || 'viridis';
        const showColorbar = !!heatmapSection?.querySelector('.show-colorbar')?.checked;
        const scale = this.getDiscreteColorscale(colorscaleName);

        container.innerHTML = '';
        const width = container.clientWidth || container.offsetWidth || 200;
        const height = container.clientHeight || 80;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        border.setAttribute('x', '0.5');
        border.setAttribute('y', '0.5');
        border.setAttribute('width', (width - 1).toString());
        border.setAttribute('height', (height - 1).toString());
        border.setAttribute('fill', 'none');
        border.setAttribute('stroke', '#e5e7eb');
        border.setAttribute('stroke-width', '1');
        svg.appendChild(border);

        // Heatmap grid 6x6
        const cols = 6, rows = 6;
        const pad = 6;
        const colorbarWidth = showColorbar ? 10 : 0;
        const plotW = width - pad * 2 - colorbarWidth - (showColorbar ? 6 : 0);
        const plotH = height - pad * 2;
        const cw = plotW / cols;
        const ch = plotH / rows;

        // Simple gradient data
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const t = (r * cols + c) / (rows * cols - 1);
                const color = scale[Math.floor(t * (scale.length - 1))];
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', (pad + c * cw).toFixed(2));
                rect.setAttribute('y', (pad + r * ch).toFixed(2));
                rect.setAttribute('width', Math.max(1, cw - 0.5).toFixed(2));
                rect.setAttribute('height', Math.max(1, ch - 0.5).toFixed(2));
                rect.setAttribute('fill', color);
                svg.appendChild(rect);
            }
        }

        // Optional colorbar
        if (showColorbar) {
            const x0 = width - pad - colorbarWidth;
            const steps = scale.length;
            const stepH = plotH / steps;
            for (let i = 0; i < steps; i++) {
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', x0.toFixed(2));
                rect.setAttribute('y', (pad + (steps - 1 - i) * stepH).toFixed(2));
                rect.setAttribute('width', colorbarWidth.toString());
                rect.setAttribute('height', Math.max(1, stepH).toFixed(2));
                rect.setAttribute('fill', scale[i]);
                svg.appendChild(rect);
            }
        }

        container.appendChild(svg);
    }

    renderPreviewPCA(includePresets = false) {
        const container = document.querySelector('#preview-pca .preview-dots');
        if (!container) return;

        const pcaSection = document.querySelector('[data-plot-type="pca_plots"]');
        const colors = Array.from(pcaSection?.querySelectorAll('.plot-color') || []).map(input => input.value);
        const opacityVal = parseFloat(pcaSection?.querySelector('.opacity-slider')?.value || '0.7');
        const lineWidthVal = parseFloat(pcaSection?.querySelector('.line-width-slider')?.value || '0');
        const markerSize = parseFloat(pcaSection?.querySelector('.marker-size-slider')?.value || '3');
        const palette = colors.length ? colors : ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'];

        container.innerHTML = '';
        const width = container.clientWidth || container.offsetWidth || 200;
        const height = container.clientHeight || 80;

        const cacheMap = this._previewCache.pca;
        let cached = cacheMap.get(container);
        if (!cached || cached.width !== width || cached.height !== height || !Array.isArray(cached.points)) {
            const points = [];
            // Create 5 groups of points with different colors for PCA visualization
            const groups = [
                { cx: width * 0.25, cy: height * 0.30, spread: Math.min(width, height) * 0.15, colorIndex: 0 },
                { cx: width * 0.70, cy: height * 0.25, spread: Math.min(width, height) * 0.12, colorIndex: 1 },
                { cx: width * 0.45, cy: height * 0.60, spread: Math.min(width, height) * 0.14, colorIndex: 2 },
                { cx: width * 0.75, cy: height * 0.70, spread: Math.min(width, height) * 0.10, colorIndex: 3 },
                { cx: width * 0.20, cy: height * 0.75, spread: Math.min(width, height) * 0.13, colorIndex: 4 }
            ];
            const nPer = 12;
            groups.forEach((g) => {
                for (let i = 0; i < nPer; i++) {
                    const angle = Math.random() * 2 * Math.PI;
                    const radius = Math.random() * g.spread;
                    const cx = Math.max(6, Math.min(width - 6, g.cx + Math.cos(angle) * radius));
                    const cy = Math.max(6, Math.min(height - 6, g.cy + Math.sin(angle) * radius));
                    points.push({ cx, cy, colorIndex: g.colorIndex });
                }
            });
            cached = { width, height, points };
            cacheMap.set(container, cached);
        }

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        border.setAttribute('x', '0.5');
        border.setAttribute('y', '0.5');
        border.setAttribute('width', (width - 1).toString());
        border.setAttribute('height', (height - 1).toString());
        border.setAttribute('fill', 'none');
        border.setAttribute('stroke', '#e5e7eb');
        border.setAttribute('stroke-width', '1');
        svg.appendChild(border);

        const r = Math.max(1.5, Math.min(8, markerSize));
        const strokeColor = (this.currentTheme === 'high_contrast') ? '#ffffff' : '#000000';
        cached.points.forEach(p => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', p.cx.toString());
            circle.setAttribute('cy', p.cy.toString());
            circle.setAttribute('r', r.toString());
            circle.setAttribute('fill', palette[p.colorIndex % palette.length]);
            circle.setAttribute('fill-opacity', opacityVal.toString());
            circle.setAttribute('stroke', strokeColor);
            circle.setAttribute('stroke-width', lineWidthVal.toString());
            svg.appendChild(circle);
        });

        container.appendChild(svg);
    }

    getDiscreteColorscale(name) {
        const scales = {
            viridis: ['#440154', '#472c7a', '#3b528b', '#2c728e', '#21918c', '#28ae80', '#5ec962', '#9bd93c', '#dce319'],
            plasma: ['#0d0887', '#5b02a3', '#9a179b', '#cb4679', '#ed7953', '#fb9f3a', '#fdca26', '#f0f921'],
            cividis: ['#00224e', '#2c2e66', '#51446f', '#72605f', '#8e7b4a', '#a89832', '#c1b80e', '#d8de00'],
            Blues: ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
            Reds: ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#99000d', '#67000d'],
            RdBu: ['#67001f', '#b2182b', '#d6604d', '#f4a582', '#fddbc7', '#e0e0e0', '#bababa', '#92c5de', '#4393c3', '#2166ac']
        };
        return scales[name] || scales['viridis'];
    }
    
    renderPreviewViolin(includePresets = false) {
        const selector = includePresets
            ? '#preview-violin .preview-shapes, #preset-preview-violin .preview-shapes'
            : '#preview-violin .preview-shapes';
        const containers = Array.from(document.querySelectorAll(selector));
        if (!containers.length) return;

        // Read current settings/colors from the violin plot section
        const violinSection = document.querySelector('[data-plot-type="violin_plots"]');
        const colors = Array.from(violinSection?.querySelectorAll('.plot-color') || []).map(input => input.value);
        const opacityVal = parseFloat(violinSection?.querySelector('.opacity-slider')?.value || '0.6');
        const lineWidthVal = parseFloat(violinSection?.querySelector('.line-width-slider')?.value || '2');

        const palette = colors.length ? colors : ['#1f77b4', '#ff7f0e', '#2ca02c'];

        containers.forEach(container => {
            // Adjust preview background for high contrast theme
            const mini = container.closest('.mini-plot');
            if (mini) {
                mini.style.backgroundColor = (this.currentTheme === 'high_contrast') ? '#000000' : '';
                mini.style.color = (this.currentTheme === 'high_contrast') ? '#ffffff' : '';
            }
            // Clear and create an SVG
            container.innerHTML = '';
            const width = container.clientWidth || container.offsetWidth || 200;
            const height = container.clientHeight || 80;
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '100%');
            svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        // Optional frame
        const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        border.setAttribute('x', '0.5');
        border.setAttribute('y', '0.5');
        border.setAttribute('width', (width - 1).toString());
        border.setAttribute('height', (height - 1).toString());
        border.setAttribute('fill', 'none');
        border.setAttribute('stroke', this.currentTheme === 'high_contrast' ? '#999999' : '#e5e7eb');
        border.setAttribute('stroke-width', '1');
        svg.appendChild(border);

        // Layout three violins across the plot
        const centers = [0.2, 0.5, 0.8].map(p => p * width);
        const yTop = 8;
        const yBottom = height - 8;
        const baseWidth = Math.min(24, width / 12); // max half-width

        const drawOne = (cx, i) => {
            const fill = palette[i % palette.length];
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');

            // Build a symmetric violin silhouette using a smooth width profile
            // width(y) ~ base * sin(pi * t)^(0.85) where t in [0,1]
            const n = 20;
            const right = [];
            const left = [];
            for (let k = 0; k <= n; k++) {
                const t = k / n;
                const y = yTop + t * (yBottom - yTop);
                const w = baseWidth * Math.pow(Math.sin(Math.PI * t), 0.85);
                right.push(`${(cx + w).toFixed(2)},${y.toFixed(2)}`);
                left.push(`${(cx - w).toFixed(2)},${y.toFixed(2)}`);
            }

            // Construct closed path (right side down, left side up)
            const d = `M ${right[0]} L ${right.slice(1).join(' L ')} L ${left.reverse().join(' L ')} Z`;
            path.setAttribute('d', d);
            path.setAttribute('fill', fill);
            path.setAttribute('fill-opacity', opacityVal.toString());
            path.setAttribute('stroke', fill);
            path.setAttribute('stroke-opacity', Math.min(1, opacityVal + 0.2).toString());
            // Apply user-controlled line width to violin outline
            path.setAttribute('stroke-width', lineWidthVal.toString());
            svg.appendChild(path);

            // Optional median line
            const yMed = (yTop + yBottom) / 2;
            const med = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            med.setAttribute('x1', (cx - baseWidth * 0.6).toFixed(2));
            med.setAttribute('x2', (cx + baseWidth * 0.6).toFixed(2));
            med.setAttribute('y1', yMed.toFixed(2));
            med.setAttribute('y2', yMed.toFixed(2));
            med.setAttribute('stroke', '#374151');
            med.setAttribute('stroke-opacity', '0.4');
            med.setAttribute('stroke-width', '1');
            svg.appendChild(med);
        };

        centers.forEach((cx, i) => drawOne(cx, i));
        container.appendChild(svg);
        });
    }
    
    
    collectPlotSettings() {
        const settings = {
            plot_types: {}
        };
        
        // Collect plot-specific settings
        document.querySelectorAll('.plot-type-section').forEach(section => {
            const plotType = section.dataset.plotType;
            const colors = Array.from(section.querySelectorAll('.plot-color')).map(input => input.value);
            const opacity = section.querySelector('.opacity-slider')?.value;
            const markerSize = section.querySelector('.marker-size-slider')?.value;
            const lineWidth = section.querySelector('.line-width-slider')?.value;
            const colorscale = section.querySelector('.colorscale-select')?.value;
            
            settings.plot_types[plotType] = {
                colors: colors,
                opacity: opacity ? parseFloat(opacity) : undefined,
                marker_size: markerSize ? parseFloat(markerSize) : undefined,
                line_width: lineWidth ? parseFloat(lineWidth) : undefined,
                colorscale: colorscale
            };
        });
        
        // Collect global settings
        settings.global = {
            background_color: document.getElementById('plot-background')?.value,
            grid_color: document.getElementById('grid-color')?.value,
            show_grid: document.getElementById('show-grid')?.checked,
            font_family: document.getElementById('plot-font-family')?.value,
            title_size: document.getElementById('title-size')?.value,
            axis_size: document.getElementById('axis-size')?.value,
            high_contrast: document.getElementById('high-contrast-plots')?.checked,
            colorblind_friendly: document.getElementById('colorblind-friendly-plots')?.checked,
            large_text: document.getElementById('large-text-plots')?.checked
        };
        
        return settings;
    }
    
    async resetTheme() {
        // Reset all controls to default values
        const defaultColors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'];
        
        // Reset plot-specific colors
        document.querySelectorAll('.plot-color').forEach((input, index) => {
            input.value = defaultColors[index % defaultColors.length];
            // Clear change flags
            try { delete input.dataset.changed; } catch (e) {}
            const section = input.closest('.plot-type-section');
            if (section) { try { delete section.dataset.colorsChanged; } catch (e) {} }
        });
        
        // Reset sliders
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.value = slider.defaultValue || slider.getAttribute('value');
            const valueDisplay = slider.parentElement.querySelector('.value-display');
            if (valueDisplay) {
                const unit = slider.className.includes('size') ? 'px' : '';
                valueDisplay.textContent = slider.value + unit;
            }
        });
        
        // Reset checkboxes
        document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = checkbox.hasAttribute('checked');
        });
        
        // Reset global colors
        document.getElementById('plot-background').value = '#ffffff';
        document.getElementById('grid-color').value = '#e5e5e5';
        
        // Set theme back to Default visually and apply
        this.currentTheme = 'default';
        // Update theme cards active state
        document.querySelectorAll('.theme-card').forEach(card => {
            card.classList.toggle('active', card.dataset.theme === 'default');
        });

        // Load default colors and update preview
        this.loadThemeColors('default');
        this.updateLivePreview('all');

        // Ensure globals are not pushed unless user changes them after reset
        this._globalsDirty = false;

        // Apply the default theme via backend
        try {
            await this.applyTheme({ closePopup: false });
            this.showMessage('Reset: Default theme applied', 'success');
        } catch (e) {
            this.showMessage('Reset completed (failed to apply server theme)', 'error');
        }
    }
    
    showThemePopup() {
        const popup = document.getElementById('theme-popup');
        if (popup) {
            popup.style.display = 'block';
            // Refresh theme cards
            const themeCards = popup.querySelector('.theme-cards');
            if (themeCards) {
                themeCards.innerHTML = this.renderThemeCards();
                // Re-setup event listeners for new cards
                popup.querySelectorAll('.theme-card').forEach(card => {
                    card.addEventListener('click', () => this.selectTheme(card.dataset.theme));
                });
            }
            
            // Initialize live preview (include preset previews once)
            setTimeout(() => {
                this.updateLivePreview('all');
            }, 100);
        }
    }
    
    hideThemePopup() {
        const popup = document.getElementById('theme-popup');
        if (popup) {
            popup.style.display = 'none';
        }
    }
    
    selectTheme(themeName) {
        // Update active state
        document.querySelectorAll('.theme-card').forEach(card => {
            card.classList.toggle('active', card.dataset.theme === themeName);
        });
        
        this.currentTheme = themeName;
        console.log('Selected theme:', themeName);

        // Show immediate selection feedback without auto-applying
        this.showMessage(`Click "Apply Theme" to activate.`, 'info');

        // If this is a predefined theme, reset custom controls to match theme colors
        if (themeName !== 'custom') {
            this.loadThemeColors(themeName);
            // Reset global UI to a safe default and clear dirty flag so we don't force grid unexpectedly
            const showGridEl = document.getElementById('show-grid');
            if (showGridEl) showGridEl.checked = false; // do not enforce grid unless user chooses
            this._globalsDirty = false;
            // Clear all slider change flags to avoid leaking opacity/size/line overrides
            document.querySelectorAll('.plot-type-section').forEach(section => {
                section.querySelectorAll('input[type="range"]').forEach(slider => {
                    try { delete slider.dataset.changed; } catch (e) {}
                });
                try { delete section.dataset.settingsChanged; } catch (e) {}
                try { delete section.dataset.colorsChanged; } catch (e) {}
            });
            // Mark theme switch
            this._justSwitchedTheme = true;
        }
    }
    
    loadThemeColors(themeKey) {
        // Load theme colors into the plot-specific controls
        const themeColors = this.getThemeColors(themeKey);
        
        // Update all plot type color pickers with theme colors
        document.querySelectorAll('.plot-type-section').forEach(section => {
            const colorInputs = section.querySelectorAll('.plot-color');
            colorInputs.forEach((input, index) => {
                if (index < themeColors.length) {
                    input.value = themeColors[index];
                    // Clear any prior user-change flags to avoid accidental overrides
                    try { delete input.dataset.changed; } catch (e) {}
                }
            });
            // Clear section change flag
            try { delete section.dataset.colorsChanged; } catch (e) {}
            // Clear any prior slider change flags
            section.querySelectorAll('input[type="range"]').forEach(el => { try { delete el.dataset.changed; } catch (e) {} });
            try { delete section.dataset.settingsChanged; } catch (e) {}
        });
        
        // Also sync sliders with backend defaults for the selected theme
        fetch('/backend/themes/plot-types/')
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                const cfgs = data?.plot_types || {};
                document.querySelectorAll('.plot-type-section').forEach(section => {
                    const pt = section.dataset.plotType;
                    const cfg = cfgs[pt] || {};
                    const opacitySlider = section.querySelector('.opacity-slider');
                    if (opacitySlider && typeof cfg.opacity === 'number') {
                        opacitySlider.value = cfg.opacity;
                        const vd = opacitySlider.parentElement.querySelector('.value-display');
                        if (vd) vd.textContent = String(cfg.opacity);
                        try { delete opacitySlider.dataset.changed; } catch(e){}
                    }
                    const sizeSlider = section.querySelector('.marker-size-slider');
                    if (sizeSlider && typeof cfg.marker_size === 'number') {
                        sizeSlider.value = cfg.marker_size;
                        const vd = sizeSlider.parentElement.querySelector('.value-display');
                        if (vd) vd.textContent = sizeSlider.value + 'px';
                        try { delete sizeSlider.dataset.changed; } catch(e){}
                    }
                    const lwSlider = section.querySelector('.line-width-slider');
                    if (lwSlider && typeof cfg.line_width === 'number') {
                        lwSlider.value = cfg.line_width;
                        const vd = lwSlider.parentElement.querySelector('.value-display');
                        if (vd) vd.textContent = lwSlider.value;
                        try { delete lwSlider.dataset.changed; } catch(e){}
                    }
                });
            })
            .catch(() => {})
            .finally(() => {
                // Update live preview for all previews on initial load
                this.updateLivePreview('all');
            });
    }
    
    updateCustomTheme() {
        const primaryColor = document.getElementById('primary-color')?.value;
        const secondaryColor = document.getElementById('secondary-color')?.value;
        const backgroundColor = document.getElementById('background-color')?.value;
        const textColor = document.getElementById('text-color')?.value;
        const fontFamily = document.getElementById('font-family')?.value;
        const fontSize = document.getElementById('font-size')?.value;
        
        const highContrast = document.getElementById('high-contrast')?.checked;
        const colorblindFriendly = document.getElementById('colorblind-friendly')?.checked;
        const largeText = document.getElementById('large-text')?.checked;
        
        this.customTheme = {
            theme_name: 'custom',
            colors: {
                primary_palette: [primaryColor, secondaryColor, '#2ca02c', '#d62728', '#9467bd'],
                background_color: backgroundColor,
                text_color: textColor
            },
            fonts: {
                family: fontFamily,
                size: parseInt(fontSize)
            },
            accessibility: {
                high_contrast: highContrast,
                colorblind_friendly: colorblindFriendly,
                large_text: largeText
            }
        };
    }

    // Snapshot current UI into a PlotThemeRequest-like object so saving/applying works
    _buildCustomThemeFromUI() {
        try {
            const violinSection = document.querySelector('[data-plot-type="violin_plots"]');
            const palette = Array.from(violinSection?.querySelectorAll('.plot-color') || [])
                .map(input => input.value)
                .filter(Boolean);
            const primary_palette = (palette.length ? palette : ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd']).slice(0,5);

            // Extract violin plot specific settings
            const violin_opacity = parseFloat(violinSection?.querySelector('.opacity-slider')?.value || '0.7');
            const violin_line_width = parseFloat(violinSection?.querySelector('.line-width-slider')?.value || '2');

            const background_color = document.getElementById('plot-background')?.value || '#ffffff';
            const grid_color = document.getElementById('grid-color')?.value || '#e5e5e5';
            const font_family = document.getElementById('plot-font-family')?.value || 'Arial, sans-serif';
            const title_size = parseInt(document.getElementById('title-size')?.value || '14', 10);
            const axis_size = parseInt(document.getElementById('axis-size')?.value || '12', 10);

            const high_contrast = !!document.getElementById('high-contrast-plots')?.checked;
            const colorblind_friendly = !!document.getElementById('colorblind-friendly-plots')?.checked;
            const large_text = !!document.getElementById('large-text-plots')?.checked;

            // Build theme data matching PlotThemeRequest schema from backend/validations.py
            this.customTheme = {
                theme_name: 'custom',
                colors: {
                    primary_palette,
                    categorical_palette: "Set3",
                    continuous_palette: "viridis",
                    diverging_palette: "RdBu",
                    background_color,
                    grid_color,
                    text_color: "#333333",
                    axis_color: "#666666",
                    highlight_color: "#ff6b6b",
                    qc_pass_color: "#2ecc71",
                    qc_fail_color: "#e74c3c",
                    qc_warning_color: "#f39c12"
                },
                fonts: {
                    family: font_family,
                    title_size,
                    axis_title_size: axis_size,
                    size: 12,
                    legend_size: 11,
                    annotation_size: 10
                },
                layout: {
                    width: 800,
                    height: 600,
                    margin: { l: 60, r: 60, t: 80, b: 60 },
                    plot_bgcolor: background_color,
                    paper_bgcolor: background_color,
                    grid_alpha: 0.3,
                    show_grid: !!document.getElementById('show-grid')?.checked,
                    show_legend: true,
                    legend_position: "right",
                    template: "plotly_white"
                },
                markers: {
                    size: 4,
                    opacity: violin_opacity,
                    line_width: Math.round(violin_line_width),
                    symbol: "circle"
                },
                accessibility: {
                    high_contrast,
                    colorblind_friendly,
                    large_text,
                    simplified_layout: false
                }
            };
        } catch (e) {
            console.warn('Failed to build custom theme from UI:', e);
        }
    }
    
    async applyTheme(options = {}) {
        const { closePopup = true } = options;
        try {
            console.log('Applying theme:', this.currentTheme);
            
            // Show immediate feedback
            this.showMessage(`Applying theme "${this.currentTheme || 'Custom'}"...`, 'info');
            
            // Push Global settings to backend first so builds/regeneration pick them up
            try {
                // Only push global settings if the user modified them in this session
                if (this._globalsDirty) {
                    const globalPayload = {
                        background_color: document.getElementById('plot-background')?.value || '#ffffff',
                        grid_color: document.getElementById('grid-color')?.value || '#e5e5e5',
                        show_grid: !!document.getElementById('show-grid')?.checked,
                        font_family: document.getElementById('plot-font-family')?.value || 'Arial, sans-serif',
                        title_size: parseInt(document.getElementById('title-size')?.value || '14', 10),
                        axis_size: parseInt(document.getElementById('axis-size')?.value || '12', 10),
                        text_color: document.getElementById('plot-font-color')?.value || '#333333'
                    };
                    await fetch('/backend/themes/global/', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(globalPayload)
                    }).catch(() => {});
                    // Reset flag after successful (or attempted) push
                    this._globalsDirty = false;
                }
            } catch (e) {
                console.warn('Failed to update global theme settings:', e);
            }

            // First priority: Apply preset/custom by name if selected
            if (this.currentTheme && this.currentTheme !== 'custom') {
                try {
                    console.log(`Attempting to apply theme "${this.currentTheme}" to endpoint: /backend/themes/current/${encodeURIComponent(this.currentTheme)}/`);
                    
                    const response = await fetch(`/backend/themes/current/${encodeURIComponent(this.currentTheme)}/`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });
                    
                    const responseText = await response.text();
                    console.log(`Theme application response for "${this.currentTheme}":`, response.status, responseText);
                    
                    if (response.ok) {
                        console.log(`Applied predefined theme "${this.currentTheme}" successfully`);
                        this.showMessage(`Theme "${this.currentTheme}" applied.`, 'success');
                    } else {
                        // If theme not found on server, try creating it from current UI or cached data, then set current
                        if (response.status === 404) {
                            console.warn(`Theme '${this.currentTheme}' not found on server. Creating it and retrying...`);
                            // Prefer saved theme data if available, else build from UI
                            const cached = this.availableThemes?.[this.currentTheme];
                            if (!this.customTheme) this._buildCustomThemeFromUI();
                            const themePayload = {
                                theme_name: this.currentTheme,
                                ...(cached && cached.colors ? { colors: cached.colors } : this.customTheme?.colors ? { colors: this.customTheme.colors } : {}),
                                ...(cached && cached.fonts ? { fonts: cached.fonts } : {}),
                                ...(cached && cached.layout ? { layout: cached.layout } : {}),
                                ...(cached && cached.accessibility ? { accessibility: cached.accessibility } : (this.customTheme?.accessibility ? { accessibility: this.customTheme.accessibility } : {}))
                            };
                            try {
                                const createRes = await fetch('/backend/themes/', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(themePayload)
                                });
                                if (createRes.ok) {
                                    await fetch(`/backend/themes/current/${encodeURIComponent(this.currentTheme)}/`, { method: 'PUT' });
                                    this.showMessage(`Created and applied theme "${this.currentTheme}"`, 'success');
                                } else {
                                    console.warn('Failed to create theme:', await createRes.text());
                                }
                            } catch (e) {
                                console.warn('Error creating theme:', e);
                            }
                        }
                        console.warn(`Failed to apply predefined theme "${this.currentTheme}": ${response.status} - ${responseText}`);
                        // If theme application failed, skip plot-specific settings
                        this.showMessage(`Theme "${this.currentTheme}" not found. Applying settings as custom theme...`, 'warning');
                        // Don't return here - let it continue to plot-specific settings which can work independently
                    }
                } catch (error) {
                    console.warn(`Error applying predefined theme: ${error.message}`);
                    this.showMessage(`Error applying theme: ${error.message}`, 'error');
                }
            }
            
            // Second priority: Apply custom plot-specific settings (skip immediately after switching theme)
            const plotSettings = this.collectPlotSettings();
            if (!this._justSwitchedTheme && this.hasCustomSettings(plotSettings)) {
                try {
                    console.log('Applying custom plot-specific settings:', plotSettings);
                    
                    // Apply each plot type configuration (sanitize payload for backend)
                    const applyPromises = Object.entries(plotSettings.plot_types).map(async ([plotType, config]) => {
                        const backendPlotType = plotType === 'heatmaps' ? 'dea_heatmaps' : plotType;
                        const payload = {};
                        const sectionEl = document.querySelector(`[data-plot-type="${plotType}"]`);
                        const colorsChanged = !!(sectionEl && Array.from(sectionEl.querySelectorAll('.plot-color')).some(inp => inp.dataset.changed === 'true'));
                        const opacityChanged = !!sectionEl?.querySelector('.opacity-slider')?.dataset.changed;
                        const sizeChanged = !!sectionEl?.querySelector('.marker-size-slider')?.dataset.changed;
                        const lineWidthChanged = !!sectionEl?.querySelector('.line-width-slider')?.dataset.changed;
                        if (backendPlotType === 'violin_plots') {
                            if (colorsChanged && Array.isArray(config.colors) && config.colors.length) payload.colors = config.colors;
                            if (opacityChanged && typeof config.opacity === 'number') payload.opacity = config.opacity;
                            if (lineWidthChanged && typeof config.line_width === 'number') payload.line_width = config.line_width;
                        } else if (backendPlotType === 'scatter_plots' || backendPlotType === 'umap_plots' || backendPlotType === 'pca_plots') {
                            if (colorsChanged && Array.isArray(config.colors) && config.colors.length) payload.colors = config.colors;
                            if (sizeChanged && typeof config.marker_size === 'number') payload.marker_size = config.marker_size;
                            if (opacityChanged && typeof config.opacity === 'number') payload.opacity = config.opacity;
                            if (lineWidthChanged && typeof config.line_width === 'number') payload.line_width = config.line_width;
                        } else if (backendPlotType === 'dea_heatmaps') {
                            if (config.colorscale) payload.colorscale = config.colorscale;
                        }
                        if (!Object.keys(payload).length) return true;
                        const res = await fetch(`/backend/themes/plot-types/${backendPlotType}/`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (res.ok) {
                            console.log(`Applied ${backendPlotType} settings successfully`);
                            return true;
                        } else {
                            console.warn(`Failed to apply ${backendPlotType} settings`);
                            return false;
                        }
                    });
                    
                    const results = await Promise.allSettled(applyPromises);
                    const successful = results.filter(r => r.status === 'fulfilled' && r.value).length;
                    
                    if (successful > 0) {
                        this.showMessage('Applied plot-specific settings', 'success');
                    }
                } catch (error) {
                    console.warn(`Error applying custom settings: ${error.message}`);
                }
            }
            
            // Regenerate plots to reflect changes and optionally close popup
            await this.regenerateExistingPlots();

            // Reset switch flag after plots are regenerated
            this._justSwitchedTheme = false;

            if (closePopup) this.hideThemePopup();
            
        } catch (error) {
            console.error('Error in applyTheme:', error);
            this.showMessage(`Failed to apply theme: ${error.message}`, 'error');
        }
    }
    
    hasCustomSettings(plotSettings) {
        // Check if any plot type has user-tweaked settings
        for (const [plotType, config] of Object.entries(plotSettings.plot_types)) {
            const sectionEl = document.querySelector(`[data-plot-type="${plotType}"]`);
            const colorsChanged = !!(sectionEl && Array.from(sectionEl.querySelectorAll('.plot-color')).some(inp => inp.dataset.changed === 'true'));
            const anySliderChanged = !!(
                sectionEl?.querySelector('.opacity-slider')?.dataset.changed ||
                sectionEl?.querySelector('.marker-size-slider')?.dataset.changed ||
                sectionEl?.querySelector('.line-width-slider')?.dataset.changed
            );
            if (colorsChanged || anySliderChanged) return true;
        }
        return false;
    }
    
    async regenerateExistingPlots() {
        try {
            // Get current UUID from session storage or page
            const uuid = sessionStorage.getItem('uuid') || this.extractUuidFromPage();
            
            if (!uuid) {
                console.log('No UUID found, trying to refresh existing plots only');
                this.refreshPagePlots();
                return;
            }
            
            console.log(`Regenerating plots for UUID: ${uuid}`);
            
            const response = await fetch(`/backend/regenerate_plots/${uuid}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Plot regeneration result:', result);
                
                // Wait longer for HTML files to be completely written and synced in Docker
                setTimeout(() => {
                    this.refreshPagePlots();
                    this.showMessage('Plots updated with new theme!', 'success');
                }, 3000);
                
            } else {
                const resultData = await response.json();
                console.log('Plot regeneration response:', resultData);
                
                if (resultData.message === 'No plots found to regenerate') {
                    // No server-side plots to regenerate, focus on client-side injection
                    console.log('No server plots found, applying theme to existing client plots');
                    this.refreshPagePlots();
                    this.showMessage('Theme saved successfully! Applying to existing plots...', 'success');
                } else {
                    console.log('Plot regeneration failed, trying page refresh');
                    this.refreshPagePlots();
                    this.showMessage('Theme applied - please refresh page if plots don\'t update', 'info');
                }
            }
            
        } catch (error) {
            console.log('Plot regeneration error:', error.message);
            this.refreshPagePlots();
            this.showMessage('Theme applied - refreshing plots', 'info');
        }
    }
    
    extractUuidFromPage() {
        // Method 1: Try to extract UUID from analysis info box
        const analysisInfoBox = document.getElementById('analysisInfoBox');
        if (analysisInfoBox) {
            const text = analysisInfoBox.textContent;
            const uuidMatch = text.match(/UUID: ([a-f0-9-]+)/i);
            if (uuidMatch) {
                console.log('Found UUID in analysisInfoBox:', uuidMatch[1]);
                return uuidMatch[1];
            }
        }
        
        // Method 2: Try URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const uuidFromUrl = urlParams.get('uuid');
        if (uuidFromUrl) {
            console.log('Found UUID in URL params:', uuidFromUrl);
            return uuidFromUrl;
        }
        
        // Method 3: Try to find UUID in any element on the page
        const allElements = document.getElementsByTagName('*');
        for (let element of allElements) {
            const text = element.textContent || element.innerText || '';
            const uuidMatch = text.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i);
            if (uuidMatch) {
                console.log('Found UUID in page element:', uuidMatch[1]);
                return uuidMatch[1];
            }
        }
        
        // Method 4: Try to find from current page URL path
        const pathMatch = window.location.pathname.match(/\/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i);
        if (pathMatch) {
            console.log('Found UUID in URL path:', pathMatch[1]);
            return pathMatch[1];
        }
        
        console.log('No UUID found on this page');
        return null;
    }
    
    async refreshPagePlots() {
        // First, try to inject theme changes into existing HTML plots
        try { await this.injectThemeIntoExistingPlots(); } catch (e) { console.warn('Inject failed:', e); }
        
        // Force refresh of plot iframes by updating their src with timestamp
        // This will trigger the server to regenerate plots with the current theme
        const iframes = document.querySelectorAll('iframe[src*="plots"], iframe[src*="preprocess"], iframe[src*="genes_vis"], iframe[src*="embedding"], iframe[src*="violin"]');
        console.log(`Refreshing ${iframes.length} plot iframes with current theme`);
        iframes.forEach(iframe => {
            const currentSrc = iframe.src;
            // Always use ? and strip any existing parameters to avoid URL encoding issues
            const baseUrl = currentSrc.split('?')[0];
            iframe.src = baseUrl + '?theme_refresh=' + Date.now();
            console.log(`Refreshed iframe: ${iframe.src}`);
        });
        
        // Also refresh any plot containers that might load content dynamically
        const plotContainers = document.querySelectorAll('.plots-container');
        plotContainers.forEach(container => {
            // Trigger a refresh event if the container has plots
            if (container.children.length > 0) {
                const refreshEvent = new CustomEvent('plotsRefresh');
                container.dispatchEvent(refreshEvent);
            }
        });
        
        // Alternative method: If we're on a results page, try to reload plots from sessionStorage
        if (typeof loadInitialPlots === 'function') {
            console.log('Attempting to reload plots using loadInitialPlots function');
            setTimeout(() => {
                // Clear existing plots
                const container = document.querySelector('.plots-container');
                if (container) {
                    container.innerHTML = '';
                    // Reload plots
                    loadInitialPlots();
                }
            }, 100);
        }
        
        // Regenerate heatmaps if we're on the heatmap page and have existing data
        if (typeof window.regenerateHeatmap === 'function') {
            console.log('Attempting to regenerate heatmap with current theme');
            setTimeout(() => {
                window.regenerateHeatmap();
            }, 500);
        }
        
        // Also refresh heatmap images directly if they exist
        const heatmapImages = document.querySelectorAll('#heatmapImage, img[alt*="heatmap"]');
        if (heatmapImages.length > 0) {
            console.log(`Refreshing ${heatmapImages.length} heatmap images with current theme`);
            heatmapImages.forEach(img => {
                if (img.src && img.src.includes('genes_vis')) {
                    const currentSrc = img.src;
                    const baseUrl = currentSrc.split('?')[0];
                    img.src = baseUrl + '?theme_refresh=' + Date.now();
                    console.log(`Refreshed heatmap image: ${img.src}`);
                }
            });
        }
    }
    
    async injectThemeIntoExistingPlots() {
        // Get current plot settings from UI
        const uiSettings = this.collectPlotSettings();
        let backendConfigs = {};
        try {
            const res = await fetch('/backend/themes/plot-types/');
            if (res.ok) {
                const data = await res.json();
                backendConfigs = data.plot_types || {};
            }
        } catch (e) { console.warn('Failed to fetch backend plot configs for injection:', e); }

        // Merge: prefer UI-changed values, otherwise use backend defaults to avoid stale slider bleed
        // When _justSwitchedTheme is true, prioritize backend configs for theme consistency
        const plotSettings = { plot_types: {} };
        document.querySelectorAll('.plot-type-section').forEach(section => {
            const pt = section.dataset.plotType;
            const backendCfg = backendConfigs[pt] || {};
            const colorsChanged = !!(Array.from(section.querySelectorAll('.plot-color')).some(inp => inp.dataset.changed === 'true'));
            const opacityChanged = !!section.querySelector('.opacity-slider')?.dataset.changed;
            const sizeChanged = !!section.querySelector('.marker-size-slider')?.dataset.changed;
            const lineChanged = !!section.querySelector('.line-width-slider')?.dataset.changed;
            const uiCfg = uiSettings.plot_types[pt] || {};

            // After theme switch, prioritize backend configs to reflect the new theme properly
            const useBackendForTheme = this._justSwitchedTheme || !opacityChanged;

            plotSettings.plot_types[pt] = {
                colors: colorsChanged ? uiCfg.colors : (backendCfg.colors || uiCfg.colors),
                opacity: useBackendForTheme && typeof backendCfg.opacity === 'number' ? backendCfg.opacity : uiCfg.opacity,
                marker_size: (!sizeChanged && typeof backendCfg.marker_size === 'number') ? backendCfg.marker_size : uiCfg.marker_size,
                line_width: (!lineChanged && typeof backendCfg.line_width === 'number') ? backendCfg.line_width : uiCfg.line_width,
                colorscale: backendCfg.colorscale || uiCfg.colorscale
            };
        });
        console.log('Injecting theme into existing plots with settings:', plotSettings);
        
        // Find all HTML plots (embedded plots or divs with Plotly plots)
        const plotElements = document.querySelectorAll('[id^="plotly-div"], .js-plotly-plot, iframe');
        console.log(`Found ${plotElements.length} plot elements to update`);
        
        let injectedCount = 0;
        plotElements.forEach((element, index) => {
            console.log(`Processing plot element ${index + 1}:`, element);
            if (element.tagName === 'IFRAME') {
                if (this.injectThemeIntoIframe(element, plotSettings)) injectedCount++;
            } else {
                if (this.injectThemeIntoPlotlyDiv(element, plotSettings)) injectedCount++;
            }
        });
        
        // Also look for HTML files loaded via fetch or embedded in the DOM
        const htmlContainers = document.querySelectorAll('.plot-container, .plots-container, [data-plot-type]');
        console.log(`Found ${htmlContainers.length} HTML containers to update`);
        
        htmlContainers.forEach((container, index) => {
            console.log(`Processing HTML container ${index + 1}:`, container);
            this.injectThemeIntoHtmlContainer(container, plotSettings);
        });
        
        console.log(`Successfully injected theme into ${injectedCount} plots`);
        
        // If no plots were found, let the user know
        if (plotElements.length === 0 && htmlContainers.length === 0) {
            console.log('No plots found on current page to inject theme into');
            this.showMessage('Theme saved! It will be applied to new plots when they are generated.', 'success');
        }
    }
    
    injectThemeIntoIframe(iframe, plotSettings) {
        try {
            // Check if we can access iframe content (same-origin policy)
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc) {
                const plotlyDivs = iframeDoc.querySelectorAll('[id^="plotly-div"], .js-plotly-plot');
                console.log(`Found ${plotlyDivs.length} Plotly divs inside iframe`);
                
                let success = false;
                plotlyDivs.forEach(div => {
                    if (this.injectThemeIntoPlotlyDiv(div, plotSettings)) success = true;
                });
                
                // Inject CSS styles for violin plots
                this.injectPlotStyles(iframeDoc, plotSettings);
                return success || plotlyDivs.length > 0;
            }
        } catch (e) {
            console.warn('Cannot access iframe content (cross-origin):', e);
            // Fallback: try to reload iframe with theme parameters
            const currentSrc = iframe.src;
            if (currentSrc) {
                // Remove old parameters and add new ones
                const baseUrl = currentSrc.split('?')[0];
                const violinConfig = plotSettings.plot_types.violin_plots;
                const themeParams = new URLSearchParams({
                    '_': Date.now().toString(),
                    'theme_applied': 'true',
                    'colors': violinConfig?.colors?.join(',') || '',
                    'opacity': violinConfig?.opacity || '0.7',
                    'line_width': violinConfig?.line_width || '2'
                });
                
                iframe.src = baseUrl + '?' + themeParams.toString();
                console.log('Reloading iframe with theme parameters:', iframe.src);
                return true;  // Consider this a success since we attempted reload
            }
        }
        return false;
    }
    
    injectThemeIntoPlotlyDiv(plotDiv, plotSettings) {
        // Check if Plotly is available and plot exists
        if (typeof Plotly !== 'undefined' && plotDiv && plotDiv.data) {
            try {
                // Determine plot type by examining the data
                const plotType = this.detectPlotType(plotDiv.data);
                const config = plotSettings.plot_types[plotType];
                console.log(`Detected plot type: ${plotType}`, config);
                
                if (config) {
                    // Update plot traces with new colors, opacity, and line width
                    const traces = plotDiv.data;
                    let updated = false;
                    
                    if (plotType === 'violin_plots') {
                        traces.forEach((trace, index) => {
                            if (trace.type === 'violin') {
                                const color = config.colors[index % config.colors.length];
                                const opacity = config.opacity || 0.7;
                                const lineWidth = config.line_width || 2;
                                
                                console.log(`Updating violin trace ${index} with color: ${color}, opacity: ${opacity}, lineWidth: ${lineWidth}`);
                                
                                // Update trace properties
                                trace.fillcolor = this.hexToRgba(color, opacity);
                                trace.line = { color: color, width: lineWidth };
                                if (trace.box) {
                                    trace.box.fillcolor = this.hexToRgba(color, opacity * 0.8);
                                }
                                updated = true;
                            }
                        });
                        
                        if (updated) {
                            // Apply the changes using Plotly.redraw
                            Plotly.redraw(plotDiv);
                            console.log('Successfully updated Plotly violin plot');
                            return true;
                        }
                    }
                } else {
                    console.log(`No configuration found for plot type: ${plotType}`);
                }
            } catch (e) {
                console.warn('Failed to inject theme into Plotly plot:', e);
            }
        } else {
            // Check if this is inside an iframe where Plotly might not be available
            const isInIframe = window !== window.top;
            console.log('Plotly not available or plot data not found', { 
                plotlyAvailable: typeof Plotly !== 'undefined', 
                plotDiv: !!plotDiv,
                hasData: plotDiv && !!plotDiv.data,
                isInIframe: isInIframe
            });
            
            // If this is a violin plot div but Plotly isn't available, 
            // we'll rely on iframe reloading instead
            if (plotDiv && plotDiv.classList && plotDiv.classList.contains('js-plotly-plot')) {
                console.log('Found plotly plot element but library not accessible - will use iframe reload strategy');
                return true; // Consider this successful since we'll handle it via iframe reload
            }
        }
        return false;
    }
    
    injectThemeIntoHtmlContainer(container, plotSettings) {
        // Look for embedded HTML plots or SVG elements
        const htmlPlots = container.querySelectorAll('iframe[src*=".html"], embed[src*=".html"], object[data*=".html"]');
        htmlPlots.forEach(plot => {
            if (plot.tagName === 'IFRAME') {
                this.injectThemeIntoIframe(plot, plotSettings);
            }
        });
        
        // Look for SVG elements that might be violin plots
        const svgElements = container.querySelectorAll('svg');
        svgElements.forEach(svg => {
            this.injectThemeIntoSvg(svg, plotSettings);
        });
    }
    
    injectThemeIntoSvg(svg, plotSettings) {
        // Check if this is a violin plot by looking for characteristic elements
        const violinPaths = svg.querySelectorAll('path[d*="M"], g.trace');
        if (violinPaths.length > 0) {
            const violinConfig = plotSettings.plot_types.violin_plots;
            if (violinConfig) {
                violinPaths.forEach((path, index) => {
                    const color = violinConfig.colors[index % violinConfig.colors.length];
                    const opacity = violinConfig.opacity || 0.7;
                    const lineWidth = violinConfig.line_width || 2;
                    
                    // Update SVG element styles
                    path.style.fill = this.hexToRgba(color, opacity);
                    path.style.stroke = color;
                    path.style.strokeWidth = lineWidth + 'px';
                });
            }
        }
    }
    
    injectPlotStyles(doc, plotSettings) {
        // Inject CSS styles for dynamic theming
        let styleElement = doc.getElementById('dynamic-theme-styles');
        if (!styleElement) {
            styleElement = doc.createElement('style');
            styleElement.id = 'dynamic-theme-styles';
            doc.head.appendChild(styleElement);
        }
        
        const violinConfig = plotSettings.plot_types.violin_plots;
        if (violinConfig) {
            const css = `
                .js-plotly-plot .trace.violins path {
                    fill-opacity: ${violinConfig.opacity || 0.7} !important;
                    stroke-width: ${violinConfig.line_width || 2}px !important;
                }
                .js-plotly-plot .trace.violins .box path {
                    fill-opacity: ${(violinConfig.opacity || 0.7) * 0.8} !important;
                }
            `;
            styleElement.textContent = css;
        }
    }
    
    detectPlotType(data) {
        // Simple heuristic to detect plot type from Plotly data
        if (!data || !Array.isArray(data)) return 'scatter_plots';
        
        for (const trace of data) {
            if (trace.type === 'violin') return 'violin_plots';
            if (trace.type === 'scatter') return 'scatter_plots';
            if (trace.type === 'scattergl') return 'scatter_plots';
            if (trace.type === 'heatmap') return 'dea_heatmaps';
        }
        
        return 'scatter_plots'; // Default fallback
    }
    
    hexToRgba(hex, alpha) {
        // Convert hex color to rgba with alpha
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (result) {
            return `rgba(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}, ${alpha})`;
        }
        return hex;
    }

    async previewTheme() {
        this.showMessage('Preview functionality coming soon!', 'info');
    }
    
    async saveCustomTheme() {
        // Build from current UI so saving works even without the old inputs
        if (!this.customTheme) {
            this._buildCustomThemeFromUI();
        }
        
        const themeName = prompt('Enter a name for your custom theme:');
        if (!themeName) return;
        
        try {
            const themeData = {
                ...this.customTheme,
                theme_name: themeName
            };
            
            const response = await fetch('/backend/themes/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(themeData)
            });
            
            if (!response.ok) throw new Error('Failed to save theme');
            
            this.availableThemes[themeName] = themeData;
            this.currentTheme = themeName;
            this.showMessage(`Custom theme "${themeName}" saved. Applying...`, 'success');
            
            // Activate the saved theme
            await fetch(`/backend/themes/current/${encodeURIComponent(themeName)}/`, { method: 'PUT' });
            
            // Apply plot-specific settings on top
            const plotSettings = this.collectPlotSettings();
            if (this.hasCustomSettings(plotSettings)) {
                const applyPromises = Object.entries(plotSettings.plot_types).map(([plotType, config]) => {
                    const backendPlotType = plotType === 'heatmaps' ? 'dea_heatmaps' : plotType;
                    let payload = {};
                    if (backendPlotType === 'violin_plots') {
                        if (config.colors && config.colors.length) payload.colors = config.colors;
                        if (typeof config.opacity === 'number') payload.opacity = config.opacity;
                        if (typeof config.line_width === 'number') payload.line_width = config.line_width;
                    } else if (backendPlotType === 'scatter_plots' || backendPlotType === 'umap_plots' || backendPlotType === 'pca_plots') {
                        if (config.colors && config.colors.length) payload.colors = config.colors;
                        if (typeof config.marker_size === 'number') payload.marker_size = config.marker_size;
                        if (typeof config.opacity === 'number') payload.opacity = config.opacity;
                    } else if (backendPlotType === 'dea_heatmaps') {
                        if (config.colorscale) payload.colorscale = config.colorscale;
                    }
                    if (Object.keys(payload).length === 0) return Promise.resolve();
                    return fetch(`/backend/themes/plot-types/${backendPlotType}/`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    }).then(res => {
                        if (!res.ok) {
                            console.warn(`Failed to apply ${plotType} settings (${res.status})`);
                            return res.text().then(errorText => {
                                console.warn(`Error: ${errorText}`);
                                return null; // Don't reject - just continue with other plot types
                            });
                        }
                        console.log(`Updated ${plotType} settings`);
                        return res.json();
                    }).catch(error => {
                        console.warn(`Network error applying ${plotType} settings:`, error);
                        return null; // Don't reject - just continue with other plot types
                    });
                });
                const results = await Promise.allSettled(applyPromises);
                const successful = results.filter(r => r.status === 'fulfilled' && r.value).length;
                const failed = results.filter(r => r.status === 'rejected' || !r.value).length;
                
                if (successful > 0) {
                    this.showMessage(`Successfully applied settings to ${successful} plot type${successful > 1 ? 's' : ''}${failed > 0 ? `, ${failed} failed` : ''}`, 'success');
                } else if (failed > 0) {
                    this.showMessage(`Failed to apply plot-specific settings. Theme base was applied.`, 'warning');
                }
            }

            // Ensure the preset list shows the new custom theme immediately
            const cards = document.querySelector('.theme-cards');
            if (cards) {
                cards.innerHTML = this.renderThemeCards();
                cards.querySelectorAll('.theme-card').forEach(card => {
                    card.addEventListener('click', () => this.selectTheme(card.dataset.theme));
                });
            }
            
            await this.regenerateExistingPlots();
        } catch (error) {
            console.error('Error saving theme:', error);
            this.showMessage('Failed to save custom theme', 'error');
        }
    }
    
    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('theme-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'theme-message';
            messageEl.className = 'theme-message';
            document.body.appendChild(messageEl);
        }
        
        messageEl.className = `theme-message ${type}`;
        messageEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;
        messageEl.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 3000);
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're not on the home page
    if (!window.location.pathname.endsWith('/') && 
        !window.location.pathname.endsWith('/scexplorer/')) {
        window.themeManager = new ThemeManager();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
