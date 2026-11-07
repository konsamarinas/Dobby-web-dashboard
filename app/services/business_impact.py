from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BusinessImpactResult:
    additional_revenue: float
    additional_gross_profit: float
    waste_savings: float
    total_monthly_benefit: float
    monthly_net_benefit: float
    annual_net_benefit: float
    roi_pct: float | None


def calculate_business_impact(
    daily_orders: float,
    operating_days: float,
    average_order_value: float,
    aov_uplift_pct: float,
    gross_profit_margin_pct: float,
    monthly_food_waste_cost: float,
    waste_reduction_pct: float,
    monthly_subscription_cost: float,
) -> BusinessImpactResult:
    values = {
        "daily_orders": daily_orders,
        "operating_days": operating_days,
        "average_order_value": average_order_value,
        "aov_uplift_pct": aov_uplift_pct,
        "gross_profit_margin_pct": gross_profit_margin_pct,
        "monthly_food_waste_cost": monthly_food_waste_cost,
        "waste_reduction_pct": waste_reduction_pct,
        "monthly_subscription_cost": monthly_subscription_cost,
    }
    if any(not math.isfinite(value) or value < 0 for value in values.values()):
        raise ValueError("Business impact assumptions cannot be negative.")
    if aov_uplift_pct > 100 or gross_profit_margin_pct > 100 or waste_reduction_pct > 100:
        raise ValueError("Percentage assumptions must be between 0 and 100.")

    additional_revenue = (
        daily_orders
        * operating_days
        * average_order_value
        * (aov_uplift_pct / 100)
    )
    additional_gross_profit = additional_revenue * (gross_profit_margin_pct / 100)
    waste_savings = monthly_food_waste_cost * (waste_reduction_pct / 100)
    total_monthly_benefit = additional_gross_profit + waste_savings
    monthly_net_benefit = total_monthly_benefit - monthly_subscription_cost
    annual_net_benefit = monthly_net_benefit * 12
    roi_pct = (
        monthly_net_benefit / monthly_subscription_cost * 100
        if monthly_subscription_cost > 0
        else None
    )
    return BusinessImpactResult(
        additional_revenue=additional_revenue,
        additional_gross_profit=additional_gross_profit,
        waste_savings=waste_savings,
        total_monthly_benefit=total_monthly_benefit,
        monthly_net_benefit=monthly_net_benefit,
        annual_net_benefit=annual_net_benefit,
        roi_pct=roi_pct,
    )
