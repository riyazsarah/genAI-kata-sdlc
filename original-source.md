# Farm-to-Table Marketplace: Original Source Document

> Source: Farm_To_Table_MarketPlace-V1.0.pdf

---

## Slide 1: Title

# Farm-to-Table Marketplace: Connecting Consumers and Local Farmers

[Image: Title slide with Farm-to-Table branding]

---

## Slide 2: Farm-to-Table Market Place

### Farm-to-Table Market Place

A Farm-to-Table Marketplace connects consumers directly with local farmers, offering fresh, seasonal produce and products. It promotes transparency by showcasing farming practices and providing detailed product information. Users enjoy the convenience of ordering online, scheduling deliveries, and receiving personalized recommendations. This platform supports sustainable agriculture and strengthens the local economy by fostering direct relationships between farmers and consumers.

**Kata Topic**

[Image: Kata topic illustration]

---

## Slide 3: Benefits for Consumers

### Benefits for Consumers

**1. Access to Fresh Produce**
Consumers get access to fresher, higher-quality produce that is harvested at peak ripeness, which often results in better taste and nutritional value.

**2. Transparency**
Consumers can learn about the origins of their food, including the farming practices used, promoting trust and confidence in the quality of their purchases.

**3. Convenience**
The app provides a convenient way to shop for fresh produce, schedule deliveries, and receive products directly at their doorstep.

**4. Health Benefits**
Access to fresh, locally-sourced food can contribute to a healthier diet, as it encourages the consumption of fruits, vegetables, and other wholesome foods.

[Image: Consumer benefits illustration]

---

## Slide 4: Benefits for Farmers

### Benefits for Farmers

**1. Direct Market Access**
Farmers can sell their produce directly to consumers, bypassing intermediaries and potentially earning higher profits.

**2. Increased Visibility**
The app provides a platform for farmers to showcase their products and farming practices, increasing their visibility and reach to a broader audience.

**3. Customer Relationships**
Direct interactions with consumers can help farmers build loyal customer bases and receive valuable feedback to improve their offerings.

**4. Revenue Stability**
Subscription models and regular orders provide a more predictable and stable income stream for farmers.

[Image: Farmer benefits illustration]

---

## Slide 5: High-level Requirements

### High-level Requirements

**Requirements:** (For KATA, consider features that are marked with \* at the end)

1. User profile management (personal information, preferences, payment details, etc.). (Must have)\*
2. Farmer profile creation and management (farm details, farming practices, product offerings). (Must have)\*
3. Product listing management (adding, updating, and removing products). (Must have)\*
4. Availability and pricing management. (Must have)\*
5. Browsing and searching for products (filters by category, seasonality, location, etc.). (Must have)\*
6. Detailed product descriptions (nutritional information, origin, farming methods). (Nice to have)\*
7. Shopping Cart and Checkout: Adding items to the shopping cart, Editing and removing items from the cart. (Must have)\*
8. Reviews and Ratings: System for users to rate and review products and farmers. Display of reviews and ratings on product and farmer profiles. (Nice to have)\*
9. Options for users to subscribe to regular deliveries (weekly, bi-weekly, monthly). (Nice to have)
10. Order Management: Order creation, processing, and tracking, Order history and reordering options. (Must have)
11. Notifications for order status updates (confirmation, shipment, delivery). (Must have)
12. Flexible delivery options (date and time selection). (Nice to have)
13. Integration with delivery services or in-house logistics. (Must have)
14. Content Management: Recipe suggestions and cooking tips based on purchased products, Educational content on sustainable farming and healthy eating. (Nice to have)

---

## Slide 6: Requirements for User Profile Creation

### Requirements for User Profile Creation

1. **Basic Information:** Full Name, Email Address, Phone Number, Profile picture, Date Of Birth

2. **Address Information:** Home Address (Street, City, State, Zip Code), Delivery Instructions

3. **Payment Information**

4. Preferred Payment Method (Credit/Debit Card, Digital Wallet)

5. Billing Address (if different from Home Address)

6. **Preferences:** Dietary Preferences (Vegetarian, Vegan, Gluten-Free, etc.)

7. Subscription Preferences (Frequency, Box Type)

8. Communication Preferences (Email, SMS, Push Notifications)

9. **Order History:** List of Past Orders, Order Details (Products, Date, Amount), Reorder Options, Reviews and Ratings, Submitted Reviews, Rating History, Review Management (Edit/Delete)

[Image: User profile wireframe]

---

## Slide 7: Requirements for Farmer Profile Creation

### Requirements for Farmer Profile Creation

1. **Basic Information:** Full Name, Email Address, Phone Number, Profile picture, Date Of Birth

2. **Farm Information:** Farm Name, Farm Address (Street, City, State, Zip Code), Farm Description, Farming Practices (Organic, Sustainable, etc.), Farm Pictures and Videos

