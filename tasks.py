from robocorp.tasks import task
from robocorp import browser
from robocorp.http import download
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

# Create a PDF object to use in your functions
pdf = PDF()

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    # Configure the browser (optional but helps see what is happening)
    browser.configure(slowmo=100)
    
    open_robot_order_website()
    orders = get_orders()
    
    # Loop through the orders
    for row in orders:
        close_annoying_modal()
        fill_the_form(row)
        preview_robot()
        submit_order()
        
        # New steps!
        # Pass the order number to the functions and save the returned paths
        pdf_path = store_receipt_as_pdf(row["Order number"])
        screenshot_path = screenshot_robot(row["Order number"])
        
        # Pass the two paths to the embedding function
        embed_screenshot_to_receipt(screenshot_path, pdf_path)
        
        # Go to order another robot
        page = browser.page()
        page.click("#order-another")
    archive_receipts()

def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    """Downloads the orders CSV file, reads it into a table, and returns the result"""
    # Overwrite=True ensures the robot can be run over and over safely
    download("https://robotsparebinindustries.com/orders.csv", overwrite=True)
    
    # Instantiate the Tables library and read the CSV
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders

def close_annoying_modal():
    """Gives up constitutional rights by accepting the modal"""
    page = browser.page()
    page.click("button:text('OK')")

def fill_the_form(row):
    """Fills out the order form using data from the current loop row"""
    page = browser.page()
    
    # Head: Select from dropdown
    page.select_option("#head", row["Head"])
    
    # Body: Radio buttons use the format #id-body-1, #id-body-2, etc.
    page.click(f"#id-body-{row['Body']}")
    
    # Legs: The ID changes constantly, so we target the placeholder attribute instead!
    page.fill("input[placeholder='Enter the part number for the legs']", row["Legs"])
    
    # Address: Standard text input
    page.fill("#address", row["Address"])

def preview_robot():
    """Clicks the preview button to generate the robot image"""
    page = browser.page()
    page.click("button:text('Preview')")

def submit_order():
    """Submits the order and retries if the server throws an error"""
    page = browser.page()
    
    # We use an infinite loop that only breaks when the receipt appears
    while True:
        page.click("#order")
        
        # If the receipt appears, the order was successful
        if page.locator("#receipt").is_visible():
            break
        # If the error banner appears, the loop simply runs again and clicks "Order"

def store_receipt_as_pdf(order_number):
    """Extracts the HTML receipt and stores it as a PDF file"""
    page = browser.page()
    
    # Get the raw HTML content of the receipt element
    receipt_html = page.locator("#receipt").inner_html()
    
    # Define the output path using the order number
    pdf_path = f"output/receipts/{order_number}.pdf"
    
    # Convert the HTML into a PDF file
    pdf.html_to_pdf(receipt_html, pdf_path)
    
    return pdf_path

def screenshot_robot(order_number):
    """Takes a screenshot of the robot image and saves it"""
    page = browser.page()
    
    # Define the output path for the screenshot
    screenshot_path = f"output/screenshots/{order_number}.png"
    
    # Target just the robot image element and take a screenshot of it
    page.locator("#robot-preview-image").screenshot(path=screenshot_path)
    
    return screenshot_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Appends the screenshot image to the end of the PDF receipt"""
    # By passing the image in a list to 'files' and using append=True, 
    # it adds the image as a new page to the existing PDF!
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True
    )

def archive_receipts():
    """Zips the receipt PDF files into a single archive"""
    lib = Archive()
    # The first argument is the folder to zip, the second is the name of the output zip file
    lib.archive_folder_with_zip("output/receipts", "output/receipts.zip")