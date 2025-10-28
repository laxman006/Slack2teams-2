# -*- coding: utf-8 -*-
"""
Teams Meeting Transcript Extractor

Extracts meeting transcripts from Microsoft Teams using Graph API.
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.documents import Document

from app.sharepoint_auth import sharepoint_auth
from urllib.parse import urlparse
import os


class TeamsTranscriptExtractor:
    """Extract transcripts from Teams meetings."""

    def __init__(self):
        self.auth = sharepoint_auth
        self.base_url = "https://graph.microsoft.com/v1.0"

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users in the organization."""
        headers = self.auth.get_headers()
        url = f"{self.base_url}/users"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('value', [])
        except Exception as e:
            print(f"[ERROR] Failed to get users: {e}")
            return []

    def get_user_meetings(self, user_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get all online meetings for a user."""
        headers = self.auth.get_headers()

        # Filter for meetings in the last X days (Graph currently doesn't filter here; left for future)
        _ = (datetime.now() - timedelta(days=days_back)).isoformat()
        url = f"{self.base_url}/users/{user_id}/onlineMeetings"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('value', [])
        except Exception as e:
            # This is expected - most meetings won't be in this endpoint
            # We'll get meeting IDs from recording metadata instead
            return []

    def get_meeting_transcripts(self, user_id: str, meeting_id: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a specific meeting."""
        headers = self.auth.get_headers()
        url = f"{self.base_url}/users/{user_id}/onlineMeetings/{meeting_id}/transcripts"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('value', [])
        except Exception as e:
            print(f"[ERROR] Failed to get transcripts for meeting {meeting_id}: {e}")
            return []

    def get_transcript_content(self, user_id: str, meeting_id: str, transcript_id: str) -> Optional[str]:
        """Get the actual transcript content in VTT format and return as text."""
        headers = self.auth.get_headers()
        url = f"{self.base_url}/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"

        params = {"$format": "text/vtt"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[ERROR] Failed to get transcript content: {e}")
            return None
    
    def get_transcript_content_by_meeting_id(self, user_id: str, meeting_id: str, transcript_id: str) -> Optional[str]:
        """Get transcript content using the correct Microsoft Graph API."""
        headers = self.auth.get_headers()
        
        # Use the correct API endpoint from Microsoft documentation
        # GET /users/{userId}/onlineMeetings/{meetingId}/transcripts/{transcriptId}/content
        url = f"{self.base_url}/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
        
        try:
            # Try getting as VTT format first
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"         [ERROR] Failed to get transcript: {e}")
            return None

    def parse_vtt_transcript(self, vtt_content: str) -> str:
        """Parse VTT format transcript to plain text."""
        if not vtt_content:
            return ""

        lines = vtt_content.split('\n')
        text_lines = []

        for line in lines:
            line = line.strip()
            # Skip VTT headers, timestamps, and empty lines
            if (
                line.startswith('WEBVTT') or
                line.startswith('NOTE') or
                '-->' in line or
                line == '' or
                line.isdigit()
            ):
                continue

            text_lines.append(line)

        return '\n'.join(text_lines)

    def extract_all_transcripts(self, user_emails: List[str] = None, days_back: int = 30) -> List[Document]:
        """
        Extract all transcripts from Teams meetings.

        Args:
            user_emails: List of user emails to fetch transcripts for.
            days_back: Number of days to look back for meetings.

        Returns:
            List of Document objects containing transcript content.
        """
        print("=" * 60)
        print("TEAMS MEETING TRANSCRIPT EXTRACTION")
        print("=" * 60)

        all_documents: List[Document] = []

        # Determine users to process
        used_user_list = False
        if user_emails:
            users = []
            for email in user_emails:
                email = email.strip()
                if not email:
                    continue
                users.append({'userPrincipalName': email, 'id': email})
            used_user_list = True
        else:
            print("[*] Fetching all users...")
            users = self.get_all_users()
            print(f"[OK] Found {len(users)} users")

        for idx, user in enumerate(users, 1):
            user_email = user.get('userPrincipalName', user.get('id', 'unknown'))
            user_id = user.get('id', user_email)

            print(f"\n[{idx}/{len(users)}] Processing user: {user_email}")

            meetings = self.get_user_meetings(user_id, days_back)
            print(f"   Found {len(meetings)} meetings")
            if not meetings:
                continue

            for meeting in meetings:
                meeting_id = meeting.get('id')
                meeting_subject = meeting.get('subject', 'Untitled Meeting')
                meeting_start = meeting.get('startDateTime', 'Unknown')

                print(f"   [*] Processing meeting: {meeting_subject}")

                transcripts = self.get_meeting_transcripts(user_id, meeting_id)
                if not transcripts:
                    print("      No transcripts found")
                    continue

                print(f"      Found {len(transcripts)} transcript(s)")
                for transcript in transcripts:
                    transcript_id = transcript.get('id')
                    created_date = transcript.get('createdDateTime', 'Unknown')

                    vtt_content = self.get_transcript_content(user_id, meeting_id, transcript_id)
                    if not vtt_content:
                        print("      Could not fetch transcript content")
                        continue

                    transcript_text = self.parse_vtt_transcript(vtt_content)
                    if not transcript_text:
                        print("      Empty transcript after parsing")
                        continue

                    doc = Document(
                        page_content=transcript_text,
                        metadata={
                            "source_type": "teams_transcript",
                            "source": "microsoft_teams",
                            "meeting_subject": meeting_subject,
                            "meeting_start": meeting_start,
                            "meeting_id": meeting_id,
                            "transcript_id": transcript_id,
                            "created_date": created_date,
                            "user_email": user_email,
                            "content_type": "meeting_transcript",
                        },
                    )

                    all_documents.append(doc)
                    print(f"      [OK] Extracted transcript ({len(transcript_text)} chars)")

        # If we had explicit users but found nothing via meeting APIs, try per-user OneDrive Recordings fallback
        if not all_documents and used_user_list and user_emails:
            print("\n[*] No transcripts from meeting APIs; scanning OneDrive 'Recordings' folders for provided users...")
            for email in user_emails:
                email = email.strip()
                if not email:
                    continue
                try:
                    od_docs = self.extract_from_user_onedrive_recordings(email)
                    if od_docs:
                        all_documents.extend(od_docs)
                except Exception as e:
                    print(f"   [WARN] OneDrive scan failed for {email}: {e}")

        # If we could not list users (403) and no user list provided, try fallback search via Graph Search API
        if not all_documents and not used_user_list and not users:
            print("\n[*] Falling back to SharePoint site drive search for .vtt transcripts...")
            try:
                sp_docs = self.search_transcripts_in_sharepoint_site(days_back=days_back)
                all_documents.extend(sp_docs)
                print(f"[OK] SharePoint site search produced {len(sp_docs)} transcript(s)")
            except Exception as e:
                print(f"[ERROR] SharePoint site drive search failed: {e}")

            print("\n[*] Falling back to organization-wide drive search for transcript files (.vtt)...")
            try:
                fallback_docs = self.search_transcripts_via_drive_search(days_back=days_back)
                all_documents.extend(fallback_docs)
                print(f"[OK] Fallback search produced {len(fallback_docs)} transcript(s)")
            except Exception as e:
                print(f"[ERROR] Fallback drive search failed: {e}")

        print("\n" + "=" * 60)
        print("[OK] Extraction complete!")
        print(f"   Total transcripts: {len(all_documents)}")
        print("=" * 60)

        return all_documents

    def search_transcripts_via_drive_search(self, days_back: int = 30) -> List[Document]:
        """Search for transcript files across OneDrive/SharePoint using Graph Search and return documents.

        Requires: Files.Read.All and Sites.Read.All application permissions.
        """
        headers = self.auth.get_headers()
        search_url = f"{self.base_url}/search/query"

        # Basic query targeting likely transcript names with .vtt extension
        query_texts = [
            "transcript filetype:vtt",
            "meeting transcript filetype:vtt",
            "*.vtt",
        ]

        collected: List[Document] = []

        for q in query_texts:
            body = {
                "requests": [
                    {
                        "entityTypes": ["driveItem"],
                        "query": {"queryString": q},
                        "from": 0,
                        "size": 25
                    }
                ]
            }
            try:
                resp = requests.post(search_url, headers=headers, json=body, timeout=60)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"   [WARN] Search '{q}' failed: {e}")
                continue

            hits_containers = data.get("value", [])
            for container in hits_containers:
                for hits in container.get("hitsContainers", []):
                    for hit in hits.get("hits", []):
                        res = hit.get("resource", {})
                        name = res.get("name", "")
                        if not name.lower().endswith(".vtt"):
                            continue
                        drive_id = res.get("parentReference", {}).get("driveId")
                        item_id = res.get("id")
                        web_url = res.get("webUrl")
                        last_modified = res.get("lastModifiedDateTime")

                        if not drive_id or not item_id:
                            continue

                        # Fetch file content
                        content_url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/content"
                        try:
                            file_resp = requests.get(content_url, headers=headers, timeout=120)
                            if file_resp.status_code != 200:
                                print(f"   [WARN] Could not fetch content for {name}: {file_resp.status_code}")
                                continue
                            vtt_content = file_resp.text
                            transcript_text = self.parse_vtt_transcript(vtt_content)
                            if not transcript_text:
                                continue
                            doc = Document(
                                page_content=transcript_text,
                                metadata={
                                    "source_type": "teams_transcript",
                                    "source": "microsoft_teams",
                                    "content_type": "meeting_transcript",
                                    "file_name": name,
                                    "web_url": web_url,
                                    "last_modified": last_modified,
                                },
                            )
                            collected.append(doc)
                            print(f"   [OK] Found transcript file: {name} ({len(transcript_text)} chars)")
                        except Exception as e:
                            print(f"   [WARN] Error fetching content for {name}: {e}")

        return collected

    def search_transcripts_in_sharepoint_site(self, days_back: int = 30) -> List[Document]:
        """Search the configured SharePoint site for .vtt transcript files using drive search."""
        headers = self.auth.get_headers()

        # Derive site id from SHAREPOINT_SITE_URL
        site_url = os.getenv("SHAREPOINT_SITE_URL")
        if not site_url:
            return []
        parsed = urlparse(site_url)
        hostname = parsed.netloc
        site_path = parsed.path
        site_endpoint = f"{self.base_url}/sites/{hostname}:{site_path}"

        try:
            site_resp = requests.get(site_endpoint, headers=headers, timeout=30)
            site_resp.raise_for_status()
            site_id = site_resp.json().get("id")
            if not site_id:
                return []
        except Exception as e:
            print(f"   [WARN] Could not resolve site id: {e}")
            return []

        # List drives (document libraries) in the site
        drives_url = f"{self.base_url}/sites/{site_id}/drives"
        try:
            drives_resp = requests.get(drives_url, headers=headers, timeout=60)
            drives_resp.raise_for_status()
            drives = drives_resp.json().get("value", [])
        except Exception as e:
            print(f"   [WARN] Could not list site drives: {e}")
            return []

        collected: List[Document] = []
        for drv in drives:
            drive_id = drv.get("id")
            drive_name = drv.get("name")
            if not drive_id:
                continue
            print(f"   [*] Searching drive: {drive_name}")
            search_url = f"{self.base_url}/drives/{drive_id}/root/search(q='vtt')"
            try:
                s_resp = requests.get(search_url, headers=headers, timeout=120)
                s_resp.raise_for_status()
                items = s_resp.json().get("value", [])
            except Exception as e:
                print(f"   [WARN] Drive search failed: {e}")
                continue

            for item in items:
                name = item.get("name", "")
                if not name.lower().endswith(".vtt"):
                    continue
                item_id = item.get("id")
                web_url = item.get("webUrl")
                last_modified = item.get("lastModifiedDateTime")
                content_url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/content"
                try:
                    file_resp = requests.get(content_url, headers=headers, timeout=120)
                    if file_resp.status_code != 200:
                        print(f"     [WARN] Could not fetch content for {name}: {file_resp.status_code}")
                        continue
                    vtt_content = file_resp.text
                    transcript_text = self.parse_vtt_transcript(vtt_content)
                    if not transcript_text:
                        continue
                    doc = Document(
                        page_content=transcript_text,
                        metadata={
                            "source_type": "teams_transcript",
                            "source": "microsoft_teams",
                            "content_type": "meeting_transcript",
                            "file_name": name,
                            "web_url": web_url,
                            "last_modified": last_modified,
                            "drive_name": drive_name,
                        },
                    )
                    collected.append(doc)
                    print(f"     [OK] Found transcript file: {name} ({len(transcript_text)} chars)")
                except Exception as e:
                    print(f"     [WARN] Error fetching content for {name}: {e}")

        return collected

    def extract_from_user_onedrive_recordings(self, user_id_or_email: str) -> List[Document]:
        """Find .vtt transcripts under a user's OneDrive 'Recordings' folder."""
        headers = self.auth.get_headers()
        collected: List[Document] = []
        
        # Try multiple possible locations for Recordings folder
        possible_paths = [
            "/Recordings",
            "/Documents/Recordings",
            "/My Documents/Recordings"
        ]
        
        drive_id = None
        folder_id = None
        found_path = None
        
        for path in possible_paths:
            folder_url = f"{self.base_url}/users/{user_id_or_email}/drive/root:{path}"
            try:
                f_resp = requests.get(folder_url, headers=headers, timeout=60)
                if f_resp.status_code == 200:
                    folder = f_resp.json()
                    drive_id = folder.get("parentReference", {}).get("driveId")
                    folder_id = folder.get("id")
                    if drive_id and folder_id:
                        found_path = path
                        print(f"   [OK] Found Recordings at: {path}")
                        break
            except Exception:
                continue
        
        if not drive_id or not folder_id:
            print(f"   [WARN] Could not find OneDrive Recordings folder for {user_id_or_email}")
            return []

        # List all files in the Recordings folder and check for embedded transcripts
        list_url = f"{self.base_url}/drives/{drive_id}/items/{folder_id}/children"
        try:
            list_resp = requests.get(list_url, headers=headers, timeout=60)
            list_resp.raise_for_status()
            all_files = list_resp.json().get("value", [])
            print(f"   [DEBUG] Found {len(all_files)} files in Recordings folder:")
            
            # Process .mp4 recordings to extract embedded transcripts
            recording_count = 0
            MAX_RECORDINGS_TO_CHECK = 3  # Limit for faster testing
            for f in all_files:
                name = f.get('name', 'unknown')
                if name.lower().endswith('.mp4'):
                    recording_count += 1
                    if recording_count > MAX_RECORDINGS_TO_CHECK:
                        print(f"      ... (skipping remaining {len([x for x in all_files if x.get('name', '').lower().endswith('.mp4')]) - recording_count + 1} recordings)")
                        break
                    file_id = f.get('id')
                    if file_id:
                        # Try to get transcript from the recording metadata
                        print(f"      - Checking recording: {name}")
                        transcript_doc = self.extract_transcript_from_recording(
                            drive_id, file_id, name, user_id_or_email
                        )
                        if transcript_doc:
                            collected.append(transcript_doc)
                        
            print(f"   [OK] Processed {recording_count} recordings")
            
        except Exception as e:
            print(f"   [WARN] Could not list files: {e}")
        
        return collected

    def extract_transcript_from_recording(self, drive_id: str, item_id: str, recording_name: str, user_email: str) -> Optional[Document]:
        """Extract transcript from a Teams recording using Graph API."""
        headers = self.auth.get_headers()
        
        # Method 1: Try to get transcript via Stream API (driveItem with transcript)
        # Check if the item has a "transcript" property or related transcript
        try:
            # Get detailed item info including potential transcript metadata
            item_url = f"{self.base_url}/drives/{drive_id}/items/{item_id}"
            item_resp = requests.get(item_url, headers=headers, timeout=60)
            item_resp.raise_for_status()
            item_data = item_resp.json()
            
            # Debug: Check what metadata is available
            web_url = item_data.get('webUrl', '')
            media_info = item_data.get('media', {})
            video_info = item_data.get('video', {})
            package_info = item_data.get('package', {})
            
            # Look for Stream video ID or meeting ID in metadata
            # Teams recordings often have a "sharepointIds" or custom metadata
            sharepoint_ids = item_data.get('sharepointIds', {})
            
            # Try to get SharePoint list item which may have meeting ID
            list_item_id = sharepoint_ids.get('listItemId') if sharepoint_ids else None
            if list_item_id:
                try:
                    list_item_url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/listItem?$expand=fields"
                    list_resp = requests.get(list_item_url, headers=headers, timeout=30)
                    if list_resp.status_code == 200:
                        list_data = list_resp.json()
                        fields = list_data.get('fields', {})
                        print(f"         [DEBUG] SharePoint list fields: {list(fields.keys())[:10]}")
                        # Look for meeting ID in fields
                        for key, val in fields.items():
                            if 'meeting' in key.lower() or 'MSo' in str(val):
                                print(f"         [DEBUG] Potential meeting field: {key} = {str(val)[:100]}")
                except Exception:
                    pass
            
            # Print first recording's metadata for debugging (only once)
            if not hasattr(self, '_debug_printed'):
                self._debug_printed = True
                print(f"\n         [DEBUG] Sample recording metadata (looking for meeting ID):")
                print(f"         - transcription_allowed: {media_info.get('viewpoint', {}).get('isTranscriptionAllowed')}")
                print(f"         - auto_transcription_allowed: {media_info.get('viewpoint', {}).get('isAutomaticTranscriptionAllowed')}")
                
                # Print ALL top-level keys to find meeting ID
                print(f"         - Available metadata fields: {list(item_data.keys())}")
                
                # Check specific fields that might contain meeting ID
                for key in ['description', 'name', 'id', 'parentReference', 'listItem']:
                    if key in item_data:
                        val = str(item_data[key])
                        if len(val) > 100:
                            val = val[:100] + '...'
                        print(f"         - {key}: {val}")
                
                print()
                
                if not media_info.get('viewpoint', {}).get('isTranscriptionAllowed'):
                    print(f"         [WARN] ISSUE: Transcription was NOT enabled when recording!")
                    print(f"         [TIP] Enable transcription in Teams settings before recording")
                    print()
            
            # Check if transcription is enabled for this recording
            is_transcription_allowed = media_info.get('viewpoint', {}).get('isTranscriptionAllowed', False)
            
            # Don't skip - sometimes transcripts exist even when flag is False
            # (e.g., when manually started during recording)
            if not is_transcription_allowed:
                print(f"         [INFO] Transcription flag is False, but checking anyway...")
            
            # Method 1: Try to extract meeting ID from recording metadata
            # Recordings may have a meeting ID stored in various places
            meeting_id = None
            
            # Check various metadata fields for meeting ID
            if 'description' in item_data:
                desc = item_data.get('description', '')
                # Meeting IDs are often in format: MSoxM2VhODJh...
                if 'MSo' in desc:
                    parts = desc.split('MSo')
                    if len(parts) > 1:
                        meeting_id = 'MSo' + parts[1].split()[0].split(',')[0]
            
            # Try to get from extended properties
            # Teams recordings may store meeting ID in custom properties
            
            # Method 2: Use the correct API with meeting ID
            # GET /users/{userId}/onlineMeetings/{meetingId}/transcripts
            if meeting_id:
                print(f"         [DEBUG] Found meeting ID: {meeting_id[:20]}...")
                try:
                    transcripts = self.get_meeting_transcripts(user_email, meeting_id)
                    if transcripts:
                        print(f"         [OK] Found {len(transcripts)} transcript(s) for meeting")
                        for transcript in transcripts:
                            transcript_id = transcript.get('id')
                            # Get transcript content
                            content = self.get_transcript_content_by_meeting_id(
                                user_email, meeting_id, transcript_id
                            )
                            if content:
                                print(f"         [OK] Successfully fetched transcript content")
                                return self._create_transcript_document(
                                    content, recording_name, web_url, user_email
                                )
                except Exception as e:
                    print(f"         [WARN] Meeting API failed: {e}")
            
            # Method 3: Try to get transcript by checking associated files/children
            # This is the most reliable method - check if transcript files exist as children
            print(f"         [*] Checking for transcript files as child items...")
            children_url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/children"
            try:
                children_resp = requests.get(children_url, headers=headers, timeout=60)
                if children_resp.status_code == 200:
                    children = children_resp.json().get('value', [])
                    print(f"         [DEBUG] Found {len(children)} child items")
                    
                    for child in children:
                        child_name = child.get('name', '')
                        child_name_lower = child_name.lower()
                        print(f"            - Child: {child_name}")
                        
                        if 'transcript' in child_name_lower or child_name_lower.endswith(('.vtt', '.docx', '.doc')):
                            print(f"            → Potential transcript file found!")
                            child_id = child.get('id')
                            content_url = f"{self.base_url}/drives/{drive_id}/items/{child_id}/content"
                            try:
                                content_resp = requests.get(content_url, headers=headers, timeout=60)
                                if content_resp.status_code == 200:
                                    if child_name_lower.endswith('.vtt'):
                                        transcript_text = self.parse_vtt_transcript(content_resp.text)
                                    elif child_name_lower.endswith(('.docx', '.doc')):
                                        import tempfile
                                        from app.doc_processor import extract_text_from_docx
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                                            tmp.write(content_resp.content)
                                            tmp_path = tmp.name
                                        transcript_text = extract_text_from_docx(tmp_path)
                                    else:
                                        transcript_text = content_resp.text
                                    
                                    if transcript_text:
                                        print(f"         [OK] Found transcript as child item: {child_name}")
                                        print(f"         [OK] Extracted {len(transcript_text)} characters")
                                        return Document(
                                            page_content=transcript_text,
                                            metadata={
                                                "source_type": "teams_transcript",
                                                "source": "microsoft_teams",
                                                "content_type": "meeting_transcript",
                                                "recording_name": recording_name,
                                                "transcript_file": child_name,
                                                "web_url": web_url,
                                                "user_email": user_email,
                                            },
                                        )
                                else:
                                    print(f"            → Could not fetch content: {content_resp.status_code}")
                            except Exception as e:
                                print(f"            → Error: {e}")
                                continue
                else:
                    print(f"         [WARN] Could not list children: {children_resp.status_code}")
            except Exception as e:
                print(f"         [WARN] Children check failed: {e}")
            
            # Method 4: Try using Microsoft Graph callTranscript API if meeting ID is available
            # Extract meeting ID from recording name (format: "Title-YYYYMMDD_HHMMSS-Meeting Recording.mp4")
            # This would require the meeting ID which we don't have from the filename
            
            print(f"         [WARN] No transcript found for this recording")
            return None
            
        except Exception as e:
            print(f"         [ERROR] Error checking transcript: {e}")
            return None
    
    def _create_transcript_document(self, content: str, recording_name: str, web_url: str, user_email: str) -> Document:
        """Helper to create a transcript document."""
        # Try to parse as VTT first, otherwise use as-is
        parsed = self.parse_vtt_transcript(content)
        transcript_text = parsed if parsed else content
        
        return Document(
            page_content=transcript_text,
            metadata={
                "source_type": "teams_transcript",
                "source": "microsoft_teams",
                "content_type": "meeting_transcript",
                "recording_name": recording_name,
                "web_url": web_url,
                "user_email": user_email,
            },
        )

    def extract_from_sharepoint_recordings_folders(self) -> List[Document]:
        """Scan site drives for a 'Recordings' folder and collect .vtt files."""
        headers = self.auth.get_headers()
        site_url = os.getenv("SHAREPOINT_SITE_URL")
        if not site_url:
            return []
        parsed = urlparse(site_url)
        hostname = parsed.netloc
        site_path = parsed.path
        site_endpoint = f"{self.base_url}/sites/{hostname}:{site_path}"
        try:
            site_resp = requests.get(site_endpoint, headers=headers, timeout=30)
            site_resp.raise_for_status()
            site_id = site_resp.json().get("id")
            if not site_id:
                return []
        except Exception:
            return []

        # List drives
        try:
            drives_resp = requests.get(f"{self.base_url}/sites/{site_id}/drives", headers=headers, timeout=60)
            drives_resp.raise_for_status()
            drives = drives_resp.json().get("value", [])
        except Exception:
            return []

        collected: List[Document] = []
        for drv in drives:
            drive_id = drv.get("id")
            drive_name = drv.get("name")
            if not drive_id:
                continue
            # Resolve /Recordings under root
            rec_url = f"{self.base_url}/drives/{drive_id}/root:/Recordings"
            try:
                r_resp = requests.get(rec_url, headers=headers, timeout=60)
                if r_resp.status_code == 404:
                    continue
                r_resp.raise_for_status()
                rec_folder = r_resp.json()
                folder_id = rec_folder.get("id")
                if not folder_id:
                    continue
            except Exception:
                continue

            # Search inside Recordings
            items = []
            for q in ("vtt", "docx"):
                try:
                    s_resp = requests.get(f"{self.base_url}/drives/{drive_id}/items/{folder_id}/search(q='{q}')", headers=headers, timeout=120)
                    s_resp.raise_for_status()
                    items.extend(s_resp.json().get("value", []))
                except Exception:
                    continue

            for item in items:
                name = item.get("name", "")
                lower = name.lower()
                is_vtt = lower.endswith(".vtt")
                is_docx = lower.endswith(".docx")
                if not (is_vtt or is_docx):
                    continue
                item_id = item.get("id")
                web_url = item.get("webUrl")
                last_modified = item.get("lastModifiedDateTime")
                content_url = f"{self.base_url}/drives/{drive_id}/items/{item_id}/content"
                try:
                    file_resp = requests.get(content_url, headers=headers, timeout=120)
                    if file_resp.status_code != 200:
                        continue
                    if is_vtt:
                        vtt_content = file_resp.text
                        transcript_text = self.parse_vtt_transcript(vtt_content)
                    else:
                        import tempfile
                        from app.doc_processor import extract_text_from_docx
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                            tmp.write(file_resp.content)
                            tmp_path = tmp.name
                        transcript_text = extract_text_from_docx(tmp_path)
                    if not transcript_text:
                        continue
                    doc = Document(
                        page_content=transcript_text,
                        metadata={
                            "source_type": "teams_transcript",
                            "source": "microsoft_teams",
                            "content_type": "meeting_transcript",
                            "file_name": name,
                            "web_url": web_url,
                            "last_modified": last_modified,
                            "drive_name": drive_name,
                        },
                    )
                    collected.append(doc)
                    print(f"     [OK] Found SharePoint transcript: {name} ({len(transcript_text)} chars)")
                except Exception as e:
                    print(f"     [WARN] Error reading {name}: {e}")
                    continue

        return collected


def extract_teams_transcripts(user_emails: List[str] = None, days_back: int = 30) -> List[Document]:
    extractor = TeamsTranscriptExtractor()
    return extractor.extract_all_transcripts(user_emails, days_back)


if __name__ == "__main__":
    docs = extract_teams_transcripts(days_back=30)
    print(f"\nDocuments: {len(docs)}")
    if docs:
        print("Sample:")
        print(f"Subject: {docs[0].metadata.get('meeting_subject')}")
        print(docs[0].page_content[:200] + "...")


