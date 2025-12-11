const productsBody = document.getElementById('productsBody');
const addProductBtn = document.getElementById('addProductBtn');
const invoiceForm = document.getElementById('invoiceForm');
const loadingOverlay = document.getElementById('loadingOverlay');

function calculateRowTotal(row) {
    const quantity = parseFloat(row.querySelector('.product-quantity').value) || 0;
    const price = parseFloat(row.querySelector('.product-price').value) || 0;
    const total = quantity * price;
    row.querySelector('.product-total').textContent = total.toFixed(2);
    updateSummary();
}

function updateSummary() {
    let subtotal = 0;
    let totalKdv = 0;

    const rows = productsBody.querySelectorAll('.product-row');
    
    rows.forEach(row => {
        const quantity = parseFloat(row.querySelector('.product-quantity').value) || 0;
        const price = parseFloat(row.querySelector('.product-price').value) || 0;
        const kdvRate = parseFloat(row.querySelector('.product-kdv').value) || 0;
        
        const lineTotal = quantity * price;
        const kdvAmount = lineTotal * (kdvRate / 100);
        
        subtotal += lineTotal;
        totalKdv += kdvAmount;
    });

    const grandTotal = subtotal + totalKdv;

    document.getElementById('subtotal').textContent = subtotal.toFixed(2) + ' ₺';
    document.getElementById('totalKdv').textContent = totalKdv.toFixed(2) + ' ₺';
    document.getElementById('grandTotal').textContent = grandTotal.toFixed(2) + ' ₺';
}

function addProductRow() {
    const newRow = document.createElement('tr');
    newRow.className = 'product-row';
    newRow.innerHTML = `
        <td><input type="text" class="product-name" placeholder="Ürün adı" required></td>
        <td><input type="number" class="product-quantity" min="1" value="1" step="0.01" required></td>
        <td><input type="number" class="product-price" min="0" step="0.01" placeholder="0.00" required></td>
        <td>
            <select class="product-kdv">
                <option value="0">0</option>
                <option value="1">1</option>
                <option value="8">8</option>
                <option value="10" selected>10</option>
                <option value="20">20</option>
            </select>
        </td>
        <td class="product-total">0.00</td>
        <td><button type="button" class="btn-remove" onclick="removeProduct(this)">×</button></td>
    `;

    const inputs = newRow.querySelectorAll('.product-quantity, .product-price, .product-kdv');
    inputs.forEach(input => {
        input.addEventListener('input', () => calculateRowTotal(newRow));
        input.addEventListener('change', () => calculateRowTotal(newRow));
    });

    productsBody.appendChild(newRow);
}

function removeProduct(button) {
    const rows = productsBody.querySelectorAll('.product-row');
    if (rows.length > 1) {
        button.closest('.product-row').remove();
        updateSummary();
    } else {
        alert('En az bir ürün bulunmalıdır!');
    }
}

function collectProducts() {
    const products = [];
    const rows = productsBody.querySelectorAll('.product-row');
    
    rows.forEach(row => {
        const name = row.querySelector('.product-name').value.trim();
        const quantity = row.querySelector('.product-quantity').value;
        const price = row.querySelector('.product-price').value;
        const kdv = row.querySelector('.product-kdv').value;
        
        if (name && quantity && price) {
            products.push({
                name: name,
                quantity: quantity,
                price: price,
                kdv: kdv
            });
        }
    });
    
    return products;
}

addProductBtn.addEventListener('click', addProductRow);

productsBody.addEventListener('input', (e) => {
    if (e.target.matches('.product-quantity, .product-price, .product-kdv')) {
        const row = e.target.closest('.product-row');
        calculateRowTotal(row);
    }
});

productsBody.addEventListener('change', (e) => {
    if (e.target.matches('.product-quantity, .product-price, .product-kdv')) {
        const row = e.target.closest('.product-row');
        calculateRowTotal(row);
    }
});

invoiceForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const products = collectProducts();
    
    if (products.length === 0) {
        alert('Lütfen en az bir ürün ekleyin!');
        return;
    }
    
    const formData = new FormData(invoiceForm);
    formData.append('products', JSON.stringify(products));
    
    loadingOverlay.classList.add('active');
    
    try {
        const response = await fetch('/generate-pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('PDF oluşturma hatası');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fatura_${new Date().getTime()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        alert('PDF oluşturulurken bir hata oluştu: ' + error.message);
    } finally {
        loadingOverlay.classList.remove('active');
    }
});

updateSummary();