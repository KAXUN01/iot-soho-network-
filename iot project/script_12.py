# Create the final project archive
import zipfile
import os

def create_project_archive():
    """Create a zip archive of the complete project"""
    
    archive_name = f"{project_name}.zip"
    
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all directories and files
        for root, dirs, files in os.walk(project_name):
            for file in files:
                file_path = os.path.join(root, file)
                # Get the relative path for the archive
                archive_path = os.path.relpath(file_path, project_name)
                zipf.write(file_path, archive_path)
    
    # Get archive size
    archive_size = os.path.getsize(archive_name) / (1024 * 1024)  # Size in MB
    
    return archive_name, archive_size

archive_name, size = create_project_archive()

print(f"\n🎉 PROJECT CREATION COMPLETE!")
print("="*50)
print(f"Archive: {archive_name}")
print(f"Size: {size:.2f} MB")
print(f"Total Files: {len([f for _, _, files in os.walk(project_name) for f in files])}")

# List all created files
print("\n📁 Project Structure:")
for root, dirs, files in os.walk(project_name):
    level = root.replace(project_name, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

print(f"\n✅ Archive created: {archive_name}")