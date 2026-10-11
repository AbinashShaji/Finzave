document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    fetchCapacity();
    calculateSIP();
    calculateEMI();

    // Toggle logic for loan type
    document.getElementById('emi-loan-type').addEventListener('change', (e) => {
        const val = e.target.value;
        const vehicleInputs = document.getElementById('emi-vehicle-inputs');
        const standardInputs = document.getElementById('emi-standard-inputs');
        if (val === 'Car' || val === 'Bike') {
            vehicleInputs.classList.remove('hidden');
            standardInputs.classList.add('hidden');
        } else {
            vehicleInputs.classList.add('hidden');
            standardInputs.classList.remove('hidden');
        }
        debouncedCalculateEMI();
    });

    const sipInputs = ['sip-monthly', 'sip-rate', 'sip-years'];
    sipInputs.forEach(id => {
        document.getElementById(id).addEventListener('input', debouncedCalculateSIP);
    });

    const emiInputs = ['emi-principal', 'emi-vehicle-price', 'emi-down-payment', 'emi-rate', 'emi-years'];
    emiInputs.forEach(id => {
        document.getElementById(id).addEventListener('input', debouncedCalculateEMI);
    });
});

let sipChartInstance = null;
let emiChartInstance = null;

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedCalculateSIP = debounce(calculateSIP, 300);
const debouncedCalculateEMI = debounce(calculateEMI, 300);

