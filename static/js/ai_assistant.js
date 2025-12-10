class AIAssistant {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.synth = window.speechSynthesis;
        this.chatHistory = []; // Memory
        this.initSpeechRecognition();
        this.createUI();
        this.checkAndPopulateInvoice(); // Check if we need to fill the form
    }

    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-IN'; // Good for Hinglish

            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateUIState('listening');
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.updateUIState('idle');
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.handleUserInput(transcript);
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error', event.error);
                this.speak("Sorry, I didn't catch that.");
            };
        } else {
            console.warn('Speech recognition not supported');
        }
    }

    createUI() {
        // Create floating button
        const btn = document.createElement('button');
        btn.id = 'ai-assistant-btn';
        btn.innerHTML = '<i class="fas fa-microphone"></i> <span class="ai-btn-text">AI Assistant</span>';
        btn.className = 'ai-assistant-btn';
        btn.onclick = () => {
            const modal = document.getElementById('ai-chat-modal');
            if (modal) {
                modal.classList.remove('hidden');
            }
            this.toggleListening();
        };
        document.body.appendChild(btn);

        // Create Chat Modal (hidden by default)
        const modal = document.createElement('div');
        modal.id = 'ai-chat-modal';
        modal.className = 'ai-chat-modal hidden';
        modal.innerHTML = `
            <div class="ai-modal-header">
                <h3 class="ai-modal-title"><i class="fas fa-robot"></i> Billing Assistant</h3>
                <button onclick="document.getElementById('ai-chat-modal').classList.add('hidden')" class="ai-close-btn">×</button>
            </div>
            <div id="ai-chat-messages" class="ai-messages">
                <div class="ai-message ai">
                    <div class="ai-avatar"><i class="fas fa-robot"></i></div>
                    <div class="ai-text">Hi! I can help you:<br>
                        • <strong>Add products:</strong> "Add product Milk price 50 stock 100"<br>
                        • <strong>Add customers:</strong> "Add customer John email john@example.com"<br>
                        • <strong>Create invoices:</strong> "Bill for Riya: 2 milks and 1 bread"<br><br>
                        Try saying any of these commands!
                    </div>
                </div>
            </div>
            <div class="ai-input-area">
                <input type="text" id="ai-text-input" class="ai-input" placeholder="Type or speak...">
                <button id="ai-send-btn" class="ai-send-btn"><i class="fas fa-paper-plane"></i></button>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close modal when clicking outside (on the modal backdrop)
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });

        // Event listeners for text input
        document.getElementById('ai-send-btn').onclick = () => {
            const input = document.getElementById('ai-text-input');
            if (input.value.trim()) {
                this.handleUserInput(input.value.trim());
                input.value = '';
            }
        };

        document.getElementById('ai-text-input').onkeypress = (e) => {
            if (e.key === 'Enter') {
                document.getElementById('ai-send-btn').click();
            }
        };
    }

    toggleListening() {
        const modal = document.getElementById('ai-chat-modal');
        if (modal && modal.classList.contains('hidden')) {
            modal.classList.remove('hidden');
        }

        if (!this.recognition) {
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    updateUIState(state) {
        const btn = document.getElementById('ai-assistant-btn');
        if (state === 'listening') {
            btn.innerHTML = '<i class="fas fa-circle" style="color: #ff0000;"></i> Listening...';
            btn.classList.add('listening');
        } else {
            btn.innerHTML = '<i class="fas fa-microphone"></i> AI Assistant';
            btn.classList.remove('listening');
        }
    }

    addMessage(text, sender) {
        const container = document.getElementById('ai-chat-messages');
        const div = document.createElement('div');
        div.className = `ai-message ${sender}`;

        if (sender === 'ai') {
            div.innerHTML = `
                <div class="ai-avatar"><i class="fas fa-robot"></i></div>
                <div class="ai-text">${text}</div>
            `;
        } else {
            div.innerHTML = `
                <div class="ai-text">${text}</div>
                <div class="ai-avatar user"><i class="fas fa-user"></i></div>
            `;
        }

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    async handleUserInput(text) {
        this.addMessage(text, 'user');
        this.chatHistory.push({ role: 'user', content: text });

        // Show loading
        const loadingId = 'ai-loading-' + Date.now();
        const container = document.getElementById('ai-chat-messages');
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'ai-message ai';
        loadingDiv.innerHTML = `
            <div class="ai-avatar"><i class="fas fa-robot"></i></div>
            <div class="ai-text"><i class="fas fa-spinner fa-spin"></i> Thinking...</div>
        `;
        container.appendChild(loadingDiv);
        container.scrollTop = container.scrollHeight;

        try {
            const response = await fetch('/api/ai/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    history: this.chatHistory
                })
            });

            const data = await response.json();
            document.getElementById(loadingId).remove();

            if (data.error) {
                this.addMessage("Error: " + data.error, 'ai');
                this.speak("Sorry, something went wrong.");
                return;
            }

            this.addMessage(data.response_text, 'ai');
            this.chatHistory.push({ role: 'model', content: data.response_text });
            this.speak(data.response_text);

            // Handle different intents
            if (data.intent === 'create_invoice') {
                this.showInvoicePreview(data.data);
            } else if (data.intent === 'add_product') {
                if (data.success && data.product_id) {
                    // Product was already added by backend, redirect to products page
                    setTimeout(() => {
                        window.location.href = '/seller/products';
                    }, 1500);
                } else {
                    // Show preview if addition failed or needs confirmation
                    this.showProductPreview(data.data);
                }
            } else if (data.intent === 'add_customer') {
                if (data.success && data.customer_id) {
                    // Customer was already added by backend, redirect to customers page
                    setTimeout(() => {
                        window.location.href = '/seller/customers';
                    }, 1500);
                } else {
                    // Show preview if addition failed or needs confirmation
                    this.showCustomerPreview(data.data);
                }
            }

        } catch (error) {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            this.addMessage("Network error. Please try again.", 'ai');
            console.error(error);
        }
    }

    speak(text) {
        if (this.synth) {
            const utterance = new SpeechSynthesisUtterance(text);
            this.synth.speak(utterance);
        }
    }

    showInvoicePreview(data) {
        const container = document.getElementById('ai-chat-messages');

        let itemsHtml = data.items.map(item => `
            <div class="ai-preview-item">
                <span>${item.product_name} x${item.quantity}</span>
                <span>${item.is_new_product ? '(New)' : ''}</span>
            </div>
        `).join('');

        const previewDiv = document.createElement('div');
        previewDiv.className = 'ai-preview-card';
        previewDiv.innerHTML = `
            <div class="ai-preview-header">Invoice Preview</div>
            <div style="margin-bottom: 8px; font-size: 13px;"><strong>Customer:</strong> ${data.customer_name} ${data.is_new_customer ? '(New)' : ''}</div>
            <div class="ai-preview-items">${itemsHtml}</div>
            <div class="ai-preview-actions">
                <button onclick="window.aiAssistant.createInvoice(${JSON.stringify(data).replace(/"/g, '&quot;')})" class="ai-confirm-btn">Confirm & Create</button>
                <button onclick="this.parentElement.parentElement.remove()" class="ai-cancel-btn">Cancel</button>
            </div>
        `;
        container.appendChild(previewDiv);
        container.scrollTop = container.scrollHeight;
    }

    async createInvoice(data) {
        this.addMessage("Redirecting to invoice creation...", 'ai');
        // Store data in session storage
        sessionStorage.setItem('aiInvoiceData', JSON.stringify(data));

        setTimeout(() => {
            window.location.href = '/seller/invoices/create';
        }, 1000);
    }

    checkAndPopulateInvoice() {
        // Check if we are on the create invoice page
        if (window.location.pathname.includes('/seller/invoices/create')) {
            const dataStr = sessionStorage.getItem('aiInvoiceData');
            if (dataStr) {
                try {
                    const data = JSON.parse(dataStr);
                    sessionStorage.removeItem('aiInvoiceData'); // Clear it

                    console.log("Populating invoice from AI data:", data);

                    // Wait for DOM to be fully ready just in case
                    setTimeout(() => {
                        this.populateInvoiceForm(data);
                    }, 500);
                } catch (e) {
                    console.error("Error parsing AI invoice data", e);
                }
            }
        }
    }

    showProductPreview(data) {
        const container = document.getElementById('ai-chat-messages');
        
        const previewDiv = document.createElement('div');
        previewDiv.className = 'ai-preview-card';
        previewDiv.innerHTML = `
            <div class="ai-preview-header">Product Preview</div>
            <div class="ai-preview-items">
                <div class="ai-preview-item">
                    <span><strong>Name:</strong></span>
                    <span>${data.name || 'N/A'}</span>
                </div>
                <div class="ai-preview-item">
                    <span><strong>Price:</strong></span>
                    <span>₹${data.price || '0.00'}</span>
                </div>
                <div class="ai-preview-item">
                    <span><strong>Stock:</strong></span>
                    <span>${data.stock || 0}</span>
                </div>
                ${data.description ? `<div class="ai-preview-item"><span><strong>Description:</strong></span><span>${data.description}</span></div>` : ''}
            </div>
            <div class="ai-preview-actions">
                <button onclick="window.aiAssistant.confirmAddProduct(${JSON.stringify(data).replace(/"/g, '&quot;')})" class="ai-confirm-btn">Confirm & Add</button>
                <button onclick="this.parentElement.parentElement.remove()" class="ai-cancel-btn">Cancel</button>
            </div>
        `;
        container.appendChild(previewDiv);
        container.scrollTop = container.scrollHeight;
    }

    showCustomerPreview(data) {
        const container = document.getElementById('ai-chat-messages');
        
        const previewDiv = document.createElement('div');
        previewDiv.className = 'ai-preview-card';
        previewDiv.innerHTML = `
            <div class="ai-preview-header">Customer Preview</div>
            <div class="ai-preview-items">
                <div class="ai-preview-item">
                    <span><strong>Name:</strong></span>
                    <span>${data.name || 'N/A'}</span>
                </div>
                <div class="ai-preview-item">
                    <span><strong>Email:</strong></span>
                    <span>${data.email || 'N/A'}</span>
                </div>
                ${data.phone ? `<div class="ai-preview-item"><span><strong>Phone:</strong></span><span>${data.phone}</span></div>` : ''}
                ${data.address ? `<div class="ai-preview-item"><span><strong>Address:</strong></span><span>${data.address}</span></div>` : ''}
            </div>
            <div class="ai-preview-actions">
                <button onclick="window.aiAssistant.confirmAddCustomer(${JSON.stringify(data).replace(/"/g, '&quot;')})" class="ai-confirm-btn">Confirm & Add</button>
                <button onclick="this.parentElement.parentElement.remove()" class="ai-cancel-btn">Cancel</button>
            </div>
        `;
        container.appendChild(previewDiv);
        container.scrollTop = container.scrollHeight;
    }

    async confirmAddProduct(data) {
        this.addMessage("Adding product...", 'ai');
        
        try {
            const response = await fetch('/api/products/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: data.name,
                    price: data.price || 0,
                    stock: data.stock || 0,
                    description: data.description || ''
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addMessage("✅ Product added successfully! Redirecting to products page...", 'ai');
                setTimeout(() => {
                    window.location.href = '/seller/products';
                }, 1500);
            } else {
                this.addMessage("❌ Failed to add product: " + (result.error || 'Unknown error'), 'ai');
            }
        } catch (error) {
            this.addMessage("❌ Network error. Please try again.", 'ai');
            console.error(error);
        }
    }

    async confirmAddCustomer(data) {
        this.addMessage("Adding customer...", 'ai');
        
        try {
            // Use the AI process endpoint which handles customer addition
            const response = await fetch('/api/ai/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: `add customer name ${data.name} email ${data.email}${data.phone ? ' phone ' + data.phone : ''}${data.address ? ' address ' + data.address : ''}`,
                    history: []
                })
            });

            const result = await response.json();
            
            if (result.success && result.customer_id) {
                this.addMessage("✅ Customer added successfully! Redirecting to customers page...", 'ai');
                setTimeout(() => {
                    window.location.href = '/seller/customers';
                }, 1500);
            } else {
                this.addMessage("❌ " + (result.response_text || 'Failed to add customer'), 'ai');
            }
        } catch (error) {
            this.addMessage("❌ Network error. Please try again.", 'ai');
            console.error(error);
        }
    }

    populateInvoiceForm(data) {
        // 1. Set Customer
        if (data.customer_id) {
            const customerSelect = document.querySelector('select[name="customer_id"]');
            if (customerSelect) {
                customerSelect.value = data.customer_id;
            }
        } else if (data.customer_name) {
            // New customer or unmatched name - might need to create temp customer or alert user
            // For now, let's try to find by text if ID wasn't passed but name matches
            const customerSelect = document.querySelector('select[name="customer_id"]');
            for (let i = 0; i < customerSelect.options.length; i++) {
                if (customerSelect.options[i].text.toLowerCase().includes(data.customer_name.toLowerCase())) {
                    customerSelect.selectedIndex = i;
                    break;
                }
            }
        }

        // 2. Add Items
        if (data.items && data.items.length > 0) {
            // Clear existing empty items if any (handled by addItem)

            data.items.forEach((item, index) => {
                // Call the global addItem function from create_invoice.html
                if (typeof window.addItem === 'function') {
                    window.addItem();

                    // The new item will be at index + 1 (since 1-based usually, but let's check logic)
                    // addItem increments itemCount. We can access the last added item.
                    // Actually, create_invoice.html uses a global itemCount.
                    // We need to find the inputs for the current itemCount.

                    // Since we are running this sequentially, the itemCount will be incremented.
                    // We can assume the inputs are named product_{itemCount}_id

                    const currentCount = window.itemCount; // Access global variable

                    const productSelect = document.querySelector(`select[name="product_${currentCount}_id"]`);
                    const quantityInput = document.querySelector(`input[name="quantity_${currentCount}"]`);

                    if (item.product_id && productSelect) {
                        productSelect.value = item.product_id;
                        // Trigger change to update price
                        productSelect.dispatchEvent(new Event('change'));
                    } else if (item.product_name && productSelect) {
                        // Try to match by name
                        for (let i = 0; i < productSelect.options.length; i++) {
                            if (productSelect.options[i].text.toLowerCase().includes(item.product_name.toLowerCase())) {
                                productSelect.selectedIndex = i;
                                productSelect.dispatchEvent(new Event('change'));
                                break;
                            }
                        }
                    }

                    if (quantityInput) {
                        quantityInput.value = item.quantity;
                        quantityInput.dispatchEvent(new Event('change'));
                    }
                }
            });
        }
    }
}

// Initialize
window.addEventListener('load', () => {
    window.aiAssistant = new AIAssistant();
});

