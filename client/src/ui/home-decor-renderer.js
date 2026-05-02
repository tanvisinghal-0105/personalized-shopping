/**
 * Home Decor UI Renderer - Phase 1
 *
 * Renders interactive UI elements (room selector, style cards, color chips)
 * inline in the chat based on ui_data from backend tool responses.
 */

import { PhotoUploadHandler } from './photo-upload-handler.js';

export class HomeDecorRenderer {
  constructor(api, outputContainer) {
    this.api = api;
    this.output = outputContainer;
    this.currentSessionId = null;
    this.selectedRoom = null;
    this.selectedStyles = [];
    this.selectedColors = [];
    this.renderedMoodboards = new Set();
    this._selectedDimensions = null;
    this._vizSelectedProducts = [];
    this.photoUploadHandler = new PhotoUploadHandler();
    this._initLightbox();
  }

  /**
   * Create a reusable fullscreen lightbox overlay for images
   */
  _initLightbox() {
    if (document.getElementById('decor-lightbox')) return;

    const overlay = document.createElement('div');
    overlay.id = 'decor-lightbox';
    overlay.style.cssText = `
      display:none; position:fixed; inset:0; z-index:9999;
      background:rgba(5,6,15,0.92); backdrop-filter:blur(8px);
      align-items:center; justify-content:center; cursor:zoom-out;
    `;

    const inner = document.createElement('div');
    inner.style.cssText = `
      position:relative; max-width:90vw; max-height:90vh;
      display:flex; flex-direction:column; align-items:center;
    `;

    const img = document.createElement('img');
    img.id = 'decor-lightbox-img';
    img.style.cssText = `
      max-width:90vw; max-height:80vh; object-fit:contain;
      border-radius:12px; box-shadow:0 8px 32px rgba(0,0,0,0.6);
    `;

    const caption = document.createElement('div');
    caption.id = 'decor-lightbox-caption';
    caption.style.cssText = `
      color:#e4e4f0; font-size:14px; margin-top:12px;
      text-align:center; max-width:600px;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:28px;">close</span>';
    closeBtn.style.cssText = `
      position:absolute; top:-40px; right:-8px;
      background:none; border:none; color:#8888a8;
      cursor:pointer; padding:4px;
    `;
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this._closeLightbox();
    });

    inner.appendChild(closeBtn);
    inner.appendChild(img);
    inner.appendChild(caption);
    overlay.appendChild(inner);

    overlay.addEventListener('click', () => this._closeLightbox());
    inner.addEventListener('click', (e) => e.stopPropagation());

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this._closeLightbox();
    });

    document.body.appendChild(overlay);
  }

  _openLightbox(src, captionText) {
    const overlay = document.getElementById('decor-lightbox');
    const img = document.getElementById('decor-lightbox-img');
    const caption = document.getElementById('decor-lightbox-caption');
    if (!overlay || !img) return;
    img.src = src;
    caption.textContent = captionText || '';
    overlay.style.display = 'flex';
  }

  _closeLightbox() {
    const overlay = document.getElementById('decor-lightbox');
    if (overlay) overlay.style.display = 'none';
  }

  /**
   * Main entry point - parses tool response and renders appropriate UI
   */
  renderUIData(uiData, sessionId) {
    if (!uiData || !uiData.display_type) {
      console.warn('[HomeDecor] No ui_data or display_type found');
      return;
    }

    this.currentSessionId = sessionId;
    console.log(`[HomeDecor] Rendering ${uiData.display_type}`, uiData);

    switch (uiData.display_type) {
      case 'room_selector':
        this.renderRoomSelector(uiData);
        break;
      case 'style_selector':
        this.renderStyleSelector(uiData);
        break;
      case 'color_selector':
        this.renderColorSelector(uiData);
        break;
      case 'room_dimensions':
        this.renderRoomDimensions(uiData);
        break;
      case 'photo_upload':
        this.renderPhotoUpload(uiData);
        break;
      case 'moodboard':
        this.renderMoodboard(uiData);
        break;
      case 'room_visualization':
        this.renderRoomVisualization(uiData);
        break;
      default:
        console.warn(`[HomeDecor] Unknown display_type: ${uiData.display_type}`);
    }
  }

  /**
   * Render Room Selector Cards
   */
  renderRoomSelector(uiData) {
    const wrapper = this.createMessageWrapper('decor-ui');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-selector-bubble');

    // Title section
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold mb-2 text-[#e4e4f0]';
    title.textContent = uiData.title || 'Select a room';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-[#8888a8] mb-4';
      subtitle.textContent = uiData.subtitle;
      bubble.appendChild(subtitle);
    }

    // Room grid
    const roomGrid = document.createElement('div');
    roomGrid.className = 'grid grid-cols-3 gap-3 my-4';

    uiData.room_options.forEach(room => {
      const roomCard = this.createRoomCard(room);
      roomGrid.appendChild(roomCard);
    });

    bubble.appendChild(roomGrid);

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-[#555570] mt-3 text-center';
    instructions.textContent = 'Click a room or say it by voice';
    bubble.appendChild(instructions);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Create individual room card
   */
  createRoomCard(room) {
    const card = document.createElement('div');
    card.className = 'room-card border-2 border-transparent rounded-xl p-4 cursor-pointer transition-all text-center';
    card.dataset.roomId = room.id;

    // Icon
    const icon = document.createElement('div');
    icon.className = 'text-4xl mb-2';
    icon.textContent = room.icon;
    card.appendChild(icon);

    // Label
    const label = document.createElement('div');
    label.className = 'text-sm font-semibold';
    label.textContent = room.label;
    card.appendChild(label);

    // Click handler
    card.addEventListener('click', () => {
      this.handleRoomSelection(room.id, room.label);
    });

    return card;
  }

  /**
   * Render Style Selector Cards
   */
  renderStyleSelector(uiData) {
    // Reset selected styles for fresh selection
    this.selectedStyles = [];

    const wrapper = this.createMessageWrapper('decor-ui');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-selector-bubble');

    // Title
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold mb-2 text-[#e4e4f0]';
    title.textContent = uiData.title || 'Choose your style';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-[#8888a8] mb-4';
      subtitle.textContent = uiData.subtitle;
      bubble.appendChild(subtitle);
    }

    // Style grid
    const styleGrid = document.createElement('div');
    styleGrid.className = 'grid grid-cols-2 md:grid-cols-3 gap-4 my-4';

    uiData.style_options.forEach(style => {
      const styleCard = this.createStyleCard(style);
      styleGrid.appendChild(styleCard);
    });

    bubble.appendChild(styleGrid);

    // Continue button
    const continueBtn = document.createElement('button');
    continueBtn.className = 'w-full btn-neon-fill py-3 rounded-lg font-semibold mt-4 disabled:opacity-50 disabled:cursor-not-allowed';
    continueBtn.textContent = 'Continue';
    continueBtn.disabled = true;
    continueBtn.id = 'stylesContinueBtn';
    continueBtn.addEventListener('click', () => {
      this.handleStyleSelection();
    });
    bubble.appendChild(continueBtn);

    // Personalisation notice
    if (uiData.personalizing_in_progress) {
      const notice = document.createElement('div');
      notice.id = 'style-personalizing-notice';
      notice.className = 'text-sm text-[#00f0ff] mt-3 text-center animate-pulse';
      notice.textContent = 'Personalising styles to your room photo -- images will update shortly...';
      bubble.appendChild(notice);
    }

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-[#555570] mt-3 text-center';
    instructions.textContent = 'Select one or more styles, or say them by voice';
    bubble.appendChild(instructions);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Create individual style card
   */
  createStyleCard(style) {
    const card = document.createElement('div');
    card.className = 'style-card relative border-3 border-transparent rounded-xl overflow-hidden cursor-pointer transition-all';
    card.dataset.styleId = style.id;

    // Image container
    const imageContainer = document.createElement('div');
    imageContainer.className = 'w-full h-48 bg-[rgba(255,255,255,0.03)] overflow-hidden';

    // Use image_url from backend if provided, otherwise use a style-based placeholder
    const img = document.createElement('img');
    const gcsBase = window.__GCS_ASSETS_BASE || '';
    img.src = style.image_url || `${gcsBase}/${style.id}_style_preview.jpg`;
    img.alt = style.label;
    img.className = 'w-full h-full object-cover';
    img.loading = 'lazy';
    img.onerror = () => {
      img.style.display = 'none';
      const placeholder = document.createElement('div');
      placeholder.className = 'w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-[rgba(255,255,255,0.05)] to-[rgba(255,255,255,0.02)]';
      placeholder.textContent = '🏠';
      imageContainer.appendChild(placeholder);
    };
    // Click image to open lightbox
    img.addEventListener('click', (e) => {
      e.stopPropagation();
      this._openLightbox(img.src, `${style.label} - ${style.description || ''}`);
    });
    imageContainer.appendChild(img);
    card.appendChild(imageContainer);

    // Content
    const content = document.createElement('div');
    content.className = 'style-card-content';

    const name = document.createElement('div');
    name.className = 'style-card-name';
    name.textContent = style.label;
    content.appendChild(name);

    if (style.description) {
      const desc = document.createElement('div');
      desc.className = 'style-card-desc';
      desc.textContent = style.description;
      content.appendChild(desc);
    }

    card.appendChild(content);

    // Checkmark overlay
    const checkmark = document.createElement('div');
    checkmark.className = 'absolute top-2 right-2 w-8 h-8 bg-[#00f0ff] text-[#05060f] rounded-full hidden items-center justify-center';
    checkmark.innerHTML = '<span class="material-symbols-outlined text-lg">check</span>';
    card.appendChild(checkmark);

    // Click handler
    card.addEventListener('click', () => {
      this.toggleStyleCard(card, style.id);
    });

    return card;
  }

  /**
   * Toggle style card selection (multi-select)
   */
  toggleStyleCard(card, styleId) {
    const isSelected = card.classList.toggle('selected');
    const checkmark = card.querySelector('.absolute');

    if (isSelected) {
      card.classList.add('border-[#00f0ff]', 'shadow-xl');
      checkmark.classList.remove('hidden');
      checkmark.classList.add('flex');
      this.selectedStyles.push(styleId);
    } else {
      card.classList.remove('border-[#00f0ff]', 'shadow-xl');
      checkmark.classList.add('hidden');
      checkmark.classList.remove('flex');
      this.selectedStyles = this.selectedStyles.filter(id => id !== styleId);
    }

    // Enable/disable continue button - find within the same bubble, not globally
    const bubble = card.closest('.decor-selector-bubble');
    const continueBtn = bubble ? bubble.querySelector('#stylesContinueBtn') : document.getElementById('stylesContinueBtn');
    if (continueBtn) {
      continueBtn.disabled = this.selectedStyles.length === 0;
    }
  }

  /**
   * Render Color Selector Chips
   */
  renderColorSelector(uiData) {
    const wrapper = this.createMessageWrapper('decor-ui');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-selector-bubble');

    // Title
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold mb-2 text-[#e4e4f0]';
    title.textContent = uiData.title || 'Choose colors';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-[#8888a8] mb-4';
      subtitle.textContent = uiData.subtitle;
      bubble.appendChild(subtitle);
    }

    // Color chips container
    const colorChips = document.createElement('div');
    colorChips.className = 'flex flex-wrap gap-3 my-4';

    uiData.color_options.forEach(color => {
      const chip = this.createColorChip(color);
      colorChips.appendChild(chip);
    });

    bubble.appendChild(colorChips);

    // Action buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex gap-3 mt-4';

    if (uiData.skip_allowed) {
      const skipBtn = document.createElement('button');
      skipBtn.className = 'flex-1 decor-btn-secondary py-3 rounded-lg font-semibold';
      skipBtn.textContent = 'Skip';
      skipBtn.addEventListener('click', () => {
        this.handleColorSelection(true); // skip=true
      });
      buttonContainer.appendChild(skipBtn);
    }

    const continueBtn = document.createElement('button');
    continueBtn.className = 'flex-1 btn-neon-fill py-3 rounded-lg font-semibold';
    continueBtn.textContent = 'Continue';
    continueBtn.id = 'colorsContinueBtn';
    continueBtn.addEventListener('click', () => {
      this.handleColorSelection(false);
    });
    buttonContainer.appendChild(continueBtn);

    bubble.appendChild(buttonContainer);

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-[#555570] mt-3 text-center';
    instructions.textContent = 'Select colors, skip, or say them by voice';
    bubble.appendChild(instructions);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Create individual color chip
   */
  createColorChip(color) {
    const chip = document.createElement('div');
    chip.className = 'relative';

    const button = document.createElement('button');
    button.className = 'w-14 h-14 rounded-full border-3 border-transparent cursor-pointer hover:scale-110 transition-transform';
    button.style.backgroundColor = color.hex;
    button.dataset.colorId = color.id;
    button.title = `${color.label} - ${color.description}`;

    // Checkmark
    const checkmark = document.createElement('span');
    checkmark.className = 'material-symbols-outlined absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white hidden';
    checkmark.style.textShadow = '0 2px 4px rgba(0,0,0,0.5)';
    checkmark.textContent = 'check';
    button.appendChild(checkmark);

    // Click handler
    button.addEventListener('click', () => {
      this.toggleColorChip(button, color.id);
    });

    // Label below
    const label = document.createElement('div');
    label.className = 'text-xs text-center mt-1 text-[#8888a8]';
    label.textContent = color.label;

    chip.appendChild(button);
    chip.appendChild(label);

    return chip;
  }

  /**
   * Toggle color chip selection
   */
  toggleColorChip(button, colorId) {
    const isSelected = button.classList.toggle('selected');
    const checkmark = button.querySelector('.material-symbols-outlined');

    if (isSelected) {
      button.classList.add('border-[#00f0ff]', 'ring-4', 'ring-[#00f0ff]', 'ring-opacity-30');
      checkmark.classList.remove('hidden');
      this.selectedColors.push(colorId);
    } else {
      button.classList.remove('border-[#00f0ff]', 'ring-4', 'ring-[#00f0ff]', 'ring-opacity-30');
      checkmark.classList.add('hidden');
      this.selectedColors = this.selectedColors.filter(id => id !== colorId);
    }
  }

  /**
   * Render Room Dimensions selector (Phase 2)
   */
  renderRoomDimensions(uiData) {
    const wrapper = this.createMessageWrapper('decor-ui');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-selector-bubble');

    // Title
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold mb-2 text-[#e4e4f0]';
    title.textContent = uiData.title || 'Room dimensions';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-[#8888a8] mb-4';
      subtitle.textContent = uiData.subtitle;
      bubble.appendChild(subtitle);
    }

    // Preset size cards
    if (uiData.presets && uiData.presets.length > 0) {
      const presetGrid = document.createElement('div');
      presetGrid.className = 'grid grid-cols-3 gap-3 my-4';

      uiData.presets.forEach(preset => {
        const card = document.createElement('div');
        card.className = 'room-size-card border-2 border-transparent rounded-xl p-4 cursor-pointer transition-all text-center';
        card.dataset.presetId = preset.id;

        const icon = document.createElement('div');
        icon.className = 'text-2xl mb-1';
        icon.textContent = preset.id === 'small' ? '\u25AB' : preset.id === 'medium' ? '\u25AB\u25AB' : '\u25AB\u25AB\u25AB';
        card.appendChild(icon);

        const label = document.createElement('div');
        label.className = 'text-sm font-semibold';
        label.textContent = preset.label;
        card.appendChild(label);

        const dims = document.createElement('div');
        dims.className = 'text-xs text-[#555570] mt-1';
        dims.textContent = `${preset.length}m x ${preset.width}m`;
        card.appendChild(dims);

        const area = document.createElement('div');
        area.className = 'text-xs text-[#555570] mt-0.5';
        area.textContent = preset.description;
        card.appendChild(area);

        card.addEventListener('click', () => {
          // Deselect all
          presetGrid.querySelectorAll('.room-size-card').forEach(c => {
            c.classList.remove('selected', 'border-[#00f0ff]', 'bg-[rgba(0,240,255,0.08)]', 'shadow-xl');
          });
          // Select this one
          card.classList.add('selected', 'border-[#00f0ff]', 'bg-[rgba(0,240,255,0.08)]', 'shadow-xl');
          // Clear custom inputs
          const lengthInput = bubble.querySelector('#dimLengthInput');
          const widthInput = bubble.querySelector('#dimWidthInput');
          if (lengthInput) lengthInput.value = preset.length;
          if (widthInput) widthInput.value = preset.width;
          this._selectedDimensions = { length: preset.length, width: preset.width };
          // Enable submit
          const submitBtn = bubble.querySelector('#dimSubmitBtn');
          if (submitBtn) submitBtn.disabled = false;
        });

        presetGrid.appendChild(card);
      });

      bubble.appendChild(presetGrid);
    }

    // Divider
    const divider = document.createElement('div');
    divider.className = 'flex items-center gap-3 my-4';
    divider.innerHTML = '<div class="flex-1 h-px bg-[rgba(255,255,255,0.08)]"></div><span class="text-xs text-[#555570]">or enter custom</span><div class="flex-1 h-px bg-[rgba(255,255,255,0.08)]"></div>';
    bubble.appendChild(divider);

    // Custom dimension inputs
    const customContainer = document.createElement('div');
    customContainer.className = 'flex gap-4 items-end';

    const customConfig = uiData.custom_input || {};

    // Length input
    const lengthGroup = document.createElement('div');
    lengthGroup.className = 'flex-1';
    const lengthLabel = document.createElement('label');
    lengthLabel.className = 'text-xs text-[#8888a8] block mb-1';
    lengthLabel.textContent = customConfig.length_label || 'Length (m)';
    lengthGroup.appendChild(lengthLabel);
    const lengthInput = document.createElement('input');
    lengthInput.type = 'number';
    lengthInput.id = 'dimLengthInput';
    lengthInput.className = 'input-glass w-full text-sm';
    lengthInput.min = customConfig.length_min || 1.5;
    lengthInput.max = customConfig.length_max || 12.0;
    lengthInput.step = customConfig.step || 0.5;
    lengthInput.placeholder = 'e.g. 4.0';
    lengthGroup.appendChild(lengthInput);
    customContainer.appendChild(lengthGroup);

    // x label
    const xLabel = document.createElement('div');
    xLabel.className = 'text-[#555570] pb-2 font-bold';
    xLabel.textContent = 'x';
    customContainer.appendChild(xLabel);

    // Width input
    const widthGroup = document.createElement('div');
    widthGroup.className = 'flex-1';
    const widthLabel = document.createElement('label');
    widthLabel.className = 'text-xs text-[#8888a8] block mb-1';
    widthLabel.textContent = customConfig.width_label || 'Width (m)';
    widthGroup.appendChild(widthLabel);
    const widthInput = document.createElement('input');
    widthInput.type = 'number';
    widthInput.id = 'dimWidthInput';
    widthInput.className = 'input-glass w-full text-sm';
    widthInput.min = customConfig.width_min || 1.5;
    widthInput.max = customConfig.width_max || 12.0;
    widthInput.step = customConfig.step || 0.5;
    widthInput.placeholder = 'e.g. 3.5';
    widthGroup.appendChild(widthInput);
    customContainer.appendChild(widthGroup);

    bubble.appendChild(customContainer);

    // Custom input change listeners - deselect presets and enable submit
    const onCustomChange = () => {
      const l = parseFloat(lengthInput.value);
      const w = parseFloat(widthInput.value);
      if (l > 0 && w > 0) {
        // Deselect preset cards
        bubble.querySelectorAll('.room-size-card').forEach(c => {
          c.classList.remove('selected', 'border-[#00f0ff]', 'bg-[rgba(0,240,255,0.08)]', 'shadow-xl');
        });
        this._selectedDimensions = { length: l, width: w };
        const submitBtn = bubble.querySelector('#dimSubmitBtn');
        if (submitBtn) submitBtn.disabled = false;
      }
    };
    lengthInput.addEventListener('input', onCustomChange);
    widthInput.addEventListener('input', onCustomChange);

    // Area display
    const areaDisplay = document.createElement('div');
    areaDisplay.className = 'text-xs text-[#555570] mt-2 text-center';
    areaDisplay.id = 'dimAreaDisplay';
    areaDisplay.textContent = '';
    bubble.appendChild(areaDisplay);

    // Update area display on any change
    const updateArea = () => {
      if (this._selectedDimensions) {
        const area = (this._selectedDimensions.length * this._selectedDimensions.width).toFixed(1);
        areaDisplay.textContent = `Room area: ~${area} m2`;
      }
    };
    lengthInput.addEventListener('input', updateArea);
    widthInput.addEventListener('input', updateArea);

    // Submit button
    const submitBtn = document.createElement('button');
    submitBtn.id = 'dimSubmitBtn';
    submitBtn.className = 'w-full btn-neon-fill py-3 rounded-lg font-semibold mt-4 disabled:opacity-50 disabled:cursor-not-allowed';
    submitBtn.textContent = 'Continue';
    submitBtn.disabled = true;
    submitBtn.addEventListener('click', () => {
      if (this._selectedDimensions) {
        this.handleDimensionsSelection(this._selectedDimensions);
      }
    });
    bubble.appendChild(submitBtn);

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-[#555570] mt-3 text-center';
    instructions.textContent = 'Pick a size or type your own measurements';
    bubble.appendChild(instructions);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Handle room dimensions selection
   */
  handleDimensionsSelection(dimensions) {
    console.log(`[HomeDecor] Dimensions selected:`, dimensions);
    this.api.sendTextMessage(
      `The room is ${dimensions.length}m by ${dimensions.width}m`
    );
  }

  /**
   * Handle room selection
   */
  handleRoomSelection(roomId, roomLabel) {
    this.selectedRoom = roomId;
    console.log(`[HomeDecor] Room selected: ${roomId}`);

    // Visual feedback
    const allCards = this.output.querySelectorAll('.room-card');
    allCards.forEach(card => {
      if (card.dataset.roomId === roomId) {
        card.classList.add('selected', 'border-[#00f0ff]', 'bg-[rgba(0,240,255,0.08)]', 'shadow-xl');
      } else {
        card.classList.remove('selected', 'border-[#00f0ff]', 'bg-[rgba(0,240,255,0.08)]', 'shadow-xl');
      }
    });

    // Send to backend
    this.api.sendTextMessage(`continue_home_decor_consultation(customer_id="${this.getCurrentCustomerId()}", session_id="${this.currentSessionId}", room_type="${roomLabel.toLowerCase()}")`);
  }

  /**
   * Handle style selection
   */
  handleStyleSelection() {
    if (this.selectedStyles.length === 0) return;

    console.log(`[HomeDecor] Styles selected:`, this.selectedStyles);

    // Format styles for backend
    const stylesFormatted = this.selectedStyles.join(', ');

    // Send to backend
    this.api.sendTextMessage(`I'd like ${stylesFormatted} styles for my ${this.selectedRoom || 'room'}`);
  }

