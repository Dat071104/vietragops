# Chunking Report

## Overview

- Input documents: 37
- Processed sections: 481

## Chunk counts by config

- `small`: 1036 chunks
  - tokens avg/min/max: 219.69 / 7 / 300
  - duplicate rate: 0.0010
- `medium`: 695 chunks
  - tokens avg/min/max: 289.69 / 7 / 500
  - duplicate rate: 0.0014
- `large`: 572 chunks
  - tokens avg/min/max: 335.78 / 7 / 800
  - duplicate rate: 0.0017

## Missing metadata summary

- `small` missing source URLs: 0
- `small` missing heading paths: 0
- `medium` missing source URLs: 0
- `medium` missing heading paths: 0
- `large` missing source URLs: 0
- `large` missing heading paths: 0

## Abnormal chunks found

- `small`: 0 flagged (none)
- `medium`: 0 flagged (none)
- `large`: 0 flagged (none)

## PDF page preservation notes

- `small`: 583 / 583 PDF chunks retain page metadata
- `medium`: 415 / 415 PDF chunks retain page metadata
- `large`: 350 / 350 PDF chunks retain page metadata

## Examples of good chunks

- `ug_course_registration_guide_s001_c001` from `ug_course_registration_guide`
  - heading path: Hướng dẫn SV đăng ký môn học > Hướng dẫn SV đăng ký môn học
  - text preview: Hướng dẫn SV đăng ký môn học > Hướng dẫn SV đăng ký môn học Sinh viên truy cập vào Hệ thống thông tin sinh viên ( https://student.tdt.edu.vn/ ). Trước khi bắt đầu ĐKMH, SV phải xem thông báo thời gian đăng ký cụ thể của 
- `ug_training_reg_k2021_pdf_s001_c001` from `ug_training_reg_k2021_pdf`
  - heading path: TỔNG LIÊN ĐOÀN LAO ĐỘNG VIỆT NAM
  - text preview: TỔNG LIÊN ĐOÀN LAO ĐỘNG VIỆT NAM TỔNG LIÊN ĐOÀN LAO ĐỘNG VIỆT NAM TRƯỜNG ĐẠI HỌC TÔN ĐỨC THẮNG CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập – Tự do – Hạnh phúc QUY CHẾ TỔ CHỨC VÀ QUẢN LÝ ĐÀO TẠO TRÌNH ĐỘ ĐẠI HỌC (Ban hành 

## Examples needing manual review

- `it_cs_curriculum_2018_s001_c001` from `it_cs_curriculum_2018`
  - heading path: Chương trình đào tạo 2018, ngành Khoa học máy tính, mã ngành 7480101, chương trình tiêu chuẩn
  - text preview: Chương trình đào tạo 2018, ngành Khoa học máy tính, mã ngành 7480101, chương trình tiêu chuẩn STT Khối kiến thức Tổng số tín chỉ Bắt buộc Tự chọn 1 Kiến thức giáo dục đại cương: 44 tín chỉ 1.1 Môn lý luận chính trị, pháp
- `tdtu_major_catalog_s001_c001` from `tdtu_major_catalog`
  - heading path: Danh mục ngành học
  - text preview: Danh mục ngành học Danh mục ngành học

## Recommended default chunk config for Phase 4

- Recommended default: `medium`
- Rationale: it offers a better balance between retrieval precision and context coverage than the smaller or larger settings for the current corpus, while keeping duplicate rates low and preserving heading/page metadata cleanly.