function getCookie(name) {
    let matches = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

function displayInsight(type, insight) {
    const container = document.getElementById(`${type}-insight-container`);
    if (!insight) {
        container.className = 'hidden';
        container.innerHTML = '';
        return;
    }

    let iconName = insight.status === 'WARNING' ? 'alert-triangle' : 'check-circle';
    let colors = '';
    let iconColors = '';
    
    if (insight.status === 'WARNING') {
        colors = 'bg-red-50 border-red-200 text-red-700';
        iconColors = 'text-red-600';
    } else {
        colors = 'bg-green-50 border-green-200 text-green-700';
        iconColors = 'text-green-600';
    }

    container.className = `mb-4 p-3 rounded-lg text-sm font-medium border ${colors}`;
    container.innerHTML = `
        <div class="flex items-start gap-2">
            <i data-lucide="${iconName}" class="w-5 h-5 mt-0.5 flex-shrink-0 ${iconColors}" aria-hidden="true"></i>
            <div>${insight.message}</div>
        </div>
    `;
    lucide.createIcons({ root: container });
}

async function fetchCapacity() {
    try {
        const csrfToken = getCookie('csrf_access_token');
        const res = await fetch('/app/api/planning/capacity', {
            method: 'GET',
            headers: { 'X-CSRF-TOKEN': csrfToken }
        });
        if (res.ok) {
            const data = await res.json();
            const savingsElem = document.getElementById('cap-savings');
            const suggestedElem = document.getElementById('cap-suggested');
            const contextElem = document.getElementById('cap-context');
            const noteElem = document.getElementById('cap-history-note');

            if (data.has_history) {
                const savingsVal = data.average_savings_capacity !== undefined ? data.average_savings_capacity : data.savings;
                if (savingsElem) savingsElem.textContent = `₹${Math.round(savingsVal).toLocaleString()}`;
                
                if (data.suggested_sip_min > 0 || data.suggested_sip_max > 0) {
                    if (suggestedElem) suggestedElem.textContent = `₹${Math.round(data.suggested_sip_min).toLocaleString()} - ₹${Math.round(data.suggested_sip_max).toLocaleString()}`;
                } else {
                    if (suggestedElem) suggestedElem.textContent = `₹0 - ₹0`;
                }
                
                if (contextElem) contextElem.textContent = data.context_message || `Based on ${data.active_months} months of financial history`;
                
                if (noteElem) {
                    if (data.active_months < 3) {
                        noteElem.textContent = "Limited financial history. Planning estimates may change as more data is recorded.";
                        noteElem.classList.remove('hidden');
                    } else {
                        noteElem.textContent = "";
                        noteElem.classList.add('hidden');
                    }
                }
            } else {
                if (savingsElem) savingsElem.textContent = "—";
                if (suggestedElem) suggestedElem.textContent = "No estimate available";
                if (contextElem) contextElem.textContent = "Not enough financial data to estimate planning capacity.";
                if (noteElem) {
                    noteElem.textContent = "Not enough financial data to estimate planning capacity.";
                    noteElem.classList.remove('hidden');
                }
            }
        }
    } catch (err) {
        console.error("Failed to fetch capacity", err);
    }
}

async function calculateSIP() {
    const monthly = document.getElementById('sip-monthly').value;
    const rate = document.getElementById('sip-rate').value;
    const years = document.getElementById('sip-years').value;
    
    const emptyState = document.getElementById('sip-empty-state');
    const resultsState = document.getElementById('sip-results-state');
    const tableContainer = document.getElementById('sip-table-container');
    
    if (!monthly || !rate || !years || monthly < 0 || rate < 0 || years < 0) {
        emptyState.classList.remove('hidden');
        resultsState.classList.add('hidden');
        tableContainer.classList.add('hidden');
        return;
    }

    emptyState.classList.add('hidden');
    resultsState.classList.remove('hidden');
    tableContainer.classList.remove('hidden');

    try {
        const csrfToken = getCookie('csrf_access_token');
        const res = await fetch('/app/api/planning/calculate_sip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
            body: JSON.stringify({ monthly_investment: monthly, annual_rate: rate, years: years })
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('sip-future-value').textContent = `₹${Math.round(data.future_value).toLocaleString()}`;
            document.getElementById('sip-invested').textContent = `₹${Math.round(data.total_invested).toLocaleString()}`;
            document.getElementById('sip-returns').textContent = `₹${Math.round(data.est_returns).toLocaleString()}`;
            displayInsight('sip', data.insight);
            
            renderSIPChart(data.yearly_breakdown);
            renderSIPTable(data.yearly_breakdown);
        } else {
            displayInsight('sip', { status: 'WARNING', message: 'Failed to retrieve insights from the server.' });
        }
    } catch (err) {
        console.error(err);
        displayInsight('sip', { status: 'WARNING', message: 'Network error occurred while fetching insights.' });
    }
}

async function calculateEMI() {
    const loanType = document.getElementById('emi-loan-type').value;
    const principal = document.getElementById('emi-principal').value;
    const vehiclePrice = document.getElementById('emi-vehicle-price').value;
    const downPayment = document.getElementById('emi-down-payment').value;
    const rate = document.getElementById('emi-rate').value;
    const years = document.getElementById('emi-years').value;
    
    const emptyState = document.getElementById('emi-empty-state');
    const resultsState = document.getElementById('emi-results-state');
    const tableContainer = document.getElementById('emi-table-container');
    
    let isValid = true;
    if (!rate || !years || rate < 0 || years < 0) isValid = false;
    if (loanType === 'Car' || loanType === 'Bike') {
        if (!vehiclePrice || !downPayment || vehiclePrice < 0 || downPayment < 0) isValid = false;
    } else {
        if (!principal || principal < 0) isValid = false;
    }
    
    if (!isValid) {
        emptyState.classList.remove('hidden');
        resultsState.classList.add('hidden');
        tableContainer.classList.add('hidden');
        return;
    }

    emptyState.classList.add('hidden');
    resultsState.classList.remove('hidden');
    tableContainer.classList.remove('hidden');

    try {
        const csrfToken = getCookie('csrf_access_token');
        const res = await fetch('/app/api/planning/calculate_emi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
            body: JSON.stringify({
                loan_type: loanType,
                principal: principal,
                vehicle_price: vehiclePrice,
                down_payment: downPayment,
                annual_rate: rate,
                years: years
            })
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('emi-monthly').textContent = `₹${Math.round(data.monthly_emi).toLocaleString()}`;
            
            let actualPrincipal = loanType === 'Car' || loanType === 'Bike' ? (vehiclePrice - downPayment) : principal;
            actualPrincipal = Math.max(0, actualPrincipal);
            
            document.getElementById('emi-display-type').textContent = loanType + ' Loan';
            document.getElementById('emi-total-principal').textContent = `₹${Math.round(actualPrincipal).toLocaleString()}`;
            
            document.getElementById('emi-principal-cost').textContent = `₹${Math.round(actualPrincipal).toLocaleString()}`;
            document.getElementById('emi-interest').textContent = `₹${Math.round(data.total_interest).toLocaleString()}`;
            document.getElementById('emi-total-paid').textContent = `₹${Math.round(Number(actualPrincipal) + Number(data.total_interest)).toLocaleString()}`;
            
            const ratioElem = document.getElementById('emi-interest-ratio');
            if (ratioElem) {
                const ratioPct = data.interest_cost_pct !== undefined ? data.interest_cost_pct : (data.interest_to_principal_ratio !== undefined ? Math.round(data.interest_to_principal_ratio) : 0);
                ratioElem.textContent = `${ratioPct}% of principal`;
            }

            const foirContainer = document.getElementById('emi-foir-details');
            const afford = data.loan_affordability || data.insight;
            if (afford && afford.foir !== undefined) {
                if (foirContainer) foirContainer.classList.remove('hidden');
                const incomeEl = document.getElementById('emi-afford-income');
                const emiEl = document.getElementById('emi-afford-emi');
                const foirEl = document.getElementById('emi-afford-foir');
                const riskEl = document.getElementById('emi-afford-risk');
                const reasonEl = document.getElementById('emi-afford-reason');
                
                if (incomeEl) incomeEl.textContent = afford.income > 0 ? `₹${Math.round(afford.income).toLocaleString()}` : '₹0';
                if (emiEl) emiEl.textContent = `₹${Math.round(afford.emi).toLocaleString()}`;
                if (foirEl) foirEl.textContent = `${Math.round(afford.foir)}%`;
                
                if (riskEl) {
                    const riskText = afford.display_risk || afford.risk_level || afford.risk || 'Moderate';
                    riskEl.textContent = riskText;
                    if (riskText.toLowerCase().includes('healthy') || riskText.toLowerCase().includes('low')) {
                        riskEl.className = 'inline-block px-2 py-0.5 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800';
                    } else if (riskText.toLowerCase().includes('moderate')) {
                        riskEl.className = 'inline-block px-2 py-0.5 text-xs font-bold rounded-full bg-amber-100 text-amber-800';
                    } else {
                        riskEl.className = 'inline-block px-2 py-0.5 text-xs font-bold rounded-full bg-rose-100 text-rose-800';
                    }
                }
                
                if (reasonEl) reasonEl.textContent = afford.reason || afford.message;
            } else if (foirContainer) {
                foirContainer.classList.add('hidden');
            }
            
            displayInsight('emi', data.insight);
            
            renderEMIChart(data.yearly_amortization);
            renderEMITable(data.yearly_amortization);
        } else {
            displayInsight('emi', { status: 'WARNING', message: 'Failed to retrieve insights from the server.' });
        }
    } catch (err) {
        console.error(err);
        displayInsight('emi', { status: 'WARNING', message: 'Network error occurred while fetching insights.' });
    }
}

function renderSIPChart(breakdown) {
    const ctx = document.getElementById('sipChart').getContext('2d');
    const labels = breakdown.map(item => `Year ${item.year}`);
    const invested = breakdown.map(item => item.invested);
    const returns = breakdown.map(item => item.returns);
    
    if (sipChartInstance) {
        sipChartInstance.destroy();
    }
    
    sipChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Invested',
                    data: invested,
                    backgroundColor: '#E5E7EB',
                },
                {
                    label: 'Returns',
                    data: returns,
                    backgroundColor: '#10B981',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true, grid: { display: false } },
                y: { stacked: true, beginAtZero: true, display: false }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderEMIChart(amortization) {
    const ctx = document.getElementById('emiChart').getContext('2d');
    const labels = amortization.map(item => `Year ${item.year}`);
    const remaining = amortization.map(item => item.remaining_balance);
    
    if (emiChartInstance) {
        emiChartInstance.destroy();
    }
    
    emiChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Remaining Balance',
                    data: remaining,
                    borderColor: '#EF4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, display: false }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderSIPTable(breakdown) {
    const tbody = document.getElementById('sip-breakdown-body');
    tbody.innerHTML = '';
    breakdown.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';
        tr.innerHTML = `
            <td class="px-4 py-3 font-medium text-fz-black">${row.year}</td>
            <td class="px-4 py-3">₹${Math.round(row.invested).toLocaleString()}</td>
            <td class="px-4 py-3 text-green-600 font-medium">₹${Math.round(row.returns).toLocaleString()}</td>
            <td class="px-4 py-3 font-bold text-fz-black">₹${Math.round(row.value).toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderEMITable(amortization) {
    const tbody = document.getElementById('emi-breakdown-body');
    tbody.innerHTML = '';
    amortization.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';
        tr.innerHTML = `
            <td class="px-4 py-3 font-medium text-fz-black">${row.year}</td>
            <td class="px-4 py-3">₹${Math.round(row.principal_paid).toLocaleString()}</td>
            <td class="px-4 py-3 text-red-500 font-medium">₹${Math.round(row.interest_paid).toLocaleString()}</td>
            <td class="px-4 py-3 font-bold text-fz-black">₹${Math.round(row.remaining_balance).toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
    });
}
