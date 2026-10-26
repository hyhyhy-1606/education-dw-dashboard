import datetime
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Education DW BI — Cloud & Local",
    layout="wide",
    page_icon="🎓",
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "silver"
PROJECT = "data-warehouse-512306"
DATASET = "education_dw"
BQ_LOCATION = "asia-southeast1"

# ─── BigQuery client ──────────────────────────────────────────────────────────
# Streamlit Community Cloud:
# App -> Settings / Manage app -> Secrets
# Store the service-account JSON fields under [gcp_service_account].
# NEVER commit the service-account JSON key to GitHub.
@st.cache_resource
def get_bq_client():
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        credentials_info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info
        )
        return bigquery.Client(
            credentials=credentials,
            project=PROJECT,
            location=BQ_LOCATION,
        )
    except Exception:
        return None


def bq_available():
    return get_bq_client() is not None


def insert_bq_row(table_name: str, row: dict):
    """Append one row without replacing or rebuilding the existing Silver table.

    The row is aligned to the actual BigQuery schema so optional columns such as
    created_at do not cause an insert to fail when they are not present.
    """
    # Import here because `bigquery` imported inside get_bq_client() is local
    # to that function and is not visible in this function's scope.
    from google.cloud import bigquery

    client = get_bq_client()
    if client is None:
        raise RuntimeError(
            "Chưa kết nối được BigQuery. Hãy kiểm tra Streamlit Secrets "
            "và quyền của service account."
        )

    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    table = client.get_table(table_id)
    schema_by_name = {field.name: field for field in table.schema}

    unknown = sorted(set(row) - set(schema_by_name))
    # Ignore fields not in the table schema; the source form may contain
    # optional values that the current table does not store.
    payload = {key: value for key, value in row.items() if key in schema_by_name}

    missing_required = []
    for field in table.schema:
        if (
            field.mode == "REQUIRED"
            and field.name not in payload
            and field.default_value_expression is None
        ):
            missing_required.append(field.name)

    if missing_required:
        raise ValueError(
            f"Bảng {table_name} yêu cầu thêm trường bắt buộc: "
            + ", ".join(missing_required)
            + ". Hãy đối chiếu schema BigQuery trước khi ghi dữ liệu."
        )

    # Use a BigQuery LOAD job instead of insert_rows_json (Streaming Insert).
    # LOAD jobs work in BigQuery Sandbox / free tier and append only this row.
    frame_data = {}
    for field_name, value in payload.items():
        field = schema_by_name[field_name]
        if value is None:
            frame_data[field_name] = [None]
        elif field.field_type == "DATE":
            frame_data[field_name] = [pd.to_datetime(value).date()]
        elif field.field_type == "TIMESTAMP":
            frame_data[field_name] = [pd.to_datetime(value, utc=True)]
        elif field.field_type == "DATETIME":
            frame_data[field_name] = [pd.to_datetime(value).to_pydatetime()]
        elif field.field_type in ("INTEGER", "INT64"):
            frame_data[field_name] = [int(value)]
        elif field.field_type in ("FLOAT", "FLOAT64", "NUMERIC", "BIGNUMERIC"):
            frame_data[field_name] = [float(value)]
        elif field.field_type in ("BOOLEAN", "BOOL"):
            frame_data[field_name] = [bool(value)]
        else:
            frame_data[field_name] = [str(value)]

    frame = pd.DataFrame(frame_data)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=table.schema,
    )
    load_job = client.load_table_from_dataframe(
        frame,
        table_id,
        job_config=job_config,
        location=BQ_LOCATION,
    )
    load_job.result()

    client.get_table(table_id)
    return table_id


def refresh_after_write(message: str):
    st.session_state["write_success_message"] = message
    st.cache_data.clear()
    st.rerun()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.title("☁️ Google Cloud & Data")

if bq_available():
    st.sidebar.success(
        f"**GCP Project:** `{PROJECT}`\n\n"
        f"**Region:** `{BQ_LOCATION}` (Singapore)\n\n"
        f"**Dataset:** `{DATASET}`"
    )
else:
    st.sidebar.error(
        "Chưa kết nối được BigQuery. Kiểm tra mục "
        "`gcp_service_account` trong Streamlit Secrets."
    )

