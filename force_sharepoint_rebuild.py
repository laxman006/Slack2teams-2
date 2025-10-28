# -*- coding: utf-8 -*-
"""
Force SharePoint content to be added to vectorstore
"""

import os
import json
from datetime import datetime

# Update metadata timestamp to force rebuild
metadata_path = "data/vectorstore_metadata.json"

if os.path.exists(metadata_path):
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Set timestamp to old date to trigger rebuild
    metadata['timestamp'] = '2025-01-01T00:00:00.000000'
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
    
    print("✅ Updated metadata timestamp to force rebuild")
    print("   Restart server to trigger SharePoint extraction")
else:
    print("❌ Metadata file not found")

