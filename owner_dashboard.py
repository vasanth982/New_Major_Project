"""
Owner (Admin & Medical Director) Dashboard for Checkup Buddy (v2).
Provides platform-wide population health analytics, sortable & searchable patient roster,
read-only medical history inspection with automated compliance access logging (owner_access_log),
and strict server-side role validation.
"""

import streamlit as st
import pandas as pd
import json

import database
import pdf_generator
import recommendations
import i18n


def render_owner_dashboard():
    """Renders the Owner administration portal with strict server-side access control."""
    # STRICT SERVER-SIDE ROLE ENFORCEMENT
    current_role = st.session_state.get("role")
    owner_id = st.session_state.get("user_id")

    if current_role != "owner" or not owner_id:
        st.error("⛔ ACCESS DENIED: This portal is restricted to authorized Medical Directors and Owners.")
        st.stop()
        return

    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <h2 style="color: #0D9488; font-weight: 800; margin-bottom: 0.2rem;">
                        {i18n.t("owner_title")}
                    </h2>
                    <p style="color: #64748B; font-size: 0.95rem;">
                        {i18n.t("owner_subtitle")}
                    </p>
                </div>
                <div style="background: #EEF2FF; border: 1px solid #C7D2FE; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; color: #3730A3; font-weight: 600;">
                    Superuser Active: {st.session_state.get("username", "Owner")}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_patients, tab_audit = st.tabs([
        i18n.t("tab_overview"),
        i18n.t("tab_patients"),
        i18n.t("tab_audits")
    ])

    # ---------------- TAB 1: AGGREGATE HEALTH ANALYTICS ----------------
    with tab_overview:
        stats = database.get_aggregate_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(i18n.t("stat_patients"), stats["total_patients"])
        with col2:
            st.metric(i18n.t("stat_assessments"), stats["total_tests"])
        with col3:
            st.metric("Completed Vitals Intake Sessions", stats["total_vitals"])

        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("#### Diagnostic Assessments by Disease")
            disease_data = stats.get("disease_counts", [])
            if disease_data:
                df_disease = pd.DataFrame(disease_data)
                df_disease.columns = ["Disease Module", "Test Count"]
                st.bar_chart(df_disease.set_index("Disease Module"), color="#2563EB")
            else:
                st.info("No diagnostic tests recorded yet.")

        with col_c2:
            st.markdown("#### Risk Stratification Breakdown")
            risk_data = stats.get("risk_distribution", [])
            if risk_data:
                df_risk = pd.DataFrame(risk_data)
                df_risk.columns = ["Risk Tier", "Total Cases"]
                st.bar_chart(df_risk.set_index("Risk Tier"), color="#DC2626")
            else:
                st.info("No risk records available.")

    # ---------------- TAB 2: PATIENT REGISTRY & RECORDS ----------------
    with tab_patients:
        st.markdown("#### Registered Patient Directory")

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            search_query = st.text_input("🔍 Search Patients by Name, Email, or Mobile", placeholder="Type name or email...").strip()
        with col_s2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Refresh Roster", use_container_width=True):
                st.rerun()

        patients = database.get_all_patients_summary(search_query)

        if not patients:
            st.info("No registered patients found matching your search criteria.")
        else:
            # Display patient summary table
            table_rows = []
            for p in patients:
                table_rows.append({
                    "Patient ID": f"CB-{p['id']:06d}",
                    "Full Name": p["full_name"] or p["username"],
                    "Email": p["email"],
                    "Mobile": p["mobile"] or "N/A",
                    "Demographics": f"{p['age'] or 'N/A'}y, {p['gender'] or 'N/A'}",
                    "Tests Run": p["test_count"],
                    "Registered": p["created_at"][:10],
                    "_id": p["id"]
                })
            df_patients = pd.DataFrame(table_rows)
            st.dataframe(
                df_patients.drop(columns=["_id"]),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
            st.markdown("#### Inspect Patient Medical History (Read-Only)")

            patient_choices = {p["id"]: f"CB-{p['id']:06d} — {p['full_name'] or p['username']} ({p['email']})" for p in patients}
            selected_patient_id = st.selectbox(
                "Select Patient to Inspect Clinical History:",
                options=list(patient_choices.keys()),
                format_func=lambda pid: patient_choices[pid]
            )

            if selected_patient_id:
                # Log audit record as required by Section 9
                database.log_owner_access(owner_id=owner_id, viewed_user_id=selected_patient_id)

                patient_profile = database.get_profile(selected_patient_id)
                vitals_history = database.get_user_vitals_history(selected_patient_id)
                test_history = database.get_user_predictions(selected_patient_id)

                col_p1, col_p2 = st.columns([1, 2])
                with col_p1:
                    st.markdown("""
                        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                            <h5 style="margin: 0 0 0.5rem 0; color: #1E3A8A;">Patient File</h5>
                            <p style="margin: 0; font-size: 0.9rem;"><b>Name:</b> {name}</p>
                            <p style="margin: 0; font-size: 0.9rem;"><b>MRN:</b> CB-{pid:06d}</p>
                            <p style="margin: 0; font-size: 0.9rem;"><b>Age/Gender:</b> {age}y, {gender}</p>
                            <p style="margin: 0; font-size: 0.9rem;"><b>Blood Group:</b> {bg}</p>
                            <p style="margin: 0; font-size: 0.9rem;"><b>Contact:</b> {email}</p>
                            <p style="margin: 0; font-size: 0.9rem;"><b>Mobile:</b> {mobile}</p>
                        </div>
                    """.format(
                        name=patient_profile.get("full_name") or patient_profile.get("username"),
                        pid=selected_patient_id,
                        age=patient_profile.get("age") or "N/A",
                        gender=patient_profile.get("gender") or "N/A",
                        bg=patient_profile.get("blood_group") or "N/A",
                        email=patient_profile.get("email"),
                        mobile=patient_profile.get("mobile") or "N/A"
                    ), unsafe_allow_html=True)

                with col_p2:
                    st.markdown(f"##### Recorded Vitals Intake Sessions ({len(vitals_history)})")
                    if vitals_history:
                        df_vitals = pd.DataFrame(vitals_history)[
                            ["id", "body_temp", "blood_pressure_sys", "blood_pressure_dia", "blood_sugar", "created_at"]
                        ]
                        df_vitals.columns = ["Session #", "Temp (°C)", "Sys BP", "Dia BP", "Sugar (mg/dL)", "Timestamp"]
                        st.dataframe(df_vitals, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No vitals intake records on file.")

                st.markdown(f"##### Diagnostic Test History ({len(test_history)})")
                if test_history:
                    for t in test_history:
                        is_high = "High" in t["risk_level"] or "Detected" in t["risk_level"]
                        card_border = "#EF4444" if is_high else "#22C55E"
                        card_bg = "#FEF2F2" if is_high else "#F0FDF4"

                        with st.expander(f"{t['disease']} — {t['risk_level'].upper()} RISK ({t['timestamp'][:16]})"):
                            st.markdown(f"""
                                <div style="background: {card_bg}; border-left: 4px solid {card_border}; padding: 0.8rem; border-radius: 4px; margin-bottom: 0.8rem;">
                                    <b>Diagnostic Result:</b> {t['result_text']}<br>
                                    <b>Clinical Summary:</b> {t.get('advice', 'N/A')}
                                </div>
                            """, unsafe_allow_html=True)

                            # Parse inputs JSON if possible
                            try:
                                in_data = json.loads(t["inputs_json"])
                                st.write("**Evaluated Inputs:**", in_data)
                            except Exception:
                                st.write("**Raw Inputs:**", t["inputs_json"])

                            # Provide Owner PDF download for the patient record
                            if t.get("vitals_session_id"):
                                v_rec = database.get_vitals_session_by_id(t["vitals_session_id"])
                                if v_rec:
                                    rec = recommendations.get_recommendation(t["disease"], t["risk_level"])
                                    pdf_bytes = pdf_generator.generate_clinical_pdf(
                                        patient_name=v_rec["patient_name"],
                                        patient_id=selected_patient_id,
                                        age=v_rec["age"],
                                        gender=v_rec["gender"],
                                        vitals=v_rec,
                                        disease_name=t["disease"],
                                        result_title=t["result_text"],
                                        risk_level=t["risk_level"],
                                        confidence_pct=90.0,
                                        inputs_dict=in_data if isinstance(in_data, dict) else {},
                                        recommendation=rec
                                    )
                                    st.download_button(
                                        label=f"📄 Download Clinical Report ({t['disease']})",
                                        data=pdf_bytes,
                                        file_name=f"Report_CB{selected_patient_id}_{t['disease'].replace(' ', '_')}.pdf",
                                        mime="application/pdf",
                                        key=f"owner_pdf_{t['id']}"
                                    )
                else:
                    st.info("No diagnostic tests have been executed by this patient yet.")

    # ---------------- TAB 3: COMPLIANCE & ACCESS LOGS ----------------
    with tab_audit:
        st.markdown("#### Medical Record Inspection Audit Log")
        st.caption("Immutable record of all medical directory access into patient health records for compliance accountability.")

        logs = database.get_aggregate_stats().get("recent_logs", [])
        if logs:
            df_logs = pd.DataFrame(logs)[["id", "owner_username", "patient_username", "accessed_at"]]
            df_logs.columns = ["Log ID", "Auditor (Owner)", "Patient File Viewed", "Timestamp"]
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No administrative record inspections logged yet.")