data_source = st.sidebar.radio(
    "Nguồn dữ liệu:",
    ("☁️ Google BigQuery Cloud (Live)", "💾 Local Silver (Offline)"),
    index=1,  # Keep Local Offline as the default.
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Làm mới dữ liệu", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if bq_available():
    if st.sidebar.button("💾 Đồng bộ Cloud → Local", use_container_width=True):
        client = get_bq_client()
        mapping = [
            ("silver_leads", "leads_clean.csv"),
            ("silver_students", "students_clean.csv"),
            ("silver_enrollments", "enrollments_clean.csv"),
            ("silver_learning_records", "learning_records_clean.csv"),
            ("silver_career_guidance", "career_guidance_clean.csv"),
            ("silver_campaigns", "campaigns_clean.csv"),
            ("silver_courses", "courses_clean.csv"),
        ]
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with st.sidebar:
                prog = st.progress(0, text="Đang đồng bộ...")
                for i, (table_name, filename) in enumerate(mapping):
                    df_sync = client.query(
                        f"SELECT * FROM `{PROJECT}.{DATASET}.{table_name}`"
                    ).to_dataframe()
                    df_sync.to_csv(DATA_DIR / filename, index=False)
                    prog.progress(
                        (i + 1) / len(mapping),
                        text=f"Đồng bộ {filename}...",
                    )
                prog.empty()
            st.cache_data.clear()
            st.sidebar.success("✅ Đồng bộ hoàn tất!")
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Đồng bộ thất bại: {exc}")


# ─── Load data ────────────────────────────────────────────────────────────────
def load_local_csv(name):
    path = DATA_DIR / name
    if not path.exists():
        st.error(f"Không tìm thấy file dữ liệu: {path}")
        st.stop()
    return pd.read_csv(path)


@st.cache_data(ttl=120)
def load_all(source):
    if source == "☁️ Google BigQuery Cloud (Live)" and bq_available():
        client = get_bq_client()
        try:
            students = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_students`"
            ).to_dataframe()
            leads = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_leads`"
            ).to_dataframe()
            enrollments = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_enrollments`"
            ).to_dataframe()
            learning = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_learning_records`"
            ).to_dataframe()
            guidance = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_career_guidance`"
            ).to_dataframe()
            campaigns = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_campaigns`"
            ).to_dataframe()
            courses = client.query(
                f"SELECT * FROM `{PROJECT}.{DATASET}.silver_courses`"
            ).to_dataframe()
            return (
                students, leads, enrollments, learning, guidance, campaigns,
                courses, True,
            )
        except Exception as exc:
            st.warning(f"⚠️ Lỗi đọc BigQuery: {exc}. Đang dùng Local Silver.")

    students = load_local_csv("students_clean.csv")
    leads = load_local_csv("leads_clean.csv")
    enrollments = load_local_csv("enrollments_clean.csv")
    learning = load_local_csv("learning_records_clean.csv")
    guidance = load_local_csv("career_guidance_clean.csv")
    campaigns = load_local_csv("campaigns_clean.csv")
    courses = load_local_csv("courses_clean.csv")
    return students, leads, enrollments, learning, guidance, campaigns, courses, False


students, leads, enrollments, learning, guidance, campaigns, courses, is_live = load_all(
    data_source
)

if "write_success_message" in st.session_state:
    st.success(st.session_state.pop("write_success_message"))

# ─── Main dashboard ───────────────────────────────────────────────────────────
st.title("EduMarketing 360° — Marketing Performance Dashboard")
if is_live:
    st.success(
        f"🟢 **Live BigQuery** | `{PROJECT}` | `{DATASET}` | `{BQ_LOCATION}`"
    )
else:
    st.info("📦 **Chế độ:** Local Silver (Offline)")

st.caption(
    "Quản trị vòng đời học viên — Marketing · Tuyển sinh · Doanh thu · Học tập · Hướng nghiệp"
)
st.caption(
    "Các biểu mẫu chỉ ghi dữ liệu khi đang chọn BigQuery Cloud (Live). "
    "Local Silver (Offline) chỉ dùng để xem dữ liệu CSV."
)

