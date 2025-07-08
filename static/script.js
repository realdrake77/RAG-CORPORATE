// Enterprise RAG Chatbot - Modern JavaScript Application

class EnterpriseRAGChatbot {
    constructor() {
        this.isInitialized = false;
        this.documentsUploaded = false;
        this.sessionId = 'default';
        this.currentFiles = [];
        this.isUploading = false;
        this.isTyping = false;
        this.settings = {
            temperature: 0.1,
            maxTokens: 1000
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Enterprise RAG Chatbot...');
        
        // Initialize UI elements
        this.initializeElements();
        this.attachEventListeners();
        
        // Check system status
        await this.checkSystemStatus();
        
        // Hide loading screen and show main app
        setTimeout(() => {
            this.hideLoadingScreen();
            this.isInitialized = true;
            console.log('✅ Enterprise RAG Chatbot initialized successfully');
        }, 2000);
    }

    initializeElements() {
        // Main elements
        this.loadingScreen = document.getElementById('loading-screen');
        this.mainContainer = document.getElementById('main-container');
        this.sidebar = document.getElementById('sidebar');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        
        // Upload elements
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.fileList = document.getElementById('file-list');
        this.uploadBtn = document.getElementById('upload-btn');
        this.clearDocsBtn = document.getElementById('clear-docs-btn');
        
        // Status elements
        this.docsCount = document.getElementById('docs-count');
        this.queriesCount = document.getElementById('queries-count');
        this.avgTime = document.getElementById('avg-time');
        this.backendStatus = document.getElementById('backend-status');
        this.uploadStatus = document.getElementById('upload-status');
        this.charCount = document.getElementById('char-count');
        
        // Settings elements
        this.temperatureSlider = document.getElementById('temperature-slider');
        this.temperatureValue = document.getElementById('temperature-value');
        this.maxTokensSlider = document.getElementById('max-tokens-slider');
        this.maxTokensValue = document.getElementById('max-tokens-value');
        
        // Modal elements
        this.settingsModal = document.getElementById('settings-modal');
        this.uploadModal = document.getElementById('upload-modal');
        this.uploadProgress = document.getElementById('upload-progress');
        this.progressPercentage = document.getElementById('progress-percentage');
        this.progressStatus = document.getElementById('progress-status');
        
        // Control elements
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.settingsBtn = document.getElementById('settings-btn');
        this.clearChatBtn = document.getElementById('clear-chat-btn');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.closeSettings = document.getElementById('close-settings');
        this.themeToggle = document.getElementById('theme-toggle');
        
        // Initialize theme
        this.initializeTheme();
    }

    attachEventListeners() {
        // File upload events
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.uploadBtn.addEventListener('click', this.uploadDocuments.bind(this));
        this.clearDocsBtn.addEventListener('click', this.clearAllDocuments.bind(this));
        
        // Chat events
        this.chatInput.addEventListener('input', this.handleInputChange.bind(this));
        this.chatInput.addEventListener('keypress', this.handleKeyPress.bind(this));
        this.sendBtn.addEventListener('click', this.sendMessage.bind(this));
        
        // Settings events
        this.temperatureSlider.addEventListener('input', this.updateTemperature.bind(this));
        this.maxTokensSlider.addEventListener('input', this.updateMaxTokens.bind(this));
        
        // Control events
        this.sidebarToggle.addEventListener('click', this.toggleSidebar.bind(this));
        this.settingsBtn.addEventListener('click', this.showSettings.bind(this));
        this.clearChatBtn.addEventListener('click', this.clearChat.bind(this));
        this.newSessionBtn.addEventListener('click', this.newSession.bind(this));
        this.closeSettings.addEventListener('click', this.hideSettings.bind(this));
        this.themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        
        // Modal close events
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) this.hideSettings();
        });
        
        // Auto-resize textarea
        this.chatInput.addEventListener('input', this.autoResizeTextarea.bind(this));
    }

    hideLoadingScreen() {
        this.loadingScreen.style.opacity = '0';
        setTimeout(() => {
            this.loadingScreen.style.display = 'none';
            this.mainContainer.classList.remove('hidden');
        }, 500);
    }

    // File Upload Handlers
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        this.addFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
        e.target.value = ''; // Clear input
    }

    addFiles(files) {
        const validFiles = files.filter(file => {
            const validTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            const maxSize = 10 * 1024 * 1024; // 10MB
            
            if (!validTypes.includes(file.type)) {
                this.showToast('error', 'Invalid File Type', `${file.name} is not a supported file type.`);
                return false;
            }
            
            if (file.size > maxSize) {
                this.showToast('error', 'File Too Large', `${file.name} exceeds the 10MB limit.`);
                return false;
            }
            
            return true;
        });

        this.currentFiles.push(...validFiles);
        this.updateFileList();
        this.updateUploadButton();
    }

    updateFileList() {
        this.fileList.innerHTML = '';
        
        this.currentFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-info">
                    <i class="fas fa-file-pdf"></i>
                    <div class="file-details">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${this.formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button class="remove-file" onclick="chatbot.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            `;
            this.fileList.appendChild(fileItem);
        });
    }

    removeFile(index) {
        this.currentFiles.splice(index, 1);
        this.updateFileList();
        this.updateUploadButton();
    }

    updateUploadButton() {
        this.uploadBtn.disabled = this.currentFiles.length === 0 || this.isUploading;
        this.uploadBtn.innerHTML = this.currentFiles.length > 0 
            ? `<i class="fas fa-upload"></i> Upload ${this.currentFiles.length} file${this.currentFiles.length > 1 ? 's' : ''}`
            : '<i class="fas fa-upload"></i> Upload Documents';
    }

    async uploadDocuments() {
        if (this.currentFiles.length === 0 || this.isUploading) return;

        this.isUploading = true;
        this.showUploadModal();
        this.updateUploadProgress(0, 'Preparing upload...');

        try {
            const formData = new FormData();
            this.currentFiles.forEach(file => {
                formData.append('files', file);
            });

            // Simulate realistic progress with better timing
            let currentProgress = 0;
            const progressInterval = setInterval(() => {
                if (currentProgress < 70) {
                    currentProgress += Math.random() * 10 + 5;
                    this.updateUploadProgress(Math.min(currentProgress, 70), 'Processing documents...');
                }
            }, 300);

            // Start upload
            this.updateUploadProgress(10, 'Uploading files...');
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const result = await response.json();
            
            // Complete progress
            this.updateUploadProgress(90, 'Finalizing...');
            
            setTimeout(() => {
                this.updateUploadProgress(100, 'Upload complete!');
                
                setTimeout(() => {
                    this.hideUploadModal();
                    this.showToast('success', 'Upload Successful', `Processed ${result.documents_processed} document chunks in ${result.processing_time.toFixed(2)}s`);
                    
                    // Clear files and update UI
                    this.currentFiles = [];
                    this.updateFileList();
                    this.updateUploadButton();
                    this.documentsUploaded = true;
                    this.updateChatInterface();
                    
                    // Force update system status after upload
                    setTimeout(() => {
                        this.checkSystemStatus();
                    }, 500);
                }, 800);
            }, 300);

        } catch (error) {
            console.error('Upload error:', error);
            this.showToast('error', 'Upload Failed', error.message);
            this.hideUploadModal();
        } finally {
            this.isUploading = false;
        }
    }

    updateUploadProgress(percentage, status) {
        // Ensure elements exist before updating
        if (this.uploadProgress && this.progressPercentage && this.progressStatus) {
            const clampedPercentage = Math.max(0, Math.min(100, percentage));
            this.uploadProgress.style.width = `${clampedPercentage}%`;
            this.progressPercentage.textContent = `${Math.round(clampedPercentage)}%`;
            this.progressStatus.textContent = status;
            
            // Add visual feedback for progress changes
            if (clampedPercentage > 0) {
                this.uploadProgress.style.opacity = '1';
            }
        } else {
            console.warn('Progress elements not found:', {
                uploadProgress: this.uploadProgress,
                progressPercentage: this.progressPercentage,
                progressStatus: this.progressStatus
            });
        }
    }

    showUploadModal() {
        if (this.uploadModal) {
            this.uploadModal.classList.add('show');
            // Reset progress bar
            if (this.uploadProgress) {
                this.uploadProgress.style.width = '0%';
                this.uploadProgress.style.opacity = '0';
            }
            console.log('Upload modal shown');
        } else {
            console.error('Upload modal element not found');
        }
    }

    hideUploadModal() {
        if (this.uploadModal) {
            this.uploadModal.classList.remove('show');
            console.log('Upload modal hidden');
        } else {
            console.error('Upload modal element not found');
        }
    }

    // Chat Handlers
    handleInputChange(e) {
        const length = e.target.value.length;
        this.charCount.textContent = length;
        
        if (length > 1000) {
            this.charCount.style.color = 'var(--error-500)';
        } else {
            this.charCount.style.color = 'var(--gray-400)';
        }
        
        this.sendBtn.disabled = !e.target.value.trim() || !this.documentsUploaded;
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    autoResizeTextarea() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || !this.documentsUploaded || this.isTyping) return;

        // Add user message
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.charCount.textContent = '0';
        this.sendBtn.disabled = true;
        this.autoResizeTextarea();

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    temperature: this.settings.temperature,
                    max_tokens: this.settings.maxTokens
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get response');
            }

            const result = await response.json();
            
            // Hide typing indicator and add response
            this.hideTypingIndicator();
            this.addMessage(result.response, 'assistant', result.sources, result.processing_time);
            
            this.showToast('success', 'Response Generated', `Processed in ${result.processing_time.toFixed(2)}s`);
            
            // Update query counter immediately
            this.updateQueryCounter();
            
            // Also check system status for other metrics
            setTimeout(() => {
                this.checkSystemStatus();
            }, 200);

        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.showToast('error', 'Chat Error', error.message);
        } finally {
            this.sendBtn.disabled = false;
        }
    }

    addMessage(content, type, sources = null, processingTime = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        const avatar = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        const name = type === 'user' ? 'You' : 'Assistant';
        
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="sources">
                    <h4><i class="fas fa-link"></i> Sources:</h4>
                    ${sources.map(source => `
                        <div class="source-item">
                            <div class="source-meta">
                                <span>${source.metadata.source || 'Document'}</span>
                                ${source.metadata.page ? `<span>Page ${source.metadata.page}</span>` : ''}
                            </div>
                            <div class="source-content">${source.content}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <div class="message-avatar">
                        <i class="${avatar}"></i>
                    </div>
                    <span>${name}</span>
                    <span class="message-time">${timestamp}</span>
                    ${processingTime ? `<span class="message-time">(${processingTime.toFixed(2)}s)</span>` : ''}
                </div>
                <div class="message-text">${this.formatMessage(content)}</div>
                ${sourcesHtml}
            </div>
        `;

        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Simple markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        this.isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <span>Assistant is typing</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    // Settings Handlers
    updateTemperature(e) {
        this.settings.temperature = parseFloat(e.target.value);
        this.temperatureValue.textContent = this.settings.temperature;
    }

    updateMaxTokens(e) {
        this.settings.maxTokens = parseInt(e.target.value);
        this.maxTokensValue.textContent = this.settings.maxTokens;
    }

    // UI Controls
    toggleSidebar() {
        this.sidebar.classList.toggle('hidden');
    }

    showSettings() {
        this.settingsModal.classList.add('show');
    }

    hideSettings() {
        this.settingsModal.classList.remove('show');
    }

    clearChat() {
        if (confirm('Are you sure you want to clear all messages?')) {
            this.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <h2>Welcome to Enterprise RAG</h2>
                    <p>Upload your documents and start asking questions. I'll help you find the information you need with AI-powered precision.</p>
                    <div class="feature-list">
                        <div class="feature-item">
                            <i class="fas fa-file-pdf"></i>
                            <span>PDF Document Analysis</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-search"></i>
                            <span>Intelligent Information Retrieval</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-quote-left"></i>
                            <span>Source Citations</span>
                        </div>
                    </div>
                </div>
            `;
            this.showToast('success', 'Chat Cleared', 'All messages have been cleared');
        }
    }

    newSession() {
        this.sessionId = 'session_' + Date.now();
        this.clearChat();
        this.showToast('success', 'New Session', 'Started a new chat session');
        this.hideSettings();
    }

    updateChatInterface() {
        if (this.documentsUploaded) {
            this.chatInput.disabled = false;
            this.chatInput.placeholder = 'Ask a question about your documents...';
            this.uploadStatus.textContent = 'Documents uploaded - Ready to chat!';
            this.uploadStatus.style.color = 'var(--success-500)';
        } else {
            this.chatInput.disabled = true;
            this.chatInput.placeholder = 'Upload documents first...';
            this.uploadStatus.textContent = 'Upload documents to start chatting';
            this.uploadStatus.style.color = 'var(--gray-500)';
        }
        this.sendBtn.disabled = !this.chatInput.value.trim() || !this.documentsUploaded;
        this.updateClearDocsButton();
    }

    // System Status
    async checkSystemStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const status = await response.json();
                this.updateSystemStatus(status);
                this.documentsUploaded = status.documents_indexed > 0;
                this.updateChatInterface();
            }
        } catch (error) {
            console.error('Failed to check system status:', error);
        }
    }

    updateSystemStatus(status) {
        this.docsCount.textContent = status.documents_indexed;
        this.queriesCount.textContent = status.queries_processed;
        this.avgTime.textContent = `${(status.avg_query_time * 1000).toFixed(0)}ms`;
        this.backendStatus.textContent = status.backend;
        
        // Add visual feedback for status updates
        this.addStatusUpdateAnimation();
    }

    updateQueryCounter() {
        // Immediately increment the query counter for responsive UI
        const currentCount = parseInt(this.queriesCount.textContent) || 0;
        this.queriesCount.textContent = currentCount + 1;
        this.addCounterAnimation(this.queriesCount);
    }

    addStatusUpdateAnimation() {
        // Add a subtle animation when status updates
        this.queriesCount.parentElement.style.transform = 'scale(1.05)';
        setTimeout(() => {
            this.queriesCount.parentElement.style.transform = 'scale(1)';
        }, 200);
    }

    addCounterAnimation(element) {
        // Add a pulse animation to the counter
        element.style.color = 'var(--primary-500)';
        element.style.fontWeight = 'bold';
        element.style.transform = 'scale(1.1)';
        
        setTimeout(() => {
            element.style.color = '';
            element.style.fontWeight = '';
            element.style.transform = 'scale(1)';
        }, 300);
    }

    // Toast Notifications
    showToast(type, title, message, duration = 5000) {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        toast.innerHTML = `
            <div class="toast-icon">
                <i class="${icons[type]}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });

        toastContainer.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);
    }

    // Utility Functions
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async clearAllDocuments() {
        if (!confirm('Are you sure you want to clear all documents? This action cannot be undone.')) {
            return;
        }

        try {
            console.log('Starting clear documents operation...');
            this.clearDocsBtn.disabled = true;
            this.clearDocsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing...';

            const response = await fetch('/api/documents', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            console.log('Clear response status:', response.status);

            if (!response.ok) {
                let errorMessage = 'Failed to clear documents';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || errorMessage;
                    console.error('Clear API error:', error);
                } catch (e) {
                    // If can't parse JSON, use status text
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    console.error('Clear API error - could not parse JSON:', response.statusText);
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            console.log('Clear operation successful:', result);
            
            // Update UI state
            this.documentsUploaded = false;
            this.updateChatInterface();
            this.updateClearDocsButton();
            
            // Clear current files
            this.currentFiles = [];
            this.updateFileList();
            this.updateUploadButton();
            
            // Update status
            setTimeout(() => {
                this.checkSystemStatus();
            }, 500);

            this.showToast('success', 'Documents Cleared', result.message || 'All documents have been removed from the system');

        } catch (error) {
            console.error('Clear documents error:', error);
            console.error('Error type:', typeof error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack
            });
            
            // Provide more detailed error message
            let errorMessage = error.message || 'Unknown error occurred';
            if (errorMessage.includes('fetch')) {
                errorMessage = 'Network error - please check your connection and try again';
            }
            
            this.showToast('error', 'Clear Failed', errorMessage);
        } finally {
            this.clearDocsBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All Documents';
            this.updateClearDocsButton();
        }
    }

    updateClearDocsButton() {
        if (this.clearDocsBtn) {
            this.clearDocsBtn.disabled = !this.documentsUploaded;
        }
    }

    // Theme Management
    initializeTheme() {
        // Check for saved theme preference or default to system preference
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
            this.applyTheme(savedTheme);
        } else {
            // If no saved theme or invalid, use system preference but don't set auto
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const initialTheme = systemPrefersDark ? 'dark' : 'light';
            this.applyTheme(initialTheme);
            localStorage.setItem('theme', initialTheme);
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        let newTheme;

        // Improved logic: Light -> Dark -> Light (no auto mode in toggle)
        if (currentTheme === 'light') {
            newTheme = 'dark';
        } else if (currentTheme === 'dark') {
            newTheme = 'light';
        } else {
            // If no theme is set (auto mode), set opposite of system preference
            newTheme = systemPrefersDark ? 'light' : 'dark';
        }

        this.applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Show toast notification
        const themeNames = {
            'light': 'Light Mode',
            'dark': 'Dark Mode'
        };
        this.showToast('success', 'Theme Changed', `Switched to ${themeNames[newTheme]}`);
    }

    applyTheme(theme) {
        const root = document.documentElement;
        
        if (theme === 'auto') {
            // Remove data-theme attribute to use system preference
            root.removeAttribute('data-theme');
        } else {
            root.setAttribute('data-theme', theme);
        }

        // Update theme toggle button title
        const themeButton = document.getElementById('theme-toggle');
        if (themeButton) {
            const titles = {
                'light': 'Switch to Dark Mode',
                'dark': 'Switch to Light Mode',
                'auto': 'Using System Theme'
            };
            themeButton.title = titles[theme] || 'Toggle Theme';
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new EnterpriseRAGChatbot();
});

// Expose globally for HTML event handlers
window.removeFile = (index) => {
    if (window.chatbot) {
        window.chatbot.removeFile(index);
    }
};
