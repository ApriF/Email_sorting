import os
import logging
import email
from email.header import decode_header, make_header
from pathlib import Path


class AttachmentHandler:
    """Handles saving email attachments to categorized folders."""
    
    def __init__(self, base_path="output/attachments"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Attachment handler initialized: {self.base_path}")
    
    def decode_str(self, value):
        """Decode RFC 2047 encoded email headers."""
        if not value:
            return ""
        decoded_parts = decode_header(value)
        header = make_header(decoded_parts)
        return str(header)
    
    def sanitize_filename(self, filename):
        """Remove invalid filesystem characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200] + ext
        
        return sanitized
    
    def extract_attachments(self, raw_email_bytes):
        """Extract attachment data from raw email bytes."""
        msg = email.message_from_bytes(raw_email_bytes)
        attachments = []
        
        if not msg.is_multipart():
            return attachments
        
        for part in msg.walk():
            if part.is_multipart():
                continue
            
            disposition = part.get_content_disposition()
            if disposition != "attachment":
                continue
            
            filename = part.get_filename()
            if not filename:
                continue
            
            decoded_filename = self.decode_str(filename)
            payload = part.get_payload(decode=True)
            
            if payload:
                attachments.append({
                    'filename': decoded_filename,
                    'data': payload
                })
        
        return attachments
    
    def save_attachments(self, raw_email_bytes, category, email_id=None):
        """Save attachments to category folder."""
        attachments = self.extract_attachments(raw_email_bytes)
        
        if not attachments:
            return []
        
        category_path = self.base_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for attachment in attachments:
            try:
                filename = self.sanitize_filename(attachment['filename'])
                file_path = category_path / filename
                
                # Handle duplicate filenames
                counter = 1
                original_path = file_path
                while file_path.exists():
                    name, ext = os.path.splitext(original_path.name)
                    file_path = category_path / f"{name}_{counter}{ext}"
                    counter += 1
                
                with open(file_path, 'wb') as f:
                    f.write(attachment['data'])
                
                saved_files.append(str(file_path))
                
                log_msg = f"Saved attachment: {filename} to {category}/"
                if email_id:
                    email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                    log_msg += f" (Email ID: {email_id_str})"
                logging.info(log_msg)
                
            except Exception as e:
                logging.error(f"Failed to save attachment {attachment['filename']}: {e}")
        
        return saved_files
