export class GeminiAPI {
    constructor(endpoint = null, customerInfo = null) {
        // If no endpoint is provided, auto-detect from current URL
        if (!endpoint) {
            const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
            if (isLocal) {
                endpoint = 'ws://localhost:8081';
            } else {
                // In production, derive backend WebSocket URL from frontend hostname
                // cymbal-frontend-xxx -> live-agent-backend-xxx
                const backendHost = window.location.hostname.replace('cymbal-frontend', 'live-agent-backend');
                endpoint = `wss://${backendHost}`;
            }
        }

        // Append customer info and auth token as query parameters
        if (customerInfo && customerInfo.customerId) {
            const params = new URLSearchParams({
                customer_id: customerInfo.customerId,
                first_name: customerInfo.firstName || '',
                last_name: customerInfo.lastName || '',
                email: customerInfo.email || ''
            });
            // Pass Google ID token for backend authentication
            if (customerInfo.googleIdToken) {
                params.set('id_token', customerInfo.googleIdToken);
            }
            endpoint = `${endpoint}?${params.toString()}`;
            console.log('Customer info added to WebSocket URL:', customerInfo);
        }

        this.endpoint = endpoint;
        this.ws = null;
        this.isSpeaking = false;
        this.connect();
        this.retryCount = 0;
        this.maxRetries = 5;
    }

    connect() {
        console.log('Initializing GeminiAPI with endpoint:', this.endpoint);
        this.ws = new WebSocket(this.endpoint);
        // Reset retry count when a new connection attempt starts
        //this.retryCount = 0; // We will reset it upon successful connection instead
        
        this.onReady = () => {};
        this.onAudioData = () => {};
        this.onTextContent = () => {};
        this.onError = () => {};
        this.onTurnComplete = () => {};
        this.onFunctionCall = (data) => {
            console.log('Function Call:', data);
            this.logMessage({type: 'tool_call', data: data});
        };
        this.onFunctionResponse = (data) => {
            console.log('Function Response:', data);
            this.logMessage({type: 'tool_result', data: data});
        };
        this.onInterrupted = () => {};  // New callback for interruption events
        this.onTriggerPhotoAnalysis = () => {};  // New callback for voice-triggered photo analysis
        
        this.setupWebSocket();
        this.logMessage = () => {};
    }

