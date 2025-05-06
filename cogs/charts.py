import matplotlib.pyplot as plt
from io import BytesIO
from discord import File
from collections import defaultdict

from utils.helpers import load_data, INCOME_FILE, AUTO_INCOME_FILE, EXPENSES_FILE


async def draw_donut_chart(interaction, data: dict, title: str):
    if not data:
        await interaction.response.send_message("📭 Немає даних для побудови діаграми.", ephemeral=True)
        return

    labels = list(data.keys())
    values = list(data.values())

    colors = plt.get_cmap('Set3').colors

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 14}
    )

    ax.set_title(title, fontsize=16)

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    file = File(buf, filename="chart.png")
    await interaction.response.send_message(f"📈 {title}:", file=file, ephemeral=True)


# 🔽 Діаграма прибутків (включає також автоматичні прибутки)
async def show_income_chart(interaction):
    user_id = str(interaction.user.id)

    income_data = load_data(INCOME_FILE).get(user_id, [])
    auto_income_data = load_data(AUTO_INCOME_FILE).get(user_id, [])

    summary = defaultdict(float)

    for e in income_data:
        cat = e.get("category", "Без категорії")
        summary[cat] += float(e.get("amount", 0))

    for e in auto_income_data:
        cat = e.get("category", "Без категорії")
        summary[cat] += float(e.get("amount", 0))

    await draw_donut_chart(interaction, summary, "Розподіл прибутків")


# 🔽 Діаграма витрат
async def show_expense_chart(interaction):
    user_id = str(interaction.user.id)

    expense_data = load_data(EXPENSES_FILE).get(user_id, [])

    summary = defaultdict(float)
    for entry in expense_data:
        if entry["amount"] > 0:
            summary[entry["category"]] += entry["amount"]

    await draw_donut_chart(interaction, summary, "Розподіл витрат")
