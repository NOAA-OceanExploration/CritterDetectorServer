# CritterDetector

This project is a web application that allows users to upload a video file and a CSV file of annotations. The application processes the video to detect unique organisms and compares these detections with the provided annotations. The results are displayed on the web interface, highlighting detections without annotations.

## Features

Upload a video file and an annotations CSV file.
Convert the video to MP4 format if necessary.
Detect unique organisms in the video using a PyTorch model.
Compare detections with annotations and highlight unannotated detections.
Display results on the web interface.
Download lists of all detections, annotated timecodes, and unannotated detections.
Demo Mode: Run a demo with predefined video and annotation data.

## Requirements

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/aquatic_detection_app.git
   cd aquatic_detection_app
   ```

2. **Create a virtual environment:**
   ```sh
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```sh
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```sh
     source venv/bin/activate
     ```

4. **Install the dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

1. **Set environment variables:**
   - Create a `.env` file in the root directory of your project and add the following line (optional but recommended for security):
     ```sh
     SECRET_KEY=your_secret_key
     ```

## Running the Application

1. **Set environment variables (if not using `.env`):**
   ```sh
   export FLASK_APP=run.py
   export FLASK_ENV=development
   ```

2. **Run the Flask application:**
   ```sh
   flask run
   ```

3. **Open your web browser and go to `http://127.0.0.1:5000`.**

## Usage

1. **Upload a video file and an annotations CSV file:**
   - Go to the homepage and use the form to select and upload your files.
   - The application will process the video and compare detections with the annotations.

2. **View the results:**
   - The results will be displayed on the web interface, showing detections, annotated timecodes, and unannotated detections.

3. **Download the lists:**
   - You can download the lists of all detections, annotated timecodes, and unannotated detections.

## Demo Mode
The demo mode allows you to experience the application's functionality with predefined data.

1. **Run the demo:**
Click the "Start Demo" button on the homepage.
The application will simulate processing the demo data with a progress bar.


2. **View the demo results:**

Predefined results will be displayed, showing detections, annotated timecodes, and unannotated detections.

## Demo Files
For the demo mode, ensure the following files are placed in the uploads/ directory:

- demo_video.mp4: The predefined video file used for the demo.
- demo_annotations.csv: The predefined CSV file containing annotations for the demo video.
- demo_detections.json: A JSON file with the predefined detection data.

## Project Structure

```
aquatic_detection_app/
│
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── model.py
│   ├── utils.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── styles.css
│
├── uploads/
│   ├── (uploaded video files)
│   ├── (uploaded CSV files)
│   ├── demo_video.mp4
│   ├── demo_annotations.csv
│   └── demo_detections.json
│
├── requirements.txt
├── config.py
├── run.py
└── README.md
```

## License

This project is licensed under the MIT License.
