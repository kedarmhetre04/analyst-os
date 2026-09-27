from src.investigation import (
    compare_months,
    category_breakdown,
    shipping_breakdown,
    discount_breakdown,
    return_breakdown,
)

print("\n=== MONTHLY PERFORMANCE: WEST ===")
print(compare_months("West").tail(8))

print("\n=== CATEGORY BREAKDOWN ===")
print(
    category_breakdown(
        "West",
        "2025-08-01",
        "2025-09-30"
    )
)

print("\n=== SHIPPING BREAKDOWN ===")
print(
    shipping_breakdown(
        "West",
        "2025-08-01",
        "2025-09-30"
    )
)

print("\n=== DISCOUNT BREAKDOWN ===")
print(
    discount_breakdown(
        "West",
        "2025-08-01",
        "2025-09-30"
    )
)

print("\n=== RETURN BREAKDOWN ===")
print(
    return_breakdown(
        "West",
        "2025-08-01",
        "2025-09-30"
    )
)