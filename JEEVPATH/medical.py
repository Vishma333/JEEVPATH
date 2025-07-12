import os
from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.media import Image as AgnoImage
from fpdf import FPDF
from datetime import datetime

# Set your Gemini API key here
GOOGLE_API_KEY = "AIzaSyB7iO88nlyd0B5gppN40Pc5dWkNnn6k3dw"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Setup medical image analysis agent
medical_agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[DuckDuckGoTools()],
    markdown=True
)

# Medical Image Analysis
def analyze_medical_image(image_path):
    query = """
    You are an expert in medical image analysis. Carefully examine the uploaded image and provide a detailed visual analysis. Please follow this structured format strictly:

    ### 1. Image Type & Region
    - Describe the imaging modality, anatomy, and quality.

    ### 2. Key Visual Findings
    - List systematic visual features and abnormalities (without diagnosis).

    ### 3. General Visual Assessment
    - Summarize visual content without diagnosing.

    ### 4. Patient-Friendly Explanation
    - Use non-technical terms to explain.

    ### 5. Research Context
    - Use DuckDuckGo to find 2-3 references on similar images.

    Do not provide medical diagnoses.
    """
    agno_image = AgnoImage(filepath=image_path)
    try:
        response = medical_agent.run(query, images=[agno_image])
        content = response.content.strip()
        sections = content.split('### 1. Image Type & Region')
        if len(sections) > 1:
            cleaned_content = '### 1. Image Type & Region' + sections[1]
        else:
            cleaned_content = content
        return cleaned_content, ""
    except Exception as e:
        return f"⚠️ Analysis error: {e}", ""

def create_pdf(patient_name, report_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, "Medical Image Analysis Report", ln=True, align='C')
    pdf.ln(10)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pdf.cell(0, 10, f"Generated on: {current_time}", ln=True)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Patient Name: {patient_name}", ln=True)
    pdf.ln(5)
    pdf.set_font('Arial', '', 12)
    for line in report_text.split('\n'):
        pdf.multi_cell(0, 8, line)
        pdf.ln()
    if not os.path.exists("static"):
        os.makedirs("static")
    filename = f"medical_report_{patient_name.replace(' ', '_')}.pdf"
    filepath = os.path.join("static", filename)
    pdf.output(filepath)
    return filepath

# Doctor's Prescription Analysis
def analyze_prescription_image(image_path):
    agno_image = AgnoImage(filepath=image_path)
    try:
        prescription_prompt = """
        You are an expert in medical document understanding. Read the prescription image carefully.
        Extract and present the content in plain, structured text. Follow this format:

        ### Doctor Details
        - Name:
        - Registration ID (if visible):
        - Hospital/Clinic:

        ### Patient Information
        - Name:
        - Age/Gender:
        - Date:

        ### Prescription Details
        - Medicines:
        - Dosage:
        - Frequency:
        - Duration:

        ### Additional Notes
        - Any test advised or general advice.

        Output only the text in this format. Do not hallucinate missing fields. If something is unclear, write "Not clear".
        """
        response = medical_agent.run(prescription_prompt, images=[agno_image])
        content = response.content.strip()
        return content
    except Exception as e:
        return f"⚠️ Prescription Analysis Error: {e}"

def create_prescription_pdf(patient_name, prescription_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "Doctor's Prescription (Digital Copy)", ln=True, align='C')
    pdf.ln(10)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Generated on: {current_time}", ln=True)
    pdf.cell(0, 10, f"Patient Name: {patient_name}", ln=True)
    pdf.ln(5)
    for line in prescription_text.split('\n'):
        pdf.multi_cell(0, 8, line)
        pdf.ln()

    if not os.path.exists("static"):
        os.makedirs("static")

    filename = f"prescription_report_{patient_name.replace(' ', '_')}.pdf"
    filepath = os.path.join("static", filename)
    pdf.output(filepath)
    return filename
