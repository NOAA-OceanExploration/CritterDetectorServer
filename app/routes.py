from flask import render_template, request, jsonify, send_file, current_app
from app import app
from werkzeug.utils import secure_filename
import os
import time
import json

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    testing_mode = current_app.config.get('TESTING', False)
    if 'video' not in request.files or 'csv' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    video = request.files['video']
    csv_file = request.files['csv']

    if video.filename == '' or csv_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    video_filename = secure_filename(video.filename)
    csv_filename = secure_filename(csv_file.filename)

    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    video.save(video_path)
    csv_file.save(csv_path)

    mp4_video_path = convert_to_mp4(video_path)
    detections, annotated, unannotated = process_video(mp4_video_path, csv_path, testing=testing_mode)

    return jsonify({
        'detections': detections,
        'annotated': annotated,
        'unannotated': unannotated
    })

@app.route('/demo', methods=['GET'])
def demo():
    # Path to the demo JSON file
    demo_data_path = os.path.join(app.config['UPLOAD_FOLDER'], 'demo', 'demo_detections.json')
    
    # Simulate processing time with a 2-minute progress bar
    time.sleep(120)  # Simulate 2 minutes of processing time

    # Load the predefined detection data
    with open(demo_data_path, 'r') as f:
        detections_data = json.load(f)

    # Return the predefined results as if they were processed
    return jsonify(detections_data)

@app.route('/download/<list_type>', methods=['GET'])
def download(list_type):
    list_types = ['detections', 'annotated', 'unannotated']
    if list_type not in list_types:
        return jsonify({'error': 'Invalid list type'}), 400

    # Path to the requested data
    list_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{list_type}.csv")

    # Check if the file exists
    if not os.path.exists(list_file_path):
        return jsonify({'error': 'File not found'}), 404

    # Send the file for download
    return send_file(list_file_path, as_attachment=True)