  /**
   * Handle color selection
   */
  handleColorSelection(skip = false) {
    if (skip) {
      console.log(`[HomeDecor] Colors skipped`);
      this.api.sendTextMessage(`I'll skip color preferences for now`);
    } else {
      console.log(`[HomeDecor] Colors selected:`, this.selectedColors);

      if (this.selectedColors.length > 0) {
        const colorsFormatted = this.selectedColors.join(', ');
        this.api.sendTextMessage(`I'd like ${colorsFormatted} colors`);
      } else {
        this.api.sendTextMessage(`I'll skip color preferences for now`);
      }
    }
  }

  /**
   * Helper: Create message wrapper
   */
  createMessageWrapper(type = 'decor-ui') {
    const wrapper = document.createElement('div');
    wrapper.classList.add('message-wrapper', 'gemini-message', `${type}-message`);
    const label = document.createElement('div');
    label.className = 'flex items-center gap-2 mb-2';
    label.innerHTML = '<div class="w-6 h-6 rounded-full bg-gradient-to-br from-[#a855f7] to-[#00f0ff] flex-shrink-0"></div><span class="text-xs font-semibold text-[#8888a8]">AI Assistant</span>';
    wrapper.appendChild(label);
    return wrapper;
  }

  /**
   * Helper: Scroll to bottom
   */
  scrollToBottom() {
    setTimeout(() => {
      this.output.scrollTo({
        top: this.output.scrollHeight,
        behavior: 'smooth'
      });
    }, 100);
  }

