
    function buildRow(cells, rowClass) {
        const tr = document.createElement('tr');
        if (rowClass) tr.className = rowClass;
        
        cells.forEach(cell => {
            const td = document.createElement('td');
            if (cell.className) td.className = cell.className;
            if (cell.html) {
                td.innerHTML = cell.html;
            } else if (cell.text) {
                td.textContent = cell.text;
            }
            tr.appendChild(td);
        });
        return tr;
    }

    document.addEventListener("DOMContentLoaded", () => {
        loadExpenses();
        loadIncome();

        // Add Fixed Income Logic
        document.getElementById('add-fixed-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errDiv = document.getElementById('add-fixed-error');
            errDiv.classList.add('hidden');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Saving...';
            
            const payload = {
                date: document.getElementById('add-fix-date').value,
                amount: document.getElementById('add-fix-amount').value,
                income_type: 'Fixed',
                description: document.getElementById('add-fix-desc').value
            };
            
            try {
                const res = await fetch('/app/api/transactions/income', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': getCookie('csrf_access_token')
                    },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    e.target.reset();
                    closeModal('add-fixed');
                    loadIncome();
                } else {
                    errDiv.textContent = data.error || data.msg || data.message || "Failed to save fixed income";
                    errDiv.classList.remove('hidden');
                }
            } catch (err) {
                console.error(err);
                errDiv.textContent = "Network error. Please try again.";
                errDiv.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Fixed Income';
            }
        });

        // Update Fixed Income Logic
        document.getElementById('update-fixed-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errDiv = document.getElementById('update-fixed-error');
            errDiv.classList.add('hidden');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Saving...';
            
            const id = document.getElementById('edit-fix-id').value;
            const payload = {
                date: document.getElementById('edit-fix-date').value,
                amount: document.getElementById('edit-fix-amount').value,
                description: document.getElementById('edit-fix-desc').value
            };
            
            try {
                const res = await fetch(`/app/api/transactions/income/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': getCookie('csrf_access_token')
                    },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    e.target.reset();
                    closeModal('update-fixed-form');
                    closeModal('update-fixed-select');
                    loadIncome();
                } else {
                    errDiv.textContent = data.error || "Failed to update fixed income";
                    errDiv.classList.remove('hidden');
                }
            } catch (err) {
                console.error(err);
                errDiv.textContent = "Network error. Please try again.";
                errDiv.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Changes';
            }
        });

        // Variable Income Logic
        document.getElementById('variable-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errDiv = document.getElementById('variable-error');
            errDiv.classList.add('hidden');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Saving...';
            
            const payload = {
                date: document.getElementById('var-date').value,
                amount: document.getElementById('var-amount').value,
                income_type: 'Variable',
                description: document.getElementById('var-desc').value
            };
            
            try {
                const res = await fetch('/app/api/transactions/income', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': getCookie('csrf_access_token')
                    },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    e.target.reset();
                    closeModal('variable');
                    loadIncome();
                } else {
                    errDiv.textContent = data.error || "Failed to save variable income";
                    errDiv.classList.remove('hidden');
                }
            } catch (err) {
                console.error(err);
                errDiv.textContent = "Network error. Please try again.";
                errDiv.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Variable Income';
            }
        });

        // Add Expense Logic
        document.getElementById('expense-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errDiv = document.getElementById('expense-error');
            errDiv.classList.add('hidden');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Saving...';
            
            const payload = {
                date: document.getElementById('exp-date').value,
                amount: document.getElementById('exp-amount').value,
                description: document.getElementById('exp-desc').value,
                category: document.getElementById('exp-category').value
            };
            
            try {
                const res = await fetch('/app/api/transactions/expense', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': getCookie('csrf_access_token')
                    },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    e.target.reset();
                    closeModal('expense');
                    loadExpenses();
                } else {
                    errDiv.textContent = data.error || "Failed to save expense";
                    errDiv.classList.remove('hidden');
                }
            } catch (err) {
                console.error(err);
                errDiv.textContent = "Network error. Please try again.";
                errDiv.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Expense';
            }
        });

        // CSV Logic
        const csvFile = document.getElementById('csv-file');
        const csvFileName = document.getElementById('csv-file-name');
        const csvPreviewBtn = document.getElementById('csv-preview-btn');
        let uploadedFile = null;

        csvFile.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadedFile = e.target.files[0];
                csvFileName.textContent = uploadedFile.name;
                csvFileName.classList.remove('hidden');
                csvPreviewBtn.classList.remove('hidden');
            }
        });

        document.getElementById('csv-upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!uploadedFile) return;
            
            const errDiv = document.getElementById('csv-error');
            errDiv.classList.add('hidden');
            csvPreviewBtn.disabled = true;
            csvPreviewBtn.innerHTML = 'Parsing...';
            
            const formData = new FormData();
            formData.append('file', uploadedFile);
            
            try {
                const res = await fetch('/app/api/transactions/upload-csv', {
                    method: 'POST',
                    headers: {
                        'X-CSRF-TOKEN': getCookie('csrf_access_token')
                    },
                    body: formData
                });
                const data = await res.json();
                
                if (res.ok && data.success) {
                    document.getElementById('csv-upload-step').classList.add('hidden');
                    document.getElementById('csv-preview-step').classList.remove('hidden');
                    
                    document.getElementById('csv-preview-stats').innerHTML = `Found <span class="font-bold text-fz-black">${data.valid_count} valid</span> and <span class="font-bold text-fz-red">${data.invalid_count} invalid</span> records.`;
                    
                    const tbody = document.getElementById('csv-preview-body');
                    tbody.innerHTML = '';
                    
                    let allRecords = [...data.valid_records, ...data.invalid_records].sort((a, b) => {
                        if (a.is_valid && !b.is_valid) return -1;
                        if (!a.is_valid && b.is_valid) return 1;
                        return a.row_number - b.row_number;
                    });
                    
                    const cats = JSON.parse(document.getElementById('expense-categories-data').dataset.categories || '[]');
                    
                    let htmlStr = '';
                    allRecords.forEach(r => {
                        const isValid = r.is_valid;
                        const rowClass = isValid ? 'bg-white hover:bg-gray-50 transition-colors' : 'bg-red-50 transition-colors';
                        const dateClass = r.errors.some(e=>e.toLowerCase().includes('date')) ? 'border-red-500 bg-red-50' : 'border-gray-200';
                        const catClass = r.errors.some(e=>e.toLowerCase().includes('category')) ? 'border-red-500 bg-red-50' : 'border-gray-200';
                        const amtClass = r.errors.some(e=>e.toLowerCase().includes('amount')) ? 'border-red-500 bg-red-50' : 'border-gray-200';
                        
                        let isCustom = r.category && !cats.includes(r.category);
                        
                        let selectOptions = `<option value="" disabled ${!r.category ? 'selected' : ''}>Select category...</option>`;
                        if (isCustom && r.category) {
                            selectOptions += `<option value="${r.category}" selected>${r.category} (Invalid)</option>`;
                        }
                        cats.forEach(c => {
                            selectOptions += `<option value="${c}" ${c === r.category && !isCustom ? 'selected' : ''}>${c}</option>`;
                        });
                        selectOptions += `<option value="__custom__">Other (Custom)</option>`;
                        
                        htmlStr += `
                            <tr class="${rowClass}" id="csv-row-${r.row_number}">
                                <td class="px-4 py-2">${r.row_number}</td>
                                <td class="px-4 py-2">
                                    <input type="date" class="csv-input-date w-full min-w-[130px] px-2 py-1 border rounded ${dateClass}" value="${r.date || ''}" data-row="${r.row_number}">
                                </td>
                                <td class="px-4 py-2 align-top">
                                    <div class="relative min-w-[160px]">
                                        <select class="csv-select-cat w-full px-2 py-1 border rounded ${catClass}" data-row="${r.row_number}">
                                            ${selectOptions}
                                        </select>
                                        <input type="text" class="csv-input-cat w-full px-2 py-1 border rounded ${catClass} hidden" value="${isCustom ? r.category : ''}" placeholder="Type category..." data-row="${r.row_number}">
                                    </div>
                                </td>
                                <td class="px-4 py-2 text-right">
                                    <input type="number" step="0.01" class="csv-input-amt w-24 px-2 py-1 border rounded text-right ${amtClass}" value="${r.amount || ''}" data-row="${r.row_number}">
                                </td>
                                <td class="px-4 py-2" id="csv-status-${r.row_number}">
                                    ${isValid ? '<span class="text-green-600 text-xs font-semibold">Valid</span>' : `<span class="text-fz-red text-xs font-semibold">${r.errors.join(', ')}</span>`}
                                </td>
                                <td class="px-4 py-2 text-center">
                                    <input type="checkbox" class="csv-row-select w-4 h-4 rounded border-gray-300 text-fz-red accent-red-600 focus:ring-fz-red cursor-pointer" value="${r.row_number}" ${isValid ? 'checked' : ''}>
                                    <input type="hidden" class="csv-input-desc" value="${(r.description || '').replace(/"/g, '&quot;')}" data-row="${r.row_number}">
                                </td>
                            </tr>
                        `;
                    });
                    tbody.innerHTML = htmlStr;
                    
                    const confirmBtn = document.getElementById('csv-confirm-btn');
                    
                    function updateSelectedCount() {
                        const selectedCount = document.querySelectorAll('.csv-row-select:checked').length;
                        if (selectedCount === 0) {
                            confirmBtn.disabled = true;
                            confirmBtn.innerHTML = 'Confirm Import (0)';
                        } else {
                            confirmBtn.disabled = false;
                            confirmBtn.innerHTML = `Confirm Import (${selectedCount})`;
                        }
                        
                        const selectAll = document.getElementById('csv-select-all');
                        const totalSelectable = document.querySelectorAll('.csv-row-select').length;
                        if (totalSelectable === 0) {
                            selectAll.checked = false;
                            selectAll.indeterminate = false;
                        } else if (selectedCount === totalSelectable) {
                            selectAll.checked = true;
                            selectAll.indeterminate = false;
                        } else if (selectedCount === 0) {
                            selectAll.checked = false;
                            selectAll.indeterminate = false;
                        } else {
                            selectAll.checked = false;
                            selectAll.indeterminate = true;
                        }
                    }
                    
                    // Initial update
                    if (data.valid_count === 0) {
                        confirmBtn.disabled = true;
                        confirmBtn.innerHTML = 'No Valid Records';
                        document.getElementById('csv-select-all').disabled = true;
                    } else {
                        document.getElementById('csv-select-all').disabled = false;
                        document.getElementById('csv-select-all').checked = true;
                        updateSelectedCount();
                    }
                    
                    // Event listeners
                    document.getElementById('csv-select-all').addEventListener('change', (e) => {
                        document.querySelectorAll('.csv-row-select').forEach(cb => {
                            cb.checked = e.target.checked;
                        });
                        updateSelectedCount();
                    });
                    
                    tbody.addEventListener('change', (e) => {
                        if (e.target.classList.contains('csv-row-select')) {
                            updateSelectedCount();
                        }
                    });
                } else {
                    errDiv.textContent = data.error || "Failed to parse CSV";
                    errDiv.classList.remove('hidden');
                }
            } catch (err) {
                console.error(err);
                errDiv.textContent = "Network error while parsing.";
                errDiv.classList.remove('hidden');
            } finally {
                csvPreviewBtn.disabled = false;
                csvPreviewBtn.innerHTML = 'Preview Import';
            }
        });
        
        // Track edits visually
        document.getElementById('csv-preview-body').addEventListener('input', (e) => {
            if (e.target.tagName === 'INPUT' && !e.target.classList.contains('csv-row-select')) {
                e.target.classList.add('bg-yellow-50', 'border-yellow-300');
                e.target.classList.remove('border-red-500', 'bg-red-50', 'border-gray-200');
                
                // Also check the checkbox automatically if user edits
                const rowNum = e.target.getAttribute('data-row');
                const cb = document.querySelector(`.csv-row-select[value="${rowNum}"]`);
                if(cb && !cb.checked) {
                    cb.checked = true;
                    // Trigger change manually to update counts
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
        
        document.getElementById('csv-preview-body').addEventListener('change', (e) => {
            const rowNum = e.target.getAttribute('data-row');
            if(!rowNum) return;
            const row = document.getElementById(`csv-row-${rowNum}`);
            if (row) {
                row.classList.remove('bg-red-50');
                row.classList.add('bg-white');
                const statusCell = document.getElementById(`csv-status-${rowNum}`);
                if (statusCell && statusCell.innerText.includes('Invalid category')) {
                    statusCell.innerHTML = '<span class="text-yellow-600 text-xs font-semibold">Edited</span>';
                }
            }

            if (e.target.classList.contains('csv-select-cat')) {
                const inputCat = row.querySelector('.csv-input-cat');
                
                e.target.classList.add('bg-yellow-50', 'border-yellow-300');
                e.target.classList.remove('border-red-500', 'bg-red-50', 'border-gray-200');
                
                if (e.target.value === '__custom__') {
                    e.target.classList.add('hidden');
                    inputCat.classList.remove('hidden');
                    inputCat.value = '';
                    inputCat.focus();
                } else {
                    inputCat.classList.add('hidden');
                    inputCat.value = e.target.value;
                }
                
                const cb = document.querySelector(`.csv-row-select[value="${rowNum}"]`);
                if(cb && !cb.checked) {
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });

        // Revert to dropdown if input is cleared
        document.getElementById('csv-preview-body').addEventListener('focusout', (e) => {
            if (e.target.classList.contains('csv-input-cat') && e.target.value.trim() === '') {
                const rowNum = e.target.getAttribute('data-row');
                const row = document.getElementById(`csv-row-${rowNum}`);
                const selectCat = row.querySelector('.csv-select-cat');
                e.target.classList.add('hidden');
                selectCat.classList.remove('hidden');
                selectCat.value = '';
                
                // Keep the yellow edit styling on the select
                selectCat.classList.add('bg-yellow-50', 'border-yellow-300');
                selectCat.classList.remove('border-red-500', 'bg-red-50', 'border-gray-200');
            }
        });

        document.getElementById('csv-confirm-btn').addEventListener('click', async () => {
            if (!uploadedFile) return;
            
            // Gather selected rows and their input values
            const selectedCheckboxes = document.querySelectorAll('.csv-row-select:checked');
            if (selectedCheckboxes.length === 0) return;
            
            const records = Array.from(selectedCheckboxes).map(cb => {
                const rowNum = cb.value;
                const row = document.getElementById(`csv-row-${rowNum}`);
                const selectCat = row.querySelector('.csv-select-cat');
                const inputCat = row.querySelector('.csv-input-cat');
                
                let finalCategory = selectCat.value;
                if (finalCategory === '__custom__' || selectCat.classList.contains('hidden')) {
                    finalCategory = inputCat.value;
                }
                
                return {
                    row_number: parseInt(rowNum, 10),
                    date: row.querySelector('.csv-input-date').value,
                    category: finalCategory,
                    amount: row.querySelector('.csv-input-amt').value,
                    description: row.querySelector('.csv-input-desc').value
                };
            });
            
            const btn = document.getElementById('csv-confirm-btn');
            btn.disabled = true;
            btn.innerHTML = 'Importing...';
            const errDiv = document.getElementById('csv-error');
            errDiv.classList.add('hidden');
            
            try {
                const res = await fetch('/app/api/transactions/confirm-csv', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': getCookie('csrf_access_token')
                    },
                    body: JSON.stringify({ records })
                });
                const data = await res.json();
                
                if (res.ok) {
                    resetCsvModal();
                    closeModal('csv');
                    loadExpenses();
                    showSuccess("Import Successful", data.message || "Your expenses have been successfully imported.");
                } else {
                    if (data.details) {
                        errDiv.textContent = "Please fix the highlighted errors before importing.";
                        // Highlight errors
                        data.details.forEach(errObj => {
                            const rowNum = errObj.row;
                            const statusCell = document.getElementById(`csv-status-${rowNum}`);
                            const row = document.getElementById(`csv-row-${rowNum}`);
                            if(statusCell) statusCell.innerHTML = `<span class="text-fz-red text-xs font-semibold">${errObj.errors.join(', ')}</span>`;
                            if(row) {
                                row.classList.add('bg-red-50');
                                row.classList.remove('bg-white');
                                
                                errObj.errors.forEach(e => {
                                    const lower = e.toLowerCase();
                                    if(lower.includes('date')) row.querySelector('.csv-input-date').classList.add('border-red-500', 'bg-red-50');
                                    if(lower.includes('amount')) row.querySelector('.csv-input-amt').classList.add('border-red-500', 'bg-red-50');
                                    if(lower.includes('category')) row.querySelector('.csv-input-cat').classList.add('border-red-500', 'bg-red-50');
                                });
                            }
                        });
                    } else {
                        errDiv.textContent = data.error || "Failed to import CSV";
                    }
                    errDiv.classList.remove('hidden');
                    btn.disabled = false;
                    btn.innerHTML = 'Try Again';
                }
            } catch (err) {
                console.error(err);
                errDiv.textContent = "Network error during import.";
                errDiv.classList.remove('hidden');
                btn.disabled = false;
                btn.innerHTML = 'Try Again';
            }
        });
    });

    function resetCsvModal() {
        document.getElementById('csv-upload-form').reset();
        document.getElementById('csv-file-name').classList.add('hidden');
        document.getElementById('csv-preview-btn').classList.add('hidden');
        document.getElementById('csv-upload-step').classList.remove('hidden');
        document.getElementById('csv-preview-step').classList.add('hidden');
        document.getElementById('csv-preview-step').classList.remove('flex');
        document.getElementById('csv-error').classList.add('hidden');
        let uploadedFile = null;
    }

    // Store globally for editing
    let allFixedIncomes = [];
    let allVariableIncomes = [];

    async function loadIncome() {
        try {
            const res = await fetch('/app/api/transactions/income');
            const tbody = document.getElementById('income-table-body');
            const fixedBody = document.getElementById('fixed-history-body');
            
            if (res.ok) {
                const data = await res.json();
                
                // Update Current Fixed Income Section
                if (data.current_fixed_income) {
                    document.getElementById('fi-amount').textContent = '₹' + data.current_fixed_income.amount.toLocaleString();
                    if (data.current_fixed_income.is_multiple) {
                        document.getElementById('fi-date').textContent = 'Multiple Sources';
                    } else {
                        document.getElementById('fi-date').textContent = new Date(data.current_fixed_income.single_date).toLocaleDateString();
                    }
                } else {
                    document.getElementById('fi-amount').textContent = '₹0';
                    document.getElementById('fi-date').textContent = 'Not Set';
                }

                // Update Fixed Income Select List
                allFixedIncomes = data.fixed_incomes;
                fixedBody.innerHTML = '';
                if (data.fixed_incomes.length === 0) {
                    fixedBody.innerHTML = '<tr><td colspan="4" class="px-4 py-6 text-center text-sm text-fz-gray-500">No fixed incomes recorded yet.</td></tr>';
                } else {
                    data.fixed_incomes.forEach((inc, index) => {
                        const tr = buildRow([
                            { text: new Date(inc.date).toLocaleDateString(), className: "px-4 py-4" },
                            { text: inc.description || '-', className: "px-4 py-4" },
                            { text: '₹' + inc.amount.toLocaleString(), className: "px-4 py-4 text-right font-medium text-fz-black" },
                            { html: `
                                    <div class="flex items-center justify-center gap-3">
                                        <button onclick="editFixedIncome(${index})" class="text-sm font-semibold text-fz-black hover:underline">Edit</button>
                                        <div class="w-px h-3.5 bg-fz-gray-300"></div>
                                        <button onclick="promptDeleteIncome(${inc.id}, 'fixed')" class="text-sm font-semibold text-fz-red hover:underline">Delete</button>
                                    </div>
                                `, className: "px-4 py-4 text-center" }
                        ], "hover:bg-fz-gray-50 transition-colors");
                        fixedBody.appendChild(tr);
                    });
                }

                // Update Variable Income Table
                allVariableIncomes = data.variable_incomes;
                tbody.innerHTML = '';
                if (data.variable_incomes.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-8 text-center">No variable income recorded yet.</td></tr>';
                    return;
                }
                
                data.variable_incomes.forEach((inc, index) => {
                    const tr = buildRow([
                        { text: new Date(inc.date).toLocaleDateString(), className: "px-6 py-4" },
                        { text: inc.description || '-', className: "px-6 py-4" },
                        { text: '₹' + inc.amount.toLocaleString(), className: "px-6 py-4 text-right font-medium text-green-600" },
                        { html: `
                                <div class="flex items-center justify-center gap-3">
                                    <button onclick="editVariableIncome(${index})" class="text-sm font-semibold text-fz-black hover:underline">Edit</button>
                                    <div class="w-px h-3.5 bg-fz-gray-300"></div>
                                    <button onclick="promptDeleteIncome(${inc.id}, 'variable')" class="text-sm font-semibold text-fz-red hover:underline">Delete</button>
                                </div>
                            `, className: "px-6 py-4 text-center" }
                    ], "hover:bg-fz-gray-50 transition-colors");
                    tbody.appendChild(tr);
                });
            }
        } catch (err) {
            console.error(err);
        }
    }

    function editFixedIncome(index) {
        const inc = allFixedIncomes[index];
        document.getElementById('edit-fix-id').value = inc.id;
        
        // Convert ISO date to YYYY-MM-DD for input[type="date" max="{{ today_date }}"]
        const dt = new Date(inc.date);
        const yyyy = dt.getFullYear();
        const mm = String(dt.getMonth() + 1).padStart(2, '0');
        const dd = String(dt.getDate()).padStart(2, '0');
        document.getElementById('edit-fix-date').value = `${yyyy}-${mm}-${dd}`;
        
        document.getElementById('edit-fix-amount').value = inc.amount;
        document.getElementById('edit-fix-desc').value = inc.description || '';
        
        closeModal('update-fixed-select');
        openModal('update-fixed-form');
    }

    function editVariableIncome(index) {
        const inc = allVariableIncomes[index];
        document.getElementById('edit-var-id').value = inc.id;
        
        const dt = new Date(inc.date);
        const yyyy = dt.getFullYear();
        const mm = String(dt.getMonth() + 1).padStart(2, '0');
        const dd = String(dt.getDate()).padStart(2, '0');
        document.getElementById('edit-var-date').value = `${yyyy}-${mm}-${dd}`;
        
        document.getElementById('edit-var-amount').value = inc.amount;
        document.getElementById('edit-var-desc').value = inc.description || '';
        
        openModal('update-variable-form');
    }

    function promptDeleteIncome(id, type) {
        document.getElementById('delete-income-id').value = id;
        const titleEl = document.getElementById('delete-income-title');
        const descEl = document.getElementById('delete-income-desc');
        
        if (type === 'fixed') {
            titleEl.textContent = 'Delete Fixed Income?';
            descEl.textContent = 'Are you sure you want to delete this fixed income version? This may affect calculations for the periods covered by this version.';
        } else {
            titleEl.textContent = 'Delete Variable Income?';
            descEl.textContent = 'Are you sure you want to delete this income record? This action cannot be undone.';
        }
        
        if (type === 'fixed') {
            closeModal('update-fixed-select');
        }
        
        document.getElementById('delete-income-error').classList.add('hidden');
        openModal('delete-income');
    }

    async function confirmDeleteIncome() {
        const id = document.getElementById('delete-income-id').value;
        const btn = document.getElementById('delete-income-btn');
        const errDiv = document.getElementById('delete-income-error');
        
        btn.disabled = true;
        btn.innerHTML = 'Deleting...';
        errDiv.classList.add('hidden');
        
        try {
            const res = await fetch(`/app/api/transactions/income/${id}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRF-TOKEN': getCookie('csrf_access_token')
                }
            });
            const data = await res.json();
            
            if (res.ok) {
                closeModal('delete-income');
                loadIncome();
            } else {
                errDiv.textContent = data.error || data.msg || "Failed to delete income";
                errDiv.classList.remove('hidden');
            }
        } catch (err) {
            console.error(err);
            errDiv.textContent = "Network error. Please try again.";
            errDiv.classList.remove('hidden');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Delete Income';
        }
    }

    // Submit listener for Update Variable Income Form
    document.addEventListener("DOMContentLoaded", () => {
        const updateVarForm = document.getElementById('update-variable-form');
        if (updateVarForm) {
            updateVarForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const errDiv = document.getElementById('update-variable-error');
                errDiv.classList.add('hidden');
                const submitBtn = e.target.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Saving...';
                
                const id = document.getElementById('edit-var-id').value;
                const payload = {
                    date: document.getElementById('edit-var-date').value,
                    amount: document.getElementById('edit-var-amount').value,
                    description: document.getElementById('edit-var-desc').value,
                    income_type: 'Variable' // Ensures backend knows if it cares, though endpoint handles both
                };
                
                try {
                    const res = await fetch(`/app/api/transactions/income/${id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-TOKEN': getCookie('csrf_access_token')
                        },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (res.ok) {
                        e.target.reset();
                        closeModal('update-variable-form');
                        loadIncome();
                    } else {
                        errDiv.textContent = data.error || data.msg || data.message || "Failed to update variable income";
                        errDiv.classList.remove('hidden');
                    }
                } catch (err) {
                    console.error(err);
                    errDiv.textContent = "Network error. Please try again.";
                    errDiv.classList.remove('hidden');
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Save Changes';
                }
            });
        }
    });

    let currentPage = 1;
    
    async function loadExpenses(page = 1) {
        try {
            currentPage = page;
            const res = await fetch(`/app/api/transactions/expense?page=${page}&per_page=5`);
            const tbody = document.getElementById('expense-table-body');
            const paginationControls = document.getElementById('pagination-controls');
            
            if (res.ok) {
                const responseData = await res.json();
                const data = responseData.transactions;
                const totalPages = responseData.total_pages;
                const totalItems = responseData.total_items;
                
                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-8 text-center">No expenses recorded yet.</td></tr>';
                    if(paginationControls) paginationControls.classList.add('hidden');
                    return;
                }
                
                data.forEach(ex => {
                    const tr = buildRow([
                        { text: new Date(ex.date).toLocaleDateString(), className: "px-6 py-4" },
                        { text: ex.category, className: "px-6 py-4" },
                        { text: ex.description || '-', className: "px-6 py-4" },
                        { text: '₹' + ex.amount.toLocaleString(), className: "px-6 py-4 text-right font-medium text-fz-black" }
                    ], "hover:bg-fz-gray-50 transition-colors");
                    tbody.appendChild(tr);
                });
                
                // Update Pagination UI
                if(paginationControls) {
                    paginationControls.classList.remove('hidden');
                    document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages} (${totalItems} items)`;
                    document.getElementById('prev-page-btn').disabled = currentPage <= 1;
                    document.getElementById('next-page-btn').disabled = currentPage >= totalPages;
                }
            }
        } catch (err) {
            console.error(err);
        }
    }
    
    function prevPage() {
        if(currentPage > 1) loadExpenses(currentPage - 1);
    }
    
    function nextPage() {
        loadExpenses(currentPage + 1);
    }

    function openModal(id) {
        document.getElementById(id + '-modal').classList.remove('hidden');
        document.getElementById(id + '-modal').classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
    
    function closeModal(id) {
        document.getElementById(id + '-modal').classList.add('hidden');
        document.getElementById(id + '-modal').classList.remove('flex');
        document.body.style.overflow = '';
        if (id === 'add-fixed') document.getElementById('add-fixed-form').reset();
        if (id === 'update-fixed-form') document.getElementById('update-fixed-form').reset();
        if (id === 'update-variable-form') document.getElementById('update-variable-form').reset();
        if (id === 'variable') document.getElementById('variable-form').reset();
        if (id === 'expense') document.getElementById('expense-form').reset();
        if (id === 'csv') resetCsvModal();
    }

    function showSuccess(title, message) {
        document.getElementById('success-modal-title').textContent = title;
        document.getElementById('success-modal-msg').textContent = message;
        openModal('success');
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
