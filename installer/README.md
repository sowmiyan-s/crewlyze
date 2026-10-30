# Crewlyze Windows Inno Setup Installer

This directory contains the files and automation needed to build a native Windows standalone installer (`.exe`) for **Crewlyze**.

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
   - Automatically detects Python 3.10 – 3.13 on the target machine.
   - If Python is not installed, it automatically downloads and installs Python with PATH integration.
   - Configures an isolated virtual environment (`.crewlyze\venv`) and provisions all required machine-learning and data analysis packages (`requirements.txt`) using prebuilt wheels.

4. **Desktop & Start Menu Shortcuts**:
   - Creates a Start Menu folder and Desktop shortcut with high-resolution multi-size icons.
   - Provides a "Crewlyze Setup & Repair" shortcut in case packages need reinstallation.
   - Includes a clean uninstaller that removes shortcuts and PATH entries cleanly.

5. **Self-Update & Release Checking**:
   - Ships with `updater.ps1` and `check_release.ps1` to query GitHub Releases for newer builds and update in-place without manual file replacement.

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
```text
installer\dist\Crewlyze_Setup_v1.2.3.exe
```

---

## 🚀 Publishing to GitHub Releases

1. Run `npm run build:installer` to produce `Crewlyze_Setup_v1.2.3.exe`.
2. Go to your GitHub repository: [sowmiyan-s/crewlyze](https://github.com/sowmiyan-s/crewlyze).
3. Create a new Release (e.g. `v1.2.3`).
4. Attach `Crewlyze_Setup_v1.2.3.exe` into the Release Assets.
5. Users can simply download `Crewlyze_Setup_v1.2.3.exe`, click **Install**, and type `crewlyze` in CMD!
