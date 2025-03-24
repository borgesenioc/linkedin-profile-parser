# app.py
from flask import Flask, send_from_directory
import os

# Import Blueprints
from convert import convert_bp
from checkSnapshot import check_snapshot_bp

app = Flask(__name__, static_folder=None)  # We'll manually serve the 'public' folder
PORT = int(os.environ.get("PORT", 3000))

# Register the Blueprints with a URL prefix
app.register_blueprint(convert_bp, url_prefix='/api')
app.register_blueprint(check_snapshot_bp, url_prefix='/api')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    """
    Serve static files from /public,
    similar to: app.use(express.static('public')) in Express.
    """
    if not path:
        # Serve the default index.html if no path is provided
        return send_from_directory('public', 'index.html')
    else:
        # If the path is a real file, serve it; otherwise, serve index.html
        file_path = os.path.join('public', path)
        if os.path.isfile(file_path):
            return send_from_directory('public', path)
        else:
            return send_from_directory('public', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)