import re

filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\transactions.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update modal wrapper to have overflow-y-auto so it scrolls on small screens
# The modal wrapper is `<div class="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl p-6 mx-4 max-h-[90vh] flex flex-col transform transition-all">`
wrapper_old = 'class="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl p-6 mx-4 max-h-[90vh] flex flex-col transform transition-all"'
wrapper_new = 'class="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl p-6 mx-4 max-h-[90vh] flex flex-col transform transition-all overflow-y-auto"'
if wrapper_old in content:
    content = content.replace(wrapper_old, wrapper_new)

# 2. Update table headers to include checkbox
thead_old = """                    <thead class="bg-fz-gray-50 text-xs uppercase text-fz-gray-500 font-medium sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th class="px-4 py-3 whitespace-nowrap">Row</th>
                            <th class="px-4 py-3 whitespace-nowrap">Date</th>
                            <th class="px-4 py-3 whitespace-nowrap">Category</th>
                            <th class="px-4 py-3 text-right whitespace-nowrap">Amount</th>
                            <th class="px-4 py-3">Status</th>
                        </tr>
                    </thead>"""
thead_new = """                    <thead class="bg-fz-gray-50 text-xs uppercase text-fz-gray-500 font-medium sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th class="px-4 py-3 whitespace-nowrap w-12 text-center">
                                <input type="checkbox" id="csv-select-all" class="w-4 h-4 rounded border-gray-300 text-fz-black focus:ring-fz-red cursor-pointer">
                            </th>
                            <th class="px-4 py-3 whitespace-nowrap">Row</th>
                            <th class="px-4 py-3 whitespace-nowrap">Date</th>
                            <th class="px-4 py-3 whitespace-nowrap">Category</th>
                            <th class="px-4 py-3 text-right whitespace-nowrap">Amount</th>
                            <th class="px-4 py-3">Status</th>
                        </tr>
                    </thead>"""
if thead_old in content:
    content = content.replace(thead_old, thead_new)

# 3. Update the JS rendering for valid and invalid rows
js_render_old = """                    // Render valid rows
                    data.valid_records.forEach(r => {
                        const tr = buildRow([
                            { text: r.row_number, className: "px-4 py-2" },
                            { text: r.date, className: "px-4 py-2" },
                            { text: r.category, className: "px-4 py-2" },
                            { text: '₹' + r.amount, className: "px-4 py-2 text-right" },
                            { html: '<span class="text-green-600 text-xs font-semibold">Valid</span>', className: "px-4 py-2" }
                        ], "bg-white");
                        tbody.appendChild(tr);
                    });
                    
                    // Render invalid rows
                    data.invalid_records.forEach(r => {
                        const tr = buildRow([
                            { text: r.row_number, className: "px-4 py-2" },
                            { text: r.date || '-', className: "px-4 py-2" },
                            { text: r.category || '-', className: "px-4 py-2" },
                            { text: r.amount ? '₹'+r.amount : '-', className: "px-4 py-2 text-right" },
                            { html: `<span class="text-fz-red text-xs font-semibold">${r.errors.map(e => e.replace(/</g, '&lt;').replace(/>/g, '&gt;')).join(', ')}</span>`, className: "px-4 py-2" }
                        ], "bg-red-50");
                        tbody.appendChild(tr);
                    });
                    
                    const confirmBtn = document.getElementById('csv-confirm-btn');
                    if (data.valid_count === 0) {
                        confirmBtn.disabled = true;
                        confirmBtn.innerHTML = 'No Valid Records';
                    } else {
                        confirmBtn.disabled = false;
                        confirmBtn.innerHTML = `Confirm Import (${data.valid_count})`;
                    }"""

js_render_new = """                    // Render valid rows
                    data.valid_records.forEach(r => {
                        const tr = buildRow([
                            { html: `<input type="checkbox" class="csv-row-select w-4 h-4 rounded border-gray-300 text-fz-black focus:ring-fz-red cursor-pointer" value="${r.row_number}" checked>`, className: "px-4 py-2 text-center" },
                            { text: r.row_number, className: "px-4 py-2" },
                            { text: r.date, className: "px-4 py-2" },
                            { text: r.category, className: "px-4 py-2" },
                            { text: '₹' + r.amount, className: "px-4 py-2 text-right" },
                            { html: '<span class="text-green-600 text-xs font-semibold">Valid</span>', className: "px-4 py-2" }
                        ], "bg-white hover:bg-gray-50 transition-colors");
                        tbody.appendChild(tr);
                    });
                    
                    // Render invalid rows
                    data.invalid_records.forEach(r => {
                        const tr = buildRow([
                            { html: `<input type="checkbox" disabled class="w-4 h-4 rounded border-gray-200 text-gray-300 cursor-not-allowed">`, className: "px-4 py-2 text-center" },
                            { text: r.row_number, className: "px-4 py-2 text-gray-400" },
                            { text: r.date || '-', className: "px-4 py-2 text-gray-400" },
                            { text: r.category || '-', className: "px-4 py-2 text-gray-400" },
                            { text: r.amount ? '₹'+r.amount : '-', className: "px-4 py-2 text-right text-gray-400" },
                            { html: `<span class="text-fz-red text-xs font-semibold">${r.errors.map(e => e.replace(/</g, '&lt;').replace(/>/g, '&gt;')).join(', ')}</span>`, className: "px-4 py-2" }
                        ], "bg-red-50");
                        tbody.appendChild(tr);
                    });
                    
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
                    });"""

if "data.valid_records.forEach(r => {" in content and "updateSelectedCount" not in content:
    content = content.replace(js_render_old, js_render_new)


# 4. Update the confirm submit logic to gather checkboxes
js_submit_old = """        document.getElementById('csv-confirm-btn').addEventListener('click', async () => {
            if (!uploadedFile) return;
            const btn = document.getElementById('csv-confirm-btn');
            btn.disabled = true;
            btn.innerHTML = 'Importing...';
            const errDiv = document.getElementById('csv-error');
            errDiv.classList.add('hidden');
            
            // To ensure strict security, we send the file again for server-side revalidation
            const formData = new FormData();
            formData.append('file', uploadedFile);"""

js_submit_new = """        document.getElementById('csv-confirm-btn').addEventListener('click', async () => {
            if (!uploadedFile) return;
            
            // Gather selected rows
            const selectedCheckboxes = document.querySelectorAll('.csv-row-select:checked');
            if (selectedCheckboxes.length === 0) return;
            const selectedRows = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value, 10));
            
            const btn = document.getElementById('csv-confirm-btn');
            btn.disabled = true;
            btn.innerHTML = 'Importing...';
            const errDiv = document.getElementById('csv-error');
            errDiv.classList.add('hidden');
            
            // To ensure strict security, we send the file again for server-side revalidation
            const formData = new FormData();
            formData.append('file', uploadedFile);
            formData.append('selected_rows', JSON.stringify(selectedRows));"""

if "Array.from(selectedCheckboxes)" not in content:
    content = content.replace(js_submit_old, js_submit_new)


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated transactions.html with CSV Selection feature.")
