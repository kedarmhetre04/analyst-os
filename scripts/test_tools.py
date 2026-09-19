from src.tools import (
    get_database_schema,
    get_regional_performance,
    get_category_performance,
    get_top_products,
    get_high_return_products,
)


print("\n=== REGIONAL PERFORMANCE ===")
print(get_regional_performance())


print("\n=== CATEGORY PERFORMANCE ===")
print(get_category_performance())


print("\n=== TOP PRODUCTS ===")
print(get_top_products(5))


print("\n=== HIGH RETURN PRODUCTS ===")
print(get_high_return_products(5))


print("\n=== DATABASE SCHEMA ===")
schema = get_database_schema()
print(schema.head(20))
