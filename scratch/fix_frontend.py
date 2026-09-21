import re

filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\transactions.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Update loadExpenses to handle new pagination and variable changes
load_exp_orig = """    async function loadExpenses() {
        try {
            const res = await fetch('/app/api/transactions/expense?limit=5');
            const tbody = document.getElementById('expense-table-body');
            const viewAllBtn = document.getElementById('view-all-expenses-btn');
            
            if (res.ok) {
                const responseData = await res.json();
                const data = responseData.data;
                const totalCount = responseData.total_count;
                
                if (totalCount > 5) {
                    viewAllBtn.classList.remove('hidden');
                } else {
                    viewAllBtn.classList.add('hidden');
                }

                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-8 text-center">No expenses recorded yet.</td></tr>';
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
            }
        } catch (err) {
            console.error(err);
        }
    }"""

load_exp_new = """    let currentPage = 1;
    
    async function loadExpenses(page = 1) {
        try {
            currentPage = page;
            const res = await fetch(`/app/api/transactions/expense?page=${page}&per_page=20`);
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
    }"""

if "let currentPage = 1;" not in content:
    content = content.replace(load_exp_orig, load_exp_new)

# Add pagination controls below the expense table
table_end = """                    <tbody id="expense-table-body" class="divide-y divide-fz-gray-100">
                        <!-- Rows injected via JS -->
                    </tbody>
                </table>
            </div>
            
            <div class="mt-4 flex justify-center">
                <button id="view-all-expenses-btn" class="hidden text-sm font-semibold text-fz-blue hover:underline">View All Expenses</button>
            </div>
        </div>"""

table_end_new = """                    <tbody id="expense-table-body" class="divide-y divide-fz-gray-100">
                        <!-- Rows injected via JS -->
                    </tbody>
                </table>
            </div>
            
            <div id="pagination-controls" class="mt-4 flex items-center justify-between hidden">
                <button id="prev-page-btn" onclick="prevPage()" class="px-4 py-2 text-sm font-medium text-fz-gray-700 bg-white border border-fz-gray-300 rounded-md hover:bg-fz-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Previous</button>
                <span id="page-info" class="text-sm text-fz-gray-600 font-medium">Page 1</span>
                <button id="next-page-btn" onclick="nextPage()" class="px-4 py-2 text-sm font-medium text-fz-gray-700 bg-white border border-fz-gray-300 rounded-md hover:bg-fz-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Next</button>
            </div>
        </div>"""

if "pagination-controls" not in content:
    content = content.replace(table_end, table_end_new)
    
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Frontend pagination fixes applied.")
