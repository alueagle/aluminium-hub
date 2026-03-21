#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aluminium Hub API
واجهة برمجية للربط مع نظام قاعدة البيانات
"""

from flask import Flask, request, jsonify, render_template_string
from database import AluminiumDatabase, init_database
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db = init_database()

# HTML Template for QR Scanner Interface
QR_SCANNER_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aluminium Hub QR Scanner</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .glass-effect {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .scan-button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 20px;
            border-radius: 15px;
            font-size: 18px;
            transition: all 0.3s ease;
        }
        .scan-button:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="p-4">
    <div class="container mx-auto max-w-4xl">
        <!-- Header -->
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold text-white mb-2">Aluminium Hub QR Scanner</h1>
            <p class="text-white text-lg">نظام مسح وتتبع عناصر الألومنيوم</p>
        </div>

        <!-- Main Scanner Interface -->
        <div class="glass-effect rounded-2xl p-6">
            <!-- User Info -->
            <div class="bg-gradient-to-r from-purple-500 to-indigo-600 text-white p-4 rounded-lg mb-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-lg font-bold">أحمد محمد</h3>
                        <p class="text-sm opacity-90">صنايعي</p>
                    </div>
                    <div class="bg-white bg-opacity-20 rounded-full p-3">
                        <i class="fas fa-user text-xl"></i>
                    </div>
                </div>
            </div>

            <!-- Scan Button -->
            <button onclick="startScan()" class="scan-button w-full mb-6">
                <i class="fas fa-qrcode text-2xl ml-2"></i>
                مسح QR Code
            </button>

            <!-- Recent Scans -->
            <div class="mb-6">
                <h3 class="text-lg font-bold mb-3">المسحات الأخيرة</h3>
                <div id="recentScans" class="space-y-3">
                    <!-- Recent scans will be loaded here -->
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="grid grid-cols-3 gap-4">
                <div class="bg-blue-50 rounded-lg p-4 text-center">
                    <i class="fas fa-qrcode text-blue-500 text-2xl mb-2"></i>
                    <p class="text-2xl font-bold text-blue-600" id="todayScans">0</p>
                    <p class="text-sm text-gray-600">مسحات اليوم</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4 text-center">
                    <i class="fas fa-cut text-green-500 text-2xl mb-2"></i>
                    <p class="text-2xl font-bold text-green-600" id="todayCuts">0</p>
                    <p class="text-sm text-gray-600">قطع اليوم</p>
                </div>
                <div class="bg-orange-50 rounded-lg p-4 text-center">
                    <i class="fas fa-recycle text-orange-500 text-2xl mb-2"></i>
                    <p class="text-2xl font-bold text-orange-600" id="todayWaste">0</p>
                    <p class="text-sm text-gray-600">فضلات اليوم</p>
                </div>
            </div>
        </div>

        <!-- Scan Result Modal -->
        <div id="scanResultModal" class="modal">
            <div class="glass-effect rounded-2xl p-6 max-w-md w-full mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">نتيجة المسح</h3>
                    <button onclick="closeScanResult()" class="text-gray-500">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div id="scanResultContent">
                    <!-- Scan result will be displayed here -->
                </div>
            </div>
        </div>

        <!-- Cut Operation Modal -->
        <div id="cutModal" class="modal">
            <div class="glass-effect rounded-2xl p-6 max-w-md w-full mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">عملية القطع</h3>
                    <button onclick="closeCutModal()" class="text-gray-500">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div id="cutModalContent">
                    <!-- Cut form will be displayed here -->
                </div>
            </div>
        </div>

        <!-- Loading Modal -->
        <div id="loadingModal" class="modal">
            <div class="glass-effect rounded-2xl p-6 text-center">
                <i class="fas fa-spinner fa-spin text-4xl text-purple-600 mb-4"></i>
                <h3 class="text-xl font-bold mb-2">جاري المعالجة...</h3>
                <p class="text-gray-600">يرجى الانتظار</p>
            </div>
        </div>
    </div>

    <script>
        let currentScanResult = null;
        let stats = {
            todayScans: 0,
            todayCuts: 0,
            todayWaste: 0
        };

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadRecentScans();
            updateStats();
        });

        function startScan() {
            // Simulate QR scan
            showLoading();
            
            setTimeout(() => {
                // Simulate finding a random item
                const mockScanResult = {
                    id: Math.floor(Math.random() * 127) + 1,
                    serial_number: "PRF-DOOR001-2024031912345-ABC123",
                    profile_code: "DOOR001",
                    item_type: "profile",
                    category: "door",
                    color: "أبيض",
                    length: 2.5,
                    original_length: 3.0,
                    weight_per_meter: 2.5,
                    total_weight: 6.25,
                    location: "ZONE-A-RACK1-POS1",
                    status: "available"
                };
                
                hideLoading();
                showScanResult(mockScanResult);
                stats.todayScans++;
                updateStats();
                addRecentScan(mockScanResult);
            }, 1500);
        }

        function showScanResult(result) {
            currentScanResult = result;
            const content = document.getElementById('scanResultContent');
            
            content.innerHTML = `
                <div class="bg-green-50 rounded-lg p-4 mb-4">
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <h4 class="font-bold text-lg">${result.serial_number}</h4>
                            <p class="text-sm text-gray-600">${result.profile_code} - ${result.color}</p>
                            <p class="text-sm text-gray-500">النوع: ${result.category} | الموقع: ${result.location}</p>
                        </div>
                        <span class="bg-green-500 text-white px-3 py-1 rounded-full text-sm">
                            ${result.status}
                        </span>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="text-gray-600">الطول الحالي:</span>
                            <span class="font-bold">${result.length}م</span>
                        </div>
                        <div>
                            <span class="text-gray-600">الطول الأصلي:</span>
                            <span class="font-bold">${result.original_length}م</span>
                        </div>
                        <div>
                            <span class="text-gray-600">الوزن/متر:</span>
                            <span class="font-bold">${result.weight_per_meter}كجم</span>
                        </div>
                        <div>
                            <span class="text-gray-600">الوزن الإجمالي:</span>
                            <span class="font-bold">${result.total_weight}كجم</span>
                        </div>
                    </div>
                </div>
                
                <div class="flex space-x-reverse space-x-2">
                    <button onclick="performCut()" class="bg-orange-500 text-white px-4 py-2 rounded-lg flex-1">
                        <i class="fas fa-cut ml-2"></i>
                        قطع
                    </button>
                    <button onclick="closeScanResult()" class="bg-gray-500 text-white px-4 py-2 rounded-lg flex-1">
                        إغلاق
                    </button>
                </div>
            `;
            
            document.getElementById('scanResultModal').classList.add('active');
        }

        function closeScanResult() {
            document.getElementById('scanResultModal').classList.remove('active');
            currentScanResult = null;
        }

        function performCut() {
            closeScanResult();
            
            const content = document.getElementById('cutModalContent');
            content.innerHTML = `
                <div class="mb-4">
                    <h4 class="font-bold mb-2">${currentScanResult.serial_number}</h4>
                    <p class="text-sm text-gray-600">الطول الحالي: ${currentScanResult.length}م</p>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-bold mb-1">الطول الجديد (متر)</label>
                        <input type="number" id="newLength" class="w-full p-3 border rounded-lg" 
                               step="0.01" max="${currentScanResult.length}" placeholder="أدخل الطول المتبقي">
                    </div>
                    <div>
                        <label class="block text-sm font-bold mb-1">ملاحظات</label>
                        <textarea id="cutNotes" class="w-full p-3 border rounded-lg" rows="2" 
                                  placeholder="ملاحظات العملية"></textarea>
                    </div>
                </div>
                
                <div class="flex space-x-reverse space-x-2 mt-4">
                    <button onclick="executeCut()" class="bg-orange-500 text-white px-4 py-2 rounded-lg flex-1">
                        <i class="fas fa-cut ml-2"></i>
                        تنفيذ القطع
                    </button>
                    <button onclick="closeCutModal()" class="bg-gray-500 text-white px-4 py-2 rounded-lg flex-1">
                        إلغاء
                    </button>
                </div>
            `;
            
            document.getElementById('cutModal').classList.add('active');
        }

        function closeCutModal() {
            document.getElementById('cutModal').classList.remove('active');
        }

        function executeCut() {
            const newLength = parseFloat(document.getElementById('newLength').value);
            const notes = document.getElementById('cutNotes').value;
            
            if (!newLength || newLength >= currentScanResult.length) {
                alert('يرجى إدخال طول جديد صحيح');
                return;
            }
            
            closeCutModal();
            showLoading();
            
            // Simulate API call
            setTimeout(() => {
                const wasteLength = currentScanResult.length - newLength;
                const wasteWeight = wasteLength * currentScanResult.weight_per_meter;
                
                hideLoading();
                
                // Show success message
                const content = document.getElementById('scanResultContent');
                content.innerHTML = `
                    <div class="bg-green-50 rounded-lg p-4">
                        <div class="text-center mb-4">
                            <i class="fas fa-check-circle text-5xl text-green-500"></i>
                        </div>
                        <h4 class="text-lg font-bold text-center mb-4">تمت العملية بنجاح!</h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span>الطول الجديد:</span>
                                <span class="font-bold">${newLength}م</span>
                            </div>
                            <div class="flex justify-between">
                                <span>طول الفضلة:</span>
                                <span class="font-bold">${wasteLength}م</span>
                            </div>
                            <div class="flex justify-between">
                                <span>وزن الفضلة:</span>
                                <span class="font-bold">${wasteWeight.toFixed(2)}كجم</span>
                            </div>
                            <div class="flex justify-between">
                                <span>تم إنشاء QR Code جديد:</span>
                                <span class="font-bold text-green-600">✓</span>
                            </div>
                        </div>
                    </div>
                    <button onclick="closeScanResult()" class="bg-green-500 text-white px-4 py-2 rounded-lg w-full mt-4">
                        حسناً
                    </button>
                `;
                
                document.getElementById('scanResultModal').classList.add('active');
                
                stats.todayCuts++;
                stats.todayWaste += wasteLength;
                updateStats();
                
            }, 2000);
        }

        function loadRecentScans() {
            // Load recent scans from API
            fetch('/api/scans/recent')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayRecentScans(data.scans);
                    }
                })
                .catch(error => {
                    console.error('Error loading recent scans:', error);
                    // Show mock data for demo
                    displayRecentScans([
                        {
                            serial_number: "PRF-DOOR001-2024031912345-ABC123",
                            scan_time: new Date().toISOString(),
                            action_taken: "cut",
                            notes: "تم القطع بنجاح"
                        }
                    ]);
                });
        }

        function displayRecentScans(scans) {
            const container = document.getElementById('recentScans');
            container.innerHTML = scans.map(scan => `
                <div class="bg-gray-50 rounded-lg p-3 fade-in">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-bold text-sm">${scan.serial_number}</h4>
                            <p class="text-xs text-gray-600">${new Date(scan.scan_time).toLocaleString('ar-SA')}</p>
                            <p class="text-xs text-gray-500">${scan.action_taken || 'view'}</p>
                        </div>
                        <i class="fas fa-qrcode text-gray-400"></i>
                    </div>
                </div>
            `).join('');
        }

        function addRecentScan(scan) {
            const container = document.getElementById('recentScans');
            const newScan = document.createElement('div');
            newScan.className = 'bg-gray-50 rounded-lg p-3 fade-in';
            newScan.innerHTML = `
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-bold text-sm">${scan.serial_number}</h4>
                        <p class="text-xs text-gray-600">${new Date().toLocaleString('ar-SA')}</p>
                        <p class="text-xs text-gray-500">scan</p>
                    </div>
                    <i class="fas fa-qrcode text-gray-400"></i>
                </div>
            `;
            container.insertBefore(newScan, container.firstChild);
            
            // Keep only last 5 scans
            while (container.children.length > 5) {
                container.removeChild(container.lastChild);
            }
        }

        function updateStats() {
            document.getElementById('todayScans').textContent = stats.todayScans;
            document.getElementById('todayCuts').textContent = stats.todayCuts;
            document.getElementById('todayWaste').textContent = stats.todayWaste.toFixed(1) + 'م';
        }

        function showLoading() {
            document.getElementById('loadingModal').classList.add('active');
        }

        function hideLoading() {
            document.getElementById('loadingModal').classList.remove('active');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """الصفحة الرئيسية لواجهة المسح"""
    return render_template_string(QR_SCANNER_TEMPLATE)

@app.route('/api/scan', methods=['POST'])
def scan_item():
    """مسح عنصر المخزون"""
    try:
        data = request.json
        serial_number = data.get('serial_number')
        user_id = data.get('user_id', 2)  # Default technician
        action = data.get('action', 'view')
        
        if not serial_number:
            return jsonify({'success': False, 'error': 'Serial number is required'})
        
        # Scan the item
        result = db.scan_stock_item(serial_number, user_id, action)
        
        return jsonify({
            'success': True,
            'item': result
        })
        
    except Exception as e:
        logger.error(f"Error scanning item: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/cut', methods=['POST'])
def cut_item():
    """معالجة عملية القطع"""
    try:
        data = request.json
        serial_number = data.get('serial_number')
        technician_id = data.get('technician_id', 2)
        new_length = data.get('new_length')
        notes = data.get('notes', '')
        
        if not serial_number or new_length is None:
            return jsonify({'success': False, 'error': 'Serial number and new length are required'})
        
        # Process cut operation
        result = db.process_cut_operation(serial_number, technician_id, new_length, notes)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error processing cut: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stock')
def get_stock():
    """الحصول على قائمة المخزون"""
    try:
        location = request.args.get('location')
        status = request.args.get('status')
        
        items = db.get_stock_items(location, status)
        
        return jsonify({
            'success': True,
            'items': items,
            'total': len(items)
        })
        
    except Exception as e:
        logger.error(f"Error getting stock: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/waste')
def get_waste():
    """الحصول على قائمة الفضلات"""
    try:
        available_only = request.args.get('available_only', 'true').lower() == 'true'
        
        items = db.get_waste_items(available_only)
        
        return jsonify({
            'success': True,
            'items': items,
            'total': len(items)
        })
        
    except Exception as e:
        logger.error(f"Error getting waste: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/scans/recent')
def get_recent_scans():
    """الحصول على المسحات الأخيرة"""
    try:
        user_id = request.args.get('user_id', 2)
        limit = int(request.args.get('limit', 10))
        
        scans = db.get_user_scan_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'scans': scans
        })
        
    except Exception as e:
        logger.error(f"Error getting recent scans: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/init', methods=['POST'])
def initialize_system():
    """تهيئة النظام"""
    try:
        data = request.json
        excel_file = data.get('excel_file')
        qr_count = data.get('qr_count', 127)
        
        # Load extraction profiles if provided
        if excel_file:
            db.load_extraction_profiles_from_excel(excel_file)
        
        # Generate initial QR codes
        result = db.generate_initial_qr_codes(qr_count)
        
        return jsonify({
            'success': True,
            'message': 'System initialized successfully',
            'qr_result': result
        })
        
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats')
def get_stats():
    """الحصول على إحصائيات النظام"""
    try:
        # Get stock count
        stock_items = db.get_stock_items()
        waste_items = db.get_waste_items()
        
        # Get today's scans (mock for now)
        today_scans = len(db.get_user_scan_history(2, 100))
        
        return jsonify({
            'success': True,
            'stats': {
                'total_stock': len(stock_items),
                'available_stock': len([item for item in stock_items if item['status'] == 'available']),
                'total_waste': len(waste_items),
                'available_waste': len([item for item in waste_items if item['status'] == 'available_for_reuse']),
                'today_scans': today_scans,
                'today_cuts': 0,  # Would need to calculate from usage logs
                'today_waste': 0  # Would need to calculate from usage logs
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting Aluminium Hub API Server...")
    print("📱 QR Scanner Interface: http://localhost:5000")
    print("🔗 API Endpoints:")
    print("   POST /api/scan - Scan QR Code")
    print("   POST /api/cut - Process cut operation")
    print("   GET  /api/stock - Get stock items")
    print("   GET  /api/waste - Get waste items")
    print("   GET  /api/scans/recent - Get recent scans")
    print("   POST /api/init - Initialize system")
    print("   GET  /api/stats - Get system stats")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
