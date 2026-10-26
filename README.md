# Education Data Warehouse & BI — Bộ khung đồ án
## Trạng thái
- Dữ liệu CSV: tổng hợp/mô phỏng, được tạo có seed cố định.
- Notebook Python: profiling, làm sạch và xuất Silver.
- SQL BigQuery và project dbt: mẫu khởi đầu, cần thay `YOUR_GCP_PROJECT_ID`.
- Dashboard: Streamlit local đọc CSV Silver.
- Báo cáo Word và slide: có placeholder cho thông tin nhóm và bằng chứng chạy thực tế.
- BigQuery cloud chưa được triển khai vì nhóm chưa tạo Google Cloud Project.

## Chạy local
1. Cài Python 3.10+.
2. Cài thư viện: `pip install pandas numpy matplotlib streamlit`.
3. Chạy notebook `notebooks/education_dw_etl_prototype.ipynb` trong Colab/Jupyter. Nếu chạy trên Colab, upload thư mục `data/raw` vào `/content/data/raw`.
4. Dashboard: `pip install -r dashboard/requirements.txt` rồi `streamlit run dashboard/app.py`.

## Triển khai BigQuery/dbt
Xem `sql/` và `dbt_project/`. Tạo project/datasets, nạp CSV, thay placeholder project ID, cấu hình OAuth, sau đó chạy `dbt debug`, `dbt run`, `dbt test`. Không commit credential.

## Chỉnh sửa trước khi nộp
- Bổ sung mẫu bìa chính thức của UEL nếu giảng viên cung cấp.
- Điền tên/MSSV 2 thành viên và thông tin giảng viên.
- Chạy code và cập nhật số liệu/bằng chứng thực tế.
- Xác minh báo cáo có tối thiểu 20 trang nội dung theo yêu cầu giảng viên.
- Chỉ đưa lên Drive các tệp đã rà soát và không chứa bí mật.
