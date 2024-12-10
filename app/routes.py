import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from owl_highlighter import OWLHighlighter
import base64
from io import BytesIO
from app import app

# Initialize the highlighter
highlighter = OWLHighlighter(score_threshold=0.85)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'video' not in request.files:
            print("No video file in request")  # Debug log
            return jsonify({'error': 'No video file provided'}), 400

        video = request.files['video']
        print(f"Received file: {video.filename}")  # Debug log

        if video.filename == '':
            print("Empty filename")  # Debug log
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(video.filename):
            print(f"File type not allowed: {video.filename}")  # Debug log
            return jsonify({'error': 'Invalid video file type'}), 400

        # Save video file
        video_filename = secure_filename(video.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video.save(video_path)
        print(f"Saved file to: {video_path}")  # Debug log

        try:
            # Convert video to MP4 if needed
            print("Converting video to MP4...")
            mp4_path = convert_to_mp4(video_path)
            print(f"Converted to MP4: {mp4_path}")  # Debug log

            # Process video with OWLHighlighter
            print("Processing video with OWLHighlighter...")
            result = highlighter.process_video(
                video_path=mp4_path
            )

            # Process results
            print("Processing results...")
            processed_data = process_results(result)
            print("Results processed successfully.")
            return jsonify(processed_data)

        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
            if 'mp4_path' in locals() and mp4_path != video_path and os.path.exists(mp4_path):
                os.remove(mp4_path)

    except Exception as e:
        print(f"Error processing video: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

def process_results(result):
    """Helper function to process OWLHighlighter results"""
    # Create timeline visualization
    timeline_path = os.path.join(app.config['UPLOAD_FOLDER'], 'timeline.png')
    highlighter.create_timeline(result, timeline_path)

    try:
        # Convert detections to JSON-serializable format
        detections = []
        for det in result.detections:
            buffered = BytesIO()
            det.image_patch.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            detection = {
                'time': float(det.timestamp),
                'description': det.label,
                'confidence': float(det.confidence),
                'image': img_str,
                'bbox': [float(x) for x in det.bbox],
                'frame_number': int(det.frame_number)
            }
            detections.append(detection)

        # Read timeline image
        with open(timeline_path, 'rb') as f:
            timeline_base64 = base64.b64encode(f.read()).decode()

        return {
            'video_info': {
                'name': result.video_name,
                'fps': result.fps,
                'frame_count': result.frame_count,
                'duration': result.duration
            },
            'detections': detections,
            'timeline_image': timeline_base64
        }

    finally:
        if os.path.exists(timeline_path):
            os.remove(timeline_path)

if __name__ == '__main__':
    app.run(debug=True)
