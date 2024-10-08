import os
import time
import json
import pandas as pd
from io import StringIO
from flask import Flask, render_template, request, jsonify, send_file, current_app, send_from_directory, abort
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store detections (in a real application, use a database)
global_detections = []

def convert_to_mp4(video_path):
    """
    Convert the input video file to MP4 format if it is not already in MP4 format.
    """
    if video_path.lower().endswith('.mp4'):
        return video_path
    
    mp4_video_path = os.path.splitext(video_path)[0] + '.mp4'
    
    video = VideoFileClip(video_path)
    video.write_videofile(mp4_video_path, codec='libx264', audio_codec='aac')
    video.close()
    
    return mp4_video_path

def process_video(video_path, csv_path, testing=False):
    """
    Process the video to detect organisms and compare the detections with annotations.
    """
    # Example detections (in a real application, these would be generated by your model)
    detections = [
        {"id": 1, "time": 12.5, "description": "Organism", "image": "Fake_Fish_Cropped.png"},
        {"id": 2, "time": 45.3, "description": "Organism", "image": "Fish_0.png"},
        {"id": 3, "time": 78.6, "description": "Fish", "image": "Fish_1_1.png"},
        {"id": 4, "time": 100.2, "description": "Unidentified", "image": "Fish_1_2.png"},
        {"id": 5, "time": 123.4, "description": "Unidentified", "image": "Fish_2.png"},
        {"id": 6, "time": 145.6, "description": "Unidentified", "image": "Fish_3.png"}
    ]
    
    annotations_df = pd.read_csv(csv_path)
    annotated_times = annotations_df['timecode'].tolist()
    total_annotations = len(annotated_times)

    annotated = []
    unannotated = []

    for detection in detections:
        is_annotated = any(abs(detection['time'] - ann_time) < 1 for ann_time in annotated_times)
        detection['is_annotated'] = is_annotated
        if is_annotated:
            annotated.append(detection)
        else:
            unannotated.append(detection)

    total_annotated_detected = len(annotated)
    total_unannotated_detected = len(unannotated)

    return detections, annotated, unannotated, total_annotations, total_annotated_detected, total_unannotated_detected

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
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
    detections, annotated, unannotated, total_annotations, total_annotated_detected, total_unannotated_detected = process_video(mp4_video_path, csv_path)

    global global_detections
    global_detections = detections

    return jsonify({
        'detections': detections,
        'annotated': annotated,
        'unannotated': unannotated,
        'total_annotations': total_annotations,
        'total_annotated_detected': total_annotated_detected,
        'total_unannotated_detected': total_unannotated_detected
    })

@app.route('/demo', methods=['GET'])
def demo():
    demo_data_path = os.path.join(app.config['UPLOAD_FOLDER'], 'demo', 'demo_detections.json')
    
    # Simulate processing time
    time.sleep(5)  # Reduced from 120 seconds to 5 seconds for testing purposes

    with open(demo_data_path, 'r') as f:
        detections_data = json.load(f)
    
    if 'total_annotations' not in detections_data:
        total_annotations = len(detections_data['annotated'])
        total_annotated_detected = len(detections_data['annotated'])
        total_unannotated_detected = len(detections_data['unannotated'])
        detections_data.update({
            'total_annotations': total_annotations,
            'total_annotated_detected': total_annotated_detected,
            'total_unannotated_detected': total_unannotated_detected
        })

    global global_detections
    global_detections = detections_data['detections']

    return jsonify(detections_data)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    if filename.startswith('uploads/'):
        filename = filename[8:]

    base_dir = app.config['UPLOAD_FOLDER']
    full_path = os.path.join(base_dir, filename)
    app.logger.debug(f"Full path: {full_path}")

    if not os.path.exists(full_path):
        app.logger.debug(f"File not found: {full_path}")
        return abort(404)

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)

    return send_from_directory(directory, filename)

@app.route('/reject_annotation', methods=['POST'])
def reject_annotation():
    data = request.json
    detection_id = data.get('id')
    
    global global_detections
    
    # Find the detection with the given id and mark it as rejected
    for detection in global_detections:
        if detection['id'] == detection_id:
            detection['rejected'] = True
            break
    
    return jsonify({
        'success': True,
        'message': f'Annotation with id {detection_id} rejected'
    })

@app.route('/edit_description', methods=['POST'])
def edit_description():
    data = request.json
    detection_id = data.get('id')
    new_description = data.get('newDescription')
    
    global global_detections
    
    # Find the detection with the given id and update its description
    for detection in global_detections:
        if detection['id'] == detection_id:
            detection['description'] = new_description
            detection['edited'] = True
            break
    
    return jsonify({
        'success': True,
        'message': f'Description for detection with id {detection_id} updated to "{new_description}"'
    })

@app.route('/get_updated_detections', methods=['GET'])
def get_updated_detections():
    global global_detections
    
    # Filter out rejected detections
    active_detections = [d for d in global_detections if not d.get('rejected', False)]
    
    annotated = [d for d in active_detections if d.get('is_annotated', False)]
    unannotated = [d for d in active_detections if not d.get('is_annotated', False)]
    
    return jsonify({
        'detections': active_detections,
        'annotated': annotated,
        'unannotated': unannotated,
        'total_annotations': len(annotated),
        'total_annotated_detected': len(annotated),
        'total_unannotated_detected': len(unannotated)
    })

@app.route('/download/<list_type>', methods=['GET'])
def download(list_type):
    global global_detections

    list_types = ['detections', 'annotated', 'unannotated']
    if list_type not in list_types:
        return jsonify({'error': 'Invalid list type'}), 400

    # Filter detections based on list_type
    if list_type == 'detections':
        data = global_detections
    elif list_type == 'annotated':
        data = [d for d in global_detections if d.get('is_annotated', False) and not d.get('rejected', False)]
    else:  # unannotated
        data = [d for d in global_detections if not d.get('is_annotated', False) and not d.get('rejected', False)]

    # Create a DataFrame
    df = pd.DataFrame(data)
    
    # Add columns to indicate if a detection was edited or rejected
    df['edited'] = df['edited'].fillna(False)
    df['rejected'] = df['rejected'].fillna(False)

    # Convert DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Send the CSV file
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        attachment_filename=f'{list_type}.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)