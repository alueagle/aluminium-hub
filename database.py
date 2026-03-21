#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aluminium Hub Database System
نظام قاعدة بيانات الألومنيوم باستخدام SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import qrcode
import os
import uuid
from pathlib import Path
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    """جدول المستخدمين"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # 'technician', 'admin', 'manager'
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_logs = relationship("ScanLog", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="technician")

class StockItem(Base):
    """جدول عناصر المخزون"""
    __tablename__ = 'stock_items'
    
    id = Column(Integer, primary_key=True)
    serial_number = Column(String(100), unique=True, nullable=False)
    qr_code_data = Column(Text, nullable=False)
    profile_code = Column(String(50))  # Reference to extraction profile
    item_type = Column(String(50), nullable=False)  # 'profile', 'accessory', etc.
    category = Column(String(50))  # 'door', 'window', etc.
    color = Column(String(50))
    length = Column(Float, nullable=False)  # Current length in meters
    original_length = Column(Float, nullable=False)
    weight_per_meter = Column(Float)  # Weight per meter from extraction profile
    total_weight = Column(Float)  # Calculated weight
    location = Column(String(100))
    storage_zone = Column(String(50))
    rack_position = Column(String(50))
    status = Column(String(20), default='available')  # 'available', 'in_use', 'reserved'
    quality_grade = Column(String(5), default='A')
    received_date = Column(DateTime, default=datetime.utcnow)
    last_used_date = Column(DateTime)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    usage_logs = relationship("UsageLog", back_populates="stock_item")
    waste_items = relationship("WasteItem", back_populates="parent_item")
    created_by_user = relationship("User", foreign_keys=[created_by])

class WasteItem(Base):
    """جدول عناصر الفضلات"""
    __tablename__ = 'waste_items'
    
    id = Column(Integer, primary_key=True)
    parent_stock_id = Column(Integer, ForeignKey('stock_items.id'), nullable=False)
    waste_serial_number = Column(String(100), unique=True, nullable=False)
    qr_code_data = Column(Text, nullable=False)
    profile_code = Column(String(50))
    item_type = Column(String(50), nullable=False)
    length = Column(Float, nullable=False)  # Waste length in meters
    weight = Column(Float)  # Calculated weight
    location = Column(String(100))
    status = Column(String(20), default='available_for_reuse')
    created_date = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    parent_item = relationship("StockItem", back_populates="waste_items")
    created_by_user = relationship("User", foreign_keys=[created_by])

class ScanLog(Base):
    """جدول سجل المسح الضوئي"""
    __tablename__ = 'scan_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    stock_item_id = Column(Integer, ForeignKey('stock_items.id'))
    serial_number = Column(String(100), nullable=False)
    scan_time = Column(DateTime, default=datetime.utcnow)
    scan_type = Column(String(20), default='qr_scan')  # 'qr_scan', 'manual_entry'
    action_taken = Column(String(50))  # 'view', 'cut', 'use'
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="scan_logs")
    stock_item = relationship("StockItem")

class UsageLog(Base):
    """جدول سجل الاستخدام"""
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True)
    stock_item_id = Column(Integer, ForeignKey('stock_items.id'), nullable=False)
    technician_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    usage_time = Column(DateTime, default=datetime.utcnow)
    operation_type = Column(String(20), nullable=False)  # 'cut', 'use', 'damage'
    original_length = Column(Float, nullable=False)
    used_length = Column(Float, nullable=False)
    remaining_length = Column(Float, nullable=False)
    waste_length = Column(Float, default=0)
    waste_generated = Column(Boolean, default=False)
    project_code = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    stock_item = relationship("StockItem", back_populates="usage_logs")
    technician = relationship("User", back_populates="usage_logs")

class ExtractionProfile(Base):
    """جدول ملفات الاستخراج المرجعية"""
    __tablename__ = 'extraction_profiles'
    
    id = Column(Integer, primary_key=True)
    profile_code = Column(String(50), unique=True, nullable=False)
    profile_name = Column(String(100), nullable=False)
    profile_type = Column(String(50))  # 'door', 'window', 'frame'
    extraction_data = Column(Text)  # JSON data with extraction parameters
    weight_per_meter = Column(Float)
    standard_length = Column(Float)
    color_options = Column(Text)  # JSON array of available colors
    created_at = Column(DateTime, default=datetime.utcnow)

class AluminiumDatabase:
    """مدير قاعدة بيانات الألومنيوم"""
    
    def __init__(self, db_url: str = "sqlite:///aluminium_hub.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.qr_codes_dir = Path("qr_codes")
        self.qr_codes_dir.mkdir(exist_ok=True)
        
    def create_tables(self):
        """إنشاء الجداول في قاعدة البيانات"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_session(self):
        """الحصول على جلسة قاعدة البيانات"""
        return self.SessionLocal()
    
    def load_extraction_profiles_from_excel(self, file_path: str):
        """تحميل ملفات الاستخراج من ملف Excel"""
        try:
            session = self.get_session()
            
            # Read Excel file
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} profiles from Excel file")
            
            for index, row in df.iterrows():
                # Extract profile data
                profile_code = str(row.get('Profile Code', f'PROF-{index:04d}'))
                profile_name = str(row.get('Profile Name', f'Profile {index}'))
                profile_type = str(row.get('Type', 'standard'))
                weight_per_meter = float(row.get('Weight per Meter', 0))
                standard_length = float(row.get('Standard Length', 6.0))
                
                # Parse color options
                colors = str(row.get('Colors', 'White,Black,Brown')).split(',')
                color_options = json.dumps([c.strip() for c in colors])
                
                # Parse extraction data
                extraction_data = {
                    'section': str(row.get('Section', 'Standard')),
                    'thickness': float(row.get('Thickness', 2.0)),
                    'width': float(row.get('Width', 50)),
                    'height': float(row.get('Height', 30)),
                    'notes': str(row.get('Notes', ''))
                }
                
                # Check if profile already exists
                existing = session.query(ExtractionProfile).filter_by(profile_code=profile_code).first()
                if not existing:
                    profile = ExtractionProfile(
                        profile_code=profile_code,
                        profile_name=profile_name,
                        profile_type=profile_type,
                        extraction_data=json.dumps(extraction_data, ensure_ascii=False),
                        weight_per_meter=weight_per_meter,
                        standard_length=standard_length,
                        color_options=color_options
                    )
                    session.add(profile)
                    logger.info(f"Added profile: {profile_code} - {profile_name}")
            
            session.commit()
            session.close()
            logger.info("Extraction profiles loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading extraction profiles: {e}")
            raise
    
    def generate_qr_code_data(self, item_data: dict) -> str:
        """توليد بيانات QR Code"""
        qr_data = {
            "serial_number": item_data["serial_number"],
            "profile_code": item_data.get("profile_code"),
            "item_type": item_data["item_type"],
            "category": item_data.get("category"),
            "color": item_data.get("color"),
            "length": item_data["length"],
            "original_length": item_data["original_length"],
            "weight_per_meter": item_data.get("weight_per_meter"),
            "total_weight": item_data.get("total_weight"),
            "location": item_data.get("location"),
            "status": item_data.get("status", "available"),
            "timestamp": datetime.utcnow().isoformat()
        }
        return json.dumps(qr_data, ensure_ascii=False)
    
    def create_qr_code_image(self, qr_data: str, serial_number: str) -> str:
        """إنشاء صورة QR Code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_file_path = self.qr_codes_dir / f"{serial_number}.png"
        img.save(qr_file_path)
        
        return str(qr_file_path)
    
    def add_stock_item(self, profile_code: str, item_type: str, color: str, 
                      length: float, location: str, created_by: int) -> int:
        """إضافة عنصر مخزون جديد"""
        session = self.get_session()
        
        try:
            # Get extraction profile
            profile = session.query(ExtractionProfile).filter_by(profile_code=profile_code).first()
            if not profile:
                raise ValueError(f"Profile {profile_code} not found")
            
            # Generate serial number
            serial_number = f"{profile_code.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Calculate weight
            total_weight = length * profile.weight_per_meter
            
            # Prepare item data
            item_data = {
                "serial_number": serial_number,
                "profile_code": profile_code,
                "item_type": item_type,
                "category": profile.profile_type,
                "color": color,
                "length": length,
                "original_length": length,
                "weight_per_meter": profile.weight_per_meter,
                "total_weight": total_weight,
                "location": location,
                "status": "available"
            }
            
            # Generate QR code
            qr_data = self.generate_qr_code_data(item_data)
            qr_image_path = self.create_qr_code_image(qr_data, serial_number)
            
            # Create stock item
            stock_item = StockItem(
                serial_number=serial_number,
                qr_code_data=qr_data,
                profile_code=profile_code,
                item_type=item_type,
                category=profile.profile_type,
                color=color,
                length=length,
                original_length=length,
                weight_per_meter=profile.weight_per_meter,
                total_weight=total_weight,
                location=location,
                created_by=created_by
            )
            
            session.add(stock_item)
            session.commit()
            
            logger.info(f"Added stock item: {serial_number}")
            return stock_item.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding stock item: {e}")
            raise
        finally:
            session.close()
    
    def scan_stock_item(self, serial_number: str, user_id: int, action: str = 'view') -> dict:
        """مسح عنصر المخزون وتسجيل العملية"""
        session = self.get_session()
        
        try:
            # Find stock item
            stock_item = session.query(StockItem).filter_by(serial_number=serial_number).first()
            if not stock_item:
                raise ValueError(f"Stock item {serial_number} not found")
            
            # Log the scan
            scan_log = ScanLog(
                user_id=user_id,
                stock_item_id=stock_item.id,
                serial_number=serial_number,
                action_taken=action,
                notes=f"QR Code scanned for {action}"
            )
            session.add(scan_log)
            
            # Update last used date
            stock_item.last_used_date = datetime.utcnow()
            
            session.commit()
            
            # Return item data
            return {
                "id": stock_item.id,
                "serial_number": stock_item.serial_number,
                "profile_code": stock_item.profile_code,
                "item_type": stock_item.item_type,
                "category": stock_item.category,
                "color": stock_item.color,
                "length": stock_item.length,
                "original_length": stock_item.original_length,
                "weight_per_meter": stock_item.weight_per_meter,
                "total_weight": stock_item.total_weight,
                "location": stock_item.location,
                "status": stock_item.status,
                "scan_logged": True
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error scanning stock item: {e}")
            raise
        finally:
            session.close()
    
    def process_cut_operation(self, serial_number: str, technician_id: int, 
                             new_length: float, notes: str = None) -> dict:
        """معالجة عملية القطع وتوليد الفضلة"""
        session = self.get_session()
        
        try:
            # Get original item
            stock_item = session.query(StockItem).filter_by(serial_number=serial_number).first()
            if not stock_item:
                raise ValueError(f"Stock item {serial_number} not found")
            
            original_length = stock_item.length
            used_length = original_length - new_length
            waste_length = used_length  # All cut becomes waste
            
            if new_length >= original_length:
                raise ValueError("New length must be less than original length")
            
            # Log the usage
            usage_log = UsageLog(
                stock_item_id=stock_item.id,
                technician_id=technician_id,
                operation_type='cut',
                original_length=original_length,
                used_length=used_length,
                remaining_length=new_length,
                waste_length=waste_length,
                waste_generated=waste_length > 0.1,  # Only track waste > 10cm
                notes=notes
            )
            session.add(usage_log)
            
            # Update original item
            stock_item.length = new_length
            stock_item.total_weight = new_length * stock_item.weight_per_meter
            stock_item.status = 'in_use'
            stock_item.last_used_date = datetime.utcnow()
            
            # Create waste item if significant
            waste_id = None
            if waste_length > 0.1:  # Only track waste > 10cm
                waste_serial = f"WST-{stock_item.profile_code}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
                waste_weight = waste_length * stock_item.weight_per_meter
                
                waste_data = {
                    "serial_number": waste_serial,
                    "profile_code": stock_item.profile_code,
                    "item_type": stock_item.item_type,
                    "length": waste_length,
                    "weight": waste_weight,
                    "location": stock_item.location,
                    "status": "available_for_reuse",
                    "parent_serial": serial_number
                }
                
                waste_qr_data = self.generate_qr_code_data(waste_data)
                waste_qr_path = self.create_qr_code_image(waste_qr_data, waste_serial)
                
                waste_item = WasteItem(
                    parent_stock_id=stock_item.id,
                    waste_serial_number=waste_serial,
                    qr_code_data=waste_qr_data,
                    profile_code=stock_item.profile_code,
                    item_type=stock_item.item_type,
                    length=waste_length,
                    weight=waste_weight,
                    location=stock_item.location,
                    created_by=technician_id
                )
                session.add(waste_item)
                waste_id = waste_item.id
            
            session.commit()
            
            result = {
                "original_item": {
                    "serial_number": stock_item.serial_number,
                    "new_length": new_length,
                    "new_weight": stock_item.total_weight
                },
                "waste_generated": waste_length > 0.1,
                "waste_length": waste_length,
                "waste_weight": waste_length * stock_item.weight_per_meter if waste_length > 0.1 else 0,
                "waste_id": waste_id,
                "operation_completed": True
            }
            
            logger.info(f"Cut operation completed for {serial_number}")
            return result
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing cut operation: {e}")
            raise
        finally:
            session.close()
    
    def get_stock_items(self, location: str = None, status: str = None) -> list:
        """الحصول على قائمة عناصر المخزون"""
        session = self.get_session()
        
        try:
            query = session.query(StockItem)
            
            if location:
                query = query.filter(StockItem.location == location)
            if status:
                query = query.filter(StockItem.status == status)
            
            items = query.all()
            
            result = []
            for item in items:
                result.append({
                    "id": item.id,
                    "serial_number": item.serial_number,
                    "profile_code": item.profile_code,
                    "item_type": item.item_type,
                    "category": item.category,
                    "color": item.color,
                    "length": item.length,
                    "original_length": item.original_length,
                    "weight_per_meter": item.weight_per_meter,
                    "total_weight": item.total_weight,
                    "location": item.location,
                    "status": item.status,
                    "received_date": item.received_date.isoformat() if item.received_date else None,
                    "last_used_date": item.last_used_date.isoformat() if item.last_used_date else None
                })
            
            return result
            
        finally:
            session.close()
    
    def get_waste_items(self, available_only: bool = True) -> list:
        """الحصول على قائمة عناصر الفضلات"""
        session = self.get_session()
        
        try:
            query = session.query(WasteItem)
            
            if available_only:
                query = query.filter(WasteItem.status == 'available_for_reuse')
            
            items = query.all()
            
            result = []
            for item in items:
                result.append({
                    "id": item.id,
                    "waste_serial_number": item.waste_serial_number,
                    "parent_stock_id": item.parent_stock_id,
                    "profile_code": item.profile_code,
                    "item_type": item.item_type,
                    "length": item.length,
                    "weight": item.weight,
                    "location": item.location,
                    "status": item.status,
                    "created_date": item.created_date.isoformat() if item.created_date else None
                })
            
            return result
            
        finally:
            session.close()
    
    def get_user_scan_history(self, user_id: int, limit: int = 50) -> list:
        """الحصول على سجل مسح المستخدم"""
        session = self.get_session()
        
        try:
            scans = session.query(ScanLog).filter(
                ScanLog.user_id == user_id
            ).order_by(ScanLog.scan_time.desc()).limit(limit).all()
            
            result = []
            for scan in scans:
                result.append({
                    "id": scan.id,
                    "serial_number": scan.serial_number,
                    "scan_time": scan.scan_time.isoformat(),
                    "scan_type": scan.scan_type,
                    "action_taken": scan.action_taken,
                    "notes": scan.notes
                })
            
            return result
            
        finally:
            session.close()
    
    def generate_initial_qr_codes(self, count: int = 127) -> dict:
        """توليد QR Codes أولية بناءً على ملفات الاستخراج"""
        session = self.get_session()
        
        try:
            # Get available profiles
            profiles = session.query(ExtractionProfile).all()
            if not profiles:
                raise ValueError("No extraction profiles found. Please load profiles first.")
            
            created_items = []
            
            for i in range(count):
                # Select a random profile
                profile = profiles[i % len(profiles)]
                
                # Parse color options
                colors = json.loads(profile.color_options)
                color = colors[i % len(colors)]
                
                # Generate item
                try:
                    item_id = self.add_stock_item(
                        profile_code=profile.profile_code,
                        item_type='profile',
                        color=color,
                        length=profile.standard_length,
                        location=f"ZONE-A-RACK{i//10 + 1}-POS{i%10 + 1}",
                        created_by=1  # Default admin user
                    )
                    created_items.append(item_id)
                except Exception as e:
                    logger.warning(f"Failed to create item {i+1}: {e}")
            
            logger.info(f"Generated {len(created_items)} initial QR codes")
            return {
                "requested": count,
                "created": len(created_items),
                "item_ids": created_items
            }
            
        finally:
            session.close()


# Initialize database
def init_database():
    """تهيئة قاعدة البيانات"""
    db = AluminiumDatabase()
    db.create_tables()
    
    # Add default admin user
    session = db.get_session()
    try:
        admin = User(
            username="admin",
            full_name="مدير النظام",
            role="admin",
            phone="0500000000"
        )
        session.add(admin)
        
        # Add sample technician
        tech = User(
            username="tech1",
            full_name="أحمد محمد",
            role="technician",
            phone="0511111111"
        )
        session.add(tech)
        
        session.commit()
        logger.info("Default users created")
    except Exception as e:
        logger.warning(f"Users might already exist: {e}")
    finally:
        session.close()
    
    return db


if __name__ == "__main__":
    # Initialize database
    db = init_database()
    
    # Try to load extraction profiles
    excel_file = "final egypt aluminium extraction profile all compans.xlsx"
    if os.path.exists(excel_file):
        try:
            db.load_extraction_profiles_from_excel(excel_file)
            print("✅ Extraction profiles loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading extraction profiles: {e}")
    else:
        print(f"⚠️ Excel file not found: {excel_file}")
    
    # Generate initial QR codes
    try:
        result = db.generate_initial_qr_codes(127)
        print(f"✅ Generated {result['created']} initial QR codes out of {result['requested']}")
    except Exception as e:
        print(f"⚠️ Error generating QR codes: {e}")
    
    print("🚀 Database initialization complete!")
