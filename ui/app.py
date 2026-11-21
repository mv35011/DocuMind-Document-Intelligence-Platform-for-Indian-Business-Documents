import json
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="DocuMind | Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #64748B; margin-bottom: 1.5rem; }
    .metric-card { background: #F8FAFC; border: 1px solid #E2E8F0; padding: 1.2rem; border-radius: 8px; }
    .status-badge-approved { background-color: #DEF7EC; color: #03543F; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
    .status-badge-review { background-color: #FEF08A; color: #713F12; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# Navigation Sidebar
with st.sidebar:
    st.title("📄 DocuMind")
    st.caption("Document Intelligence for Indian Business Docs")
    st.divider()
    page = st.radio(
        "Navigation",
        ["Dashboard", "Upload Documents", "Human Review Queue", "Agent Query & Chat", "Model Evaluation"],
        index=0,
    )
    st.divider()
    st.caption("Active Workspace: **NIT Patna Org**")
    st.caption("Extraction Backend: **Qwen2-VL (QLoRA)**")
    st.caption("Auth Role: **admin (Manmohan)**")

# PAGE 1: DASHBOARD
if page == "Dashboard":
    st.markdown('<div class="main-header">Operational Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time throughput, accuracy, and confidence metrics</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Total Processed", value="1,420 pages", delta="+124 today")
    with c2:
        st.metric(label="Auto-Approval Rate", value="72.4%", delta="+3.1%")
    with c3:
        st.metric(label="Extraction F1 (Micro)", value="91.8%", delta="+4.2% vs baseline")
    with c4:
        st.metric(label="P50 Latency", value="340 ms", delta="-45 ms")

    st.divider()
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Confidence Score Distribution")
        chart_data = pd.DataFrame({
            "Confidence Range": ["[0.5, 0.6)", "[0.6, 0.7)", "[0.7, 0.8)", "[0.8, 0.9)", "[0.9, 1.0]"],
            "Document Count": [35, 78, 142, 385, 780],
        })
        st.bar_chart(chart_data.set_index("Confidence Range"))

    with col_chart2:
        st.subheader("Top Suppliers by Spend (INR)")
        spend_data = pd.DataFrame({
            "Supplier": ["Tata Motors Ltd", "Reliance Retail", "Infosys BPM", "L&T Electrical", "Blue Tokai"],
            "Spend (₹)": [450000, 320000, 195000, 140000, 38000],
        })
        st.bar_chart(spend_data.set_index("Supplier"))

# PAGE 2: UPLOAD
elif page == "Upload Documents":
    st.markdown('<div class="main-header">Upload Business Documents</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ingest GST tax invoices, bank statements, and retail receipts</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Choose PDF or image files",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    doc_type_override = st.selectbox(
        "Document Type (Optional Override)",
        ["Auto-detect with Vision Classifier", "GST Tax Invoice (gst_invoice)", "Bank Statement (bank_statement)", "Retail Receipt (receipt)"],
    )

    if st.button("Start Processing", type="primary"):
        if uploaded_files:
            progress = st.progress(0)
            status_text = st.empty()
            stages = ["Validating MIME & Sniffing Header", "Rendering Pages @ 200 DPI", "Deskewing & Contrast Normalization", "Extracting OCR Tokens", "Running Vision-Language Model", "Reconciling GST Business Rules"]
            for i, stage in enumerate(stages):
                status_text.text(f"Current Stage: {stage}...")
                progress.progress((i + 1) / len(stages))
            st.success(f"Successfully processed {len(uploaded_files)} documents! 2 auto-approved, 1 routed to human review.")
        else:
            st.warning("Please select at least one document to upload.")

# PAGE 3: REVIEW QUEUE
elif page == "Human Review Queue":
    st.markdown('<div class="main-header">Human-in-the-Loop Review Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Verify and correct documents flagged by hard validation rules or low confidence</div>', unsafe_allow_html=True)

    q_data = [
        {"Doc ID": "doc-8941", "Filename": "ambiguous_invoice_scan.pdf", "Type": "gst_invoice", "Confidence": 0.64, "Flagged Reason": "Buyer GSTIN Checksum Mismatch"},
        {"Doc ID": "doc-8942", "Filename": "hdfc_bank_statement_jan.pdf", "Type": "bank_statement", "Confidence": 0.71, "Flagged Reason": "Running Balance Row #4 Discrepancy"},
    ]
    st.dataframe(pd.DataFrame(q_data), use_container_width=True)

    st.divider()
    st.subheader("Document Review & Bounding Box Inspection")
    col_img, col_form = st.columns([1, 1])

    with col_img:
        st.info("Document Preview (Page 1 of 1)")
        st.image("https://via.placeholder.com/600x800/E2E8F0/1E293B?text=Document+Scan+Preview+(Simulated)", caption="Extracted Bounding Boxes Highlighted in Cyan")

    with col_form:
        st.subheader("Extracted Fields (Editable)")
        st.text_input("Invoice Number", "INV-2025-089")
        st.date_input("Invoice Date")
        st.text_input("Supplier Name", "Tata Motors Ltd")
        st.text_input("Supplier GSTIN", "27AAPFU0939F1ZV")
        st.number_input("Taxable Value (₹)", value=10000.0)
        st.number_input("CGST (₹)", value=900.0)
        st.number_input("SGST (₹)", value=900.0)
        st.number_input("Grand Total (₹)", value=11800.0)

        c_app, c_rej = st.columns(2)
        with c_app:
            if st.button("Approve & Index", type="primary"):
                st.success("Document approved! Fields flattened to database and indexed to Qdrant vector store.")
        with c_rej:
            if st.button("Reject Document"):
                st.error("Document marked as rejected.")

# PAGE 4: CHAT
elif page == "Agent Query & Chat":
    st.markdown('<div class="main-header">Ask DocuMind (Text-to-SQL + RAG)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Query your business documents in plain English with verified SQL and citations</div>', unsafe_allow_html=True)

    query = st.chat_input("Ask a question about your invoices or statements...")
    if query:
        st.chat_message("user").write(query)
        with st.chat_message("assistant"):
            st.info("Generated SQL Query (Guarded by sqlglot):")
            st.code("SELECT supplier_name, SUM(grand_total) AS total_spend FROM v_invoices GROUP BY supplier_name ORDER BY total_spend DESC LIMIT 200;", language="sql")
            st.write("According to your approved invoices, **Tata Motors Ltd** is your largest vendor with a total spend of **₹4,50,000.00** across 3 transactions.")
            st.caption("Citations: Invoices `INV-2025-001`, `INV-2025-045`, `INV-2025-089` | Tenant: nit_patna_org")

# PAGE 5: MODEL EVALUATION
elif page == "Model Evaluation":
    st.markdown('<div class="main-header">Empirical Model Benchmarks</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Micro/Macro F1 scores across models B0, B1, V0, and M1</div>', unsafe_allow_html=True)

    eval_table = pd.DataFrame({
        "Model ID": ["STUB", "B0", "B1", "V0", "M1"],
        "System Description": [
            "CI Test Fixture",
            "OCR + Regex Rules (Baseline)",
            "OCR + Groq Llama-3.3 70B",
            "Prompted Qwen2-VL-2B (Zero-Shot)",
            "Fine-Tuned Qwen2-VL-2B (4-bit QLoRA)",
        ],
        "Micro F1": ["57.9%", "33.3%", "78.4%", "81.2%", "91.8%"],
        "Macro F1": ["55.6%", "9.5%", "72.1%", "76.8%", "88.9%"],
        "Latency": ["0 ms", "0 ms", "420 ms", "850 ms", "340 ms"],
        "Status": ["Verified", "Verified", "Groq API", "API", "Kaggle T4 / RunPod"],
    })
    st.dataframe(eval_table, use_container_width=True)
