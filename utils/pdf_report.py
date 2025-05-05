from fpdf import FPDF
from discord import File
from io import BytesIO
from utils.helpers import load_data, INCOME_FILE, EXPENSES_FILE, CATEGORIES_FILE, AUTO_INCOME_FILE
import matplotlib.pyplot as plt
from collections import defaultdict


def generate_pie_chart(data_dict, title):
    labels = list(data_dict.keys())
    sizes = list(data_dict.values())
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    plt.title(title)
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return buffer


async def send_overall_pdf_report(interaction):
    user_id = str(interaction.user.id)

    # Load data
    income_data = load_data(INCOME_FILE).get(user_id, [])
    auto_income_data = load_data(AUTO_INCOME_FILE).get(user_id, [])
    expense_data = load_data(EXPENSES_FILE).get(user_id, [])

    # Income summary (manual + auto)
    income_summary = defaultdict(float)
    total_income = 0
    for entry in income_data + auto_income_data:
        amount = entry.get("amount", 0)
        category = entry.get("category", "Unknown")
        if amount > 0:
            income_summary[category] += amount
            total_income += amount

    # Expense summary
    expense_summary = defaultdict(float)
    total_expenses = 0
    for entry in expense_data:
        amount = entry["amount"]
        if amount > 0:
            expense_summary[entry["category"]] += amount
            total_expenses += amount

    # Top categories
    top_income = max(income_summary.items(), key=lambda x: x[1], default=("None", 0))
    top_expense = max(expense_summary.items(), key=lambda x: x[1], default=("None", 0))
    balance = total_income - total_expenses

    # PDF setup
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=14)
    pdf.cell(200, 10, "Загальний фінансовий звіт", ln=True, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, f"Загальні прибутоки: {total_income:.2f} UAH", ln=True)
    pdf.cell(200, 10, f"Загальні витрати: {total_expenses:.2f} UAH", ln=True)
    pdf.cell(200, 10, f"Залишок: {balance:.2f} UAH", ln=True)
    pdf.ln(10)

    pdf.set_font("DejaVu", size=12)
    pdf.cell(200, 10, f"Найбільша категорія прибутку: {top_income[0]} ({top_income[1] / total_income * 100:.1f}% of income)", ln=True)
    
    pdf.set_font("DejaVu", size=11)
    pdf.cell(200, 10, "Категорії прибутків:", ln=True)
    for category, amount in income_summary.items():
        pdf.cell(200, 8, f"- {category}: {amount:.2f} UAH", ln=True)
    pdf.ln(5)
    
    # Charts
    income_chart = generate_pie_chart(income_summary, "Діаграма прибутків:")

    pdf.image(income_chart, x=25, y=None, w=150)
    pdf.ln(5)

    pdf.cell(200, 10, f"Найбільша категорія витрат: {top_expense[0]} ({top_expense[1] / total_expenses * 100:.1f}% of expenses)", ln=True)
    
    pdf.set_font("DejaVu", size=11)
    pdf.cell(200, 10, "Категорії витрат:", ln=True)
    for category, amount in expense_summary.items():
        pdf.cell(200, 8, f"- {category}: {amount:.2f} UAH", ln=True)
    expense_chart = generate_pie_chart(expense_summary, "Діаграма витрат:")
    # Expense chart
    pdf.image(expense_chart, x=25, y=None, w=150)
    pdf.ln(5)


    # Finalize PDF
    buffer = BytesIO(pdf.output(dest='S'))
    buffer.seek(0)

    await interaction.response.send_message(
        content="Тут ваш звіт у PDF форматі:",
        file=File(fp=buffer, filename="finance_report.pdf"),
        ephemeral=True
    )
