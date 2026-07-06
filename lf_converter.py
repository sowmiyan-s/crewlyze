import os

file_path = os.path.join(os.getcwd(), 'bin', 'crewlyze.js')
print(f"Reading {file_path}...")
with open(file_path, 'rb') as f:
    content = f.read()

# Replace CRLF with LF
lf_content = content.replace(b'\r\n', b'\n')

print(f"Writing {file_path} with LF line endings...")
with open(file_path, 'wb') as f:
    f.write(lf_content)

print("Done!")
