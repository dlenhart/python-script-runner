# Python Script Runner

A desktop utility for running Python scripts. Define scripts in JSON manifest files and the app gives each one its own tab with a console, run/stop controls, logging, and status indicators. Also includes a Script Manager to manage manifest files.

## Features

- Tabbed interface with a live console output window per script
- Start and stop scripts with one click
- Add scripts manually by dropping a `.manifest.json` file into `scripts/manifests/`
- Add scripts by using the `Script Manager` by clicking the manage button
- Reorder tabs from the script manager via drag-and-drop
- Auto-creates a `.venv` and installs dependencies on first launch
- Per-script requirements: place a `<script_name>.requirements.txt` with your script for automatic installation

## Getting Started

Python 3.8+ and tkinter (included with most Python installs) required

```bash
python PythonScriptRunner.py
```

Or use the included launcher:

```bash
./launch_gui.sh
```

On first launch the app creates a virtual environment and installs dependencies from `requirements.txt`.

## Adding Scripts

Create a manifest file in `scripts/manifests/` with the `.manifest.json` extension:

```json
{
  "tab_name": "My Script",
  "script_name": "My Script",
  "script_file": "scripts/my_script.py",
  "description": "A short description of what the script does.",
  "enabled": true,
  "order": 1,
  "args": [],
  "logging": false,
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `tab_name` | Yes | Display name on the tab |
| `script_name` | No | Name shown in the console (defaults to `tab_name`) |
| `script_file` | Yes | Path to the script, relative to the project root |
| `description` | No | Shown in the console and as a tab tooltip |
| `enabled` | No | Set to `false` to hide the tab (default `true`) |
| `order` | No | Tab display order, lower numbers appear first (default `999`) |
| `args` | No | List of command-line arguments passed to the script |
| `logging` | No | Enable logging to a file |

You can also create and edit manifests from the **Manage** button in the app.

