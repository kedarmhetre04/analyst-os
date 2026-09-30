
# AnalystOS Business Semantic Layer

## Data Source

Synthetic retail data covering January 2024 to December 2025.

## Core Relationships

- customers.customer_id = orders.customer_id
- orders.order_id = order_items.order_id
- products.product_id = order_items.product_id
- orders.order_id = shipping.order_id
- order_items.order_item_id = returns.order_item_id
- products.product_id = inventory.product_id

## Data Grain

- orders: one row per order
- order_items: one row per purchased line item
- shipping: one row per order
- returns: one row per returned line item
- inventory: one row per product per month
- marketing_spend: one row per month, region and channel
- targets: one row per month and region
- sales_analysis: one row per purchased line item

## Business Metrics

Revenue = SUM(sales_analysis.net_sales)

Gross Profit = SUM(sales_analysis.gross_profit)

## Contribution Profit

At the line-item level:

Contribution Profit =
Gross Profit
- Refund Amount
- Allocated Shipping Cost

Where:

Gross Profit =
Net Sales - COGS

Allocated Shipping Cost =
Order Shipping Cost / Number of Line Items in the Order

For aggregated analysis:

Contribution Profit =
SUM(sales_analysis.contribution_profit)

Contribution profit in AnalystOS is a simplified business metric.
It does not include marketing costs, payment processing fees,
labor costs, overhead, or other operating expenses.

Gross Margin = Gross Profit / Revenue

Order Count = COUNT(DISTINCT order_id)

Customer Count = COUNT(DISTINCT customer_id)

Return Rate = Returned Line Items / Total Line Items

Late Delivery Rate = Late Orders / Total Orders

Average Order Value = Revenue / Order Count

## Important Rules

1. Never SUM the original shipping cost from an item-level join.
2. Use allocated_shipping_cost for item-level profitability.
3. Count distinct orders for order-level metrics.
4. Return rate is measured at the line-item level.
5. Late delivery rate must be calculated at the order level.
6. Marketing spend and targets are monthly regional aggregates.
7. Inventory snapshots are synthetic and not yet reconciled
   with recorded sales. Do not claim reliable stockout risk.
8. Distinguish observed relationships from proven causation.
9. Do not invent values or business outcomes.
10. Ask for clarification when a metric definition is ambiguous.

## Discount Rate

Discount Rate =
SUM(discount_amount) / SUM(gross_sales)

This is a sales-value-weighted discount rate.

Do not use AVG(discount_pct) for aggregated business analysis unless
explicitly labeled as average line-item discount percentage.