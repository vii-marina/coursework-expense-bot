from fpdf import FPDF
from discord import File
from io import BytesIO

async def send_overall_pdf_report(interaction):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)

    pdf.cell(200, 10, txt="Finance Summary Report", ln=True, align='C')
    pdf.ln(10)

    label_map = {
        "day": "Today",
        "week": "This week",
        "month": "This month"
    }

    for key, label in label_map.items():
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Period: {label}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(200, 10, txt=f"Total Income: ...", ln=True)
        pdf.cell(200, 10, txt=f"Total Expenses: ...", ln=True)
        pdf.cell(200, 10, txt=f"Balance: ...", ln=True)
        pdf.ln(5)

    # Збереження в пам'ять
    buffer = BytesIO()
    buffer.write(pdf.output(dest='S').encode('latin-1'))
    buffer.seek(0)

    await interaction.response.send_message(
        content="📄 Here is your general finance summary:",
        file=File(fp=buffer, filename="finance_report.pdf"),
        ephemeral=True
    )