if data_source == "☁️ Google BigQuery Cloud (Live)" and not is_live:
    st.warning(
        "Bạn đã chọn BigQuery Live nhưng chưa đọc được dữ liệu BigQuery. "
        "Biểu mẫu ghi dữ liệu sẽ không hoạt động cho đến khi kết nối được."
    )

# ─── KPI ──────────────────────────────────────────────────────────────────────
lead_total = len(leads)
converted = int((leads["lead_status"] == "Converted").sum())
conversion = converted / lead_total if lead_total else 0

valid_revenue = ~enrollments["enrollment_status"].isin(["Cancelled", "Refunded"])
recognized = enrollments.loc[valid_revenue, "amount_paid_vnd"].sum()
attendance = (
    (learning["attendance_status"] == "Present").mean() if len(learning) else 0
)
total_students = len(students)
total_enroll = len(enrollments)

k1, k2, k3 = st.columns(3)
k1.metric("👥 Học viên", f"{total_students:,}")
k2.metric("📋 Đăng ký", f"{total_enroll:,}")
k3.metric("📣 Leads", f"{lead_total:,}")

k4, k5, k6 = st.columns(3)
k4.metric("✅ Chuyển đổi", f"{converted:,}")
k5.metric("📊 Tỷ lệ CĐ", f"{conversion:.1%}")
k6.metric(
    "💰 Doanh thu (VND)",
    f"{recognized:,.0f}",
    help=f"Doanh thu đầy đủ: {recognized:,.0f} VND",
)

st.markdown("---")

tab_dash, tab_form_student, tab_form_enroll, tab_form_lead = st.tabs(
    ["📊 Dashboard", "➕ Thêm học viên mới", "📝 Đăng ký khóa học", "📣 Thêm Lead mới"]
)

# ─── Tab 1: Dashboard ─────────────────────────────────────────────────────────
with tab_dash:
    st.subheader("📈 1. Marketing & Tuyển sinh")
    camp_summary = campaigns.merge(
        leads.groupby("campaign_id")
        .agg(total_leads=("lead_id", "nunique"))
        .reset_index(),
        on="campaign_id",
        how="left",
    )
    camp_summary["total_leads"] = camp_summary["total_leads"].fillna(0)

    cm1, cm2 = st.columns([3, 2])
    with cm1:
        st.markdown("**Leads theo chiến dịch**")
        st.bar_chart(camp_summary.set_index("campaign_name")["total_leads"])
    with cm2:
        st.markdown("**Ngân sách & hiệu quả kênh**")
        st.dataframe(
            camp_summary[
                ["campaign_name", "channel", "marketing_spend", "total_leads"]
            ],
            use_container_width=True,
        )

    st.markdown("---")
    st.subheader("💰 2. Tuyển sinh & Doanh thu")
    rev = enrollments.copy()
    rev["recognized_revenue_vnd"] = rev["amount_paid_vnd"].where(
        ~rev["enrollment_status"].isin(["Cancelled", "Refunded"]), 0
    )
    cr1, cr2 = st.columns([3, 2])
    with cr1:
        st.markdown("**Doanh thu theo môn học (VND)**")
        st.bar_chart(rev.groupby("course_name")["recognized_revenue_vnd"].sum())
    with cr2:
        st.markdown("**Cơ cấu trạng thái đăng ký**")
        st.dataframe(
            rev.groupby(["course_name", "enrollment_status"])
            .agg(
                dk=("enrollment_id", "nunique"),
                rev=("recognized_revenue_vnd", "sum"),
            )
            .reset_index(),
            use_container_width=True,
        )

    st.markdown("---")
    st.subheader("🎓 3. Học tập & Đào tạo")
    cl1, cl2 = st.columns(2)
    cl1.metric("Tỷ lệ điểm danh", f"{attendance:.1%}")
    cl2.metric("Điểm TB", f"{learning['assessment_score'].mean():.2f}/10")
    st.bar_chart(learning.groupby("course_id")["assessment_score"].mean())

    st.markdown("---")
    st.subheader("🧭 4. Tư vấn Hướng nghiệp")
    cg1, cg2 = st.columns([3, 2])
    with cg1:
        st.bar_chart(guidance["guidance_type"].value_counts())
    with cg2:
        st.dataframe(
            guidance.groupby("outcome").agg(
                sessions=("guidance_id", "count"),
                avg_sat=("satisfaction_score", "mean"),
            ).reset_index(),
            use_container_width=True,
        )


