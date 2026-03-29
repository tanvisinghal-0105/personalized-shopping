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
        // Clear previous content
        statusDisplay.innerHTML = '';

        if (typeof data === 'object' && data !== null) {
            // Define the order and labels for keys
            const displayOrder = {
                customer_id: 'Customer ID',
                approval_status: 'Approval Status',
                discount_type: 'Discount Type',
                discount_value: 'Discount Value',
                product_id: 'Product ID',
                crmAccountId: 'CRM Account ID',
                escalationHost: 'Escalation Host',
                menuLang: 'Menu Language',
                menuId: 'Menu ID',
                messages: 'Messages' // Special handling
            };

            for (const key in displayOrder) {
                if (data.hasOwnProperty(key)) {
                    const value = data[key];
                    const label = displayOrder[key];

                    const itemDiv = document.createElement('div');
                    itemDiv.classList.add('detail-item');

                    const keySpan = document.createElement('span');
                    keySpan.classList.add('detail-key');
                    keySpan.textContent = `${label}:`;
                    itemDiv.appendChild(keySpan);

                    const valueSpan = document.createElement('span');
                    valueSpan.classList.add('detail-value');

                    if (key === 'approval_status') {
                        // Special styling for approval status
                        const statusBadge = document.createElement('span');
                        statusBadge.classList.add('status-badge');
                        statusBadge.textContent = value;
                        // Add classes based on value (e.g., approved, pending, denied)
                        statusBadge.classList.add(value.toLowerCase()); 
                        valueSpan.appendChild(statusBadge);
                    } else if (key === 'messages' && typeof value === 'object' && value !== null) {
                        // Handle messages object
                        const messagesList = document.createElement('div');
                        messagesList.classList.add('messages-details');
                        for (const msgKey in value) {
                            if (value.hasOwnProperty(msgKey)) {
                                const msgItemDiv = document.createElement('div');
                                msgItemDiv.classList.add('message-item');
                                
                                const msgKeySpan = document.createElement('span');
                                msgKeySpan.classList.add('message-key');
                                msgKeySpan.textContent = `${msgKey}:`;
                                msgItemDiv.appendChild(msgKeySpan);

                                const msgValueSpan = document.createElement('span');
                                msgValueSpan.classList.add('message-value');
                                if (Array.isArray(value[msgKey])) {
                                    // Display agent messages as a list
                                    const agentList = document.createElement('ul');
                                    value[msgKey].forEach(agentMsg => {
                                        const li = document.createElement('li');
                                        li.textContent = agentMsg;
                                        agentList.appendChild(li);
                                    });
                                    msgValueSpan.appendChild(agentList);
                                } else {
                                    msgValueSpan.textContent = value[msgKey];
                                }
                                msgItemDiv.appendChild(msgValueSpan);
                                messagesList.appendChild(msgItemDiv);
                            }
                        }
                        valueSpan.appendChild(messagesList);
                    } else {
                        // Default display for other values
                        valueSpan.textContent = value;
                    }

                    itemDiv.appendChild(valueSpan);
                    statusDisplay.appendChild(itemDiv);
                }
            }
             // Handle keys not in displayOrder (optional, for completeness)
             for (const key in data) {
                 if (data.hasOwnProperty(key) && !displayOrder.hasOwnProperty(key)) {
                     const itemDiv = document.createElement('div');
                     itemDiv.classList.add('detail-item', 'extra-detail'); // Mark as extra
                     const keySpan = document.createElement('span');
                     keySpan.classList.add('detail-key');
                     keySpan.textContent = `${key}:`;
                     itemDiv.appendChild(keySpan);
                     const valueSpan = document.createElement('span');
                     valueSpan.classList.add('detail-value');
                     valueSpan.textContent = typeof data[key] === 'object' ? JSON.stringify(data[key]) : data[key];
                     itemDiv.appendChild(valueSpan);
                     statusDisplay.appendChild(itemDiv);
                 }
             }

        } else {
            // Handle non-object data (e.g., simple success message)
            const simpleText = document.createElement('p');
            simpleText.textContent = data;
            statusDisplay.appendChild(simpleText);
        }

        customerInfoDiv.style.display = 'block'; // Show info div
        errorMessageDiv.style.display = 'none'; // Hide error div
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
            const response = await fetch(`${API_BASE_URL}/${customerId}`);
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
            const response = await fetch(`${API_BASE_URL}/${customerId}`, {
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
            const response = await fetch(resetApiUrl, {
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
            const response = await fetch(resetApprovalApiUrl, {
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