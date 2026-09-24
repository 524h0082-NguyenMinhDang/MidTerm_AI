# Sokoban Game

A Python Sokoban game built with Pygame.

## Requirements

- Python 3.8 or later
- Windows PowerShell or Command Prompt

## Setup

1. Open a terminal in the project folder:

   ```powershell
   cd e:\baitap\AI\MidTerm
   ```

2. Create a virtual environment:

   ```powershell
   python -m venv venv
   ```

3. Activate the virtual environment.

   **PowerShell:**

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   **Command Prompt:**

   ```bat
   venv\Scripts\activate.bat
   ```

4. Install Pygame:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install pygame
   ```

   You can also install the version specified by the project requirements file:

   ```powershell
   python -m pip install -r requiement.txt
   ```

## Run the Game

Make sure the virtual environment is active, then run:

```powershell
python main.py
```

To start the game with a specific map, pass the map file as an argument:

```powershell
python main.py map\1.txt
```

## Deactivate the Virtual Environment

When you finish playing, deactivate the virtual environment with:

```powershell
deactivate
```
