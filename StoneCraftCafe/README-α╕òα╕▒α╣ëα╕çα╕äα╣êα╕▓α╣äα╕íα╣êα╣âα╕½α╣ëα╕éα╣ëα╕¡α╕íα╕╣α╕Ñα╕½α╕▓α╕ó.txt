STONE CRAFT CAFE — PostgreSQL + Cloudinary
===========================================

เวอร์ชันนี้แก้ให้:
1) ข้อมูลเมนู รีวิว การจอง และข้อมูลร้านเก็บใน PostgreSQL
2) รูปเมนูและแกลเลอรีเก็บใน Cloudinary
3) Deploy/Restart Render แล้วข้อมูลและรูปไม่หาย
4) เครื่องตัวเองยังใช้ SQLite + uploads ได้ เมื่อไม่ได้ตั้ง env

ตั้งค่าบน Render
-----------------
1. สร้าง PostgreSQL ใน Render
2. เปิด Web Service > Environment
3. เพิ่ม DATABASE_URL โดยใช้ Internal Database URL ของ PostgreSQL
4. สมัคร/เข้า Cloudinary แล้วคัดลอก CLOUDINARY_URL
5. เพิ่ม Environment Variables:
   DATABASE_URL=<Internal Database URL>
   CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
   ADMIN_PASSWORD=<รหัสผ่านแอดมินใหม่>
   SECRET_KEY=<ข้อความสุ่มยาว>
6. กด Save Changes
7. Manual Deploy > Clear build cache & deploy

สำคัญ
------
- หลังย้ายไป PostgreSQL ฐานข้อมูลจะเป็นฐานใหม่ ต้องเพิ่มข้อมูลใหม่ หรือย้ายจาก SQLite ด้วยสคริปต์ migrate_sqlite_to_postgres.py
- รูปเก่าที่อยู่ใน uploads จะยังไม่ถูกย้ายไป Cloudinary อัตโนมัติ
- ห้ามใส่รหัสจริงใน GitHub ให้ใส่เฉพาะใน Environment ของ Render
