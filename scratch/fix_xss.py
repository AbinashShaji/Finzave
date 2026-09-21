import re

file_path = r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\transactions.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the helper function to insert
helper_func = """
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
"""

# Insert the helper function right after <script>
if "function buildRow" not in content:
    content = content.replace("<script>", "<script>\n" + helper_func)

# Fix csv-preview valid rows
csv_valid_orig = """                    data.valid_records.forEach(r => {
                        tbody.innerHTML += `
                            <tr class="bg-white">
                                <td class="px-4 py-2">${r.row_number}</td>
                                <td class="px-4 py-2">${r.date}</td>
                                <td class="px-4 py-2">${r.category}</td>
                                <td class="px-4 py-2 text-right">₹${r.amount}</td>
                                <td class="px-4 py-2"><span class="text-green-600 text-xs font-semibold">Valid</span></td>
                            </tr>
                        `;
                    });"""

csv_valid_new = """                    data.valid_records.forEach(r => {
                        const tr = buildRow([
                            { text: r.row_number, className: "px-4 py-2" },
                            { text: r.date, className: "px-4 py-2" },
                            { text: r.category, className: "px-4 py-2" },
                            { text: '₹' + r.amount, className: "px-4 py-2 text-right" },
                            { html: '<span class="text-green-600 text-xs font-semibold">Valid</span>', className: "px-4 py-2" }
                        ], "bg-white");
                        tbody.appendChild(tr);
                    });"""
content = content.replace(csv_valid_orig, csv_valid_new)

# Fix csv-preview invalid rows
csv_invalid_orig = """                    data.invalid_records.forEach(r => {
                        tbody.innerHTML += `
                            <tr class="bg-red-50">
                                <td class="px-4 py-2">${r.row_number}</td>
                                <td class="px-4 py-2">${r.date || '-'}</td>
                                <td class="px-4 py-2">${r.category || '-'}</td>
                                <td class="px-4 py-2 text-right">${r.amount ? '₹'+r.amount : '-'}</td>
                                <td class="px-4 py-2"><span class="text-fz-red text-xs font-semibold">${r.errors.join(', ')}</span></td>
                            </tr>
                        `;
                    });"""

csv_invalid_new = """                    data.invalid_records.forEach(r => {
                        const tr = buildRow([
                            { text: r.row_number, className: "px-4 py-2" },
                            { text: r.date || '-', className: "px-4 py-2" },
                            { text: r.category || '-', className: "px-4 py-2" },
                            { text: r.amount ? '₹'+r.amount : '-', className: "px-4 py-2 text-right" },
                            { html: `<span class="text-fz-red text-xs font-semibold">${r.errors.map(e => e.replace(/</g, '&lt;').replace(/>/g, '&gt;')).join(', ')}</span>`, className: "px-4 py-2" }
                        ], "bg-red-50");
                        tbody.appendChild(tr);
                    });"""
content = content.replace(csv_invalid_orig, csv_invalid_new)

# Fix fixed income rows
fixed_orig = """                    data.fixed_incomes.forEach((inc, index) => {
                        fixedBody.innerHTML += `
                            <tr class="hover:bg-fz-gray-50 transition-colors">
                                <td class="px-4 py-4">${new Date(inc.date).toLocaleDateString()}</td>
                                <td class="px-4 py-4">${inc.description || '-'}</td>
                                <td class="px-4 py-4 text-right font-medium text-fz-black">₹${inc.amount.toLocaleString()}</td>
                                <td class="px-4 py-4 text-center">
                                    <div class="flex items-center justify-center gap-3">
                                        <button onclick="editFixedIncome(${index})" class="text-sm font-semibold text-fz-black hover:underline">Edit</button>
                                        <div class="w-px h-3.5 bg-fz-gray-300"></div>
                                        <button onclick="promptDeleteIncome(${inc.id}, 'fixed')" class="text-sm font-semibold text-fz-red hover:underline">Delete</button>
                                    </div>
                                </td>
                            </tr>
                        `;
                    });"""

fixed_new = """                    data.fixed_incomes.forEach((inc, index) => {
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
                    });"""
content = content.replace(fixed_orig, fixed_new)

# Fix variable income rows
var_orig = """                data.variable_incomes.forEach((inc, index) => {
                    tbody.innerHTML += `
                        <tr class="hover:bg-fz-gray-50 transition-colors">
                            <td class="px-6 py-4">${new Date(inc.date).toLocaleDateString()}</td>
                            <td class="px-6 py-4">${inc.description || '-'}</td>
                            <td class="px-6 py-4 text-right font-medium text-green-600">₹${inc.amount.toLocaleString()}</td>
                            <td class="px-6 py-4 text-center">
                                <div class="flex items-center justify-center gap-3">
                                    <button onclick="editVariableIncome(${index})" class="text-sm font-semibold text-fz-black hover:underline">Edit</button>
                                    <div class="w-px h-3.5 bg-fz-gray-300"></div>
                                    <button onclick="promptDeleteIncome(${inc.id}, 'variable')" class="text-sm font-semibold text-fz-red hover:underline">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `;
                });"""

var_new = """                data.variable_incomes.forEach((inc, index) => {
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
                });"""
content = content.replace(var_orig, var_new)

# Fix expenses rows
exp_orig = """                data.forEach(ex => {
                    tbody.innerHTML += `
                        <tr class="hover:bg-fz-gray-50 transition-colors">
                            <td class="px-6 py-4">${new Date(ex.date).toLocaleDateString()}</td>
                            <td class="px-6 py-4">${ex.category}</td>
                            <td class="px-6 py-4">${ex.description || '-'}</td>
                            <td class="px-6 py-4 text-right font-medium text-fz-black">₹${ex.amount.toLocaleString()}</td>
                        </tr>
                    `;
                });"""

exp_new = """                data.forEach(ex => {
                    const tr = buildRow([
                        { text: new Date(ex.date).toLocaleDateString(), className: "px-6 py-4" },
                        { text: ex.category, className: "px-6 py-4" },
                        { text: ex.description || '-', className: "px-6 py-4" },
                        { text: '₹' + ex.amount.toLocaleString(), className: "px-6 py-4 text-right font-medium text-fz-black" }
                    ], "hover:bg-fz-gray-50 transition-colors");
                    tbody.appendChild(tr);
                });"""
content = content.replace(exp_orig, exp_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated transactions.html to remove innerHTML vulnerabilities.")
