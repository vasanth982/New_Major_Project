"""
Clinical Guidance & Recommendations engine for Checkup Buddy (v2).
Provides evidence-based lifestyle modifications, warning flags for medical escalation,
and physician discussion questions for all 7 disease modules and risk tiers.
"""

RECOMMENDATIONS = {
    "Heart Disease": {
        "High": {
            "summary": "Your assessment indicates an elevated cardiovascular risk profile.",
            "lifestyle": [
                "Adopt a heart-healthy Mediterranean diet rich in fresh vegetables, whole grains, and omega-3 fatty acids.",
                "Engage in at least 150 minutes of moderate aerobic exercise per week under medical clearance.",
                "Limit sodium intake to under 2,000 mg per day and avoid processed saturated/trans fats.",
                "Cease all tobacco use immediately and minimize alcohol consumption.",
                "Monitor daily resting blood pressure and maintain a clinical tracking journal."
            ],
            "urgent_signs": [
                "Sudden crushing chest pain, tightness, or pressure radiating to the jaw, neck, back, or left arm.",
                "Unexplained shortness of breath or dizziness while resting.",
                "Sudden rapid, fluttering, or irregular heartbeat accompanied by lightheadedness."
            ],
            "doctor_questions": [
                "Would you recommend a comprehensive 12-lead ECG, echocardiogram, or cardiac stress test?",
                "Are my lipid profile and apoB levels within an optimal therapeutic target?",
                "Should we consider cardioprotective preventative medications (e.g. statin therapy)?"
            ]
        },
        "Low": {
            "summary": "Your assessment indicates no significant immediate indicators of heart disease.",
            "lifestyle": [
                "Maintain regular physical cardiovascular activity (brisk walking, cycling, swimming).",
                "Keep dietary saturated fats low and focus on fiber-dense whole foods.",
                "Maintain healthy body weight and monitor blood pressure annually."
            ],
            "urgent_signs": [
                "Unusual chest tightness or acute shortness of breath during exertion.",
                "Episodes of sudden unprovoked fainting or severe palpitations."
            ],
            "doctor_questions": [
                "What is my 10-year atherosclerotic cardiovascular disease (ASCVD) risk estimation?",
                "How often should I schedule lipid and blood glucose panels?"
            ]
        }
    },

    "Diabetes": {
        "High": {
            "summary": "Your biometric markers suggest elevated risk or predisposition to glycemic dysregulation.",
            "lifestyle": [
                "Prioritize complex carbohydrates with low glycemic index (legumes, leafy greens, steel-cut oats).",
                "Eliminate sugar-sweetened beverages, commercial sodas, and refined flours.",
                "Incorporate post-meal 15-minute walks to enhance peripheral insulin sensitivity.",
                "Monitor fasting blood glucose and postprandial glucose levels consistently."
            ],
            "urgent_signs": [
                "Persistent severe thirst, extreme dry mouth, and confusion (signs of hyperosmolar state).",
                "Deep, rapid breathing with fruity-scented breath (ketoacidosis warning).",
                "Sudden blurred vision, lethargy, or non-healing sores on the feet or lower legs."
            ],
            "doctor_questions": [
                "Should we order a diagnostic venous HbA1c and fasting plasma glucose confirmation?",
                "Do I qualify for medical nutrition therapy or continuous glucose monitoring (CGM)?",
                "Is metformin or another insulin-sensitizing intervention appropriate at this stage?"
            ]
        },
        "Low": {
            "summary": "Your indicators suggest a healthy glycemic profile within expected clinical bounds.",
            "lifestyle": [
                "Maintain balanced meals with adequate lean proteins and dietary fiber.",
                "Avoid frequent consumption of ultra-processed snacks and excessive refined sugars.",
                "Keep active to preserve muscular glucose uptake."
            ],
            "urgent_signs": [
                "Unexplained sudden weight loss accompanied by excessive thirst and frequent urination."
            ],
            "doctor_questions": [
                "When is my next recommended routine HbA1c screening based on my age and family history?"
            ]
        }
    },

    "Parkinson's Disease": {
        "High": {
            "summary": "Your vocal acoustic profile exhibits frequency/amplitude jitter and harmonic alterations correlated with motor control changes.",
            "lifestyle": [
                "Consult a movement disorder specialist (neurologist) for formal clinical neurological evaluation.",
                "Engage in targeted physical therapy focusing on balance, gait cadence, and postural stability.",
                "Participate in vocal articulation exercises (such as LSVT LOUD therapy) to sustain phonatory strength.",
                "Prioritize restorative sleep hygiene and an anti-inflammatory dietary pattern."
            ],
            "urgent_signs": [
                "Sudden acute progression in unsteadiness leading to frequent falls or head trauma.",
                "Severe difficulty swallowing liquids or pills (dysphagia with aspiration risk).",
                "Acute hallucinations or severe nocturnal sleep behavior disruptions."
            ],
            "doctor_questions": [
                "Would a formal UPDRS (Unified Parkinson's Disease Rating Scale) examination and DaTscan be indicated?",
                "Are there early symptomatic or neuroprotective treatment options suitable for my presentation?",
                "Can you refer me to a specialized physical or speech-language therapist?"
            ]
        },
        "Low": {
            "summary": "Your phonatory and vocal acoustic features are within expected physiological variations.",
            "lifestyle": [
                "Maintain regular aerobic exercise and cognitive agility activities.",
                "Stay socially active and practice vocal health with proper hydration."
            ],
            "urgent_signs": [
                "Noticeable unilateral hand tremors at rest, unexplained limb rigidity, or micrographia (shrinking handwriting)."
            ],
            "doctor_questions": [
                "Are there any baseline neurological health screenings indicated for my demographic?"
            ]
        }
    },

    "Chronic Kidney Disease": {
        "High": {
            "summary": "Your renal indicators (filtration, albumin, or specific gravity) suggest potential renal strain or early impairment.",
            "lifestyle": [
                "Strictly control blood pressure (target < 130/80 mmHg or as directed by your physician).",
                "Avoid all nephrotoxic agents, particularly over-the-counter NSAIDs (ibuprofen, naproxen).",
                "Moderate dietary protein intake according to medical guidance and reduce dietary phosphorus and sodium.",
                "Maintain optimal daily hydration unless fluid-restricted by a nephrologist."
            ],
            "urgent_signs": [
                "Severe swelling (edema) in ankles, legs, or periorbital eye region with sudden weight gain.",
                "Marked reduction in urine output or visible blood in the urine (hematuria).",
                "Intractable nausea, metallic taste in the mouth, or acute shortness of breath."
            ],
            "doctor_questions": [
                "What is my estimated Glomerular Filtration Rate (eGFR) and Urine Albumin-to-Creatinine Ratio (uACR)?",
                "Should we initiate renal-protective therapy (such as ACE inhibitors or SGLT2 inhibitors)?",
                "Is a formal renal ultrasound evaluation recommended?"
            ]
        },
        "Low": {
            "summary": "Your kidney parameters reflect stable renal excretion and electrolyte balance.",
            "lifestyle": [
                "Drink 2 to 2.5 liters of clean water daily.",
                "Keep dietary salt moderate and avoid prolonged use of high-dose painkillers.",
                "Maintain healthy blood pressure and blood glucose."
            ],
            "urgent_signs": [
                "Persistent foamy urine, flank pain, or sudden high blood pressure spikes."
            ],
            "doctor_questions": [
                "How often should routine serum creatinine and urinalysis be evaluated?"
            ]
        }
    },

    "Liver Disease": {
        "High": {
            "summary": "Your hepatic biochemical profile demonstrates enzyme elevations or albumin/bilirubin alterations suggestive of hepatic stress.",
            "lifestyle": [
                "Completely eliminate alcohol intake to prevent hepatocellular strain.",
                "Review all prescription medications, vitamins, and herbal supplements with your physician to prevent drug-induced liver injury.",
                "Adopt an antioxidant-rich diet low in saturated fats and refined sugars to address fatty liver infiltration.",
                "Aim for gradual, sustainable weight management (5-10% reduction if overweight)."
            ],
            "urgent_signs": [
                "Yellowing of the skin or whites of the eyes (jaundice).",
                "Abdominal distension with rapid fluid accumulation (ascites) or right upper quadrant pain.",
                "Confusion, severe disorientation, or dark tea-colored urine."
            ],
            "doctor_questions": [
                "Would you recommend a liver ultrasound, FibroScan, or viral hepatitis panel (Hep B/C)?",
                "Do these enzyme patterns reflect metabolic-associated steatohepatitis (MASH/NASH) or another etiology?",
                "What specific medications or supplements should I strictly avoid?"
            ]
        },
        "Low": {
            "summary": "Your liver enzyme and bilirubin markers are within normal physiologic thresholds.",
            "lifestyle": [
                "Limit alcohol consumption to moderate or zero levels.",
                "Maintain a balanced diet avoiding excess fructose and fried foods.",
                "Ensure vaccination against Hepatitis A and B if traveling or at risk."
            ],
            "urgent_signs": [
                "Unexplained persistent fatigue accompanied by dark urine or pale-colored stools."
            ],
            "doctor_questions": [
                "Are my routine annual liver function panels (LFTs) up to date?"
            ]
        }
    },

    "Stroke Risk": {
        "High": {
            "summary": "Your cerebrovascular profile indicates heightened predisposition to ischemic or hemorrhagic vascular events.",
            "lifestyle": [
                "Achieve strict blood pressure control — hypertension is the primary modifiable risk factor for stroke.",
                "Adhere rigorously to prescribed anti-hypertensive or anti-platelet medications without skipping doses.",
                "Cease tobacco smoking immediately; smoking doubles ischemic stroke risk.",
                "Undergo screening for cardiac arrhythmias, specifically Atrial Fibrillation (AFib)."
            ],
            "urgent_signs": [
                "BE-FAST symptoms: Loss of Balance, Eyes (sudden vision loss), Facial drooping, Arm weakness, Slurred Speech. CALL 911 / EMERGENCY IMMEDIATELY IF ANY OCCUR!"
            ],
            "doctor_questions": [
                "Should we perform a carotid artery duplex ultrasound or Holter monitor to check for occult AFib?",
                "Is my antiplatelet or anticoagulation therapy optimized?",
                "What is my personalized target for blood pressure and LDL cholesterol?"
            ]
        },
        "Low": {
            "summary": "Your current indicators reflect low immediate probability of acute cerebrovascular events.",
            "lifestyle": [
                "Maintain an active lifestyle and engage in weekly aerobic conditioning.",
                "Keep blood pressure monitored periodically.",
                "Emphasize stress management and quality nocturnal rest."
            ],
            "urgent_signs": [
                "Sudden transient numbness on one side of the face or body, even if resolving within minutes (TIA warning)."
            ],
            "doctor_questions": [
                "Are my cardiovascular health metrics tracked adequately for preventative stroke care?"
            ]
        }
    },

    "Breast Cancer Risk": {
        "High": {
            "summary": "Fine-needle aspiration (FNA) nuclear morphology indicators correlate with high cellular suspicion or malignancy characteristics.",
            "lifestyle": [
                "Schedule immediate formal clinical consultation with a surgical oncologist or breast specialist.",
                "Obtain diagnostic imaging (high-resolution bilateral diagnostic mammogram and targeted ultrasound).",
                "Prepare pathology and biopsy records for comprehensive multidisciplinary tumor board review.",
                "Maintain a supportive healthcare network and avoid unverified alternative delays."
            ],
            "urgent_signs": [
                "A hard, non-tender lump in the breast tissue or axillary underarm region.",
                "Visible skin changes: dimpling (peau d'orange), nipple inversion, or spontaneous bloody nipple discharge.",
                "Rapid erythema, warmth, or persistent breast skin inflammation."
            ],
            "doctor_questions": [
                "Do you recommend a core needle biopsy (CNB) or breast MRI for definitive histological confirmation?",
                "Should we perform genetic screening for BRCA1/BRCA2 or related hereditary mutations?",
                "What is the recommended timeline for staging and multidisciplinary evaluation?"
            ]
        },
        "Low": {
            "summary": "Cellular and morphological values are consistent with benign, non-malignant tissue characteristics.",
            "lifestyle": [
                "Continue routine age-appropriate breast screening mammography as recommended by clinical guidelines.",
                "Maintain monthly self-awareness of breast tissue texture and report any new or persistent changes.",
                "Limit alcohol intake and maintain regular exercise to reduce long-term baseline risk."
            ],
            "urgent_signs": [
                "Any newly palpable solitary discrete mass, localized persistent focal pain, or nipple skin changes."
            ],
            "doctor_questions": [
                "Based on my personal and family history, what is my recommended mammogram frequency (annual vs biennial)?"
            ]
        }
    }
}


def get_recommendation(disease_name: str, risk_level: str) -> dict:
    """Returns the recommendation dictionary for a given disease and risk level."""
    normalized_risk = "High" if "High" in risk_level or "Detected" in risk_level else "Low"
    disease_data = RECOMMENDATIONS.get(disease_name, {})
    return disease_data.get(normalized_risk, {
        "summary": "Please review these findings with your primary healthcare provider.",
        "lifestyle": ["Maintain regular exercise, balanced nutrition, and routine checkups."],
        "urgent_signs": ["Any new, severe, or worsening clinical symptoms require immediate medical care."],
        "doctor_questions": ["What follow-up diagnostics are appropriate for my profile?"]
    })
