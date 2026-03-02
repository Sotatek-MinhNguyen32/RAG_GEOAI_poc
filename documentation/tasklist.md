# Task List

## Tổng quan

| Vai trò | Man-day |
|---------|---------|
| BE (API+AI) | 7.5 |
| BE (Worker) | 2.5 |
| Setup | 2.5 |
| **Tổng** | **12.5** |

## Chi tiết

| No | Giai đoạn | Nội dung công việc | BE(API+AI) | BE(Worker) | Setup | Ghi chú | Người thực hiện |
|----|-----------|---------------------|------------|------------|-------|---------|-----------------|
| 1 | Tiền xử lý | Thiết lập Redis + Celery | 0 | 0.5 | 0.5 | Xây dựng nền tảng xử lý bất đồng bộ | Minh Nguyễn |
| 2 | Tiền xử lý | API lấy dữ liệu từ S3 + tạo Job | 1 | 0 | 0 | Tạo job từ dữ liệu có sẵn trên S3 | Tư Nguyễn |
| 3 | Ingestion | Cấu hình môi trường Elasticsearch | 0 | 0 | 1 | Khách setup trên AWS (cần cung cấp hướng dẫn setup cho khách) | Thành Ngô |
| 4 | Ingestion | Setup Jina Serving API | 0.75 | 0 | 0.5 | Cần EC2 do khách cung cấp (cần cung cấp cấu hình sv để khách bật) | Tư Nguyễn |
| 5 | Ingestion | Setup Qwen vLLM Serving | 0.75 | 0 | 0.5 | Cần GPU EC2 do khách cung cấp | Tư Nguyễn |
| 6 | Ingestion | Worker: Xây dựng pipeline xử lý AI | 1 | 1 | 0 | Sinh text + tạo Embedding | Minh Nguyễn |
| 7 | Ingestion | Đăng ký index vào Elasticsearch | 0.5 | 0.5 | 0 | Lưu metadata + text | Tư Nguyễn |
| 8 | Ingestion | Lưu vector vào Qdrant | 0.5 | 0.5 | 0 | Lưu vector phục vụ semantic search | Minh Nguyễn |
| 9 | Search | Branch A: Semantic Search | 1 | 0 | 0 | Embedding query → Qdrant Top-K | Thành Ngô |
| 10 | Search | Branch B: Lexical & Geo Search | 1 | 0 | 0 | Tìm kiếm bằng Elasticsearch | Tư Nguyễn |
| 11 | Search | Hợp nhất kết quả bằng RRF + gọi LLM | 1 | 0 | 0 | Logic Hybrid RAG | Minh Nguyễn |
