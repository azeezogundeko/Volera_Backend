import os
import json
import boto3

from datetime import datetime
from appwrite.client import Client
from appwrite.services.databases import Databases
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .logging import logger

class BackupManager:
    def __init__(self):
        # Initialize Appwrite client
        self.appwrite_client = Client()
        self.appwrite_client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
        self.appwrite_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        self.appwrite_client.set_key(os.getenv('APPWRITE_API_KEY'))
        
        # Initialize Cloudflare R2 client (S3 compatible)
        self.r2_client = boto3.client(
            's3',
            endpoint_url=os.getenv('CLOUDFLARE_R2_ENDPOINT'),
            aws_access_key_id=os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
        )
        
        self.bucket_name = os.getenv('CLOUDFLARE_R2_BUCKET_NAME')
        self.database_id = os.getenv('APPWRITE_DATABASE_ID')
        self.databases = Databases(self.appwrite_client)
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        
    async def create_backup(self):
        """Create a backup of the Appwrite database"""
        try:
            # Get all collections in the database
            collections = self.databases.list_collections(self.database_id)
            
            backup_data = {}
            for collection in collections['collections']:
                collection_id = collection['$id']
                # Get all documents in the collection
                documents = self.databases.list_documents(
                    database_id=self.database_id,
                    collection_id=collection_id
                )
                backup_data[collection_id] = documents['documents']
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'appwrite_backup_{timestamp}.json'
            
            # Upload backup to R2
            self.r2_client.put_object(
                Bucket=self.bucket_name,
                Key=backup_filename,
                Body=json.dumps(backup_data, indent=2)
            )
            
            logger.info(f'Backup created successfully: {backup_filename}')
            return True
            
        except Exception as e:
            logger.error(f'Error creating backup: {str(e)}')
            return False
    
    def schedule_weekly_backup(self, day_of_week=0, hour=0, minute=0):
        """Schedule weekly backups
        Args:
            day_of_week (int): Day of week (0-6, Monday is 0)
            hour (int): Hour of day (0-23)
            minute (int): Minute of hour (0-59)
        """
        try:
            self.scheduler.add_job(
                self.create_backup,
                trigger=CronTrigger(
                    day_of_week=day_of_week,
                    hour=hour,
                    minute=minute
                ),
                id='weekly_backup',
                name='Weekly Appwrite Backup',
                replace_existing=True
            )
            
            if not self.scheduler.running:
                self.scheduler.start()
                
            logger.info(f'Backup scheduled for every week on day {day_of_week} at {hour:02d}:{minute:02d}')
            
        except Exception as e:
            logger.error(f'Error scheduling backup: {str(e)}')
    
    def list_backups(self):
        """List all available backups in R2"""
        try:
            response = self.r2_client.list_objects(Bucket=self.bucket_name)
            backups = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    backups.append({
                        'filename': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
                    
            return backups
            
        except Exception as e:
            logger.error(f'Error listing backups: {str(e)}')
            return []
    
    def restore_backup(self, backup_filename):
        """Restore database from a backup file
        Args:
            backup_filename (str): Name of the backup file to restore from
        """
        try:
            # Download backup file from R2
            response = self.r2_client.get_object(
                Bucket=self.bucket_name,
                Key=backup_filename
            )
            
            backup_data = json.loads(response['Body'].read())
            
            # Restore each collection
            for collection_id, documents in backup_data.items():
                # First, delete existing documents
                existing_docs = self.databases.list_documents(
                    database_id=self.database_id,
                    collection_id=collection_id
                )
                
                for doc in existing_docs['documents']:
                    self.databases.delete_document(
                        database_id=self.database_id,
                        collection_id=collection_id,
                        document_id=doc['$id']
                    )
                
                # Then create new documents from backup
                for doc in documents:
                    doc_id = doc.pop('$id')
                    self.databases.create_document(
                        database_id=self.database_id,
                        collection_id=collection_id,
                        document_id=doc_id,
                        data=doc
                    )
            
            logger.info(f'Backup restored successfully from {backup_filename}')
            return True
            
        except Exception as e:
            logger.error(f'Error restoring backup: {str(e)}')
            return False 