# ─── Tab 2: Add student ────────────────────────────────────────────────────────
with tab_form_student:
    st.subheader("➕ Nhập thông tin học viên mới")
    if not is_live:
        st.info(
            "Bạn đang ở chế độ Local Offline. Hãy chọn **Google BigQuery Cloud (Live)** "
            "ở thanh bên để lưu bản ghi lên BigQuery."
        )

    with st.form("form_add_student", clear_on_submit=True):
        fa1, fa2 = st.columns(2)
        with fa1:
            s_gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Chưa xác định"])
            s_dob = st.date_input(
                "Ngày sinh",
                value=datetime.date(2008, 1, 1),
                min_value=datetime.date(1995, 1, 1),
                max_value=datetime.date(2012, 12, 31),
            )
        with fa2:
            s_grade = st.selectbox("Khối lớp", [10, 11, 12])
            s_district = st.text_input("Quận/Huyện", placeholder="Ví dụ: Quận 1")
            s_school = st.text_input("Mã trường (tuỳ chọn)", placeholder="Ví dụ: SCH_001")

        submitted_student = st.form_submit_button(
            "💾 Lưu học viên lên BigQuery",
            use_container_width=True,
            type="primary",
            disabled=not is_live or not bq_available(),
        )

    if submitted_student:
        if not s_district.strip():
            st.error("Vui lòng nhập Quận/Huyện.")
        else:
            new_id = "STU_" + uuid.uuid4().hex[:6].upper()
            row = {
                "student_id": new_id,
                "gender": s_gender,
                "date_of_birth": s_dob.isoformat(),
                "grade": s_grade,
                "school_id": s_school.strip() or "SCH_UNKNOWN",
                "district": s_district.strip(),
            }
            try:
                with st.spinner("Đang lưu học viên lên BigQuery..."):
                    insert_bq_row("silver_students", row)
                refresh_after_write(f"✅ Đã thêm học viên `{new_id}` vào BigQuery.")
            except Exception as exc:
                st.error(f"Không thể lưu học viên: {exc}")


# ─── Tab 3: Course enrollment ─────────────────────────────────────────────────
with tab_form_enroll:
    st.subheader("📝 Đăng ký khóa học cho học viên")
    if not is_live:
        st.info(
            "Bạn đang ở chế độ Local Offline. Hãy chọn **Google BigQuery Cloud (Live)** "
            "ở thanh bên để lưu bản ghi lên BigQuery."
        )

    student_options = students["student_id"].dropna().astype(str).tolist()
    course_options = {
        str(row["course_name"]): (row["course_id"], row["standard_fee_vnd"])
        for _, row in courses.iterrows()
    }
    campaign_options = campaigns["campaign_id"].dropna().astype(str).tolist()

    if not student_options:
        st.warning("Chưa có học viên để đăng ký khóa học.")
    elif not course_options:
        st.warning("Chưa có khóa học trong bảng silver_courses.")
    elif not campaign_options:
        st.warning("Chưa có chiến dịch trong bảng silver_campaigns.")
    else:
        with st.form("form_add_enrollment", clear_on_submit=True):
            fe1, fe2 = st.columns(2)
            with fe1:
                e_student = st.selectbox("Mã học viên", student_options)
                e_course_name = st.selectbox("Khóa học", list(course_options.keys()))
                e_status = st.selectbox(
                    "Trạng thái", ["Confirmed", "Waitlisted", "Pending"]
                )
            with fe2:
                e_campaign = st.selectbox("Chiến dịch Marketing", campaign_options)
                e_date = st.date_input("Ngày đăng ký", value=datetime.date.today())
                e_discount = st.number_input(
                    "Giảm giá (VND)", min_value=0, value=0, step=100000
                )

            st.markdown(
                "*(Học phí niêm yết sẽ tự động lấy theo khóa học được chọn.)*"
            )
            submitted_enroll = st.form_submit_button(
                "💾 Lưu đăng ký lên BigQuery",
                use_container_width=True,
                type="primary",
                disabled=not is_live or not bq_available(),
            )

        if submitted_enroll:
            course_id, list_price = course_options[e_course_name]
            list_price = float(list_price)
            discount = float(e_discount)
            amount_paid = max(0.0, list_price - discount)
            new_eid = "ENR_" + uuid.uuid4().hex[:8].upper()
            row = {
                "enrollment_id": new_eid,
                "student_id": e_student,
                "lead_id": None,
                "campaign_id": e_campaign,
                "course_id": str(course_id),
                "course_name": e_course_name,
                "enrollment_date": e_date.isoformat(),
                "enrollment_status": e_status,
                "list_price_vnd": list_price,
                "discount_vnd": discount,
                "amount_paid_vnd": amount_paid,
            }
            try:
                with st.spinner("Đang lưu đăng ký lên BigQuery..."):
                    insert_bq_row("silver_enrollments", row)
                refresh_after_write(
                    f"✅ Đã đăng ký khóa học `{e_course_name}` cho học viên "
                    f"`{e_student}`. Mã đăng ký: `{new_eid}`. "
                    f"Doanh thu dự kiến ghi nhận: {amount_paid:,.0f} VND."
                )
            except Exception as exc:
                st.error(f"Không thể lưu đăng ký: {exc}")


