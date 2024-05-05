# Vitapharm API Documentation

## Home

### `/vitapharm/home`

- **Method:** GET
- **Description:** Retrieves a welcome message.
- **Usage:** Simply make a GET request to the `/vitapharm/home` endpoint.

## Admin Signup

### `/vitapharm/signup`

- **Method:** POST
- **Description:** Creates a new admin account.
- **Parameters:**
  - `email` (string): Email of the admin.
  - `password` (string): Password for the admin account.
- **Usage:** Send a POST request with JSON payload containing email and password to `/vitapharm/signup`.

## Products

### Add a New Product

#### `/vitapharm/products`

- **Method:** POST
- **Description:** Adds a new product to the database.
- **Parameters:**
  - `name` (string): Name of the product.
  - `description` (string): Description of the product.
  - `price` (integer): Price of the product.
  - `brand` (string): Brand of the product.
  - `quantity` (integer): Quantity of the product.
  - `category` (string): Category of the product.
  - `sub_category` (string): Sub-category of the product.
  - `admin_id` (integer): ID of the admin adding the product.
  - `images` (file): Images of the product.
- **Usage:** Send a POST request with form data or JSON payload containing product details and images to `/vitapharm/products`.

### Retrieve All Products

#### `/vitapharm/products`

- **Method:** GET
- **Description:** Retrieves all products from the database.
- **Usage:** Simply make a GET request to the `/vitapharm/products` endpoint.

### Retrieve a Single Product

#### `/vitapharm/products/<productId>`

- **Method:** GET
- **Description:** Retrieves details of a single product by its ID.
- **Parameters:**
  - `productId` (integer): ID of the product.
- **Usage:** Send a GET request to `/vitapharm/products/<productId>` to retrieve details of the product with the specified ID.

### Update a Product

#### `/vitapharm/products/<productId>`

- **Method:** PATCH
- **Description:** Updates details of a product.
- **Parameters:**
  - `productId` (integer): ID of the product.
  - (optional) Fields to be updated: `name`, `description`, `price`, `brand`, `quantity`, `category`, `sub_category`, `admin_id`, `deal_price`, `deal_start_time`, `deal_end_time`.
- **Usage:** Send a PATCH request with JSON payload containing the fields to be updated to `/vitapharm/products/<productId>`.

### Delete a Product

#### `/vitapharm/products/<productId>`

- **Method:** DELETE
- **Description:** Deletes a product from the database.
- **Parameters:**
  - `productId` (integer): ID of the product.
- **Usage:** Send a DELETE request to `/vitapharm/products/<productId>` to delete the product with the specified ID.

## Cart

### Add Item to Cart

#### `/vitapharm/cart/add`

- **Method:** POST
- **Description:** Adds an item to the user's cart.
- **Parameters:**
  - `product_id` (integer): ID of the product to add to cart.
  - `quantity` (integer): Quantity of the product to add (default is 1).
- **Usage:** Send a POST request with JSON payload containing product ID and quantity to `/vitapharm/cart/add`.

### Retrieve Cart Contents

#### `/vitapharm/cart`

- **Method:** GET
- **Description:** Retrieves the contents of the user's cart.
- **Parameters:**
  - `session_id` (string): Session ID of the user.
- **Usage:** Send a GET request with the session ID as a query parameter to `/vitapharm/cart`.

### Update Cart Item Quantity

#### `/vitapharm/cart/update`

- **Method:** POST
- **Description:** Updates the quantity of a product in the user's cart.
- **Parameters:**
  - `product_id` (integer): ID of the product in the cart.
  - `quantity_change` (integer): Change in quantity (+/-).
- **Usage:** Send a POST request with JSON payload containing product ID and quantity change to `/vitapharm/cart/update`.

## Product Search

### Search Products

#### `/vitapharm/products/search`

- **Method:** GET
- **Description:** Search products based on brand, category, or sub-category.
- **Parameters:**
  - (optional) `brand` (string): Brand of the product.
  - (optional) `category` (string): Category of the product.
  - (optional) `sub_category` (string): Sub-category of the product.
- **Usage:** Send a GET request with optional query parameters (brand, category, sub_category) to `/vitapharm/products/search`.

## Products on Offer

### Get Products on Offer

#### `/vitapharm/products/offer`

- **Method:** GET
- **Description:** Retrieves products currently on offer.
- **Usage:** Simply make a GET request to the `/vitapharm/products/offer` endpoint.

## Book Appointment

### Book an Appointment

#### `/vitapharm/book`

- **Method:** POST
- **Description:** Books an appointment with Vitapharm.
- **Parameters:**
  - `customer_name` (string): Name of the customer.
  - `customer_email` (string): Email of the customer.
  - `customer_phone` (string): Phone number of the customer.
  - `appointment_date` (string): Date of the appointment (YYYY-MM-DD).
- **Usage:** Send a POST request with JSON payload containing customer details and appointment date to `/vitapharm/book`.

### Retrieve Appointments

#### `/vitapharm/book`

- **Method:** GET
- **Description:** Retrieves all appointments.
- **Usage:** Simply make a GET request to the `/vitapharm/book` endpoint.

## Place Order

### Place an Order

#### `/vitapharm/order/place`

- **Method:** POST
- **Description:** Places an order for items in the user's cart.
- **Parameters:**
  - `customerFirstName` (string): First name of the customer.
  - `customerLastName` (string): Last name of the customer.
  - `customerEmail` (string): Email of the customer.
  - `address` (string): Shipping address of the customer.
  - `town` (string): Town of the customer.
  - `phone` (string): Phone number of the customer.
- **Usage:** Send a POST request with JSON payload containing customer details to `/vitapharm/order/place`.
