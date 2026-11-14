import os
import cv2
from PIL import Image, ImageEnhance

# ================= CẤU HÌNH =================
THU_MUC_GOC = "anh_goc"                # Thư mục chứa toàn bộ ảnh của bạn
THU_MUC_XUAT = "avatar_tiktok_chuan"   # Thư mục xuất ảnh 720x720
KICH_THUOC_CHUAN = (720, 720)
# ============================================

os.makedirs(THU_MUC_XUAT, exist_ok=True)

# Load bộ nhận diện khuôn mặt có sẵn của OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def cat_avatar_thong_minh(input_path, output_path):
    try:
        # Đọc ảnh bằng Pillow để hỗ trợ tốt tên file tiếng Việt/ký tự đặc biệt
        pil_img = Image.open(input_path).convert("RGB")
        w, h = pil_img.size

        # Chuyển sang mảng numpy để OpenCV dò khuôn mặt
        cv_img = cv2.cvtColor(cv2.imread(input_path), cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(cv_img, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))

        if len(faces) > 0:
            # Lấy khuôn mặt lớn nhất trong ảnh (x, y, rộng, cao)
            fx, fy, fw, fh = max(faces, key=lambda rect: rect[2] * rect[3])
            tam_x = fx + fw // 2
            tam_y = fy + fh // 2 + int(fh * 0.25)  # Dịch tâm xuống nhẹ để lấy cả phần cổ/vai

            # Nếu mặt quá nhỏ (ảnh chụp xa), tự động zoom vào (khung cắt = 3.2 lần kích thước mặt)
            canh_vuong = min(w, h, int( max(fw, fh) * 3.2 ))
        else:
            # Nếu ảnh nghiêng/che mặt không dò được, dùng quy tắc cắt giữa ưu tiên nửa trên
            canh_vuong = min(w, h)
            tam_x = w // 2
            tam_y = int(h * 0.4) if h > w else h // 2

        # Tính tọa độ 4 cạnh đảm bảo không vượt ra ngoài viền ảnh gốc
        left = max(0, min(w - canh_vuong, tam_x - canh_vuong // 2))
        top = max(0, min(h - canh_vuong, tam_y - canh_vuong // 2))
        right = left + canh_vuong
        bottom = top + canh_vuong

        # Cắt vuông, resize về 720x720 và làm nét nhẹ
        img_cropped = pil_img.crop((left, top, right, bottom))
        img_resized = img_cropped.resize(KICH_THUOC_CHUAN, Image.Resampling.LANCZOS)
        img_final = ImageEnhance.Sharpness(img_resized).enhance(1.15)

        img_final.save(output_path, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"[Lỗi] {input_path}: {e}")
        return False

if __name__ == "__main__":
    files = [f for f in os.listdir(THU_MUC_GOC) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    print(f"[*] Đang xử lý thông minh {len(files)} ảnh...")

    thanh_cong = 0
    for idx, f in enumerate(files):
        in_p = os.path.join(THU_MUC_GOC, f)
        out_p = os.path.join(THU_MUC_XUAT, f"avt_tik_{idx + 1:04d}.jpg")
        if cat_avatar_thong_minh(in_p, out_p):
            thanh_cong += 1

    print(f"[HOÀN TẤT] Đã tạo {thanh_cong}/{len(files)} avatar tại: {os.path.abspath(THU_MUC_XUAT)}")
