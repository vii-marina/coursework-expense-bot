from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Test works!", ln=True)
pdf.output("test_output.pdf")
print("✅ FPDF is working.")
