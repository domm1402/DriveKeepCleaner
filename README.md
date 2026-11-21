# DriveKeepCleaner

A Windows desktop tool to select a target folder/drive, list items to preserve, preview top-level cleanup candidates, and send unchecked items to the Recycle Bin.

## Safety
- Operates on the selected folder's top-level entries, not an unrestricted recursive wipe.
- Protects Windows/system folders by name and blocks cleaning the C: root.
- Review preview before cleanup.
- Uses Recycle Bin via Send2Trash.

## Build
GitHub Actions builds a Windows EXE on pushes to main or via Actions > Build Windows EXE > Run workflow. Download the workflow artifact after it finishes.
