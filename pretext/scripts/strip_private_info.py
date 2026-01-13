import os
import subprocess
import sys

import xml.etree.ElementTree as ET

"""Script to strip <solution> elements from <exercise> elements in XML files.

Part of a workflow to copy a private repository to a public one, stripping out private information.
"""


def is_git_repo_clean():
    """
    Checks if the current working directory is a clean Git repository
    (i.e., has no uncommitted or untracked changes).
    Returns True if clean, False otherwise.
    """
    try:
        # Run 'git status --porcelain' to get a clean, script-friendly output.
        # It returns an empty string if the repository is clean.
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        return not result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Handle cases where git command fails or is not found.
        # Treat this as a non-clean state for safety.
        print(
            "Warning: Could not check git status. Assuming repository is not clean.",
            file=sys.stderr,
        )
        return False


def strip_solutions_from_xml_files(directory):
    """
    Finds all XML files in a directory and removes <solution> elements
    that are children of <exercise> elements.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ptx"):
                modified = False
                filepath = os.path.join(root, file)
                try:
                    tree = ET.parse(filepath)
                    root_element = tree.getroot()

                    for xpath in ['.//exercise', './/exercise/task']:
                        for elt in root_element.findall(xpath):
                            for child in ['solution','answer']:
                                for sol in elt.findall(child):
                                    elt.remove(sol)
                                    modified = True

                    # Write the modified XML back to the file
                    # The 'short_empty_elements' is a nice-to-have for cleaner XML
                    if modified:
                        tree.write(
                            filepath,
                            encoding="UTF-8",
                            xml_declaration=True,
                            short_empty_elements=True,
                        )
                        print(f"Processed: {filepath}")
                    else:
                        print(f"No changes made to: {filepath}")

                except ET.ParseError as e:
                    print(f"Skipping invalid XML file {filepath}: {e}")


if __name__ == "__main__":
    # This doesn't work right now because the GitHub Actions runner doesn't have a clean repo.
    # if not is_git_repo_clean():
    #     print(
    #         "Error: The Git repository is not clean. Please commit or stash your changes before running this script.",
    #         file=sys.stderr,
    #     )
    #     sys.exit(1)

    # If the repository is clean, proceed with the main task.
    strip_solutions_from_xml_files(".")
