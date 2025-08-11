import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)


print("--- Running the script ---")

logging.debug(
    "This is a detailed debug message. Good for tracking a variable's value.")
logging.info("The script is starting to do some work now.")
logging.warning(
    "The 'discount_rate' setting was not found. Using default value of 10%.")
logging.error(
    "Failed to connect to the database. Cannot proceed with this task.")
logging.critical("Catastrophic failure! Out of memory.")

print("--- Script finished ---")
