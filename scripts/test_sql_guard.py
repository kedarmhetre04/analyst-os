from src.database import (
    QueryTimeoutError,
    UnsafeQueryError,
    run_query,
    run_read_only_sql,
)
from src.investigation import compare_months


def expect_rejected(query, error_type=UnsafeQueryError):
    try:
        run_read_only_sql(query)
    except error_type:
        return
    raise AssertionError(f"Query was not rejected: {query}")


def expect_blocked(query):
    try:
        run_read_only_sql(query)
    except Exception:
        return
    raise AssertionError(f"Query was not blocked: {query}")


# Only single SELECT statements are allowed.
expect_rejected("DROP TABLE orders")
expect_rejected("DELETE FROM orders")
expect_rejected("CREATE TABLE t AS SELECT 1")
expect_rejected("COPY orders TO 'orders_copy.csv'")
expect_rejected("ATTACH 'other.duckdb'")
expect_rejected("SET enable_external_access = true")
expect_rejected("SELECT 1; DROP TABLE orders")
expect_rejected("")

# SELECTs cannot read files outside the database.
expect_blocked("SELECT * FROM read_csv('data/orders.csv')")

# Valid queries run, and large results are truncated.
df, truncated = run_read_only_sql(
    "WITH x AS (SELECT region FROM orders) "
    "SELECT region, COUNT(*) AS n FROM x GROUP BY 1"
)
assert len(df) == 4 and not truncated

df, truncated = run_read_only_sql(
    "SELECT order_id FROM orders ORDER BY order_id",
    max_rows=10,
)
assert len(df) == 10 and truncated
assert df["order_id"].tolist() == list(range(1, 11))

# Long-running queries are interrupted.
try:
    run_read_only_sql(
        "SELECT SUM(a.range * b.range) "
        "FROM range(1000000) a, range(1000000) b",
        timeout_seconds=1,
    )
except QueryTimeoutError:
    pass
else:
    raise AssertionError("Long query was not interrupted")

# Parameterized helpers treat input as data, not SQL.
injection = "West' OR '1'='1"
assert compare_months(injection).empty
assert not compare_months("West").empty

# The trusted path is read-only too.
try:
    run_query("DROP TABLE orders")
except Exception:
    pass
else:
    raise AssertionError("run_query allowed a write")

print("PASS: SQL guardrails")
