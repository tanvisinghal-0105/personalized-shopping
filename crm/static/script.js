// Authenticated fetch helper -- adds Bearer token from localStorage
function authFetch(url, options = {}) {
    const saved = localStorage.getItem('cymbalUser');
    if (saved) {
        try {
            const user = JSON.parse(saved);
            if (user.googleIdToken) {
                options.headers = options.headers || {};
                options.headers['Authorization'] = 'Bearer ' + user.googleIdToken;
            }
        } catch(e) {}
    }
    return fetch(url, options);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed.');
    const customerIdInput = document.getElementById('customerId');
    const getStatusBtn = document.getElementById('getStatusBtn');
    const approveBtn = document.getElementById('approveBtn');
    const statusDisplay = document.getElementById('statusDisplay');
    const customerInfoDiv = document.getElementById('customerInfo');
    const errorMessageDiv = document.getElementById('errorMessage');
    const resetCartBtn = document.getElementById('resetCartBtn');

    // Base URL for the API - Adjust if your FastAPI server runs elsewhere
    // if project id 
    // const API_BASE_URL = 'http://localhost:8082/api/v1/approvals';
    // const API_BASE_URL = 'https://live-agent-crm-666465463731.us-central1.run.app/api/v1/approvals';
    const API_BASE_URL = '/api/v1/approvals'; // Use relative path

    function displayError(message) {
        console.error('Error:', message);
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'flex';
        customerInfoDiv.style.display = 'none';
    }

    function displayStatus(data) {
        console.log('Displaying status:', data);
        statusDisplay.innerHTML = '';

        if (typeof data === 'string') {
            const simpleText = document.createElement('p');
            simpleText.textContent = data;
            statusDisplay.appendChild(simpleText);
            customerInfoDiv.style.display = 'block';
            errorMessageDiv.style.display = 'none';
            return;
        }

        if (typeof data !== 'object' || data === null) return;

        function addRow(label, value, className) {
            const row = document.createElement('div');
            row.classList.add('detail-item');
            if (className) row.classList.add(className);
            const keyEl = document.createElement('span');
            keyEl.classList.add('detail-key');
            keyEl.textContent = label + ':';
            row.appendChild(keyEl);
            const valEl = document.createElement('span');
            valEl.classList.add('detail-value');
            if (typeof value === 'object' && value !== null) {
                const badge = document.createElement('span');
                badge.classList.add('status-badge', (value.class || ''));
                badge.textContent = value.text || '';
                valEl.appendChild(badge);
            } else {
                valEl.textContent = value;
            }
            row.appendChild(valEl);
            statusDisplay.appendChild(row);
        }

        // Header info
        addRow('Customer ID', data.customer_id || 'N/A');
        addRow('Approval Status', {
            text: data.approval_status || 'unknown',
            class: (data.approval_status || '').toLowerCase()
        });
        addRow('Requested At', data.requested_at || 'N/A');

        // Discount details
        if (data.discount_type) {
            addRow('Discount Type', data.discount_type);
            addRow('Discount Value', data.discount_type === 'percentage'
                ? data.discount_value + '%'
                : data.discount_value + ' EUR');
            if (data.reason) addRow('Reason', data.reason);
        }

        // Cart items
        if (data.cart_items && data.cart_items.length > 0) {
            const cartHeader = document.createElement('div');
            cartHeader.style.cssText = 'margin-top:12px;padding-top:12px;border-top:1px solid var(--color-border);font-weight:600;font-size:0.9em;margin-bottom:8px;';
            cartHeader.textContent = 'Cart Items';
            statusDisplay.appendChild(cartHeader);

            data.cart_items.forEach(item => {
                addRow(item.name, (item.price || 0).toFixed(2) + ' EUR x' + (item.quantity || 1));
            });

            addRow('Cart Subtotal', (data.cart_subtotal || 0).toFixed(2) + ' EUR');
            if (data.discount_amount_eur) {
                addRow('Discount Amount', '-' + data.discount_amount_eur.toFixed(2) + ' EUR');
            }
            if (data.new_total_after_discount !== undefined) {
                addRow('New Total', data.new_total_after_discount.toFixed(2) + ' EUR');
            }
        }

        customerInfoDiv.style.display = 'block';
        errorMessageDiv.style.display = 'none';
    }

    function clearMessages() {
        errorMessageDiv.textContent = '';
        errorMessageDiv.style.display = 'none';
        statusDisplay.textContent = '';
        customerInfoDiv.style.display = 'none';
    }

    async function getApprovalStatus() {
        console.log('"Get Approval Status" button clicked.');
        const customerId = customerIdInput.value.trim();
        if (!customerId) {
            console.warn('Customer ID input is empty.');
            displayError('Please enter a Customer ID.');
            return;
        }
        clearMessages();
        customerInfoDiv.style.display = 'block';
        statusDisplay.textContent = 'Loading...';

        try {
            console.log(`Fetching status for customer ID: ${customerId} from ${API_BASE_URL}/${customerId}`);
            const response = await authFetch(`${API_BASE_URL}/${customerId}`);
            console.log('Received response:', response);
            const data = await response.json();

            if (!response.ok) {
                console.error(`API Error: Status ${response.status}, Message: ${data.detail || data.error || 'Unknown error'}`);
                throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`);
            }

            console.log('Successfully fetched status:', data);
            displayStatus(data);
        } catch (error) {
            console.error('Error fetching approval status:', error);
            customerInfoDiv.style.display = 'none';
            displayError(`Failed to fetch status: ${error.message}`);
        }
    }

    async function approveCustomer() {
        console.log('"Approve Customer" button clicked.');
        const customerId = customerIdInput.value.trim();
        if (!customerId) {
            console.warn('Customer ID input is empty.');
            displayError('Please enter a Customer ID.');
            return;
        }
        clearMessages();
        customerInfoDiv.style.display = 'block';
        statusDisplay.textContent = 'Approving...';

        try {
            console.log(`Sending PUT request to approve customer ID: ${customerId} at ${API_BASE_URL}/${customerId}`);
            const response = await authFetch(`${API_BASE_URL}/${customerId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            console.log('Received response:', response);
            const data = await response.json();

            if (!response.ok) {
                console.error(`API Error: Status ${response.status}, Message: ${data.detail || data.error || 'Unknown error'}`);
                throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`);
            }

            console.log('Successfully approved customer:', data);
            displayStatus(`Approval successful for customer ${data.customer_id}. Status updated to 'approved'.`);
        } catch (error) {
            console.error('Error approving customer:', error);
            customerInfoDiv.style.display = 'none';
            displayError(`Failed to approve: ${error.message}`);
        }
    }

    // Function to reset the cart
    async function resetCustomerCart() {
        const customerId = customerIdInput.value.trim(); // Use customer ID from input field
        if (!customerId) {
            console.warn('Customer ID input is empty.');
            displayError('Please enter a Customer ID.');
            return;
        }
        const resetApiUrl = `/api/v1/reset_cart/${customerId}`; // Adjust path as needed
        console.log(`Sending POST request to reset cart for customer ID: ${customerId} at ${resetApiUrl}`);

        clearMessages(); // Clear previous messages
        customerInfoDiv.style.display = 'block'; // Show info div to display message
        statusDisplay.textContent = 'Resetting cart...'; // Show loading message

        try {
            const response = await authFetch(resetApiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            console.log('Received response:', response);
            const data = await response.json();

            if (!response.ok) {
                console.error(`API Error: Status ${response.status}, Message: ${data.detail || data.error || 'Unknown error'}`);
                throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`);
            }

            console.log('Successfully reset cart:', data);
            // Display a simple success message in the status area
            displayStatus(`Cart successfully reset for customer ${customerId}.`);
        } catch (error) {
            console.error('Error resetting cart:', error);
            customerInfoDiv.style.display = 'none'; // Hide info div on error
            displayError(`Failed to reset cart: ${error.message}`);
        }
    }

    // Function to reset approval status
    async function resetApprovalStatus() {
        const customerId = customerIdInput.value.trim();
        if (!customerId) {
            console.warn('Customer ID input is empty.');
            displayError('Please enter a Customer ID.');
            return;
        }
        const resetApprovalApiUrl = `/api/v1/reset_approval/${customerId}`;
        console.log(`Sending POST request to reset approval status for customer ID: ${customerId} at ${resetApprovalApiUrl}`);

        clearMessages();
        customerInfoDiv.style.display = 'block';
        statusDisplay.textContent = 'Resetting approval status...';

        try {
            const response = await authFetch(resetApprovalApiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            console.log('Received response:', response);
            const data = await response.json();

            if (!response.ok) {
                console.error(`API Error: Status ${response.status}, Message: ${data.detail || data.error || 'Unknown error'}`);
                throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`);
            }

            console.log('Successfully reset approval status:', data);
            displayStatus(`Approval status successfully reset to pending for customer ${customerId}.`);
        } catch (error) {
            console.error('Error resetting approval status:', error);
            customerInfoDiv.style.display = 'none';
            displayError(`Failed to reset approval status: ${error.message}`);
        }
    }

    getStatusBtn.addEventListener('click', getApprovalStatus);
    approveBtn.addEventListener('click', approveCustomer);
    resetCartBtn.addEventListener('click', resetCustomerCart);
    const resetApprovalBtn = document.getElementById('resetApprovalBtn');
    resetApprovalBtn.addEventListener('click', resetApprovalStatus);
    console.log('Event listeners added.');
}); 