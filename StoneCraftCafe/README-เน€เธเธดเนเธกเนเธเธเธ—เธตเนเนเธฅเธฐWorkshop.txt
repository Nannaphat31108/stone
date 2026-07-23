อัปเดตเวอร์ชัน Google Maps + Workshop

เพิ่มให้แล้ว:
1. Admin > ข้อมูลร้าน
   - Google Maps Embed URL
   - ลิงก์เปิดแผนที่/นำทาง
   - รองรับการวางทั้ง Embed URL และโค้ด iframe จาก Google Maps
   - แสดงตัวอย่างแผนที่ในแอดมิน

2. หน้าเว็บไซต์ลูกค้า
   - /contact แสดงแผนที่แบบ Dashboard
   - ปุ่มเปิดเส้นทาง Google Maps
   - /workshops แสดง Workshop และกิจกรรมพิเศษ
   - /workshops/<id> หน้ารายละเอียดกิจกรรม

3. Admin > Workshop / กิจกรรม
   - เพิ่ม แก้ไข ลบ
   - ไทย/อังกฤษ
   - วันที่ เวลา สถานที่ ราคา จำนวนคน
   - ลิงก์จอง รูป Cloudinary
   - สถานะเผยแพร่และ Featured

Deploy:
git add .
git commit -m "Add Google Maps dashboard and workshops"
git push origin main

Render:
Root Directory: StoneCraftCafe
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app

หลัง Deploy เข้า /admin/settings เพื่อใส่แผนที่ และ /admin/workshops เพื่อเพิ่มกิจกรรม
