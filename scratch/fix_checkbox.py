import re

filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\templates\app\transactions.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Move the select-all th to the end
thead_old = """                    <thead class="bg-fz-gray-50 text-xs uppercase text-fz-gray-500 font-medium sticky top-0 z-10 shadow-sm">
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

thead_new = """                    <thead class="bg-fz-gray-50 text-xs uppercase text-fz-gray-500 font-medium sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th class="px-4 py-3 whitespace-nowrap">Row</th>
                            <th class="px-4 py-3 whitespace-nowrap">Date</th>
                            <th class="px-4 py-3 whitespace-nowrap">Category</th>
                            <th class="px-4 py-3 text-right whitespace-nowrap">Amount</th>
                            <th class="px-4 py-3">Status</th>
                            <th class="px-4 py-3 whitespace-nowrap w-12 text-center">
                                <input type="checkbox" id="csv-select-all" class="w-4 h-4 rounded border-gray-300 text-fz-red accent-red-600 focus:ring-fz-red cursor-pointer">
                            </th>
                        </tr>
                    </thead>"""

content = content.replace(thead_old, thead_new)

# 2. Update JS render valid rows
js_render_valid_old = """                    // Render valid rows
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
                    });"""

js_render_valid_new = """                    // Render valid rows
                    data.valid_records.forEach(r => {
                        const tr = buildRow([
                            { text: r.row_number, className: "px-4 py-2" },
                            { text: r.date, className: "px-4 py-2" },
                            { text: r.category, className: "px-4 py-2" },
                            { text: '₹' + r.amount, className: "px-4 py-2 text-right" },
                            { html: '<span class="text-green-600 text-xs font-semibold">Valid</span>', className: "px-4 py-2" },
                            { html: `<input type="checkbox" class="csv-row-select w-4 h-4 rounded border-gray-300 text-fz-red accent-red-600 focus:ring-fz-red cursor-pointer" value="${r.row_number}" checked>`, className: "px-4 py-2 text-center" }
                        ], "bg-white hover:bg-gray-50 transition-colors");
                        tbody.appendChild(tr);
                    });"""

content = content.replace(js_render_valid_old, js_render_valid_new)

# 3. Update JS render invalid rows
js_render_invalid_old = """                    // Render invalid rows
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
                    });"""

js_render_invalid_new = """                    // Render invalid rows
                    data.invalid_records.forEach(r => {
                        const tr = buildRow([
                            { text: r.row_number, className: "px-4 py-2 text-gray-400" },
                            { text: r.date || '-', className: "px-4 py-2 text-gray-400" },
                            { text: r.category || '-', className: "px-4 py-2 text-gray-400" },
                            { text: r.amount ? '₹'+r.amount : '-', className: "px-4 py-2 text-right text-gray-400" },
                            { html: `<span class="text-fz-red text-xs font-semibold">${r.errors.map(e => e.replace(/</g, '&lt;').replace(/>/g, '&gt;')).join(', ')}</span>`, className: "px-4 py-2" },
                            { html: `<input type="checkbox" disabled class="w-4 h-4 rounded border-gray-200 text-gray-300 cursor-not-allowed">`, className: "px-4 py-2 text-center" }
                        ], "bg-red-50");
                        tbody.appendChild(tr);
                    });"""

content = content.replace(js_render_invalid_old, js_render_invalid_new)


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated checkbox position and color.")
