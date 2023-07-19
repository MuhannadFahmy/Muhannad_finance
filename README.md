# Muhannad_finance
a web application called "Finance" that allows to learn stock trading in a controlled environment


The project is about building a web application called "Finance" that allows to learn stock trading in a controlled environment. Users to register, log in, buy and sell stocks, view their portfolio, transaction history, and make certain customizations. The application uses Flask, SQLite, HTML templates, Restful API and various Python libraries.

The project consists of several files and folders, including app.py, helpers.py, requirements.txt, static/, and templates/.

In app.py, the main Flask application file, the routes for registering, logging in, logging out, quoting stock prices, buying and selling stocks, viewing the portfolio, transaction history, and making customizations are implemented. The file interacts with the database using SQLite and CS50's SQL module. The implementation includes rendering HTML templates, handling forms, querying the database, and providing appropriate responses based on user actions.

helpers.py contains helper functions used in app.py. These functions include formatting values as USD, validating user input, generating apologies, and implementing login requirements.

requirements.txt lists the required Python packages and versions needed to run the application.

The static/ folder contains static files such as CSS stylesheets and images used in the application's frontend.

The templates/ folder contains HTML templates that define the structure and appearance of the web pages. Templates include login, register, quote, buy, sell, index, history, and apology pages.