3. **Product Information:** List of Products Offered, Detailed Descriptions for Each Product, Pricing and Availability, Seasonal Availability

4. **Order Management:** Order History and Details, Current Orders, Order Fulfillment Status

5. **Payment Information:** Bank Account Details for Receiving Payments, Payment History

6. **Reviews and Ratings:** Customer Reviews, Overall Rating, Review Responses (Reply to Reviews)

[Image: Farmer profile wireframe]

---

## Slide 8: Requirements for Product Listing

### Requirements for Product Listing

**(adding, updating, and removing products)**

**User Interface:**

- Provide a user-friendly dashboard for farmers to manage their product listings.
- Include clear buttons and icons for adding, updating, and removing products.

**Adding Products:**

1. Form fields for product name, category, description, price, quantity, and seasonality.
2. Ability to upload multiple images of the product.

**Updating Products:**

1. Allow farmers to edit any field in their product listings.
2. Real-time updates to reflect changes immediately.
3. Notification system to inform customers of significant changes (price changes, out-of-stock updates).

**Removing Products:**

1. Simple process for removing products from the listing.
2. Confirmation prompt before final deletion to prevent accidental removal.
3. Option to archive products instead of deleting, allowing for reactivation later.

**Backend Requirements:**

_Database:_

1. Store detailed information for each product.
2. Ensure data consistency and integrity.

[Image: Product listing interface]

---

## Slide 9: Requirements for Availability and Price Management

### Requirements for Availability and Price Management

**User Interface:**

1. Dashboard section for managing product availability and pricing.
2. Visual indicators for low stock levels.

**Availability Management:**

1. Feature to update product quantities.
2. Option to mark products as out-of-stock.
3. Automated low-stock alerts to notify farmers.

**Pricing Management:**

1. Fields to set and update product prices.
2. Support for different pricing strategies (e.g., discounts, bulk pricing).
3. Price history tracking to help farmers analyze pricing trends.

**Backend Requirements:**

_Database:_

1. Track inventory levels and pricing changes.

[Image: Availability management interface]

---

## Slide 10: Requirements for Searching Products, Product Description

### Requirements for Searching Products, Product Description

**Browsing and Searching for Products (filters by category, seasonality, location, etc.)**

**User Interface:**

1. Search bar with autocomplete suggestions.
2. Filters for category, seasonality, location, price range, and other attributes, Sort options (e.g., by price, popularity, rating).

**Browsing Experience:**

1. Categorized product listings.
2. Visual representation of product availability based on seasonality.
3. Map view to locate products by farmer's location.

**Backend Requirements:**

- Database: Index products based on searchable attributes.

**Detailed Product Descriptions (nutritional information, origin, farming methods) - (Nice to Have)**

**User Interface:**

1. Extended form fields for adding detailed descriptions.
2. Sections for nutritional information, product origin, and farming methods.

**Backend Requirements:**

1. Database: Store detailed descriptions and additional metadata.

[Image: Search and browsing interface]

---

## Slide 11: Visual Slide

[Image: Visual content slide]

---

## Slide 12: User Journey

### User Journey

_(Highlighted items are the scope for KATA)_

| User Action                                              | System Response                                                                                              | Notes                                                                               |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| User visits the website or opens the app                 | Display homepage with options to sign up or log in, browse products, and view featured seasonal items        | Ensure a user-friendly and visually appealing interface                             |
| User signs up with email and password                    | Send verification email and prompt user to verify their account                                              | Include social media sign-up options for convenience                                |
| User logs in                                             | Redirect to personalized dashboard with user profile, past orders, and recommendations                       | Ensure secure login and encryption of user data                                     |
| User navigates to the product catalog                    | Display list of products with filters for seasonality, category, price, and farm location                    | Include high-quality images and detailed descriptions                               |
| User applies filters to find seasonal products           | Update product list based on applied filters and show relevant seasonal items                                | Ensure quick and responsive filtering                                               |
| User selects a product to view details                   | Display product details page with description, price, availability, and farm information                     | Include customer reviews and ratings                                                |
| User adds product to shopping cart                       | Update cart icon and show a confirmation message with the option to continue shopping or proceed to checkout | Provide clear feedback and easy navigation options                                  |
| User proceeds to checkout                                | Display checkout page with order summary, delivery options, and payment methods                              | Ensure secure payment processing and data protection                                |
| User enters delivery details and selects a delivery time | Validate delivery address and show available time slots                                                      | Include delivery instructions option for better service                             |
| User completes the payment                               | Process payment securely and show order confirmation with estimated delivery time                            | Send email/SMS confirmation and order details                                       |
| User tracks order status                                 | Provide real-time tracking updates on the order status page                                                  | Include notifications for important updates (e.g., order shipped, out for delivery) |
| User receives the order and leaves a review              | Prompt user to rate the product and leave feedback                                                           | Encourage reviews to build trust and improve service quality                        |
| User subscribes to a weekly delivery box                 | Allow customization of subscription preferences and confirm subscription details                             | Offer flexible subscription management options                                      |

