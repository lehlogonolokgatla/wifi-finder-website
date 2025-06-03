Project Title:
Flask Cafe Finder: A Directory of Work-Friendly Cafes

Short Description:
A web application built with Flask that serves as a dynamic directory for cafes, highlighting their amenities crucial for remote work or study. Users can browse, search by location, and (with an API key) contribute new cafe entries or update existing ones.

Purpose: To provide a web-based directory for discovering cafes based on their amenities, such as Wi-Fi availability, power sockets, toilet access, and suitability for calls. Users can search for cafes, and administrators (or authenticated users with API key) can add, update, and delete cafe entries.

Core Functionality:

Cafe Listing & Search:

Displays a comprehensive list of all registered cafes on the home page.
Allows users to search for cafes by location, with partial and case-insensitive matching.
Shows key amenities (Wi-Fi, sockets, toilets, etc.) for each cafe.
Cafe Management (Admin/API Access):

Add New Cafes: Provides a dedicated form for adding new cafe entries, including name, location, map URL, image upload, number of seats, coffee price, and various boolean amenities (has toilet, has Wi-Fi, has sockets, can take calls).
Image Upload: Supports local image uploads for cafe entries, storing them in a static/uploads directory and handling filename security and uniqueness.
Update Coffee Price: An API endpoint (PATCH request) to modify the coffee price for any given cafe.
Delete Cafe: An API endpoint (POST request) to remove a cafe entry from the database. This endpoint includes a basic API key authentication and also handles the deletion of associated uploaded image files.
Data Persistence:

All cafe information is stored persistently in an SQLite database (cafes.db).
Utilizes Flask-SQLAlchemy for seamless object-relational mapping, simplifying database interactions.
Technical Stack:

Backend Framework: Flask (Python web microframework)
Database: SQLite (cafes.db)
Object-Relational Mapper (ORM): Flask-SQLAlchemy
File Uploads: Werkzeug's secure_filename for secure file handling, os module for file system operations, and random for unique filenames.
API Design: Implements RESTful principles for update and delete operations (PATCH for update, POST for delete with basic key check).
Frontend (Implied): HTML (for structure), CSS (for styling), and JavaScript (for dynamic interactions, especially with API endpoints).

Features:
Comprehensive Cafe Listings: Displays all registered cafes with details on amenities like Wi-Fi, sockets, toilet access, call-friendliness, and coffee price.
Location-Based Search: Efficiently find cafes by searching for locations (case-insensitive and partial matching).
New Cafe Submission: A user-friendly form allows for adding new cafes, including image uploads.
Robust Image Handling: Securely stores uploaded cafe images, generates unique filenames, and cleans up images upon cafe deletion.
API Endpoints: Includes API endpoints for programmatic updates (e.g., PATCH for price) and deletions (with basic API key authentication).
Persistent Data: All cafe information is stored in an SQLite database.


How it Works (Technical Overview):
The application's backend is powered by Flask, handling web requests and interacting with the database.
SQLAlchemy is used as the ORM to manage the SQLite database (cafes.db), defining the Cafe model and facilitating data storage and retrieval.
File Uploads are managed by Flask and Werkzeug, ensuring files are saved securely with unique names in static/uploads/.
Frontend HTML templates (index.html, add_cafe.html) render the user interface.
JavaScript (implied for PATCH/DELETE/AJAX search if present) handles dynamic interactions by making requests to Flask API endpoints.
The /search route uses func.lower() and like() for flexible, case-insensitive location searches.
Deletion of cafes via /delete-cafe-web requires a simple API key check and includes logic to remove the corresponding image file from the server.
