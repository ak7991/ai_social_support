import os
from pathlib import Path

def save_uploaded_file(uploadedfile):
    # Create target directory if it doesn't exist
    save_folder = "uploaded_files"
    Path(save_folder).mkdir(parents=True, exist_ok=True)
    
    # Construct the full file path
    save_path = Path(save_folder, uploadedfile.name)
    
    # Write the file to disk in binary mode
    with open(save_path, "wb") as f:
        f.write(uploadedfile.getbuffer())
    
    return True
