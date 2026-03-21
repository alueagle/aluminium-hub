#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aluminium Hub System Runner
تشغيل النظام المتكامل
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def check_requirements():
    """فحص المتطلبات"""
    print("🔍 فحص المتطلبات...")
    
    try:
        import flask
        import sqlalchemy
        import pandas
        import qrcode
        print("✅ جميع المتطلبات مثبتة")
        return True
    except ImportError as e:
        print(f"❌ متطلب مفقود: {e}")
        print("📦 تثبيت المتطلبات:")
        print("pip install -r requirements_full.txt")
        return False

def initialize_database():
    """تهيئة قاعدة البيانات"""
    print("🗄️ تهيئة قاعدة البيانات...")
    
    try:
        from database import init_database
        
        # Check if Excel file exists
        excel_file = "final egypt aluminium extraction profile all compans.xlsx"
        if os.path.exists(excel_file):
            print(f"📊 تحميل ملف الاستخراج: {excel_file}")
        
        db = init_database()
        
        # Try to load extraction profiles
        if os.path.exists(excel_file):
            try:
                db.load_extraction_profiles_from_excel(excel_file)
                print("✅ تم تحميل ملفات الاستخراج بنجاح")
            except Exception as e:
                print(f"⚠️ خطأ في تحميل ملفات الاستخراج: {e}")
        
        # Generate initial QR codes
        try:
            result = db.generate_initial_qr_codes(127)
            print(f"✅ تم توليد {result['created']} من {result['requested']} QR code")
        except Exception as e:
            print(f"⚠️ خطأ في توليد QR codes: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
        return False

def start_api_server():
    """بدء خادم API"""
    print("🚀 بدء خادم API...")
    
    try:
        from api import app
        
        def run_server():
            print("📱 واجهة المسح: http://localhost:5000")
            print("🔗 نقاط النهاية:")
            print("   POST /api/scan - مسح QR Code")
            print("   POST /api/cut - معالجة القطع")
            print("   GET  /api/stock - عرض المخزون")
            print("   GET  /api/waste - عرض الفضلات")
            app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
        # Run server in separate thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a bit for server to start
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في بدء خادم API: {e}")
        return False

def open_browser():
    """فتح المتصفح"""
    print("🌐 فتح المتصفح...")
    
    try:
        import webbrowser
        webbrowser.open('http://localhost:5000')
        print("✅ تم فتح المتصفح")
        return True
    except Exception as e:
        print(f"⚠️ لم يتم فتح المتصفح تلقائياً: {e}")
        print("🔗 يرجى فتح الرابط يدوياً: http://localhost:5000")
        return False

def show_system_info():
    """عرض معلومات النظام"""
    print("\n" + "="*60)
    print("🏭 Aluminium Hub Stock Management System")
    print("="*60)
    print("📋 المميزات:")
    print("   • قاعدة بيانات SQLAlchemy متكاملة")
    print("   • توليد QR Codes تلقائي")
    print("   • تتبع الفضلات عند القطع")
    print("   • حساب الوزن آلياً")
    print("   • واجهة ويب تفاعلية")
    print("   • سجل كامل للعمليات")
    print("="*60)

def main():
    """الدالة الرئيسية"""
    show_system_info()
    
    # Check requirements
    if not check_requirements():
        input("اضغط Enter للخروج...")
        return
    
    # Initialize database
    if not initialize_database():
        input("اضغط Enter للخروج...")
        return
    
    # Start API server
    if not start_api_server():
        input("اضغط Enter للخروج...")
        return
    
    # Open browser immediately after server starts
    print("🌐 فتح المتصفح تلقائياً...")
    try:
        import webbrowser
        import threading
        def delayed_browser_open():
            time.sleep(3)  # Wait 3 seconds for server to fully start
            webbrowser.open('http://localhost:5000')
            print("✅ تم فتح المتصفح على http://localhost:5000")
        
        browser_thread = threading.Thread(target=delayed_browser_open, daemon=True)
        browser_thread.start()
    except Exception as e:
        print(f"⚠️ لم يتم فتح المتصفح تلقائياً: {e}")
        print("🔗 يرجى فتح الرابط يدوياً: http://localhost:5000")
    
    print("\n✅ النظام يعمل الآن!")
    print("📱 الواجهة: http://localhost:5000")
    print("⏹️  للإيقاف: اضغط Ctrl+C")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  تم إيقاف النظام بنجاح")

if __name__ == "__main__":
    main()
