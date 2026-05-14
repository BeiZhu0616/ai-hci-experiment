You are a senior Streamlit developer.

Create a clean and professional "Consent + Intro Page" for an online behavioral experiment.

Requirements:

1. The page should be minimal, clear, and divided into THREE sections:

SECTION 1: Study Introduction
- Short description
- Mention: research team from Xi’an Jiaotong-Liverpool University
- Mention: AI-assisted decision-making study
- Emphasize: no right or wrong answers

SECTION 2: Participation Information
- Bullet points:
  - duration: 5–8 minutes
  - task: review project scenarios and AI advice
  - system records interaction behavior (clicks, timing, decisions)
  - no personal identifiable information collected
  - no performance evaluation involved

SECTION 3: Consent Form
- Checkbox-based consent (required before continuing)
- Include:
  - read and understood
  - voluntary participation
  - data recording agreement
  - anonymisation and no withdrawal after submission
  - agreement to participate

2. Add a "Start Experiment" button:
- Disabled until all checkboxes are checked
- When clicked, update st.session_state.step = "experiment"

3. Use:
- st.title()
- st.markdown()
- st.checkbox()
- st.button()

4. Style:
- Clean
- Professional
- No long paragraphs
- No emojis

5. Do NOT include:
- Any mention of bias, illusion, or experimental manipulation
- Any academic jargon

Return complete runnable Streamlit code.
