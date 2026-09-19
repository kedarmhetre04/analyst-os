from pathlib import Path
import duckdb

DB_PATH = "analyst_os.duckdb"
DATA_DIR = Path("data")


def create_database():
    con = duckdb.connect(DB_PATH)

    tables = [
        "customers",
        "products",
        "orders",
        "order_items",
        "shipping",
        "returns",
        "inventory",
        "marketing_spend",
        "targets",
    ]

    for table in tables:
        csv_path = DATA_DIR / f"{table}.csv"

        con.execute(
            f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT *
            FROM read_csv_auto('{csv_path}');
            """
        )

        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"Loaded {table:<20} {count:,} rows")

    create_views(con)

    con.close()


def create_views(con):
    # Enriched sales-level view
    con.execute(
        """
        CREATE OR REPLACE VIEW sales_analysis AS
        SELECT
            o.order_id,
            o.customer_id,
            o.order_date,
            o.sales_channel,
            o.payment_method,
            o.state,
            o.region,
            o.segment,

            oi.order_item_id,
            oi.product_id,
            oi.quantity,
            oi.unit_price,
            oi.unit_cost,
            oi.category,
            oi.subcategory,
            oi.discount_pct,
            oi.gross_sales,
            oi.discount_amount,
            oi.net_sales,
            oi.cogs,
            oi.gross_profit,

            s.shipping_mode,
            s.delivery_days,
            s.shipping_cost,
            s.late_delivery,

            CASE
                WHEN r.return_id IS NOT NULL THEN 1
                ELSE 0
            END AS returned,

            COALESCE(r.refund_amount, 0) AS refund_amount,

            oi.gross_profit
                - COALESCE(r.refund_amount, 0)
                - s.shipping_cost
                AS contribution_profit

        FROM orders o

        JOIN order_items oi
            ON o.order_id = oi.order_id

        LEFT JOIN shipping s
            ON o.order_id = s.order_id

        LEFT JOIN returns r
            ON oi.order_item_id = r.order_item_id;
        """
    )

    # Monthly performance view
    con.execute(
        """
        CREATE OR REPLACE VIEW monthly_performance AS
        SELECT
            DATE_TRUNC('month', order_date) AS month,
            region,

            SUM(net_sales) AS revenue,
            SUM(gross_profit) AS gross_profit,
            SUM(contribution_profit) AS contribution_profit,

            COUNT(DISTINCT order_id) AS orders,
            COUNT(DISTINCT customer_id) AS customers,

            SUM(quantity) AS units_sold,

            AVG(discount_pct) AS avg_discount_pct,
            AVG(delivery_days) AS avg_delivery_days,

            SUM(returned) * 1.0
                / COUNT(*) AS return_rate,

            SUM(late_delivery) * 1.0
                / COUNT(*) AS late_delivery_rate

        FROM sales_analysis

        GROUP BY 1, 2;
        """
    )

    print("Created view: sales_analysis")
    print("Created view: monthly_performance")


def run_query(query):
    con = duckdb.connect(DB_PATH)

    result = con.execute(query).df()

    con.close()

    return result


if __name__ == "__main__":
    create_database()