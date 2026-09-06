# Crewlyze Windows Inno Setup Installer

This directory contains the files and automation needed to build a native Windows installer (`.exe`) for **Crewlyze**.

## 📦 What the Installer Does

1. **Native Windows Installation**:
   - Packages the complete Crewlyze application into a compact installer (`Crewlyze_Setup_v1.2.3.exe`).
   - Installs to `%ProgramFiles%\Crewlyze` (for All Users) or `%LocalAppData%\Programs\Crewlyze` (for Current User).

2. **Global System Command (`crewlyze`)**:
   - Automatically registers Crewlyze in the Windows system `PATH`.
   - Any user can open Command Prompt (`cmd.exe`) or PowerShell from any folder and run:
     ```cmd
     crewlyze
     ```
   - Instantly starts the local FastAPI server and launches the web dashboard at `http://127.0.0.1:8000`.

3. **Automated Python & Dependency Setup**:
   - Automatically detects Python 3.9 – 3.13 on the target machine.
   - If Python is not installed, it automatically downloads and installs Python 3.11 with PATH integration.
   - Configures an isolated virtual environment (`.crewlyze\venv`) and provisions all required machine-learning and data analysis packages (`requirements.txt`).

4. **Desktop & Start Menu Shortcuts**:
   - Creates a Start Menu folder and Desktop shortcut with high-resolution multi-size icons.
   - Provides a "Crewlyze Setup & Repair" shortcut in case packages need reinstallation.
   - Includes a clean uninstaller that removes shortcuts and PATH entries cleanly.

---

## 🛠️ How to Build the Installer

### Option A: Using npm script
```cmd
npm run build:installer
```

### Option B: Running the batch builder
```cmd
installer\build_installer.bat
```

### Option C: Compiling directly with Inno Setup CLI
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\crewlyze_installer.iss
```

The output installer executable will be generated at:
`installer\dist\Crewlyze_Setup_v1.2.3.exe`

---

## 🚀 Publishing to GitHub Releases (Open Source)

1. Run `npm run build:installer` to produce `Crewlyze_Setup_v1.2.3.exe`.
2. Go to your GitHub repository: [sowmiyan-s/crewlyze](https://github.com/sowmiyan-s/crewlyze).
3. Create a new Release (e.g. `v1.2.3`).
4. Drag and drop `Crewlyze_Setup_v1.2.3.exe` into the Release Assets.
5. Users can simply download `Crewlyze_Setup_v1.2.3.exe`, click **Install**, and type `crewlyze` in CMD!

---

## 🔄 Self-Update & Release Checking

Crewlyze now includes automated release detection and in-place updating:

1. **Installer Pre-flight Check**:
   - When running the installer, it queries GitHub Releases for newer builds.
   - If an update exists, it prompts the user to download the latest installer directly.

2. **CLI Terminal Update**:
   - Run from anywhere in Command Prompt or PowerShell:
     ```cmd
     crewlyze update
     ```
   - Automatically checks GitHub Releases, fetches the new `.exe` setup installer, and updates the installation in-place.

3. **Start Menu Shortcut**:
   - A **Check for Updates** shortcut is installed in the Start Menu folder for one-click updates.