  /**
   * Helper: Get current customer ID from user session
   */
  getCurrentCustomerId() {
    const savedUser = localStorage.getItem('cymbalUser');
    if (savedUser) {
      const user = JSON.parse(savedUser);
      return user.customerId || 'CY-DEFAULT';
    }
    return 'CY-DEFAULT';
  }

  /**
   * Render Moodboard with product grid (Phase 2)
   */
  renderMoodboard(moodboardData) {
    if (!moodboardData || !moodboardData.products) {
      console.warn('[HomeDecor] No moodboard data or products found');
      return;
    }

    const moodboardId = moodboardData.moodboard_id;
    if (this.renderedMoodboards.has(moodboardId)) {
      console.log(`[HomeDecor] Moodboard ${moodboardId} already rendered, skipping duplicate`);
      return;
    }

    this.renderedMoodboards.add(moodboardId);
    console.log(`[HomeDecor] Rendering moodboard ${moodboardId} with ${moodboardData.products.length} products`, moodboardData);

    const wrapper = this.createMessageWrapper('decor-moodboard');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-moodboard-bubble');

    const header = document.createElement('div');
    header.className = 'moodboard-header mb-4';

    const title = document.createElement('h3');
    title.className = 'text-xl font-bold mb-2 text-[#e4e4f0]';
    title.textContent = 'Your Personalized Moodboard';
    header.appendChild(title);

    const subtitle = document.createElement('p');
    subtitle.className = 'text-sm text-[#8888a8] mb-2';
    subtitle.textContent = moodboardData.message || `Curated ${moodboardData.selected_styles?.join(' & ')} style for your ${moodboardData.room_type || 'space'}`;
    header.appendChild(subtitle);

    const productCount = document.createElement('p');
    productCount.className = 'text-xs text-[#555570]';
    productCount.textContent = `${moodboardData.product_count || moodboardData.products.length} curated products`;
    header.appendChild(productCount);

    bubble.appendChild(header);

    const productsGrid = document.createElement('div');
    productsGrid.className = 'grid grid-cols-2 md:grid-cols-3 gap-4 my-4';

    moodboardData.products.forEach(product => {
      const productCard = this.createMoodboardProductCard(product);
      productsGrid.appendChild(productCard);
    });

    bubble.appendChild(productsGrid);

    const footer = document.createElement('div');
    footer.className = 'moodboard-footer mt-4 pt-4 border-t border-[rgba(255,255,255,0.08)]';

    // --- Cart action buttons ---
    const cartActions = document.createElement('div');
    cartActions.className = 'flex gap-3 mb-4';

    const addSelectedBtn = document.createElement('button');
    addSelectedBtn.className = 'flex-1 btn-neon-fill py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed';
    addSelectedBtn.textContent = 'Add Selected to Cart';
    addSelectedBtn.disabled = true;
    addSelectedBtn.id = 'addSelectedToCartBtn';
    cartActions.appendChild(addSelectedBtn);

    const addAllMoodboardBtn = document.createElement('button');
    addAllMoodboardBtn.className = 'flex-1 decor-btn-secondary py-3 rounded-lg font-semibold';
    addAllMoodboardBtn.textContent = 'Add All to Cart';
    addAllMoodboardBtn.addEventListener('click', () => {
      const allProducts = moodboardData.products || [];
      if (allProducts.length > 0) {
        addAllMoodboardBtn.textContent = 'Adding...';
        addAllMoodboardBtn.disabled = true;
        const names = allProducts.map(p => p.name).join(', ');
        this.api.sendTextMessage(`Please add all these items to my cart: ${names}`);
        setTimeout(() => {
          addAllMoodboardBtn.textContent = 'Added All!';
          addAllMoodboardBtn.classList.add('opacity-50');
        }, 2000);
      }
    });
    cartActions.appendChild(addAllMoodboardBtn);

    footer.appendChild(cartActions);

    // --- Visualization selection panel (always present, collapsed initially) ---
    const vizPanel = document.createElement('div');
    vizPanel.className = 'viz-panel';
    vizPanel.dataset.state = 'collapsed';

    // Expand button
    const vizExpandBtn = document.createElement('button');
    vizExpandBtn.className = 'w-full btn-violet-fill py-3 rounded-lg font-semibold mb-2 flex items-center justify-center gap-2';
    vizExpandBtn.innerHTML = '<span class="material-symbols-outlined text-lg">auto_awesome</span> Visualize in my room';
    vizPanel.appendChild(vizExpandBtn);

    // Selection controls (hidden until expanded)
    const vizControls = document.createElement('div');
    vizControls.className = 'viz-controls p-3 bg-[rgba(168,85,247,0.05)] rounded-lg border border-[rgba(168,85,247,0.2)] mb-2';
    vizControls.style.display = 'none';

    const vizLabel = document.createElement('p');
    vizLabel.className = 'text-sm text-[#c084fc] text-center mb-2 font-medium';
    vizLabel.textContent = 'Tap products above to select them';
    vizControls.appendChild(vizLabel);

    const vizActions = document.createElement('div');
    vizActions.className = 'flex gap-2';

    const selectAllBtn = document.createElement('button');
    selectAllBtn.className = 'flex-1 decor-btn-secondary py-2 rounded-lg text-sm font-semibold';
    selectAllBtn.textContent = 'Select All';
    vizActions.appendChild(selectAllBtn);

    const generateBtn = document.createElement('button');
    generateBtn.className = 'flex-1 btn-violet-fill py-2 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed';
    generateBtn.textContent = 'Generate';
    generateBtn.disabled = true;
    vizActions.appendChild(generateBtn);

    vizControls.appendChild(vizActions);
    vizPanel.appendChild(vizControls);
    footer.appendChild(vizPanel);

    // Track selected product IDs for this moodboard
    const vizState = { selectedIds: [], active: false };

    const updateVizUI = () => {
      const count = vizState.selectedIds.length;
      vizLabel.textContent = count > 0
        ? `${count} product${count > 1 ? 's' : ''} selected`
        : 'Tap products above to select them';
      generateBtn.disabled = count === 0;
      generateBtn.textContent = 'Generate';
      generateBtn.classList.remove('opacity-50');
      // Also update cart selected button
      addSelectedBtn.disabled = count === 0;
      addSelectedBtn.textContent = count > 0
        ? `Add ${count} Selected to Cart`
        : 'Add Selected to Cart';
    };

    // Wire up Add Selected to Cart
    addSelectedBtn.addEventListener('click', () => {
      if (vizState.selectedIds.length > 0) {
        addSelectedBtn.textContent = 'Adding...';
        addSelectedBtn.disabled = true;
        const selectedProducts = (moodboardData.products || []).filter(
          p => vizState.selectedIds.includes(p.product_id)
        );
        const names = selectedProducts.map(p => p.name).join(', ');
        this.api.sendTextMessage(`Please add these items to my cart: ${names}`);
        setTimeout(() => {
          addSelectedBtn.textContent = 'Added!';
          addSelectedBtn.classList.add('opacity-50');
        }, 2000);
      }
    });

    const setCardSelected = (card, selected) => {
      const indicator = card.querySelector('.viz-indicator');
      if (selected) {
        card.style.outline = '3px solid #a855f7';
        card.style.outlineOffset = '-1px';
        if (indicator) {
          indicator.style.background = '#a855f7';
          indicator.innerHTML = '<span class="material-symbols-outlined" style="color:#fff;font-size:16px">check</span>';
        }
      } else {
        card.style.outline = '';
        card.style.outlineOffset = '';
        if (indicator) {
          indicator.style.background = 'rgba(10,14,39,0.8)';
          indicator.innerHTML = '';
        }
      }
    };

    // Add selection indicators to all product cards upfront (hidden until active)
    const allCards = bubble.querySelectorAll('.moodboard-product-card');
    allCards.forEach(card => {
      card.style.position = 'relative';
      const indicator = document.createElement('div');
      indicator.className = 'viz-indicator';
      indicator.style.cssText = 'position:absolute;top:8px;left:8px;width:28px;height:28px;border-radius:50%;border:2px solid #a855f7;background:rgba(10,14,39,0.8);display:none;align-items:center;justify-content:center;z-index:20;pointer-events:none;transition:all 0.15s;';
      card.appendChild(indicator);
    });

    // Expand/collapse handler
    vizExpandBtn.addEventListener('click', () => {
      vizState.active = !vizState.active;
      if (vizState.active) {
        vizControls.style.display = 'block';
        vizExpandBtn.innerHTML = '<span class="material-symbols-outlined text-lg">close</span> Cancel selection';
        vizExpandBtn.className = 'w-full decor-btn-secondary py-3 rounded-lg font-semibold mb-2 flex items-center justify-center gap-2';
        // Show indicators
        allCards.forEach(card => {
          const ind = card.querySelector('.viz-indicator');
          if (ind) ind.style.display = 'flex';
        });
      } else {
        vizControls.style.display = 'none';
        vizExpandBtn.innerHTML = '<span class="material-symbols-outlined text-lg">auto_awesome</span> Visualize in my room';
        vizExpandBtn.className = 'w-full btn-violet-fill py-3 rounded-lg font-semibold mb-2 flex items-center justify-center gap-2';
        // Hide indicators and clear selection
        vizState.selectedIds = [];
        allCards.forEach(card => {
          const ind = card.querySelector('.viz-indicator');
          if (ind) ind.style.display = 'none';
          setCardSelected(card, false);
        });
        updateVizUI();
      }
      this.scrollToBottom();
    });

    // Card click handler for selection (only when viz mode is active)
    allCards.forEach(card => {
      card.addEventListener('click', (e) => {
        if (!vizState.active) return;
        if (e.target.closest('button')) return; // Don't block Add to Cart
        e.stopPropagation();

        const pid = card.dataset.productId;
        const idx = vizState.selectedIds.indexOf(pid);
        if (idx === -1) {
          vizState.selectedIds.push(pid);
          setCardSelected(card, true);
        } else {
          vizState.selectedIds.splice(idx, 1);
          setCardSelected(card, false);
        }
        updateVizUI();
      });
    });

    // Select All
    selectAllBtn.addEventListener('click', () => {
      vizState.selectedIds = [];
      allCards.forEach(card => {
        vizState.selectedIds.push(card.dataset.productId);
        setCardSelected(card, true);
      });
      updateVizUI();
    });

    // Generate
    generateBtn.addEventListener('click', () => {
      if (vizState.selectedIds.length === 0) return;
      generateBtn.textContent = 'Generating...';
      generateBtn.disabled = true;
      generateBtn.classList.add('opacity-50');

      // Safety reset after 60s
      setTimeout(() => {
        if (generateBtn.textContent === 'Generating...') {
          generateBtn.textContent = 'Generate';
          generateBtn.disabled = false;
          generateBtn.classList.remove('opacity-50');
        }
      }, 60000);

      // Send directly to backend -- bypasses Gemini agent to avoid context bloat
      this.api.sendMessage({
        type: 'visualize_room',
        data: {
          customer_id: this.getCurrentCustomerId(),
          session_id: this.currentSessionId,
          product_ids: vizState.selectedIds,
        }
      });
    });

    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-[#555570] text-center';
    instructions.textContent = 'Click on any product to add it to your cart';
    footer.appendChild(instructions);

    bubble.appendChild(footer);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Create individual product card for moodboard
   */
  createMoodboardProductCard(product) {
    const card = document.createElement('div');
    card.className = 'moodboard-product-card rounded-xl overflow-hidden cursor-pointer transition-all duration-300';
    card.dataset.productId = product.product_id;

    const imageContainer = document.createElement('div');
    imageContainer.className = 'relative w-full h-40 bg-[rgba(255,255,255,0.03)]';

    if (product.image_url) {
      const img = document.createElement('img');
      img.src = product.image_url;
      img.alt = product.name;
      img.className = 'w-full h-full object-cover';
      img.loading = 'lazy';
      img.onerror = () => {
        img.style.display = 'none';
        const placeholder = document.createElement('div');
        placeholder.className = 'w-full h-full flex items-center justify-center text-4xl';
        placeholder.textContent = '🏠';
        imageContainer.appendChild(placeholder);
      };
      // Click image to open lightbox
      img.style.cursor = 'zoom-in';
      img.addEventListener('click', (e) => {
        e.stopPropagation();
        this._openLightbox(img.src, `${product.name} - ${product.category} - ${product.price.toFixed(2)}`);
      });
      imageContainer.appendChild(img);
    } else {
      const placeholder = document.createElement('div');
      placeholder.className = 'w-full h-full flex items-center justify-center text-4xl';
      placeholder.textContent = '🏠';
      imageContainer.appendChild(placeholder);
    }

    card.appendChild(imageContainer);

    const content = document.createElement('div');
    content.className = 'p-3';

    const name = document.createElement('div');
    name.className = 'text-sm font-semibold mb-1 line-clamp-2 text-[#e4e4f0]';
    name.textContent = product.name;
    content.appendChild(name);

    const category = document.createElement('div');
    category.className = 'text-xs text-[#555570] mb-2';
    category.textContent = product.category;
    content.appendChild(category);

    const price = document.createElement('div');
    price.className = 'text-lg font-bold text-[#00f0ff] mb-2';
    price.textContent = `${product.price.toFixed(2)}`;
    content.appendChild(price);

    const addButton = document.createElement('button');
    addButton.className = 'w-full btn-neon-fill py-2 rounded-lg text-sm font-semibold';
    addButton.textContent = 'Add to Cart';
    addButton.addEventListener('click', (e) => {
      e.stopPropagation();
      this.handleAddToCart(product, e);
    });
    content.appendChild(addButton);

    card.appendChild(content);

    return card;
  }

  // toggleVisualizationMode and handleVisualizeRoom are now inline in renderMoodboard

  /**
   * Render Room Visualization (Phase 3)
   */
  renderRoomVisualization(uiData) {
    const vizId = uiData.visualization_id;
    if (this.renderedMoodboards.has(vizId)) {
      console.log(`[HomeDecor] Visualization ${vizId} already rendered, skipping`);
      return;
    }
    this.renderedMoodboards.add(vizId);
    console.log(`[HomeDecor] Rendering visualization ${vizId}`, uiData);

    // Check if we can update an existing visualization card in place
    const existingViz = this.output.querySelector('.decor-visualization-message');
    if (existingViz) {
      // Update the image
      const img = existingViz.querySelector('img');
      if (img && uiData.image_base64) {
        img.src = `data:image/jpeg;base64,${uiData.image_base64}`;
      }
      // Update subtitle
      const subtitle = existingViz.querySelector('.viz-subtitle');
      if (subtitle) {
        subtitle.textContent = uiData.message || '';
      }
      // Reset buttons
      existingViz.querySelectorAll('button').forEach(btn => {
        if (btn.textContent === 'Generating...') {
          btn.textContent = 'Try Another Look';
          btn.disabled = false;
          btn.classList.remove('opacity-50');
        }
      });
      // Reset moodboard Generate buttons too
      this.output.querySelectorAll('.viz-controls button').forEach(btn => {
        if (btn.textContent === 'Generating...') {
          btn.textContent = 'Generate';
          btn.disabled = false;
          btn.classList.remove('opacity-50');
        }
      });
      this.scrollToBottom();
      return;
    }

    // Reset ALL "Generating..." buttons across the entire UI
    this.output.querySelectorAll('button').forEach(btn => {
      if (btn.textContent === 'Generating...') {
        if (btn.closest('.viz-controls')) {
          btn.textContent = 'Generate';
        } else {
          btn.textContent = 'Try Another Look';
        }
        btn.disabled = false;
        btn.classList.remove('opacity-50');
      }
    });

    const wrapper = this.createMessageWrapper('decor-visualization');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-moodboard-bubble');

    // Header
    const header = document.createElement('div');
    header.className = 'mb-4';

    const title = document.createElement('h3');
    title.className = 'text-xl font-bold mb-2 text-[#e4e4f0]';
    title.textContent = 'Your Room, Reimagined';
    header.appendChild(title);

    const subtitle = document.createElement('p');
    subtitle.className = 'viz-subtitle text-sm text-[#8888a8] mb-2';
    subtitle.textContent = uiData.message || 'See how your selected products look in your space';
    header.appendChild(subtitle);

    if (uiData.room_dimensions) {
      const dims = uiData.room_dimensions;
      const area = (dims.length * dims.width).toFixed(1);
      const dimLabel = document.createElement('p');
      dimLabel.className = 'text-xs text-[#555570]';
      dimLabel.textContent = `Room: ${dims.length}m x ${dims.width}m (~${area} m2)`;
      header.appendChild(dimLabel);
    }

    bubble.appendChild(header);

    // Visualization image
    const imageContainer = document.createElement('div');
    imageContainer.className = 'relative w-full rounded-xl overflow-hidden mb-4';

    if (uiData.image_base64) {
      const img = document.createElement('img');
      img.src = `data:image/jpeg;base64,${uiData.image_base64}`;
      img.alt = 'Room visualization';
      img.className = 'w-full h-auto rounded-xl shadow-lg';
      img.style.cursor = 'zoom-in';
      img.loading = 'lazy';
      img.addEventListener('click', (e) => {
        e.stopPropagation();
        this._openLightbox(img.src, uiData.message || 'Your Room, Reimagined');
      });
      imageContainer.appendChild(img);
    } else {
      // Fallback: show a styled description card
      const fallback = document.createElement('div');
      fallback.className = 'w-full bg-gradient-to-br from-[rgba(168,85,247,0.05)] to-[rgba(0,240,255,0.05)] rounded-xl p-6 text-center';

      const icon = document.createElement('div');
      icon.className = 'text-5xl mb-3';
      icon.textContent = '\u2728';
      fallback.appendChild(icon);

      const desc = document.createElement('p');
      desc.className = 'text-sm text-[#8888a8]';
      desc.textContent = uiData.fallback_description
        ? uiData.fallback_description.substring(0, 200) + '...'
        : 'Room visualization is being prepared...';
      fallback.appendChild(desc);

      imageContainer.appendChild(fallback);
    }

    bubble.appendChild(imageContainer);

    // Products shown list
    if (uiData.products_shown && uiData.products_shown.length > 0) {
      const productsSection = document.createElement('div');
      productsSection.className = 'mb-4';

      const productsLabel = document.createElement('div');
      productsLabel.className = 'text-xs font-semibold text-[#8888a8] uppercase tracking-wide mb-2';
      productsLabel.textContent = 'Products in this visualization';
      productsSection.appendChild(productsLabel);

      const productsList = document.createElement('div');
      productsList.className = 'flex flex-wrap gap-2';

      uiData.products_shown.forEach(product => {
        const tag = document.createElement('div');
        tag.className = 'bg-[rgba(255,255,255,0.05)] rounded-full px-3 py-1 text-xs text-[#c0c0d8] border border-[rgba(255,255,255,0.08)]';
        tag.textContent = `${product.name} - ${product.price.toFixed(2)}`;
        productsList.appendChild(tag);
      });

      productsSection.appendChild(productsList);
      bubble.appendChild(productsSection);
    }

    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'flex gap-3 mt-4';

    const addAllBtn = document.createElement('button');
    addAllBtn.className = 'flex-1 btn-neon-fill py-3 rounded-lg font-semibold';
    addAllBtn.textContent = 'Add All to Cart';
    addAllBtn.addEventListener('click', () => {
      if (uiData.products_shown && uiData.products_shown.length > 0) {
        addAllBtn.textContent = 'Adding...';
        addAllBtn.disabled = true;
        const items = uiData.products_shown.map(p => ({
          product_id: p.product_id,
          quantity: 1,
        }));
        this.api.sendCartAction(this.getCurrentCustomerId(), items);
        setTimeout(() => {
          addAllBtn.textContent = 'Added!';
          addAllBtn.classList.add('opacity-50');
        }, 1500);
      }
    });
    actions.appendChild(addAllBtn);

    const regenerateBtn = document.createElement('button');
    regenerateBtn.className = 'flex-1 decor-btn-secondary py-3 rounded-lg font-semibold';
    regenerateBtn.textContent = 'Try Another Look';
    regenerateBtn.addEventListener('click', () => {
      regenerateBtn.textContent = 'Generating...';
      regenerateBtn.disabled = true;
      regenerateBtn.classList.add('opacity-50');

      // Safety reset after 60s in case render doesn't trigger
      setTimeout(() => {
        if (regenerateBtn.textContent === 'Generating...') {
          regenerateBtn.textContent = 'Try Another Look';
          regenerateBtn.disabled = false;
          regenerateBtn.classList.remove('opacity-50');
        }
      }, 60000);

      const productIds = (uiData.products_shown || []).map(p => p.product_id);
      this.api.sendMessage({
        type: 'visualize_room',
        data: {
          customer_id: this.getCurrentCustomerId(),
          session_id: this.currentSessionId,
          product_ids: productIds,
        }
      });
    });
    actions.appendChild(regenerateBtn);

    bubble.appendChild(actions);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Handle add to cart from moodboard
   */
  handleAddToCart(product, e) {
    console.log(`[HomeDecor] Adding product to cart:`, product);

    this.api.sendCartAction(
      this.getCurrentCustomerId(),
      [{ product_id: product.product_id, quantity: 1 }]
    );

    const button = e.target;
    const originalText = button.textContent;
    button.textContent = 'Added!';
    button.disabled = true;
    button.classList.add('opacity-50');

    setTimeout(() => {
      button.textContent = originalText;
      button.disabled = false;
      button.classList.remove('opacity-50');
    }, 2000);
  }

  /**
   * Render Photo Upload UI (Phase 3)
   */
  renderPhotoUpload(uiData) {
    const wrapper = this.createMessageWrapper('decor-ui');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-selector-bubble');

    // Title
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold mb-2 text-[#e4e4f0]';
    title.textContent = uiData.title || 'Show me your space';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-[#8888a8] mb-4';
      subtitle.textContent = uiData.subtitle;
      bubble.appendChild(subtitle);
    }

    // Upload container
    const uploadContainer = document.createElement('div');
    uploadContainer.className = 'photo-upload-container';

    // Guidelines
    if (uiData.photo_guidelines && uiData.photo_guidelines.length > 0) {
      const guidelines = document.createElement('div');
      guidelines.className = 'photo-upload-guidelines';
      guidelines.innerHTML = '<strong>Tips for great photos:</strong>';

      const list = document.createElement('ul');
      uiData.photo_guidelines.forEach(guideline => {
        const li = document.createElement('li');
        li.textContent = guideline;
        list.appendChild(li);
      });
      guidelines.appendChild(list);
      uploadContainer.appendChild(guidelines);
    }

    // Photo options buttons
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'photo-upload-options';

    // Option 1: Upload photos
    const uploadBtn = document.createElement('button');
    uploadBtn.className = 'photo-upload-btn';
    uploadBtn.innerHTML = '<span class="material-symbols-outlined">upload</span> Upload Photos';
    uploadBtn.addEventListener('click', () => this.handlePhotoUploadClick());
    optionsContainer.appendChild(uploadBtn);

    uploadContainer.appendChild(optionsContainer);

    // Preview grid (initially hidden)
    const previewGrid = document.createElement('div');
    previewGrid.className = 'photo-preview-grid';
    previewGrid.id = `photo-preview-${this.currentSessionId}`;
    previewGrid.style.display = 'none';
    uploadContainer.appendChild(previewGrid);

    // Submit button (initially hidden)
    const submitBtn = document.createElement('button');
    submitBtn.className = 'photo-upload-submit';
    submitBtn.textContent = 'Analyze Photos';
    submitBtn.id = `photo-submit-${this.currentSessionId}`;
    submitBtn.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.addEventListener('click', () => this.handlePhotoSubmit());
    uploadContainer.appendChild(submitBtn);

    bubble.appendChild(uploadContainer);

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-[#555570] mt-3 text-center';
    instructions.textContent = 'Choose your preferred method to show the room';
    bubble.appendChild(instructions);

    wrapper.appendChild(bubble);
    this.output.appendChild(wrapper);
    this.scrollToBottom();
  }

  /**
   * Handle photo upload button click
   */
  handlePhotoUploadClick() {
    const fileInput = this.photoUploadHandler.createFileInput();

    fileInput.addEventListener('change', async (e) => {
      const files = e.target.files;
      if (files.length > 0) {
        await this.photoUploadHandler.handleFileSelection(files);
        this.updatePhotoPreview();
      }
    });

    fileInput.click();
  }

  /**
   * Handle live camera button click
   */
  handleLiveCameraClick() {
    console.log('[HomeDecor] Switching to live camera mode');
    // Trigger the existing camera button in the main UI
    const cameraButton = document.getElementById('cameraButton');
    if (cameraButton) {
      cameraButton.click();
      this.api.sendTextMessage('Starting live camera view of the room');
    } else {
      console.error('[HomeDecor] Camera button not found');
      this.api.sendTextMessage('Unable to start camera. Please use the camera button in the input area.');
    }
  }

  /**
   * Update photo preview grid
   */
  updatePhotoPreview() {
    const previewGrid = document.getElementById(`photo-preview-${this.currentSessionId}`);
    const submitBtn = document.getElementById(`photo-submit-${this.currentSessionId}`);

    if (!previewGrid || !submitBtn) return;

    const photos = this.photoUploadHandler.getPhotos();

    if (photos.length > 0) {
      previewGrid.style.display = 'grid';
      submitBtn.style.display = 'block';
      submitBtn.disabled = false;

      // Clear existing previews
      previewGrid.innerHTML = '';

      // Add photo previews
      photos.forEach((photo, index) => {
        const previewItem = document.createElement('div');
        previewItem.className = 'photo-preview-item';

        const img = document.createElement('img');
        img.src = photo.preview;
        img.alt = `Photo ${index + 1}`;
        previewItem.appendChild(img);

        // Remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'photo-preview-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.addEventListener('click', () => {
          this.photoUploadHandler.removePhoto(index);
          this.updatePhotoPreview();
        });
        previewItem.appendChild(removeBtn);

        previewGrid.appendChild(previewItem);
      });

      // Add upload more button if not at max
      if (!this.photoUploadHandler.isMaxReached()) {
        const addMoreBtn = document.createElement('div');
        addMoreBtn.className = 'photo-preview-item flex items-center justify-center cursor-pointer bg-[rgba(255,255,255,0.03)] hover:bg-[rgba(255,255,255,0.06)] border-2 border-dashed border-[rgba(255,255,255,0.1)]';
        addMoreBtn.innerHTML = '<span class="material-symbols-outlined text-4xl text-[#555570]">add_photo_alternate</span>';
        addMoreBtn.addEventListener('click', () => this.handlePhotoUploadClick());
        previewGrid.appendChild(addMoreBtn);
      }
    } else {
      previewGrid.style.display = 'none';
      submitBtn.style.display = 'none';
    }

    this.scrollToBottom();
  }

  /**
   * Handle photo submission to backend
   */
  handlePhotoSubmit() {
    const photos = this.photoUploadHandler.getPhotoData();

    if (photos.length === 0) {
      console.warn('[HomeDecor] No photos to submit');
      return;
    }

    console.log(`[HomeDecor] Submitting ${photos.length} photos for analysis`);

    // Send each photo as image data
    // The WebSocket handler will automatically intercept and analyze them
    photos.forEach((photoBase64, index) => {
      setTimeout(() => {
        this.api.sendImage(photoBase64);
        console.log(`[HomeDecor] Sent photo ${index + 1}/${photos.length}`);
      }, index * 100); // Stagger sends by 100ms
    });

    // Disable submit button
    const submitBtn = document.getElementById(`photo-submit-${this.currentSessionId}`);
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Analyzing...';
    }

    // Clear photos after submission
    setTimeout(() => {
      this.photoUploadHandler.clearPhotos();
    }, photos.length * 100 + 500);
  }

  /**
   * Reset selections for new session
   */
  reset() {
    this.currentSessionId = null;
    this.selectedRoom = null;
    this.selectedStyles = [];
    this.selectedColors = [];
    this.renderedMoodboards.clear();
    this._selectedDimensions = null;
    this._vizSelectedProducts = [];
    this.photoUploadHandler.clearPhotos();
  }
}
