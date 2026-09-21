import re

filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\expenses.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Pagination Controls HTML
table_html = """                <tbody id="expense-table-body" class="divide-y divide-fz-gray-100">
                    <tr><td colspan="5" class="px-6 py-8 text-center">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>"""

table_html_new = """                <tbody id="expense-table-body" class="divide-y divide-fz-gray-100">
                    <tr><td colspan="5" class="px-6 py-8 text-center">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        <!-- Pagination Controls -->
        <div id="pagination-controls" class="px-6 py-4 flex items-center justify-between border-t border-fz-gray-100 hidden">
            <button id="prev-page-btn" onclick="prevPage()" class="px-4 py-2 text-sm font-medium text-fz-gray-700 bg-white border border-fz-gray-300 rounded-md hover:bg-fz-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Previous</button>
            <span id="page-info" class="text-sm text-fz-gray-600 font-medium">Page 1</span>
            <button id="next-page-btn" onclick="nextPage()" class="px-4 py-2 text-sm font-medium text-fz-gray-700 bg-white border border-fz-gray-300 rounded-md hover:bg-fz-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Next</button>
        </div>
    </div>
</div>"""

if "pagination-controls" not in content:
    content = content.replace(table_html, table_html_new)

# 2. Add buildRow helper and variables
script_start = """<script>
    let allExpenses = [];"""
script_start_new = """<script>
    let allExpenses = [];
    let currentPage = 1;

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
    }"""
if "let currentPage = 1;" not in content:
    content = content.replace(script_start, script_start_new)

# 3. Modify buildQueryString and add pagination functions
build_query_orig = """    function buildQueryString(excludeFilters = false) {
        if (excludeFilters) return '';
        const start = document.getElementById('filter-start').value;
        const end = document.getElementById('filter-end').value;
        const cat = document.getElementById('filter-category').value;
        
        const params = new URLSearchParams();
        if (start) params.append('start_date', start);
        if (end) params.append('end_date', end);
        if (cat) params.append('category', cat);
        return params.toString() ? '?' + params.toString() : '';
    }"""
build_query_new = """    function buildQueryString(excludeFilters = false, page = 1) {
        const params = new URLSearchParams();
        if (!excludeFilters) {
            const start = document.getElementById('filter-start').value;
            const end = document.getElementById('filter-end').value;
            const cat = document.getElementById('filter-category').value;
            
            if (start) params.append('start_date', start);
            if (end) params.append('end_date', end);
            if (cat) params.append('category', cat);
        }
        params.append('page', page);
        params.append('per_page', 20);
        return '?' + params.toString();
    }
    
    function prevPage() {
        if (currentPage > 1) {
            loadExpenses(currentPage - 1);
        }
    }
    
    function nextPage() {
        loadExpenses(currentPage + 1);
    }"""
if "function prevPage" not in content:
    content = content.replace(build_query_orig, build_query_new)

# 4. Modify loadExpenses
load_exp_orig = """    async function loadExpenses() {
        const query = buildQueryString();
        const statusDiv = document.getElementById('filter-status');
        
        if (query) {
            statusDiv.textContent = 'Loading filters...';
            statusDiv.classList.remove('hidden');
        } else {
            statusDiv.classList.add('hidden');
        }

        try {
            const res = await fetch(`/app/api/transactions/expense${query}`);
            const tbody = document.getElementById('expense-table-body');
            
            if (res.ok) {
                const responseData = await res.json();
                const data = responseData.data;
                const totalCount = responseData.total_count;
                allExpenses = data;

                if (query) {
                    if (totalCount === 0) {
                        statusDiv.textContent = "No expenses match your selected filters.";
                    } else {
                        statusDiv.textContent = `${totalCount} expense${totalCount === 1 ? '' : 's'} found.`;
                    }
                    statusDiv.classList.remove('hidden');
                }

                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-8 text-center text-fz-gray-500">No expenses found.</td></tr>';
                    return;
                }
                
                data.forEach((ex, index) => {
                    tbody.innerHTML += `
                        <tr class="hover:bg-fz-gray-50 transition-colors">
                            <td class="px-6 py-4">${new Date(ex.date).toLocaleDateString()}</td>
                            <td class="px-6 py-4">${ex.category}</td>
                            <td class="px-6 py-4">${ex.description || '-'}</td>
                            <td class="px-6 py-4 text-right font-medium text-fz-black">₹${ex.amount.toLocaleString()}</td>
                            <td class="px-6 py-4 text-center">
                                <div class="flex items-center justify-center gap-3">
                                    <button onclick="editExpense(${index})" class="text-sm font-semibold text-fz-black hover:underline">Edit</button>
                                    <div class="w-px h-3.5 bg-fz-gray-300"></div>
                                    <button onclick="promptDeleteExpense(${ex.id})" class="text-sm font-semibold text-fz-red hover:underline">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
            }
        } catch (err) {
            console.error(err);
        }
    }"""
load_exp_new = """    async function loadExpenses(page = 1) {
        currentPage = page;
        const query = buildQueryString(false, page);
        const statusDiv = document.getElementById('filter-status');
        const paginationControls = document.getElementById('pagination-controls');
        
        statusDiv.textContent = 'Loading...';
        statusDiv.classList.remove('hidden');

        try {
            const res = await fetch(`/app/api/transactions/expense${query}`);
            const tbody = document.getElementById('expense-table-body');
            
            if (res.ok) {
                const responseData = await res.json();
                const data = responseData.transactions;
                const totalPages = responseData.total_pages;
                const totalItems = responseData.total_items;
                allExpenses = data;

                if (totalItems === 0) {
                    statusDiv.textContent = "No expenses found.";
                } else {
                    statusDiv.textContent = `${totalItems} expense${totalItems === 1 ? '' : 's'} found.`;
                }

                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-8 text-center text-fz-gray-500">No expenses found.</td></tr>';
                    paginationControls.classList.add('hidden');
                    return;
                }
                
                data.forEach((ex, index) => {
                    const tr = buildRow([
                        { text: new Date(ex.date).toLocaleDateString(), className: "px-6 py-4" },
                        { text: ex.category, className: "px-6 py-4" },
                        { text: ex.description || '-', className: "px-6 py-4" },
                        { text: '₹' + ex.amount.toLocaleString(), className: "px-6 py-4 text-right font-medium text-fz-black" },
                        { html: `
                                <div class="flex items-center justify-center gap-3">
                                    <button onclick="editExpense(${index})" class="text-sm font-semibold text-fz-black hover:underline">Edit</button>
                                    <div class="w-px h-3.5 bg-fz-gray-300"></div>
                                    <button onclick="promptDeleteExpense(${ex.id})" class="text-sm font-semibold text-fz-red hover:underline">Delete</button>
                                </div>
                            `, className: "px-6 py-4 text-center" }
                    ], "hover:bg-fz-gray-50 transition-colors");
                    tbody.appendChild(tr);
                });
                
                // Update Pagination UI
                paginationControls.classList.remove('hidden');
                document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages || 1}`;
                document.getElementById('prev-page-btn').disabled = currentPage <= 1;
                document.getElementById('next-page-btn').disabled = currentPage >= totalPages;
            }
        } catch (err) {
            console.error(err);
        }
    }"""
content = content.replace(load_exp_orig, load_exp_new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("expenses.html frontend fixes applied.")
