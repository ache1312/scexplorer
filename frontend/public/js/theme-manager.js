/**
 * Theme Management System for scExplorer
 * Handles theme selection, customization, and preview functionality
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'default';
        this.availableThemes = {};
        this.customTheme = null;
        this.previewModal = null;
        this.initialized = false;
        
        this.init();
    }
    
    async init() {
        if (this.initialized) return;
        
        try {
            await this.loadAvailableThemes();
            this.setupEventListeners();
            this.createThemeSelector();
            this.initialized = true;
            console.log('Theme Manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Theme Manager:', error);
        }
    }
    
    async loadAvailableThemes() {
        try {
            const base = (window.API_BASE_URL || '/backend');
            const response = await fetch(`${base}/themes/`);
            if (!response.ok) throw new Error('Failed to load themes');
            
            const data = await response.json();
            this.availableThemes = data.themes || data;
            this.currentTheme = data.current_theme || 'default';
        } catch (error) {
            console.error('Error loading themes:', error);
            // Fallback to default themes
            this.availableThemes = {
                'default': { theme_name: 'Default', description: 'Clean scientific theme' },
                'dark': { theme_name: 'Dark', description: 'Dark mode for low-light environments' },
                'colorblind_friendly': { theme_name: 'Colorblind Friendly', description: 'Accessible colors for colorblind users' },
                'high_contrast': { theme_name: 'High Contrast', description: 'Maximum contrast for accessibility' },
                'publication': { theme_name: 'Publication', description: 'Publication-ready grayscale theme' },
                'vibrant': { theme_name: 'Vibrant', description: 'Bright and colorful theme' }
            };
            this.currentTheme = 'default';
        }
    }
    
    createThemeSelector() {
        const container = document.getElementById('theme-selector-container');
        if (!container) return;
        
        const html = `
            <div class="theme-selector-container">
                <!-- Collapsed State: Just the Icon -->
                <div class="theme-icon-trigger" id="theme-icon-trigger">
                    <div class="tooltip-enhanced">
                        <i class="fas fa-palette theme-palette-icon"></i>
                        <div class="tooltip-content">
                            <h5>🎨 Theme Customization</h5>
                            <p>Click to customize plot colors, fonts, and styles for your visualizations.</p>
                            <ul>
                                <li>6 predefined themes available</li>
                                <li>Custom color picker</li>
                                <li>Font family & size controls</li>
                                <li>Accessibility options</li>
                            </ul>
                            <div class="tooltip-shortcut">Click palette icon to open</div>
                        </div>
                    </div>
                </div>
                
                <!-- Expanded State: Full Panel -->
                <div class="theme-expanded-panel" id="theme-expanded-panel" style="display: none;">
                    <div class="theme-selector-header">
                        <h3 class="theme-selector-title">
                            <i class="fas fa-palette"></i>
                            Plot Theme Customization
                        </h3>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <button class="btn btn-secondary" id="collapse-themes" style="padding: 6px 12px; border-radius: 6px; border: none; background: rgba(255,255,255,0.15); color: white; cursor: pointer; font-size: 0.8rem;">
                                <i class="fas fa-times"></i> Close
                            </button>
                        </div>
                    </div>
                
                <div class="theme-grid">
                    ${this.renderThemeCards()}
                </div>
                
                <div class="theme-customization" id="theme-customization">
                    <div class="customization-section">
                        <h4><i class="fas fa-swatchbook"></i> Color Palette</h4>
                        <div class="color-picker-group">
                            <div class="color-picker-item">
                                <input type="color" class="color-picker" id="primary-color" value="#1f77b4">
                                <label class="color-picker-label">Primary</label>
                            </div>
                            <div class="color-picker-item">
                                <input type="color" class="color-picker" id="secondary-color" value="#ff7f0e">
                                <label class="color-picker-label">Secondary</label>
                            </div>
                            <div class="color-picker-item">
                                <input type="color" class="color-picker" id="background-color" value="#ffffff">
                                <label class="color-picker-label">Background</label>
                            </div>
                            <div class="color-picker-item">
                                <input type="color" class="color-picker" id="text-color" value="#333333">
                                <label class="color-picker-label">Text</label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="customization-section">
                        <h4><i class="fas fa-font"></i> Typography</h4>
                        <div class="font-controls">
                            <div>
                                <label>Font Family</label>
                                <select class="font-family-select" id="font-family">
                                    <option value="Arial, sans-serif">Arial</option>
                                    <option value="Times New Roman, serif">Times New Roman</option>
                                    <option value="Helvetica, sans-serif">Helvetica</option>
                                    <option value="Georgia, serif">Georgia</option>
                                    <option value="Courier New, monospace">Courier New</option>
                                </select>
                            </div>
                            <div>
                                <label>Font Size</label>
                                <div class="font-size-control">
                                    <input type="range" class="font-size-slider" id="font-size" 
                                           min="8" max="24" value="12">
                                    <span class="font-size-value" id="font-size-value">12px</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="customization-section">
                        <h4><i class="fas fa-universal-access"></i> Accessibility</h4>
                        <div class="accessibility-options">
                            <label class="checkbox-option">
                                <input type="checkbox" id="high-contrast"> High Contrast Mode
                            </label>
                            <label class="checkbox-option">
                                <input type="checkbox" id="colorblind-friendly"> Colorblind Friendly
                            </label>
                            <label class="checkbox-option">
                                <input type="checkbox" id="large-text"> Large Text
                            </label>
                        </div>
                    </div>
                    
                    <div class="theme-actions">
                        <button class="btn btn-primary" id="preview-theme">
                            <i class="fas fa-eye"></i> Preview Theme
                        </button>
                        <button class="btn btn-success" id="apply-theme">
                            <i class="fas fa-check"></i> Apply Theme
                        </button>
                        <button class="btn btn-secondary" id="save-theme">
                            <i class="fas fa-save"></i> Save Custom Theme
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Theme Preview Modal -->
            <div class="theme-preview-modal" id="theme-preview-modal">
                <div class="theme-preview-content">
                    <div class="theme-preview-header">
                        <h3 class="theme-preview-title">Theme Preview</h3>
                        <button class="theme-preview-close" id="close-preview">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="theme-preview-body">
                        <div class="theme-preview-plots" id="preview-plots">
                            <!-- Preview plots will be generated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        this.setupThemeInteractions();
    }
    
    renderThemeCards() {
        return Object.entries(this.availableThemes).map(([key, theme]) => {
            const isActive = key === this.currentTheme ? 'active' : '';
            const category = this.getThemeCategory(key);
            const colors = this.getThemeColors(key);
            
            return `
                <div class="theme-card ${isActive}" data-theme="${key}">
                    <div class="theme-category">${category}</div>
                    <h4 class="theme-name">${theme.theme_name || key}</h4>
                    <p class="theme-description">${theme.description || 'Custom theme'}</p>
                    <div class="theme-colors">
                        ${colors.map(color => `<div class="theme-color-dot" style="background-color: ${color}"></div>`).join('')}
                    </div>
                    ${this.hasAccessibilityFeatures(key) ? '<span class="accessibility-badge">Accessible</span>' : ''}
                </div>
            `;
        }).join('');
    }
    
    getThemeCategory(themeKey) {
        const categories = {
            'default': 'Scientific',
            'dark': 'Dark Mode',
            'colorblind_friendly': 'Accessibility',
            'high_contrast': 'Accessibility',
            'publication': 'Publication',
            'vibrant': 'Creative'
        };
        return categories[themeKey] || 'Custom';
    }
    
    getThemeColors(themeKey) {
        const colorSets = {
            'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'dark': ['#8b5a96', '#d1729b', '#7a9e9f', '#b8860b', '#9b59b6'],
            'colorblind_friendly': ['#0173b2', '#de8f05', '#029e73', '#cc78bc', '#ca9161'],
            // Replace black with white in UI palette for high contrast
            'high_contrast': ['#ffffff', '#ff0000', '#00ff00', '#0000ff', '#ff00ff'],
            'publication': ['#000000', '#666666', '#cccccc', '#999999', '#333333'],
            'vibrant': ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
        };
        return colorSets[themeKey] || ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'];
    }
    
    hasAccessibilityFeatures(themeKey) {
        return ['colorblind_friendly', 'high_contrast'].includes(themeKey);
    }
    
    setupEventListeners() {
        // Global theme change events
        document.addEventListener('click', (e) => {
            if (e.target.closest('.theme-card')) {
                this.handleThemeCardClick(e.target.closest('.theme-card'));
            }
        });
        
        // Keyboard navigation for themes
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.closest('.theme-card')) {
                this.handleThemeCardClick(e.target.closest('.theme-card'));
            }
        });
    }
    
    setupThemeInteractions() {
        // Theme card interactions
        document.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('click', () => this.selectTheme(card.dataset.theme));
            card.addEventListener('dblclick', () => this.toggleCustomization());
        });
        
        // Customization controls
        const fontSizeSlider = document.getElementById('font-size');
        const fontSizeValue = document.getElementById('font-size-value');
        
        if (fontSizeSlider && fontSizeValue) {
            fontSizeSlider.addEventListener('input', (e) => {
                fontSizeValue.textContent = `${e.target.value}px`;
            });
        }
        
        // Action buttons
        const previewBtn = document.getElementById('preview-theme');
        const applyBtn = document.getElementById('apply-theme');
        const saveBtn = document.getElementById('save-theme');
        const closeBtn = document.getElementById('close-preview');
        const iconTrigger = document.getElementById('theme-icon-trigger');
        const collapseBtn = document.getElementById('collapse-themes');
        
        if (previewBtn) previewBtn.addEventListener('click', () => this.previewTheme());
        if (applyBtn) applyBtn.addEventListener('click', () => this.applyTheme());
        if (saveBtn) saveBtn.addEventListener('click', () => this.saveCustomTheme());
        if (closeBtn) closeBtn.addEventListener('click', () => this.closePreview());
        if (iconTrigger) iconTrigger.addEventListener('click', () => this.expandThemePanel());
        if (collapseBtn) collapseBtn.addEventListener('click', () => this.collapseThemePanel());
        
        // Color picker changes
        document.querySelectorAll('.color-picker').forEach(picker => {
            picker.addEventListener('change', () => this.updateCustomTheme());
        });
        
        // Font family changes
        const fontSelect = document.getElementById('font-family');
        if (fontSelect) {
            fontSelect.addEventListener('change', () => this.updateCustomTheme());
        }
        
        // Accessibility options
        document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateCustomTheme());
        });
    }
    
    handleThemeCardClick(card) {
        const themeName = card.dataset.theme;
        this.selectTheme(themeName);
    }
    
    selectTheme(themeName) {
        // Update active state
        document.querySelectorAll('.theme-card').forEach(card => {
            card.classList.toggle('active', card.dataset.theme === themeName);
        });
        
        this.currentTheme = themeName;
        this.showMessage(`Selected theme: ${themeName}`, 'success');
        
        // Auto-preview if not custom theme
        if (themeName !== 'custom') {
            this.hideCustomization();
        }
    }
    
    toggleCustomization() {
        const customization = document.getElementById('theme-customization');
        if (customization) {
            customization.classList.toggle('active');
        }
    }
    
    hideCustomization() {
        const customization = document.getElementById('theme-customization');
        if (customization) {
            customization.classList.remove('active');
        }
    }
    
    expandThemePanel() {
        const iconTrigger = document.getElementById('theme-icon-trigger');
        const expandedPanel = document.getElementById('theme-expanded-panel');
        
        if (iconTrigger && expandedPanel) {
            iconTrigger.style.display = 'none';
            expandedPanel.style.display = 'block';
            expandedPanel.style.animation = 'slideDown 0.3s ease-out';
        }
    }
    
    collapseThemePanel() {
        const iconTrigger = document.getElementById('theme-icon-trigger');
        const expandedPanel = document.getElementById('theme-expanded-panel');
        
        if (iconTrigger && expandedPanel) {
            expandedPanel.style.display = 'none';
            iconTrigger.style.display = 'block';
        }
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
    
    async previewTheme() {
        this.showLoading('Generating theme preview...');
        
        try {
            const themeData = this.currentTheme === 'custom' && this.customTheme 
                ? this.customTheme 
                : { theme_name: this.currentTheme };
                
            const base = (window.API_BASE_URL || '/backend');
            const response = await fetch(`${base}/themes/preview/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(themeData)
            });
            
            if (!response.ok) throw new Error('Failed to generate preview');
            
            const previewData = await response.json();
            this.showPreviewModal(previewData);
            
        } catch (error) {
            console.error('Error generating preview:', error);
            this.showMessage('Failed to generate theme preview', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async applyTheme() {
        this.showLoading('Applying theme...');
        
        try {
            const themeData = this.currentTheme === 'custom' && this.customTheme 
                ? this.customTheme 
                : { theme_name: this.currentTheme };
                
            const base = (window.API_BASE_URL || '/backend');
            const response = await fetch(`${base}/themes/current/${this.currentTheme}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) throw new Error('Failed to apply theme');
            
            this.showMessage(`Theme "${this.currentTheme}" applied successfully!`, 'success');
            
            // Trigger plot regeneration if on visualization page
            if (window.location.pathname.includes('visualization')) {
                this.regeneratePlots();
            }
            
        } catch (error) {
            console.error('Error applying theme:', error);
            this.showMessage('Failed to apply theme', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async saveCustomTheme() {
        if (!this.customTheme) {
            this.showMessage('Please customize theme settings first', 'error');
            return;
        }
        
        const themeName = prompt('Enter a name for your custom theme:');
        if (!themeName) return;
        
        this.showLoading('Saving custom theme...');
        
        try {
            const themeData = {
                ...this.customTheme,
                theme_name: themeName
            };
            
            const base = (window.API_BASE_URL || '/backend');
            const response = await fetch(`${base}/themes/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(themeData)
            });
            
            if (!response.ok) throw new Error('Failed to save theme');
            
            this.availableThemes[themeName] = themeData;
            this.recreateThemeGrid();
            this.showMessage(`Custom theme "${themeName}" saved successfully!`, 'success');
            
        } catch (error) {
            console.error('Error saving theme:', error);
            this.showMessage('Failed to save custom theme', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    showPreviewModal(previewData) {
        const modal = document.getElementById('theme-preview-modal');
        const plotsContainer = document.getElementById('preview-plots');
        const content = modal ? modal.querySelector('.theme-preview-content') : null;
        const body = modal ? modal.querySelector('.theme-preview-body') : null;

        if (modal && plotsContainer) {
            plotsContainer.innerHTML = previewData.html || '<p>Preview not available</p>';

            // Apply high-contrast preview styling only for this theme
            const isHighContrast = this.currentTheme === 'high_contrast';
            if (content && body) {
                content.classList.toggle('high-contrast', isHighContrast);
                body.classList.toggle('high-contrast', isHighContrast);
            }

            modal.style.display = 'block';
        }
    }
    
    closePreview() {
        const modal = document.getElementById('theme-preview-modal');
        if (modal) {
            const content = modal.querySelector('.theme-preview-content');
            const body = modal.querySelector('.theme-preview-body');
            if (content) content.classList.remove('high-contrast');
            if (body) body.classList.remove('high-contrast');
            modal.style.display = 'none';
        }
    }
    
    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('theme-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'theme-message';
            messageEl.className = 'theme-message';
            
            const container = document.querySelector('.theme-selector-container');
            if (container) {
                container.insertBefore(messageEl, container.firstChild);
            }
        }
        
        messageEl.className = `theme-message ${type}`;
        messageEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 5000);
    }
    
    showLoading(message = 'Loading...') {
        const container = document.querySelector('.theme-selector-container');
        if (container) {
            const loading = document.createElement('div');
            loading.id = 'theme-loading';
            loading.className = 'theme-loading';
            loading.textContent = message;
            container.appendChild(loading);
        }
    }
    
    hideLoading() {
        const loading = document.getElementById('theme-loading');
        if (loading && loading.parentNode) {
            loading.parentNode.removeChild(loading);
        }
    }
    
    recreateThemeGrid() {
        const grid = document.querySelector('.theme-grid');
        if (grid) {
            grid.innerHTML = this.renderThemeCards();
            this.setupThemeInteractions();
        }
    }
    
    async regeneratePlots() {
        // Trigger plot regeneration on visualization page
        if (window.regenerateAllPlots && typeof window.regenerateAllPlots === 'function') {
            window.regenerateAllPlots();
        }
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('theme-selector-container')) {
        window.themeManager = new ThemeManager();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
