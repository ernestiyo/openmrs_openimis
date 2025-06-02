import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date, timedelta

# Constants
BASE_URL = "http://localhost:8000"

# Dropdown Options untuk Klinik Desa
CHIEF_COMPLAINTS = [
    "Batuk", "Demam", "Pusing", "Mual", "Sesak Napas", "Lainnya"
]

# List obat dan harga dalam Rupiah
MEDICATIONS = {
    "Paracetamol 500mg (10 tablet)": 15000,
    "Amoxicillin 500mg (10 kapsul)": 25000,
    "CTM 4mg (10 tablet)": 8000,
    "Antasida (botol)": 20000,
    "OBH (botol)": 18000,
    "Vitamin C 500mg (10 tablet)": 12000,
    "Dexamethasone 0.5mg (10 tablet)": 10000,
    "Omeprazole 20mg (10 kapsul)": 30000
}

# Configure the page with consistent styling
st.set_page_config(
    page_title="Integrasi OpenMRS-OpenIMIS",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper Functions
def make_request(method, endpoint, data=None, params=None):
    """Centralized request handling with error management"""
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.request(method, url, json=data, params=params)
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Tidak dapat terhubung ke server. Pastikan server sedang berjalan.")
        return None

def fetch_patients():
    """Fetch all patients with error handling"""
    response = make_request("GET", "patients")
    if response and response.status_code == 200:
        return response.json()
    return []

def fetch_encounters():
    """Fetch all encounters with error handling"""
    response = make_request("GET", "encounters")
    if response and response.status_code == 200:
        return response.json()
    return []

def fetch_claims():
    """Fetch all claims with error handling"""
    response = make_request("GET", "claims")
    if response and response.status_code == 200:
        return response.json()
    return []

def generate_month_options(months_back=12):
    """Generate a list of recent months for reporting"""
    today = date.today()
    months = []
    for i in range(months_back):
        current = today.replace(day=1) - timedelta(days=i*30)
        months.append(current.strftime("%Y-%m"))
    return sorted(months, reverse=True)

def apply_custom_css():
    """Apply custom CSS for consistent styling"""
    st.markdown("""
        <style>
        .main .block-container { padding-top: 2rem; }
        h1 { margin-bottom: 2rem; }
        .stAlert { margin-top: 1rem; }
        .row-widget.stButton { margin-top: 1rem; }
        </style>
    """, unsafe_allow_html=True)

def confirm_action(message="Apakah Anda yakin?", confirmation_text="YA"):
    """Reusable confirmation dialog"""
    col1, col2 = st.columns([3, 1])
    with col1:
        user_confirmation = st.text_input(
            f'{message} Ketik "{confirmation_text}" untuk konfirmasi:',
            key=f"confirm_{message}"
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        return st.button("Konfirmasi", disabled=user_confirmation != confirmation_text)

def init_session_state():
    """Initialize session state variables"""
    if 'custom_procedures' not in st.session_state:
        st.session_state.custom_procedures = []
    if 'custom_medications' not in st.session_state:
        st.session_state.custom_medications = []
    if 'custom_complaints' not in st.session_state:
        st.session_state.custom_complaints = []

def reset_patient_form():
    """Reset the patient form state"""
    st.session_state.custom_complaints = []

def show_register_patient():
    st.header("🧑‍⚕️ Pendaftaran Pasien")
    st.write("Masukkan informasi pasien baru di bawah ini")

    # Initialize session state for custom complaints
    init_session_state()

    with st.form("patient_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input(
                "Nama Lengkap",
                placeholder="Masukkan nama lengkap pasien",
                help="Wajib diisi: Nama lengkap sesuai KTP"
            )
        with col2:
            age = st.number_input(
                "Usia",
                min_value=0,
                max_value=120,
                help="Wajib diisi: Usia pasien saat ini"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            gender = st.selectbox(
                "Jenis Kelamin",
                options=["", "Laki-laki", "Perempuan", "Lainnya"],
                help="Wajib diisi: Jenis kelamin pasien"
            )
        with col4:
            st.write("") # Spacing for alignment
        
        # Chief complaint section
        st.subheader("Keluhan Utama")
        
        # Display existing complaints
        if st.session_state.custom_complaints:
            st.write("Keluhan yang dipilih:")
            for complaint in st.session_state.custom_complaints:
                st.info(f"• {complaint}")
        
        # Standard complaints
        selected_complaints = []
        for complaint in CHIEF_COMPLAINTS[:-1]:  # Excluding "Lainnya"
            if st.checkbox(complaint, key=f"complaint_{complaint}"):
                selected_complaints.append(complaint)
        
        # Custom complaint section
        if st.checkbox("Lainnya", key="other_complaint"):
            custom_complaint = st.text_area(
                "Keluhan Lainnya",
                placeholder="Deskripsikan keluhan lainnya",
                help="Tulis keluhan yang tidak ada dalam daftar"
            )
            if custom_complaint:
                if custom_complaint not in selected_complaints:
                    selected_complaints.append(custom_complaint)
        
        # Submit button
        submitted = st.form_submit_button("🆕 Daftar Pasien")

        if submitted:
            if not full_name or not gender or not selected_complaints:
                st.error("❌ Harap isi semua kolom yang wajib diisi.")
                return

            # Join all complaints with semicolon
            chief_complaint = "; ".join(selected_complaints)

            patient_data = {
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "chief_complaint": chief_complaint
            }

            response = make_request("POST", "patient", data=patient_data)
            if response and response.status_code == 201:
                result = response.json()
                st.success("✅ Pasien berhasil didaftarkan!")
                
                # Reset custom complaints after successful submission
                reset_patient_form()
                
                with st.expander("Lihat Detail Pasien", expanded=True):
                    st.json(result["data"])

def show_record_encounter():
    st.header("📝 Catat Kunjungan Medis")
    st.write("Catat kunjungan medis baru untuk pasien yang sudah terdaftar")

    patients = fetch_patients()
    if not patients:
        st.warning("⚠️ Tidak ada pasien yang terdaftar. Harap daftarkan pasien terlebih dahulu.")
        if st.button("Ke Pendaftaran Pasien"):
            st.session_state.app_section = "Pendaftaran Pasien"
            st.experimental_rerun()
        return

    with st.form("encounter_form", clear_on_submit=True):
        # Patient selection with search
        patient_options = {
            f"{p['full_name']} (ID: {p['patient_id']})": p['patient_id']
            for p in patients
        }
        selected_patient = st.selectbox(
            "Pilih Pasien",
            options=list(patient_options.keys()),
            help="Pilih pasien untuk kunjungan ini"
        )
        
        patient_id = patient_options[selected_patient]

        col1, col2 = st.columns(2)
        with col1:
            visit_date = st.date_input(
                "Tanggal Kunjungan",
                value=datetime.now(),
                max_value=date.today()
            )
        with col2:
            attending_clinician = st.text_input(
                "Dokter Penanggung Jawab",
                placeholder="Masukkan nama dokter (opsional)"
            )

        diagnosis = st.text_area(
            "Diagnosis",
            placeholder="Masukkan diagnosis lengkap",
            help="Wajib diisi: Diagnosis medis untuk kunjungan ini"
        )
        
        # Medication selection section
        st.subheader("Pengobatan/Medikasi")
        selected_medications = []
        total_price = 0
        
        # Standard medications dropdown
        st.write("Pilih Obat:")
        for med_name, price in MEDICATIONS.items():
            if st.checkbox(f"{med_name} - Rp {price:,}", key=f"med_{med_name}"):
                selected_medications.append(f"{med_name} (Rp {price:,})")
                total_price += price
        
        # Custom medication
        if st.checkbox("Obat Lainnya", key="other_medication"):
            custom_med = st.text_area(
                "Rincian Obat Lainnya",
                placeholder="Masukkan nama obat, dosis, dan jumlah",
                help="Tulis obat yang tidak ada dalam daftar"
            )
            custom_price = st.number_input(
                "Harga Obat Lainnya (Rp)",
                min_value=0,
                step=1000,
                help="Masukkan harga dalam Rupiah"
            )
            if custom_med and custom_price > 0:
                selected_medications.append(f"{custom_med} (Rp {custom_price:,})")
                total_price += custom_price

        # Display total price
        if total_price > 0:
            st.info(f"💰 Total Biaya Obat: Rp {total_price:,}")

        treatment = "Medikasi yang diresepkan:\n" + "\n".join([f"- {med}" for med in selected_medications]) if selected_medications else ""
        
        # Additional treatment notes
        additional_notes = st.text_area(
            "Catatan Tambahan Pengobatan",
            placeholder="Masukkan instruksi atau catatan tambahan pengobatan",
            help="Opsional: Tambahkan catatan khusus untuk pengobatan"
        )
        
        if additional_notes:
            treatment += f"\n\nCatatan Tambahan:\n{additional_notes}"

        submitted = st.form_submit_button("💾 Catat Kunjungan")

        if submitted:
            if not diagnosis or not selected_medications:
                st.error("❌ Harap isi diagnosis dan pilih setidaknya satu obat.")
                return

            encounter_data = {
                "patient_id": patient_id,
                "diagnosis": diagnosis,
                "treatment": treatment,
                "visit_date": visit_date.isoformat(),
                "attending_clinician": attending_clinician if attending_clinician else None,
                "total_price": total_price  # Adding price to the data
            }

            response = make_request("POST", "encounter", data=encounter_data)
            if response and response.status_code == 201:
                result = response.json()
                st.success("✅ Kunjungan medis berhasil dicatat!")
                
                with st.expander("Lihat Detail Kunjungan", expanded=True):
                    st.json(result["data"])

def show_submit_claim():
    st.header("💰 Ajukan & Proses Klaim Asuransi")
    
    tab1, tab2 = st.tabs(["📤 Ajukan Klaim Baru", "✅ Proses Klaim"])
    
    with tab1:
        st.write("Buat dan ajukan Klaim FHIR dari kunjungan yang sudah ada")

        encounters = fetch_encounters()
        if not encounters:
            st.warning("⚠️ Tidak ada kunjungan yang tercatat. Harap catat kunjungan terlebih dahulu.")
            if st.button("Ke Catat Kunjungan"):
                st.session_state.app_section = "Catat Kunjungan"
                st.experimental_rerun()
            return

        # Search/filter encounters
        search_term = st.text_input(
            "🔍 Cari Kunjungan",
            placeholder="Cari berdasarkan nama pasien atau diagnosis"
        ).lower()

        filtered_encounters = encounters
        if search_term:
            filtered_encounters = [
                enc for enc in encounters
                if search_term in enc['patient_name'].lower() or
                   search_term in enc['diagnosis'].lower()
            ]

        if not filtered_encounters:
            st.info("Tidak ada kunjungan yang cocok dengan kriteria pencarian Anda.")
            return

        encounter_options = {
            f"{enc['patient_name']} - {enc['visit_date']} ({enc['diagnosis']})": enc['encounter_id']
            for enc in filtered_encounters
        }

        selected_encounter = st.selectbox(
            "Pilih Kunjungan",
            options=list(encounter_options.keys()),
            help="Pilih kunjungan untuk menghasilkan klaim"
        )

        if selected_encounter:
            encounter_id = encounter_options[selected_encounter]
            
            # Get the FHIR Claim preview
            claim_response = make_request("GET", f"encounters/{encounter_id}/claim")
            if claim_response and claim_response.status_code == 200:
                claim_data = claim_response.json()
                
                st.subheader("📋 Prabaca Klaim FHIR")
                with st.expander("Lihat Detail Klaim", expanded=True):
                    st.json(claim_data)
                
                if st.button("📤 Ajukan Klaim"):
                    submit_response = make_request("POST", "claim", data=claim_data)
                    if submit_response and submit_response.status_code == 201:
                        result = submit_response.json()
                        st.success("✅ Klaim berhasil diajukan!")
                        st.json(result)
                    else:
                        st.error("❌ Gagal mengajukan klaim. Silakan coba lagi.")

    with tab2:
        st.write("Proses klaim yang sudah diajukan")
        claims = fetch_claims()
        
        if not claims:
            st.info("⚠️ Tidak ada klaim yang perlu diproses.")
            return
        
        # Filter untuk menampilkan klaim yang belum diproses
        pending_claims = [claim for claim in claims if claim.get("status") == "active"]
        
        if not pending_claims:
            st.success("✅ Semua klaim sudah diproses!")
            return
        
        st.subheader("Klaim yang Menunggu Persetujuan")
        for claim in pending_claims:
            with st.expander(f"Klaim: {claim.get('id')} - {claim.get('patient', {}).get('reference')}"):
                # Tampilkan detail klaim
                st.write("Detail Klaim:")
                st.json(claim)
                
                # Form persetujuan
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Setujui", key=f"accept_{claim['id']}"):
                        response = make_request(
                            "PUT", 
                            f"claims/{claim['id']}/process", 
                            params={"status": "accepted"}
                        )
                        if response and response.status_code == 200:
                            st.success("Klaim berhasil disetujui!")
                            st.experimental_rerun()
                
                with col2:
                    if st.button("❌ Tolak", key=f"reject_{claim['id']}"):
                        response = make_request(
                            "PUT", 
                            f"claims/{claim['id']}/process", 
                            params={"status": "rejected"}
                        )
                        if response and response.status_code == 200:
                            st.warning("Klaim ditolak.")
                            st.experimental_rerun()

def show_monthly_report():
    st.header("📊 Laporan Bulanan")
    st.write("Lihat data dan statistik terintegrasi untuk bulan tertentu")

    # Get available months
    months_response = make_request("GET", "reports/months")
    if not months_response or months_response.status_code != 200:
        st.error("❌ Gagal mengambil data bulan yang tersedia")
        return

    available_months = months_response.json()
    if not available_months:
        st.warning("⚠️ Tidak ada data yang tersedia untuk laporan")
        return

    # Report controls
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_month = st.selectbox(
            "Pilih Bulan Laporan",
            options=available_months,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B %Y")
        )
    
    with col2:
        st.write("")  # Spacing
        if st.button("🔄 Segarkan Data"):
            st.experimental_rerun()

    # Fetch and display data
    with st.spinner("📊 Memuat data laporan..."):
        # Get all data for the month
        patients_data = make_request("GET", f"reports/patients?month={selected_month}").json()
        
        diagnosis_filter = st.text_input("🔍 Filter berdasarkan Diagnosis", "")
        encounters_url = f"reports/encounters?month={selected_month}"
        if diagnosis_filter:
            encounters_url += f"&diagnosis={diagnosis_filter}"
        encounters_data = make_request("GET", encounters_url).json()
        
        claims_data = make_request("GET", f"reports/claims?month={selected_month}").json()
        
        # Calculate total revenue and costs
        total_medication_cost = sum(float(enc.get("total_price", 0)) for enc in encounters_data)
        total_claims_amount = sum(float(claim.get("total", {}).get("value", 0)) for claim in claims_data)
        
        # Display metrics
        st.subheader("📈 Statistik Bulanan")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🧑‍⚕️ Pasien Baru", len(patients_data))
        with col2:
            st.metric("📝 Total Kunjungan", len(encounters_data))
        with col3:
            st.metric("💰 Klaim Diajukan", len(claims_data))
        
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("💊 Total Biaya Obat", f"Rp {total_medication_cost:,.2f}")
        with col5:
            st.metric("💵 Total Klaim", f"Rp {total_claims_amount:,.2f}")
        with col6:
            accepted_claims = sum(1 for claim in claims_data if claim.get("status") == "accepted")
            st.metric("✅ Klaim Diterima", f"{accepted_claims} dari {len(claims_data)}")
        
        # Display detailed tables
        st.markdown("---")
        
        # Patients table
        st.subheader("🧑‍⚕️ Pendaftaran Pasien Baru")
        if patients_data:
            patients_df = pd.DataFrame([{
                "ID Pasien": p["patient_id"],
                "Nama Lengkap": p["full_name"],
                "Tanggal Daftar": p["created_at"],
                "Usia": p["age"],
                "Jenis Kelamin": p["gender"]
            } for p in patients_data])
            st.dataframe(patients_df, use_container_width=True)
        else:
            st.info("Tidak ada pasien baru yang mendaftar bulan ini")
        
        # Encounters table
        st.subheader("📝 Kunjungan Medis")
        if encounters_data:
            encounters_df = pd.DataFrame([{
                "ID Kunjungan": e["encounter_id"],
                "Nama Pasien": e["patient_name"],
                "Tanggal Kunjungan": e["visit_date"],
                "Diagnosis": e["diagnosis"],
                "Pengobatan": e["treatment"],
                "Biaya Obat": f"Rp {float(e.get('total_price', 0)):,.2f}",
                "Dokter": e["attending_clinician"] or "N/A"
            } for e in encounters_data])
            st.dataframe(encounters_df, use_container_width=True)
        else:
            st.info("Tidak ada kunjungan yang tercatat bulan ini")
        
        # Claims table
        st.subheader("💰 Klaim Asuransi")
        if claims_data:
            claims_list = [{
                "ID Klaim": claim.get("id", ""),
                "Nama Pasien": claim.get("patient_name", ""),
                "Tanggal Diajukan": claim.get("created", ""),
                "Status": claim.get("status", ""),
                "Jumlah": f"Rp {float(claim.get('total', {}).get('value', 0)):,.2f}"
            } for claim in claims_data]
            claims_df = pd.DataFrame(claims_list)
            st.dataframe(claims_df, use_container_width=True)
        else:
            st.info("Tidak ada klaim yang diajukan bulan ini")

def show_administration():
    st.header("⚙️ Administrasi")
    st.write("Manajemen dan statistik sistem")

    # Runtime statistics
    stats_response = make_request("GET", "stats")
    if stats_response and stats_response.status_code == 200:
        stats = stats_response.json()
        
        st.subheader("📊 Statistik Sistem")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Pasien", stats["total_patients"])
        with col2:
            st.metric("Total Kunjungan", stats["total_encounters"])
        with col3:
            st.metric("Total Klaim", stats["total_claims"])
    
    st.markdown("---")
    
    # Data reset section
    st.subheader("⚠️ Zona Berbahaya")
    st.warning("Tindakan berikut tidak dapat dibatalkan!")
    
    if confirm_action(
        message="Reset semua data sistem?",
        confirmation_text="RESET"
    ):
        response = make_request("POST", "reset")
        if response and response.status_code == 200:
            st.success("✅ Semua data telah berhasil direset!")
            st.button("Segarkan Halaman", on_click=st.experimental_rerun)

def main():
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state for navigation
    if 'app_section' not in st.session_state:
        st.session_state.app_section = "Pendaftaran Pasien"
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🏥 Middleware Klinik")
        st.markdown("---")
        
        sections = {
            "Pendaftaran Pasien": "🧑‍⚕️",
            "Catat Kunjungan": "📝",
            "Ajukan Klaim": "💰",
            "Laporan Bulanan": "📊",
            "Administrasi": "⚙️"
        }
        
        selected_section = st.radio(
            "Navigasi",
            options=list(sections.keys()),
            format_func=lambda x: f"{sections[x]} {x}",
            key="nav_radio"
        )
        st.session_state.app_section = selected_section
    
    # Main content
    if st.session_state.app_section == "Pendaftaran Pasien":
        show_register_patient()
    elif st.session_state.app_section == "Catat Kunjungan":
        show_record_encounter()
    elif st.session_state.app_section == "Ajukan Klaim":
        show_submit_claim()
    elif st.session_state.app_section == "Laporan Bulanan":
        show_monthly_report()
    else:
        show_administration()

if __name__ == "__main__":
    main()
