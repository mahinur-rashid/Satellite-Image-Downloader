from flask import Flask, render_template, request, jsonify
import os
import ee
from config import COUNTRIES, UPLOAD_FOLDER
from gee_utils import download_images, validate_resolution
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()
PROJECT_ID = os.getenv('project')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'downloads')

# Basic Earth Engine initialization
try:
    ee.Initialize(project=PROJECT_ID)
    print("✓ Earth Engine initialized")
except:
    print("Authenticating Earth Engine...")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# Create downloads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('download_form.html', countries=COUNTRIES)

@app.route('/validate-resolution', methods=['POST'])
def validate_res():
    country = request.form.get('country')
    resolution = int(request.form.get('resolution'))
    is_valid, suggested_res = validate_resolution(country, resolution)
    return jsonify({
        'valid': is_valid,
        'suggested_resolution': suggested_res
    })

@app.route('/download', methods=['POST'])
def download():
    countries = request.form.getlist('countries')
    start_year = int(request.form.get('start_year'))
    end_year = int(request.form.get('end_year'))
    resolution = int(request.form.get('resolution'))
    
    try:
        results = download_images(countries, start_year, end_year, 
                                resolution, app.config['UPLOAD_FOLDER'])
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({"status": "error", "message": "File too large (max 64MB)"}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Server error, please try with a lower resolution"}), 500

if __name__ == '__main__':
    app.run(debug=True)
