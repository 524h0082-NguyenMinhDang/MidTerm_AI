import sys
from gui import SokobanGUI

def main():
    map_file = sys.argv[1] if len(sys.argv) > 1 else None
    app = SokobanGUI(map_path=map_file)
    app.run()

if __name__ == "__main__":
    main()