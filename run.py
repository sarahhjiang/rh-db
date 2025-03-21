from routes import app  # Import the app instance from routes.py

# Only run the app if this script is executed directly
if __name__ == '__main__':
    app.run(debug=True)  # You can set debug=True for development purposes

    app.run()
