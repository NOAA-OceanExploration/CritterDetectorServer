from flask import render_template, request, jsonify, send_file
from app import app
from app.utils import convert_to_mp4, process_video
from werkzeug.utils import secure_filename
import os
import pandas as pd

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # Check if the post request has the file part
    if 'video' not in request.files or 'csv' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    video = request.files['video']
    csv_file = request.files['csv']

    # If the user does not select a file, the browser also submits an empty part without filename
    if video.filename == '' or csv_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Secure filenames
    video_filename = secure_filename(video.filename)
    csv_filename = secure_filename(csv_file.filename)

    # Save files to the upload folder
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    video.save(video_path)
    csv_file.save(csv_path)

    # Convert video to MP4 if necessary
    mp4_video_path = convert_to_mp4(video_path)
    
    # Process the video and annotations
    detections, annotated, unannotated = process_video(mp4_video_path, csv_path)

    # Return the results as JSON
    return jsonify({
        'detections': detections,
        'annotated': annotated,
        'unannotated': unannotated
    })

@app.route('/download/<list_type>', methods=['GET'])
def download(list_type):
    list_types = ['detections', 'annotated', 'unannotated']
    if list_type not in list_types:
        return jsonify({'error': 'Invalid list type'}), 400

    # Assuming the lists are stored in session or temporary files
    list_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{list_type}.csv")

    # Send the file for download
    return send_file(list_file_path, as_attachment=True)
