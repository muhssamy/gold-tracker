document.addEventListener('DOMContentLoaded', function() {
    // Set default date to today
    document.getElementById('purchase-date').valueAsDate = new Date();
    
    // Fetch and display current gold price (initial load uses cache)
    fetchCurrentPrice(false);
    
    // Load existing purchases (initial load uses cache)
    loadPurchases(false);
    
    // Set up form submission
    document.getElementById('gold-purchase-form').addEventListener('submit', function(event) {
        event.preventDefault();
        addPurchase();
    });
    
    // Set up historical price fetch button
    document.getElementById('fetch-historical-price').addEventListener('click', function() {
        fetchHistoricalPrice();
    });
    
    // Set up refresh button
    document.getElementById('refresh-prices').addEventListener('click', function() {
        // Show loading state for the button
        const button = document.getElementById('refresh-prices');
        button.disabled = true;
        button.innerHTML = '<span class="refresh-icon spin">↻</span> Refreshing...';
        
        // Force refresh from API (bypass cache)
        fetchCurrentPrice(true);
        loadPurchases(true);
        
        // Reset button after a short delay
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = '<span class="refresh-icon">↻</span> Refresh Prices';
        }, 2000);
    });
});

function fetchCurrentPrice(forceRefresh = false) {
    fetch(`/api/current-price?refresh=${forceRefresh}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const priceDisplay = document.getElementById('current-price-display');
                const priceValue = priceDisplay.querySelector('.price-value');
                const priceTime = priceDisplay.querySelector('.price-time');
                
                // Format price with 2 decimal places
                priceValue.textContent = `${data.price.toFixed(2)} SAR per gram (${data.price_usd.toFixed(2)} USD)`;
                
                // Format timestamp and show cached status
                const cachedText = data.cached ? ' • Cached' : ' • Fresh data';
                
                if (data.last_updated) {
                    priceTime.textContent = `Last updated: ${data.last_updated} • Exchange rate: 1 USD = ${data.exchange_rate.toFixed(2)} SAR${cachedText}`;
                } else {
                    const timestamp = new Date(data.timestamp * 1000); // Convert UNIX timestamp to date
                    priceTime.textContent = `Last updated: ${timestamp.toLocaleString()} • Exchange rate: 1 USD = ${data.exchange_rate.toFixed(2)} SAR${cachedText}`;
                }
                
                // Update cached status indicator
                updateCacheStatus(data.cached, data.last_updated);
                
            } else {
                showError(data.message || 'Failed to fetch current price');
            }
        })
        .catch(error => {
            showError('Network error when fetching current price');
            console.error('Error:', error);
        });
}

function fetchHistoricalPrice() {
    const purchaseDate = document.getElementById('purchase-date').value;
    
    if (!purchaseDate) {
        showError('Please select a purchase date first');
        return;
    }
    
    fetch(`/api/historical-price?date=${purchaseDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('purchase-price').value = data.price.toFixed(2);
            } else {
                showError(data.message || 'Failed to fetch historical price');
            }
        })
        .catch(error => {
            showError('Network error when fetching historical price');
            console.error('Error:', error);
        });
}

function addPurchase() {
    // Get form values
    const purchaseDate = document.getElementById('purchase-date').value;
    const purchasePrice = parseFloat(document.getElementById('purchase-price').value);
    const grams = parseFloat(document.getElementById('grams').value);
    const description = document.getElementById('description').value || '';
    
    // Validate inputs
    if (!purchaseDate || isNaN(purchasePrice) || isNaN(grams)) {
        showError('Please fill in all required fields with valid values');
        return;
    }
    
    // Send purchase data to server
    fetch('/api/purchases', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            purchase_date: purchaseDate,
            purchase_price: purchasePrice,
            grams: grams,
            description: description
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset form
            document.getElementById('purchase-date').valueAsDate = new Date();
            document.getElementById('purchase-price').value = '';
            document.getElementById('grams').value = '';
            document.getElementById('description').value = '';
            
            // Reload purchases using cache
            loadPurchases(false);
        } else {
            showError(data.message || 'Failed to add purchase');
        }
    })
    .catch(error => {
        showError('Network error when adding purchase');
        console.error('Error:', error);
    });
}

