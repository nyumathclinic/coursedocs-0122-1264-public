#!/usr/bin/env python3
"""
Preprocessor for PreTeXt XML files that expands xi:include elements with set-xml-id attributes.

This tool resolves xi:include elements that have set-xml-id attributes by:
1. Loading the referenced file
2. Evaluating the xpointer to extract the element
3. Cloning the element and modifying its @xml:id
4. Replacing the xi:include with the modified element

Usage:
    python expand_xi_include_with_id.py <input_file> <output_file> [--base-dir <dir>]
"""

import argparse
import copy
import os
import re
import sys
from pathlib import Path
from lxml import etree


def parse_xpointer(xpointer_str):
    """
    Parse an xpointer string and return a dict with its components.
    
    Supports: xpointer(//exercise[@xml:id='id']) or xpointer(//section[1])
    """
    # Extract the expression inside xpointer()
    match = re.match(r"xpointer\((.*)\)", xpointer_str)
    if not match:
        return None
    
    return match.group(1)


def load_xml_file(filepath):
    """Load and parse an XML file, preserving namespaces."""
    parser = etree.XMLParser(remove_blank_text=False)
    try:
        tree = etree.parse(str(filepath), parser)
        return tree.getroot()
    except etree.XMLSyntaxError as e:
        print(f"Error parsing XML file {filepath}: {e}", file=sys.stderr)
        raise


def find_element_by_xpointer(root, xpointer_expr, namespaces):
    """
    Evaluate an XPath expression (extracted from xpointer) and return the first matching element.
    """
    # Define namespaces for XPath evaluation
    ns = {
        'xml': 'http://www.w3.org/XML/1998/namespace',
        'xi': 'http://www.w3.org/2001/XInclude',
    }
    ns.update(namespaces)
    
    try:
        # Try to find elements using the XPath expression
        results = root.xpath(xpointer_expr, namespaces=ns)
        if results:
            return results[0]
    except Exception as e:
        print(f"Error evaluating XPath '{xpointer_expr}': {e}", file=sys.stderr)
    
    return None


def expand_all_xi_includes(element, base_dir, namespaces, processed_files=None):
    """
    Expand ALL xi:include elements (with or without set-xml-id).
    For includes with set-xml-id, apply the ID renaming.
    
    Args:
        element: The root element to process
        base_dir: Base directory for resolving relative paths
        namespaces: Dict of namespace prefixes to URIs
        processed_files: Set of already processed files (to prevent infinite loops)
    """
    if processed_files is None:
        processed_files = set()
    
    xi_ns = "http://www.w3.org/2001/XInclude"
    
    # Keep expanding until no more xi:includes are found
    made_replacements = True
    iteration = 0
    max_iterations = 100  # Prevent infinite loops
    
    while made_replacements and iteration < max_iterations:
        iteration += 1
        made_replacements = False
        
        # Find all xi:include elements
        includes_to_process = []
        for include in element.iter(f"{{{xi_ns}}}include"):
            includes_to_process.append(include)
        
        for include in includes_to_process:
            # Skip if already processed (check if parent is gone)
            if include.getparent() is None:
                continue
                
            href = include.get("href")
            xpointer = include.get("xpointer")
            set_xml_id = include.get("set-xml-id")
            
            if not href:
                continue
            
            # Resolve the href relative to base_dir
            if not os.path.isabs(href):
                included_path = os.path.join(base_dir, href)
            else:
                included_path = href
            
            included_path = os.path.normpath(included_path)
            
            # Prevent infinite loops for this specific file
            file_key = (included_path, xpointer, set_xml_id)
            if file_key in processed_files:
                continue
            
            if not os.path.exists(included_path):
                print(f"Warning: Include file not found: {included_path}", file=sys.stderr)
                continue
            
            processed_files.add(file_key)
            
            # Load the included file
            try:
                included_root = load_xml_file(included_path)
            except Exception as e:
                print(f"Error loading include file {included_path}: {e}", file=sys.stderr)
                continue
            
            # Get the element to insert
            if xpointer:
                xpointer_expr = parse_xpointer(xpointer)
                if not xpointer_expr:
                    print(f"Warning: Invalid xpointer: {xpointer}", file=sys.stderr)
                    continue
                
                included_element = find_element_by_xpointer(included_root, xpointer_expr, namespaces)
                if included_element is None:
                    print(f"Warning: xpointer '{xpointer_expr}' did not match any element in {included_path}", file=sys.stderr)
                    continue
            else:
                # If no xpointer, use the root of the included file
                included_element = included_root
            
            # Clone the element
            cloned_element = copy.deepcopy(included_element)
            
            # Update the @xml:id attribute if set-xml-id is specified
            if set_xml_id:
                cloned_element.set(f"{{{namespaces.get('xml', 'http://www.w3.org/XML/1998/namespace')}}}id", set_xml_id)
            
            # Replace the xi:include element with the cloned element
            parent = include.getparent()
            if parent is not None:
                index = list(parent).index(include)
                parent.remove(include)
                parent.insert(index, cloned_element)
                made_replacements = True
    
    if iteration >= max_iterations:
        print(f"Warning: Reached maximum iterations ({max_iterations}) while expanding xi:includes", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Expand xi:include elements with set-xml-id attributes in PreTeXt files"
    )
    parser.add_argument("input_file", help="Input XML file")
    parser.add_argument("output_file", help="Output XML file")
    parser.add_argument("--base-dir", help="Base directory for resolving relative paths", default=None)
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Determine base directory
    base_dir = args.base_dir or str(input_path.parent)
    
    # Define namespaces
    namespaces = {
        'xml': 'http://www.w3.org/XML/1998/namespace',
        'xi': 'http://www.w3.org/2001/XInclude',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
    }
    
    # Load the input file
    try:
        root = load_xml_file(input_path)
    except Exception as e:
        print(f"Error loading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Expand all xi:include elements (including those with set-xml-id for ID renaming)
    try:
        expand_all_xi_includes(root, base_dir, namespaces)
    except Exception as e:
        print(f"Error expanding xi:include elements: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Write the output file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree = etree.ElementTree(root)
        tree.write(
            str(output_path),
            xml_declaration=True,
            encoding="UTF-8",
            pretty_print=True
        )
        print(f"Successfully wrote expanded XML to: {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
