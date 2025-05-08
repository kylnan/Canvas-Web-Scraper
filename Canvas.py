from canvasapi import Canvas
import os
import requests
from datetime import datetime

API_URL = "https://canvas.eee.*.edu" # * is a wildcard, change this to your uni's domain.
API_KEY = "your api key here"  # Replace with your actual token

ALLOWED_EXTENSIONS = ['.pdf', '.zip', '.docx']
LOG_FILE = "canvas_download_log.txt"

canvas = Canvas(API_URL, API_KEY)
user = canvas.get_current_user()
courses = user.get_courses(enrollment_state='all')

base_folder = r"desired download path here"  # Replace with your desired download path
# Example: base_folder = r"C:\Users\YourUsername\Downloads\CanvasFiles"
os.makedirs(base_folder, exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with open(LOG_FILE, "a") as log_file:
        log_file.write(line + "\n")

def has_allowed_extension(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def download_file(file_obj, folder_path):
    try:
        file_path = os.path.join(folder_path, file_obj.display_name)
        if not os.path.exists(file_path):
            r = requests.get(file_obj.url, stream=True)
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            log(f"Downloaded: {file_obj.display_name}")
        else:
            log(f"Already exists: {file_obj.display_name}")
    except Exception as e:
        log(f"Failed to download {file_obj.display_name}: {e}")

for course in courses:
    log(f"Processing course: (ID: {course.id})")
    try:
        # Process course folders (existing functionality)
        folders = list(course.get_folders())
        for folder in folders:
            folder_files = folder.get_files()
            rel_folder_path = folder.full_name.replace("course files", "").strip("/")
            folder_path = os.path.join(base_folder, f"{course.id}".replace("/", "_"), rel_folder_path)
            os.makedirs(folder_path, exist_ok=True)

            for f in folder_files:
                if has_allowed_extension(f.display_name):
                    download_file(f, folder_path)

        # Process assignments and submissions
        log(f"Fetching assignments for course: {course.id}")
        assignments = course.get_assignments()
        for assignment in assignments:
            log(f"Processing assignment: {assignment.name} (ID: {assignment.id})")
            submissions = assignment.get_submissions()
            for submission in submissions:
                if submission.attachments:
                    for attachment in submission.attachments:
                        file_name = attachment['filename']
                        file_url = attachment['url']
                        if has_allowed_extension(file_name):
                            submission_folder = os.path.join(base_folder, f"{course.id}".replace("/", "_"), "Submissions", f"{assignment.id}")
                            os.makedirs(submission_folder, exist_ok=True)
                            file_path = os.path.join(submission_folder, file_name)
                            if not os.path.exists(file_path):
                                try:
                                    r = requests.get(file_url, stream=True)
                                    with open(file_path, 'wb') as f:
                                        for chunk in r.iter_content(1024):
                                            f.write(chunk)
                                    log(f"Downloaded submission file: {file_name}")
                                except Exception as e:
                                    log(f"Failed to download submission file {file_name}: {e}")
                            else:
                                log(f"Submission file already exists: {file_name}")

    except Exception as e:
        log(f"Error in course '{course.id}': {e}")
