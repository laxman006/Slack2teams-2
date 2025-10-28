# -*- coding: utf-8 -*-
"""
Convert SharePoint Word Document to Text Files for Vectorstore
"""

from docx import Document
import os
from pathlib import Path

def convert_word_to_text(word_file: str, output_dir: str = "sharepoint_content"):
    """Convert Word document to separate text files."""
    
    print("=" * 60)
    print("CONVERTING SHAREPOINT WORD DOCUMENT")
    print("=" * 60)
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Read Word document
    doc = Document(word_file)
    
    print(f"[*] Processing: {word_file}")
    
    current_heading = None
    current_content = []
    file_count = 0
    
    for para in doc.paragraphs:
        text = para.text.strip()
        
        # Check if it's a heading
        if para.style.name.startswith('Heading'):
            # Save previous content if exists
            if current_heading and current_content:
                save_content(current_heading, current_content, output_dir)
                file_count += 1
            
            # Start new section
            current_heading = text
            current_content = []
        else:
            # Add to current content
            if text:
                current_content.append(text)
    
    # Save last section
    if current_heading and current_content:
        save_content(current_heading, current_content, output_dir)
        file_count += 1
    
    print(f"[OK] Created {file_count} text files in {output_dir}/")
    return file_count

def save_content(heading: str, content: list, output_dir: str):
    """Save content to a text file."""
    
    # Clean up heading for filename
    filename = heading.lower().replace(':', '').replace('?', '').replace('/', '-')
    filename = ''.join(c if c.isalnum() or c in ('-', '_', ' ') else '' for c in filename)
    filename = filename.strip().replace(' ', '_')
    
    filepath = os.path.join(output_dir, f"{filename}.txt")
    
    # Write content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {heading}\n\n")
        f.write('\n'.join(content))
    
    print(f"   Created: {filename}.txt")

if __name__ == "__main__":
    word_file = "SharePoint_Test_Content.docx"
    
    if not os.path.exists(word_file):
        print(f"❌ File not found: {word_file}")
        exit(1)
    
    count = convert_word_to_text(word_file)
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Review files in sharepoint_content/ directory")
    print("2. Add more SharePoint content to text files")
    print("3. Use this content in your vectorstore")

