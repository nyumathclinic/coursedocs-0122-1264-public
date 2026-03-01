#!/usr/bin/env python3


import os
import os.path
import xml.etree.ElementTree as ET

def generate_pretext_xml_tree(path):
    """
    Walks through the specified directory, finds PreTeXt files, and
    generates a PreTeXt project XML tree with all necessary targets.

    Args:
        path (str): The path to the directory containing the source files.
    
    Returns:
        xml.etree.ElementTree.ElementTree: The generated XML tree.
    """
    # Create the root <project> element with the required attribute
    project = ET.Element("project", attrib={"ptx-version": "2"})
    
    # Create the <targets> child element
    targets = ET.SubElement(project, "targets")
    
    # Define the formats and solution states
    formats = ["scorm", "pdf", "tex"]
    has_solutions = [True, False]
    
    # Walk through the directory to find relevant files
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.startswith("ps") and filename.endswith(".ptx"):
                # Remove the .ptx extension to get the basename
                basename = filename[:-4]
                
                # Create the target stem by replacing underscores with hyphens
                stem = basename.replace("_", "-")
                source_attr = os.path.join(os.path.basename(root), filename)

                for has_sol in has_solutions:
                    for fmt in formats:
                        # Construct the target attributes
                        target_name = f"{stem}-{fmt}"
                        sol_suffix = "-sol" if has_sol else ""
                        output_ext = "zip" if fmt == "scorm" else fmt
                        
                        target_output_filename = f"{basename}{sol_suffix}.{output_ext}"
                        
                        if has_sol:
                            target_name += "-sols"
                            publication_file = "publication_standalone.ptx"
                        else:
                            publication_file = "publication_standalone_nosols.ptx"
                        
                        output_dir = ""
                        format_attr = ""
                        compress_attr = None
                        
                        if fmt == "scorm":
                            output_dir = "scorms"
                            format_attr = "html"
                            compress_attr = "scorm"
                        elif fmt == "pdf":
                            output_dir = "pdfs"
                            format_attr = "pdf"
                        else: # fmt == "tex"
                            output_dir = "tex"
                            format_attr = "latex"

                        # Create the new <target> element
                        target = ET.SubElement(targets, "target")
                        
                        # Add sub-elements and attributes
                        target.set("name", target_name)
                        target.set("source", source_attr)
                        target.set("output-filename", target_output_filename)
                        # target.set("standalone", "yes")
                        target.set("format", format_attr)
                        target.set("output-dir", output_dir)
                        target.set("publication", publication_file)
                        
                        if compress_attr:
                            target.set("compression", compress_attr)

                        # print (f"Added target: {target_name} -> {target_output_filename}")

    return ET.ElementTree(project)

def write_xml_to_file(tree, output_file):
    """
    Writes an XML ElementTree to a file with proper indentation.

    Args:
        tree (xml.etree.ElementTree.ElementTree): The XML tree to write.
        output_file (str): The name of the output file.
    """
    try:
        ET.indent(tree, space="\t", level=0)
        tree.write(output_file, encoding="UTF-8", xml_declaration=True)
        print(f"Successfully generated {output_file}.")
    except Exception as e:
        # Fallback for older Python versions
        try:
            tree.write(output_file, encoding="UTF-8", xml_declaration=True)
            print(f"Warning: Could not format XML due to a missing Python library feature. Generated file {output_file} without pretty printing.")
            print(f"Error details: {e}")
        except Exception as e:
            print(f"Failed to write XML file {output_file}.")
            print(f"Error details: {e}")

# Entry point of the script
if __name__ == "__main__":
    path = "source/psets"
    
    if not os.path.isdir(path):
        print(f"Error: The directory '{path}' was not found.")
        print("Please ensure this script is in the same folder as your `activities` directory.")
    else:
        xml_tree = generate_pretext_xml_tree(path)
        
        # Convert the XML tree to a formatted string and print to stdout
        try:
            ET.indent(xml_tree, space="\t", level=0)
            xml_string = ET.tostring(xml_tree.getroot(), encoding='unicode')
            print(xml_string)
        except Exception as e:
            print(f"Warning: Could not format XML for printing. Printing raw XML string.")
            print(ET.tostring(xml_tree.getroot(), encoding='unicode'))
            print(f"Error details: {e}")