    setupWebSocket() {
        this.ws.onopen = () => {
            console.log('WebSocket connection is opening...');
            console.log('WebSocket connection established successfully.');
            this.retryCount = 0; // Reset retry count on successful connection
            this.onReady();
        };

        this.ws.onmessage = async (event) => {
            console.log('Receiving...', event);
            try {
                let response;
                if (event.data instanceof Blob) {
                    console.log('Received blob data, converting to text...');
                    const responseText = await event.data.text();
                    response = JSON.parse(responseText);
                } else {
                    response = JSON.parse(event.data);
                }
                
                console.log('WebSocket Response:', response);

                if (response.type === 'error') {
                    console.error('Server error:', response.data);
                    this.onError(response.data);
                    return;
                }

                if (response.ready) {
                    console.log('Received ready signal from server');
                    this.onReady();
                    return;
                }

                if (response.type === 'interrupted') {
                    console.log('Response interrupted:', response.data);
                    this.isSpeaking = false;
                    this.onInterrupted(response.data);
                } else if (response.type === 'trigger_photo_analysis') {
                    console.log('Voice command triggered photo analysis:', response.data);
                    this.onTriggerPhotoAnalysis(response.data);
                } else if (response.type === 'audio') {
                    console.log('Received audio data');
                    this.onAudioData(response.data);
                } else if (response.type === 'text') {
                    console.log('Received text content:', response.data);
                    this.onTextContent(response.data);
                } else if (response.type === 'turn_complete') {
                    console.log('Turn complete');
                    this.onTurnComplete();
                } else if (response.type === 'tool_call') {
                    console.log('Received function call:', response.data);
                    this.onFunctionCall(response.data);
                } else if (response.type === 'tool_result') {
                    console.log('Received function response:', response.data);
                    this.onFunctionResponse(response.data);
                } else if (response.type === 'style_preview_update') {
                    console.log('Received style preview update:', response.data?.style_id);
                    if (this.onStylePreviewUpdate) {
                        this.onStylePreviewUpdate(response.data);
                    }
                } else if (response.type === 'style_preview_done') {
                    console.log('Style preview personalisation complete');
                    if (this.onStylePreviewDone) {
                        this.onStylePreviewDone();
                    }
                } else {
                    console.log('Received unknown message type:', response);
                }
            } catch (error) {
                console.error('Error parsing response:', error);
                console.error('Raw response data:', event.data);
                this.onError({
                    message: 'Error parsing response: ' + error.message,
                    error_type: 'client_error'
                });
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
            this.onError({
                message: 'Connection error occurred',
                action: 'Please check your internet connection and try again',
                error_type: 'websocket_error'
            });
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed:', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            
            // Only show error if it wasn't a clean close
            if (!event.wasClean) {
                this.onError({
                    message: 'Connection was interrupted',
                    action: 'Attempting to reconnect...',
                    error_type: 'connection_closed'
                });
                
                this._attemptReconnection();
            }
        };
    }

    sendAudioChunk(base64Audio) {
        console.log('Sending audio chunk...');
        this.sendMessage({
            type: 'audio',
            data: base64Audio
        });
    }

    sendImage(base64Image) {
        console.log('Sending image data...');
        this.sendMessage({
            type: 'image',
            data: base64Image
        });
    }

    sendEndMessage() {
        console.log('Sending end message: <end>');
        this.sendMessage({
            type: 'end'
        });
    }

    sendTextMessage(text) {
        console.log('Sending text message:', text);
        this.sendMessage({
            type: 'text',
            data: text
        });
    }

    sendCartAction(customerId, itemsToAdd = [], itemsToRemove = []) {
        console.log('Sending cart action:', { customerId, itemsToAdd, itemsToRemove });
        this.sendMessage({
            type: 'cart_action',
            data: {
                customer_id: customerId,
                items_to_add: itemsToAdd,
                items_to_remove: itemsToRemove,
            }
        });
    }

    sendMessage(message) {
        if (this.ws.readyState === WebSocket.OPEN) {
            console.log('Sending message:', {
                type: message.type,
                dataLength: message.data ? message.data.length : 0
            });
            this.ws.send(JSON.stringify(message));
        } else {
            const states = {
                0: 'CONNECTING',
                1: 'OPEN',
                2: 'CLOSING',
                3: 'CLOSED'
            };
            const currentState = states[this.ws.readyState];
            console.error('WebSocket is not open. Current state:', currentState);
            this.onError(`WebSocket is not ready (State: ${currentState}). Attempting to reconnect.`);
            
            // Attempt to reconnect if the state is CLOSING or CLOSED
            if (this.ws.readyState === WebSocket.CLOSING || this.ws.readyState === WebSocket.CLOSED) {
                console.log('Attempting reconnection from sendMessage...');
                // Reset retry count before starting a new sequence from sendMessage
                this.retryCount = 0; 
                this._attemptReconnection();
            } else if (this.ws.readyState === WebSocket.CONNECTING) {
                console.warn('WebSocket is currently connecting. Message not sent.');
                // Optionally: Queue the message here to send once connected
            }
        }
    }

    async ensureConnected() {
        console.log('Ensuring WebSocket connection...');
        if (this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                console.error('Connection timeout after 5000ms');
                reject(new Error('Connection timeout'));
            }, 5000);

            const onOpen = () => {
                console.log('WebSocket connection established');
                clearTimeout(timeout);
                this.ws.removeEventListener('open', onOpen);
                this.ws.removeEventListener('error', onError);
                resolve();
            };

            const onError = (error) => {
                console.error('WebSocket connection failed:', error);
                clearTimeout(timeout);
                this.ws.removeEventListener('open', onOpen);
                this.ws.removeEventListener('error', onError);
                reject(error);
            };

            this.ws.addEventListener('open', onOpen);
            this.ws.addEventListener('error', onError);
        });
    }

    _attemptReconnection() {
        this.retryCount++;
        if (this.retryCount <= this.maxRetries) {
            // Calculate delay with exponential backoff (e.g., 1s, 2s, 4s, 8s, 16s)
            // Add some jitter (randomness +/- 500ms) to prevent thundering herd
            const delay = Math.pow(2, this.retryCount - 1) * 1000 + (Math.random() * 1000 - 500);
            console.log(`Attempting reconnect ${this.retryCount}/${this.maxRetries} in ${delay.toFixed(0)}ms...`);
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error(`Max retries (${this.maxRetries}) reached. Giving up.`);
            this.onError({
                message: 'Connection failed after multiple retries',
                action: 'Please check your connection or refresh the page',
                error_type: 'connection_failed'
            });
        }
    }
}