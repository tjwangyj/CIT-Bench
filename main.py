"""Launch the standalone chiplet benchmark viewer."""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.data_manager import DEFAULT_BENCHMARK


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-dir', type=Path, default=DEFAULT_BENCHMARK,
                        help='Benchmark root or a single case directory')
    args = parser.parse_args()
    from PySide6.QtWidgets import QApplication
    from ui.main_window import PhysicalDesignPlatform
    app = QApplication([sys.argv[0]])
    app.setStyle('Fusion')
    window = PhysicalDesignPlatform(args.benchmark_dir)
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
