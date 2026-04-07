/**
 * Home Decor UI Renderer - Phase 1
 *
 * Renders interactive UI elements (room selector, style cards, color chips)
 * inline in the chat based on ui_data from backend tool responses.
 */

export class HomeDecorRenderer {
  constructor(api, outputContainer) {
    this.api = api;
    this.output = outputContainer;
    this.currentSessionId = null;
    this.selectedRoom = null;
    this.selectedStyles = [];
    this.selectedColors = [];
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
    title.className = 'text-lg font-bold mb-2';
    title.textContent = uiData.title || 'Select a room';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-gray-600 mb-4';
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
    instructions.className = 'text-xs text-gray-500 mt-3 text-center';
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
    card.className = 'room-card bg-gray-100 border-2 border-transparent rounded-xl p-4 cursor-pointer hover:bg-gray-200 transition-all text-center';
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
    const wrapper = this.createMessageWrapper('decor-ui');
    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble', 'decor-selector-bubble');

    // Title
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold mb-2';
    title.textContent = uiData.title || 'Choose your style';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-gray-600 mb-4';
      subtitle.textContent = uiData.subtitle;
      bubble.appendChild(subtitle);
    }

    // Style grid
    const styleGrid = document.createElement('div');
    styleGrid.className = 'grid grid-cols-2 md:grid-cols-4 gap-4 my-4';

    uiData.style_options.forEach(style => {
      const styleCard = this.createStyleCard(style);
      styleGrid.appendChild(styleCard);
    });

    bubble.appendChild(styleGrid);

    // Continue button
    const continueBtn = document.createElement('button');
    continueBtn.className = 'w-full bg-black text-white py-3 rounded-lg font-semibold mt-4 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed';
    continueBtn.textContent = 'Continue';
    continueBtn.disabled = true;
    continueBtn.id = 'stylesContinueBtn';
    continueBtn.addEventListener('click', () => {
      this.handleStyleSelection();
    });
    bubble.appendChild(continueBtn);

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-gray-500 mt-3 text-center';
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
    card.className = 'style-card relative bg-gray-100 border-3 border-transparent rounded-xl overflow-hidden cursor-pointer hover:shadow-lg transition-all';
    card.dataset.styleId = style.id;

    // Placeholder image (you can add real images later)
    const imagePlaceholder = document.createElement('div');
    imagePlaceholder.className = 'w-full h-32 bg-gradient-to-br from-gray-300 to-gray-400 flex items-center justify-center';
    imagePlaceholder.innerHTML = `<span class="text-4xl opacity-50">🏠</span>`;
    card.appendChild(imagePlaceholder);

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
    checkmark.className = 'absolute top-2 right-2 w-8 h-8 bg-black text-white rounded-full hidden items-center justify-center';
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
      card.classList.add('border-black', 'shadow-xl');
      checkmark.classList.remove('hidden');
      checkmark.classList.add('flex');
      this.selectedStyles.push(styleId);
    } else {
      card.classList.remove('border-black', 'shadow-xl');
      checkmark.classList.add('hidden');
      checkmark.classList.remove('flex');
      this.selectedStyles = this.selectedStyles.filter(id => id !== styleId);
    }

    // Enable/disable continue button
    const continueBtn = document.getElementById('stylesContinueBtn');
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
    title.className = 'text-lg font-bold mb-2';
    title.textContent = uiData.title || 'Choose colors';
    bubble.appendChild(title);

    if (uiData.subtitle) {
      const subtitle = document.createElement('p');
      subtitle.className = 'text-sm text-gray-600 mb-4';
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
      skipBtn.className = 'flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-colors';
      skipBtn.textContent = 'Skip';
      skipBtn.addEventListener('click', () => {
        this.handleColorSelection(true); // skip=true
      });
      buttonContainer.appendChild(skipBtn);
    }

    const continueBtn = document.createElement('button');
    continueBtn.className = 'flex-1 bg-black text-white py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity';
    continueBtn.textContent = 'Continue';
    continueBtn.id = 'colorsContinueBtn';
    continueBtn.addEventListener('click', () => {
      this.handleColorSelection(false);
    });
    buttonContainer.appendChild(continueBtn);

    bubble.appendChild(buttonContainer);

    // Instructions
    const instructions = document.createElement('p');
    instructions.className = 'text-xs text-gray-500 mt-3 text-center';
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
    label.className = 'text-xs text-center mt-1 text-gray-600';
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
      button.classList.add('border-black', 'ring-4', 'ring-black', 'ring-opacity-30');
      checkmark.classList.remove('hidden');
      this.selectedColors.push(colorId);
    } else {
      button.classList.remove('border-black', 'ring-4', 'ring-black', 'ring-opacity-30');
      checkmark.classList.add('hidden');
      this.selectedColors = this.selectedColors.filter(id => id !== colorId);
    }
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
        card.classList.add('selected', 'border-black', 'bg-white', 'shadow-xl');
      } else {
        card.classList.remove('selected', 'border-black', 'bg-white', 'shadow-xl');
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
   * Reset selections for new session
   */
  reset() {
    this.currentSessionId = null;
    this.selectedRoom = null;
    this.selectedStyles = [];
    this.selectedColors = [];
  }
}
