from configs.db_config import get_warehouse_db_connector
from src.utils.logger import get_logger


logger = get_logger("ANALYTICS")


def run_sample_analytics():
    """Run analytics using the simplified unified query method"""
    logger.info("Running sample analytics...")

    db = get_warehouse_db_connector()
    db.connect()

    try:
        # Using the new unified query method - cleaner and more consistent
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
        top_products = db.query(top_products_query)  # Simplified call
        if top_products is not None:
            logger.info("\nTop 5 Best-Selling Products:")
            logger.info(f"\n{top_products}")

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
        monthly_sales = db.query(monthly_sales_query)  # Simplified call
        if monthly_sales is not None:
            logger.info("\nTotal Sales Amount per Month:")
            logger.info(f"\n{monthly_sales}")

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
        inventory_aging_report = db.query(
            inventory_aging_query)  # Simplified call
        if inventory_aging_report is not None:
            logger.info("\nInventory Aging Report:")
            logger.info(f"\n{inventory_aging_report}")

    except Exception as e:
        logger.error(f"An error occurred during analytics: {e}")
    finally:
        db.disconnect()
        logger.info("Analytics run complete.")


def main():
    run_sample_analytics()


if __name__ == "__main__":
    main()
