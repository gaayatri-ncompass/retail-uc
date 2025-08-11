from src.utils.config import get_warehouse_db_connector


def run_sample_analytics():

    print("Running sample analytics...")

    db = get_warehouse_db_connector()
    db.connect()

    try:

        top_products_query = """
            SELECT
                p.product_name,
                SUM(fs.quantity) AS total_quantity_sold
            FROM factsales fs
            JOIN dimproduct p ON fs.product_key = p.product_key
            GROUP BY p.product_name
            ORDER BY total_quantity_sold DESC
            LIMIT 5;
        """
        top_products = db.run_query(top_products_query)
        if top_products is not None:
            print("\nTop 5 Best-Selling Products:")
            print(top_products)

        
        monthly_sales_query = """
            SELECT
                d.year,
                d.month,
                SUM(fs.total_amount) AS total_sales
            FROM factsales fs
            JOIN dimdate d ON fs.date_key = d.date_key
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month;
        """
        monthly_sales = db.run_query(monthly_sales_query)
        if monthly_sales is not None:
            print("\nTotal Sales Amount per Month:")
            print(monthly_sales)

       
        inventory_aging_query = """
            SELECT
                CASE
                    WHEN DATEDIFF(CURDATE(), d.full_date) <= 30 THEN '0-30 Days'
                    WHEN DATEDIFF(CURDATE(), d.full_date) BETWEEN 31 AND 60 THEN '31-60 Days'
                    WHEN DATEDIFF(CURDATE(), d.full_date) BETWEEN 61 AND 90 THEN '61-90 Days'
                    ELSE '90+ Days'
                END AS age_bucket,
                SUM(fis.stock_level) AS total_stock
            FROM factinventorysnapshot fis
            JOIN dimdate d ON fis.date_key = d.date_key
            GROUP BY age_bucket
            ORDER BY age_bucket;
        """
        inventory_aging_report = db.run_query(inventory_aging_query)
        if inventory_aging_report is not None:
            print("\nInventory Aging Report:")
            print(inventory_aging_report)

    except Exception as e:
        print(f"An error occurred during analytics: {e}")
    finally:
        db.disconnect()
        print("\nAnalytics run complete.")


def main():
    run_sample_analytics()


if __name__ == "__main__":
    main()
