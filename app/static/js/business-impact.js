let impactChart;

const impactCurrency = new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0
});

function impactNumber(value) {
  if (value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function calculateImpact(values) {
  const additionalRevenue = values.dailyOrders * values.operatingDays
    * values.averageOrderValue * (values.aovUpliftPct / 100);
  const additionalGrossProfit = additionalRevenue * (values.grossProfitMarginPct / 100);
  const wasteSavings = values.monthlyFoodWasteCost * (values.wasteReductionPct / 100);
  const totalMonthlyBenefit = additionalGrossProfit + wasteSavings;
  const monthlyNetBenefit = totalMonthlyBenefit - values.monthlySubscriptionCost;
  return {
    additionalRevenue,
    additionalGrossProfit,
    wasteSavings,
    totalMonthlyBenefit,
    monthlyNetBenefit,
    annualNetBenefit: monthlyNetBenefit * 12,
    roiPct: values.monthlySubscriptionCost > 0
      ? (monthlyNetBenefit / values.monthlySubscriptionCost) * 100
      : null
  };
}

function readImpactInputs(form) {
  const values = {};
  const fieldNames = {
    daily_orders: 'dailyOrders',
    operating_days: 'operatingDays',
    average_order_value: 'averageOrderValue',
    aov_uplift_pct: 'aovUpliftPct',
    gross_profit_margin_pct: 'grossProfitMarginPct',
    monthly_food_waste_cost: 'monthlyFoodWasteCost',
    waste_reduction_pct: 'wasteReductionPct',
    monthly_subscription_cost: 'monthlySubscriptionCost'
  };
  for (const input of form.querySelectorAll('.impact-input')) {
    const value = impactNumber(input.value);
    if (value === null || value < 0 || (input.max && value > Number(input.max))) {
      return {error: `${input.previousSibling?.textContent || 'Input'} must be a valid non-negative value.`};
    }
    values[fieldNames[input.name]] = value;
  }
  return {values};
}

function setImpactValue(id, value) {
  document.getElementById(id).textContent = impactCurrency.format(value);
}

function renderImpactChart(result, subscriptionCost) {
  if (impactChart) impactChart.destroy();
  impactChart = new Chart(document.getElementById('impact-chart'), {
    type: 'bar',
    data: {
      labels: ['Additional gross profit', 'Waste savings', 'Subscription cost'],
      datasets: [{
        data: [result.additionalGrossProfit, result.wasteSavings, subscriptionCost],
        backgroundColor: ['#8b7bff', '#41d6a1', '#303b5d'],
        borderRadius: 5
      }]
    },
    options: {
      ...DobbyCharts.options(),
      plugins: {legend: {display: false}},
      scales: {
        ...DobbyCharts.options().scales,
        y: { ...DobbyCharts.options().scales.y, ticks: { ...DobbyCharts.options().scales.y.ticks, callback: value => impactCurrency.format(value) } }
      }
    }
  });
}

function renderImpact() {
  const form = document.getElementById('impact-form');
  const validation = document.getElementById('impact-validation');
  const parsed = readImpactInputs(form);
  if (parsed.error) {
    validation.textContent = parsed.error;
    validation.classList.remove('d-none');
    return;
  }
  validation.classList.add('d-none');
  const result = calculateImpact(parsed.values);
  setImpactValue('monthly-net-benefit', result.monthlyNetBenefit);
  setImpactValue('annual-net-benefit', result.annualNetBenefit);
  document.getElementById('roi').textContent = result.roiPct === null ? 'Not available' : `${result.roiPct.toFixed(1)}%`;
  setImpactValue('additional-revenue', result.additionalRevenue);
  setImpactValue('additional-gross-profit', result.additionalGrossProfit);
  setImpactValue('waste-savings', result.wasteSavings);
  setImpactValue('total-monthly-benefit', result.totalMonthlyBenefit);
  setImpactValue('subscription-cost', parsed.values.monthlySubscriptionCost);
  setImpactValue('annual-summary-value', result.annualNetBenefit);
  document.getElementById('impact-outcome').innerHTML = result.monthlyNetBenefit >= 0
    ? '<i class="bi bi-arrow-up-right"></i> This scenario produces a positive monthly net benefit.'
    : '<i class="bi bi-exclamation-triangle"></i> This scenario produces a negative monthly net benefit.';
  renderImpactChart(result, parsed.values.monthlySubscriptionCost);
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.impact-input').forEach(input => input.addEventListener('input', renderImpact));
  renderImpact();
});
