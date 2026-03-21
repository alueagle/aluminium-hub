#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aluminium Hub Database System (Minimal Version)
نظام قاعدة بيانات الألومنيوم بدون pandas
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
    profile_name = Column(String(100))  # Profile name for display
    length = Column(Float)  # Length in mm
    weight_per_meter = Column(Float)  # Weight per meter in kg
    total_weight = Column(Float)  # Total weight in kg
    status = Column(String(20), default='available')  # 'available', 'in_use', 'used'
    location = Column(String(100))  # Storage location
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_logs = relationship("ScanLog", back_populates="stock_item")
    usage_logs = relationship("UsageLog", back_populates="stock_item")

class ScanLog(Base):
    """جدول سجلات المسح"""
    __tablename__ = 'scan_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    stock_item_id = Column(Integer, ForeignKey('stock_items.id'), nullable=False)
    scan_type = Column(String(20), nullable=False)  # 'in', 'out', 'check'
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="scan_logs")
    stock_item = relationship("StockItem", back_populates="scan_logs")

class UsageLog(Base):
    """جدول سجلات الاستخدام"""
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True)
    stock_item_id = Column(Integer, ForeignKey('stock_items.id'), nullable=False)
    technician_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    operation_type = Column(String(20), nullable=False)  # 'cut', 'waste', 'return'
    cut_length = Column(Float)  # Length cut in mm
    waste_weight = Column(Float)  # Weight of waste in kg
    remaining_length = Column(Float)  # Remaining length in mm
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    stock_item = relationship("StockItem", back_populates="usage_logs")
    technician = relationship("User", back_populates="usage_logs")

