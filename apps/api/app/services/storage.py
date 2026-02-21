import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from PIL import Image
import io

# Allowed image types for medical images
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".dcm"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class StorageService:
    def __init__(self):
        self.use_s3 = settings.use_s3
        if not self.use_s3:
            # Ensure local storage directory exists
            self.local_path = Path(settings.LOCAL_STORAGE_PATH)
            self.local_path.mkdir(parents=True, exist_ok=True)

    async def save_image(self, file: UploadFile, session_id: str) -> Tuple[str, dict]:
        """
        Save an uploaded image file.
        
        Returns:
            Tuple of (file_url, metadata_dict)
        """
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Validate it's a valid image (except DICOM)
        if file_ext != ".dcm":
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()
                # Get image dimensions
                img = Image.open(io.BytesIO(content))  # Re-open after verify
                width, height = img.size
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image file: {str(e)}"
                )
        else:
            width, height = None, None
        
        # Generate unique filename
        unique_filename = f"{session_id}_{uuid.uuid4().hex}{file_ext}"
        
        # Save to storage
        if self.use_s3:
            file_url = await self._save_to_s3(content, unique_filename, file.content_type)
        else:
            file_url = await self._save_to_local(content, unique_filename)
        
        metadata = {
            "filename": file.filename,
            "stored_as": unique_filename,
            "size": file_size,
            "content_type": file.content_type or "image/jpeg",
            "dimensions": {"width": width, "height": height} if width else None
        }
        
        return file_url, metadata

    async def _save_to_local(self, content: bytes, filename: str) -> str:
        """Save file to local storage"""
        file_path = self.local_path / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Return relative URL path
        return f"/uploads/{filename}"

    async def _save_to_s3(self, content: bytes, filename: str, content_type: Optional[str]) -> str:
        """Save file to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            # Upload to S3
            s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=f"medical-images/{filename}",
                Body=content,
                ContentType=content_type or "image/jpeg",
                ServerSideEncryption='AES256'  # Encrypt at rest
            )
            
            # Generate URL
            return f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/medical-images/{filename}"
        
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to S3: {str(e)}"
            )

    async def delete_image(self, file_url: str) -> bool:
        """Delete an image from storage"""
        if self.use_s3:
            return await self._delete_from_s3(file_url)
        else:
            return await self._delete_from_local(file_url)

    async def _delete_from_local(self, file_url: str) -> bool:
        """Delete file from local storage"""
        try:
            filename = file_url.split('/')[-1]
            file_path = self.local_path / filename
            
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    async def _delete_from_s3(self, file_url: str) -> bool:
        """Delete file from S3"""
        try:
            import boto3
            
            s3_client = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            # Extract key from URL
            key = file_url.split('.com/')[-1]
            
            s3_client.delete_object(
                Bucket=settings.S3_BUCKET,
                Key=key
            )
            
            return True
        except Exception:
            return False

    def get_image_path(self, file_url: str) -> Optional[Path]:
        """Get local file path for an image (only for local storage)"""
        if self.use_s3:
            return None
        
        filename = file_url.split('/')[-1]
        file_path = self.local_path / filename
        
        return file_path if file_path.exists() else None


# Singleton instance
storage_service = StorageService()