function loadPurchases(forceRefresh = false) {
    fetch(`/api/purchases?refresh=${forceRefresh}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPurchases(data.purchases, data.summary);
                updateCacheStatus(data.summary.cached, data.summary.last_updated);
            } else {
                showError(data.message || 'Failed to load purchases');
            }
        })
        .catch(error => {
            showError('Network error when loading purchases');
            console.error('Error:', error);
        });
}

function updateCacheStatus(isCached, lastUpdated) {
    const lastUpdatedText = document.getElementById('last-updated-text');
    const cacheStatus = document.getElementById('cache-status');
    
    if (lastUpdated) {
        lastUpdatedText.textContent = `Last updated: ${lastUpdated}`;
    } else {
        lastUpdatedText.textContent = 'Last updated: Unknown';
    }
    
    if (isCached) {
        cacheStatus.textContent = 'Cached';
        cacheStatus.classList.add('cached');
        cacheStatus.classList.remove('fresh');
    } else {
        cacheStatus.textContent = 'Fresh Data';
        cacheStatus.classList.add('fresh');
        cacheStatus.classList.remove('cached');
    }
}

function displayPurchases(purchases, summary) {
    const tableBody = document.getElementById('purchases-body');
    const summaryRow = document.getElementById('summary-row');
    
    // Clear the table body
    tableBody.innerHTML = '';
    
    if (purchases.length === 0) {
        tableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="8">No purchases yet. Add a purchase above.</td>
            </tr>
        `;
        summaryRow.classList.add('hidden');
        return;
    }
    
    // Add each purchase to the table
    purchases.forEach(purchase => {
        const row = document.createElement('tr');
        
        // Format the purchase date
        const date = new Date(purchase.purchase_date);
        const formattedDate = date.toLocaleDateString();
        
        // Determine profit/loss class
        const profitLossClass = purchase.is_profit ? 'profit' : 'loss';
        const profitLossSign = purchase.is_profit ? '+' : '';
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td>${purchase.description || '-'}</td>
            <td>${purchase.grams.toFixed(2)} g</td>
            <td>${purchase.purchase_price.toFixed(2)} SAR</td>
            <td>${purchase.purchase_value.toFixed(2)} SAR</td>
            <td>${purchase.current_value.toFixed(2)} SAR</td>
            <td class="${profitLossClass}">
                ${profitLossSign}${purchase.profit_loss.toFixed(2)} SAR 
                (${profitLossSign}${purchase.profit_loss_percentage.toFixed(2)}%)
            </td>
            <td>
                <button class="delete-button" data-id="${purchase.id}">Delete</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', function() {
            const purchaseId = this.getAttribute('data-id');
            deletePurchase(purchaseId);
        });
    });
    
    // Update summary row
    document.getElementById('total-investment').textContent = `${summary.total_investment.toFixed(2)} SAR`;
    document.getElementById('total-current-value').textContent = `${summary.total_current_value.toFixed(2)} SAR`;
    
    const totalProfitLossElement = document.getElementById('total-profit-loss');
    const profitLossSign = summary.is_profit ? '+' : '';
    totalProfitLossElement.textContent = `${profitLossSign}${summary.total_profit_loss.toFixed(2)} SAR (${profitLossSign}${summary.total_profit_loss_percentage.toFixed(2)}%)`;
    totalProfitLossElement.className = summary.is_profit ? 'profit' : 'loss';
    
    // Show summary row
    summaryRow.classList.remove('hidden');
}

function deletePurchase(purchaseId) {
    fetch(`/api/purchases/${purchaseId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadPurchases(false);  // Use cached price data
        } else {
            showError(data.message || 'Failed to delete purchase');
        }
    })
    .catch(error => {
        showError('Network error when deleting purchase');
        console.error('Error:', error);
    });
}

function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.querySelector('.error-text').textContent = message;
    errorElement.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorElement.classList.add('hidden');
    }, 5000);
}