class AluminiumDatabase:
    """فئة إدارة قاعدة بيانات الألومنيوم"""
    
    def __init__(self, database_url='sqlite:///aluminium_hub.db'):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized successfully")
    
    def get_session(self):
        """الحصول على جلسة قاعدة البيانات"""
        return self.SessionLocal()
    
    def create_user(self, username, full_name, role, phone=None, email=None):
        """إنشاء مستخدم جديد"""
        session = self.get_session()
        try:
            user = User(
                username=username,
                full_name=full_name,
                role=role,
                phone=phone,
                email=email
            )
            session.add(user)
            session.commit()
            logger.info(f"Created user: {username}")
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            session.close()
    
    def get_user_by_username(self, username):
        """الحصول على مستخدم بالاسم"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()
    
    def create_stock_item(self, serial_number, profile_code, profile_name, length, weight_per_meter):
        """إنشاء عنصر مخزون جديد"""
        session = self.get_session()
        try:
            # Generate QR code data
            qr_data = json.dumps({
                'serial_number': serial_number,
                'profile_code': profile_code,
                'profile_name': profile_name,
                'length': length,
                'weight_per_meter': weight_per_meter,
                'created_at': datetime.utcnow().isoformat()
            })
            
            # Calculate total weight
            total_weight = (length / 1000) * weight_per_meter
            
            stock_item = StockItem(
                serial_number=serial_number,
                qr_code_data=qr_data,
                profile_code=profile_code,
                profile_name=profile_name,
                length=length,
                weight_per_meter=weight_per_meter,
                total_weight=total_weight
            )
            
            session.add(stock_item)
            session.commit()
            logger.info(f"Created stock item: {serial_number}")
            return stock_item
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating stock item: {e}")
            raise
        finally:
            session.close()
    
    def get_stock_item_by_serial(self, serial_number):
        """الحصول على عنصر مخزون بالرقم التسلسلي"""
        session = self.get_session()
        try:
            return session.query(StockItem).filter(StockItem.serial_number == serial_number).first()
        finally:
            session.close()
    
    def log_scan(self, user_id, stock_item_id, scan_type):
        """تسجيل عملية مسح"""
        session = self.get_session()
        try:
            scan_log = ScanLog(
                user_id=user_id,
                stock_item_id=stock_item_id,
                scan_type=scan_type
            )
            session.add(scan_log)
            session.commit()
            logger.info(f"Logged scan: user_id={user_id}, stock_item_id={stock_item_id}, type={scan_type}")
            return scan_log
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging scan: {e}")
            raise
        finally:
            session.close()
    
    def log_usage(self, stock_item_id, technician_id, operation_type, cut_length=None, waste_weight=None, remaining_length=None, notes=None):
        """تسجيل عملية استخدام"""
        session = self.get_session()
        try:
            usage_log = UsageLog(
                stock_item_id=stock_item_id,
                technician_id=technician_id,
                operation_type=operation_type,
                cut_length=cut_length,
                waste_weight=waste_weight,
                remaining_length=remaining_length,
                notes=notes
            )
            session.add(usage_log)
            session.commit()
            logger.info(f"Logged usage: stock_item_id={stock_item_id}, operation={operation_type}")
            return usage_log
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging usage: {e}")
            raise
        finally:
            session.close()
    
    def generate_initial_qr_codes(self, count):
        """توليد QR codes أولية"""
        created_count = 0
        session = self.get_session()
        try:
            for i in range(1, count + 1):
                serial_number = f"ALU-{i:04d}"
                
                # Check if already exists
                existing = session.query(StockItem).filter(StockItem.serial_number == serial_number).first()
                if existing:
                    continue
                
                # Create stock item with default values
                stock_item = StockItem(
                    serial_number=serial_number,
                    qr_code_data=json.dumps({
                        'serial_number': serial_number,
                        'profile_code': 'DEFAULT',
                        'profile_name': 'Default Profile',
                        'length': 6000.0,
                        'weight_per_meter': 1.5,
                        'created_at': datetime.utcnow().isoformat()
                    }),
                    profile_code='DEFAULT',
                    profile_name='Default Profile',
                    length=6000.0,
                    weight_per_meter=1.5,
                    total_weight=9.0
                )
                
                session.add(stock_item)
                created_count += 1
            
            session.commit()
            logger.info(f"Generated {created_count} QR codes")
            return {'created': created_count, 'requested': count}
        except Exception as e:
            session.rollback()
            logger.error(f"Error generating QR codes: {e}")
            raise
        finally:
            session.close()
    
    def get_all_stock_items(self):
        """الحصول على جميع عناصر المخزون"""
        session = self.get_session()
        try:
            return session.query(StockItem).all()
        finally:
            session.close()
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        session = self.get_session()
        try:
            return session.query(User).all()
        finally:
            session.close()

def init_database():
    """تهيئة قاعدة البيانات وإنشاء المستخدمين الافتراضيين"""
    db = AluminiumDatabase()
    
    # Create default users only if they don't exist
    try:
        # Check if admin user exists
        admin_user = db.get_user_by_username('admin')
        if not admin_user:
            db.create_user('admin', 'Administrator', 'admin', '+201234567890', 'admin@aluminium-hub.com')
        
        # Check if worker1 user exists
        worker1_user = db.get_user_by_username('worker1')
        if not worker1_user:
            db.create_user('worker1', 'Technician 1', 'technician', '+201234567891', 'worker1@aluminium-hub.com')
        
        # Check if supervisor user exists
        supervisor_user = db.get_user_by_username('supervisor')
        if not supervisor_user:
            db.create_user('supervisor', 'Supervisor', 'supervisor', '+201234567892', 'supervisor@aluminium-hub.com')
        
        # Generate initial QR codes only if no stock items exist
        stock_items = db.get_all_stock_items()
        if len(stock_items) == 0:
            result = db.generate_initial_qr_codes(50)
            logger.info(f"Generated {result['created']} QR codes")
        
        logger.info(f"Database initialized with {len(db.get_all_users())} users and {len(db.get_all_stock_items())} stock items")
        return db
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    # Test database initialization
    db = init_database()
    print("Database initialized successfully!")
    print(f"Users: {len(db.get_all_users())}")
    print(f"Stock items: {len(db.get_all_stock_items())}")