---

## Slide 13: Farmer Journey

### Farmer Journey

_(Highlighted items are the scope for KATA)_

| Farmer Action                                   | System Response                                                                                                                          | Notes                                                                                            |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Farmer visits the website or opens the app      | Display homepage with options to sign up or log in, and information about the platform                                                   | Ensure clear information about benefits for farmers and a simple, user-friendly interface        |
| Farmer signs up with email and password         | Send verification email and prompt farmer to verify their account                                                                        | Include social media sign-up options for convenience and ensure secure account creation          |
| Farmer logs in                                  | Redirect to farmer dashboard with profile setup prompt                                                                                   | Ensure secure login and encryption of farmer data                                                |
| Farmer completes profile setup                  | Display profile fields (farm name, location, description, farming practices, contact details, etc.) and save information upon submission | Include an option to upload farm pictures and videos for better visibility                       |
| Farmer adds a new product listing               | Provide a form to enter product details (name, description, price, availability, seasonality) and upload images                          | Ensure an intuitive form layout and validation for required fields                               |
| Farmer tags product with seasonal availability  | Display season options and allow tagging of products with relevant seasons                                                               | Make sure seasonal tags are clear and easy to select                                             |
| Farmer updates product listing                  | Allow editing of product details, pricing, and availability                                                                              | Ensure quick and easy updates to keep product information current                                |
| Farmer views and manages orders                 | Show list of incoming orders with details (product, quantity, customer information, delivery date)                                       | Include order status management (pending, confirmed, shipped) and easy filtering/sorting options |
| Farmer confirms order and prepares for shipment | Update order status to confirmed and notify the customer                                                                                 | Provide guidance on packing and shipping best practices                                          |
| Farmer updates order status to shipped          | Notify customer with tracking information and update order status in the system                                                          | Integration with delivery services for real-time tracking is beneficial                          |
| Farmer checks payment history                   | Display detailed payment history with dates, amounts, and transaction IDs                                                                | Ensure clear and detailed financial records for transparency                                     |
| Farmer responds to customer reviews             | Notify farmer of new reviews and allow them to respond to feedback                                                                       | Encourage positive engagement with customers to build trust and loyalty                          |
| Farmer views analytics and reports              | Provide dashboard with sales metrics, popular products, customer demographics, and seasonal trends                                       | Ensure visual representation of data for easy interpretation and decision-making                 |
| Farmer participates in community events         | Allow farmers to list and manage events like farm tours or workshops                                                                     | Promote events to users and provide registration management tools                                |
| Farmer contacts customer support                | Provide easy access to customer support for any issues or inquiries                                                                      | Ensure responsive and helpful support to address farmer concerns quickly                         |

---

## Slide 14: Further AI Enhancements

### Further AI Enhancements - Example of GenAI Integration in the Farmer Journey

**Farmer logs in using voice command**

- System confirms login and presents dashboard

**Farmer wants to add a new product**

- System asks for product details via voice prompts or text input

**Farmer uploads a photo of the product**

- System analyzes image for quality and consistency

**Farmer receives AI-generated description for review**

- System displays generated description and allows edits

**Farmer checks inventory predictions**

- System shows demand forecast and inventory suggestions

**Farmer uses AI-generated marketing content**

- System provides ready-to-use content for social media and newsletters

[Image: AI integration illustration]

---

## Slide 15: Kata Challenge Expectations

### Kata Challenge: Expectations

- Aim to integrate GenAI capabilities across various phases of the SDLC, including Discovery, Design, Implementation, and Testing.
- Collaborate in roles such as BA, DEV, QA, PM, and others to apply AI throughout the project lifecycle.
- Choose one or two features for a complete end-to-end implementation that leverages AI.
- If time allows, explore additional features, but ensure to have a core working solution first.
- Don't worry about including every detail in the features; focus on a minimum viable product that works well.
- Develop a solution using AI capabilities, whether your end product is AI-based or not.

---

## Slide 16: For Your Consideration

### For Your Consideration:

- Prompt effectiveness
- Prompt technique applied
- Context
- Output expectations
- Test cases
- Less human intervention
- Design patterns
- Tech stack specific output
- Usage of guiding principles – SOLID, KISS, YAGNI
- Workable solution

[Image: Consideration points illustration]

---

## Slide 17: Artifacts to be Shared with Jury

### Artifacts to be Shared with Jury:

**Required:**

- Prompts
- Chat conversation
- Workable solution (Application)
- Requirements (user-stories with acceptance criteria)
- Code
- Test cases – manual/automation testing

**Nice to Have:**

- UML diagrams (flow, sequence, class diagrams, etc.)

[Image: Artifacts checklist]

---

## Slide 18: Closing

### Thank you!

---

_Document preserved from Farm_To_Table_MarketPlace-V1.0.pdf export_
