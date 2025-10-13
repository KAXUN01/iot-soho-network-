import os
import zipfile
import shutil

# Create main project directory structure
project_name = "adaptive_zero_trust_iot_framework"
directories = [
    f"{project_name}/src/onboarding",
    f"{project_name}/src/trust_management",
    f"{project_name}/src/sdn_controller", 
    f"{project_name}/src/honeypot",
    f"{project_name}/src/database",
    f"{project_name}/src/utils",
    f"{project_name}/config",
    f"{project_name}/certificates",
    f"{project_name}/logs",
    f"{project_name}/tests",
    f"{project_name}/docs",
    f"{project_name}/scripts"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    
print("Created project directory structure:")
for directory in directories:
    print(f"  {directory}")