# ─── Tab 4: Add lead ──────────────────────────────────────────────────────────
with tab_form_lead:
    st.subheader("📣 Ghi nhận khách hàng tiềm năng (Lead) mới")
    if not is_live:
        st.info(
            "Bạn đang ở chế độ Local Offline. Hãy chọn **Google BigQuery Cloud (Live)** "
            "ở thanh bên để lưu bản ghi lên BigQuery."
        )

    student_options = students["student_id"].dropna().astype(str).tolist()
    campaign_options = campaigns["campaign_id"].dropna().astype(str).tolist()

    with st.form("form_add_lead", clear_on_submit=True):
        fl1, fl2 = st.columns(2)
        with fl1:
            l_student = st.selectbox(
                "Học viên liên quan",
                ["(Khách mới, chưa có trong hệ thống)"] + student_options,
            )
            l_source = st.selectbox(
                "Nguồn Lead",
                [
                    "Facebook Ads", "Google Ads", "Zalo Ads", "Website",
                    "Referral (Giới thiệu)", "Hotline", "Khác",
                ],
            )
            l_status = st.selectbox(
                "Trạng thái Lead",
                ["New", "Contacted", "Qualified", "Converted", "Lost"],
            )
        with fl2:
            if campaign_options:
                l_campaign = st.selectbox("Chiến dịch Marketing", campaign_options)
            else:
                l_campaign = None
                st.warning("Chưa có chiến dịch trong bảng silver_campaigns.")
            l_date = st.date_input("Ngày phát sinh Lead", value=datetime.date.today())
            l_attempts = st.number_input(
                "Số lần đã liên hệ", min_value=0, max_value=50, value=1
            )
            l_hours = st.number_input(
                "Thời gian phản hồi đầu (giờ)",
                min_value=0.0,
                max_value=72.0,
                value=2.0,
                step=0.5,
            )

        submitted_lead = st.form_submit_button(
            "💾 Lưu Lead lên BigQuery",
            use_container_width=True,
            type="primary",
            disabled=not is_live or not bq_available() or not campaign_options,
        )

    if submitted_lead:
        new_lid = "LEAD_" + uuid.uuid4().hex[:8].upper()
        student_value = None if l_student.startswith("(") else l_student
        row = {
            "lead_id": new_lid,
            "student_id": student_value,
            "campaign_id": l_campaign,
            "lead_created_date": l_date.isoformat(),
            "lead_source": l_source,
            "lead_status": l_status,
            "contact_attempts": int(l_attempts),
            "first_response_hours": float(l_hours),
        }
        try:
            with st.spinner("Đang lưu Lead lên BigQuery..."):
                insert_bq_row("silver_leads", row)
            refresh_after_write(
                f"✅ Đã ghi nhận Lead `{new_lid}`. Nguồn: {l_source}; "
                f"chiến dịch: {l_campaign}; trạng thái: {l_status}."
            )
        except Exception as exc:
            st.error(f"Không thể lưu Lead: {exc}")
