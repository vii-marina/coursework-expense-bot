import matplotlib.pyplot as plt
from io import BytesIO
from discord import File

async def draw_donut_chart(interaction, data: dict, title: str):
    if not data:
        await interaction.response.send_message("📭 Немає даних для побудови діаграми.", ephemeral=True)
        return

    labels = list(data.keys())
    values = list(data.values())

    # Встановлюємо стиль кольорів
    colors = plt.get_cmap('Set3').colors  # Яскрава палітра

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
