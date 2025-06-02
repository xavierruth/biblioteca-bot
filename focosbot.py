import logging
import random
import os
import csv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)
from dotenv import load_dotenv

# Carrega o token do arquivo .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_API")

# Estados da conversa
MENU, ESCOLHER_HALL, ESCOLHER_SALA, INFORMAR_NOME, INFORMAR_CURSO, CONFIRMAR_RESERVA = range(6)

# Cursos disponíveis
cursos = {
    "1": "Análise e Desenvolvimento de Sistemas",
    "2": "Jogos Digitais",
    "3": "Design de Moda",
    "4": "Gastronomia",
    "5": "Enfermagem"
}


logging.basicConfig(level=logging.INFO)

# Salvar reservas em CSV
def registrar_reserva_csv(nome, sala, curso):
    caminho = "reservas.csv"
    escrever_cabecalho = not os.path.exists(caminho)

    with open(caminho, mode="a", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        if escrever_cabecalho:
            writer.writerow(["Nome", "Sala e Hall", "Curso"])
        writer.writerow([nome, sala, curso])

# Botão voltar ao menu principal
def teclado_voltar():
    return [["Voltar ao menu"]]

# Boas-vindas
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.full_name
    mensagem = (
        f"Olá, {nome}! É bom ter você aqui na *Biblioteca Guerra de Holanda* 📚.\n\n"
        "Sou a Sofia, a assistente virtual que irá te ajudar a reservar salas de estudos, "
        "além de te dar dicas sobre a nossa biblioteca.\n\n"
        "*Escolha uma opção:*"
    )
    teclado = [["1. Reserva de salas", "2. Regras para sala de estudo"],
               ["3. Contatos da biblioteca", "4. Informativos sobre a biblioteca"]]
    await update.message.reply_text(mensagem, parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True))
    return MENU

# Menu principal
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()

    if "1" in texto:
        teclado = [["Hall Norte"], ["Hall Sul"]] + teclado_voltar()
        await update.message.reply_text("Escolha o hall:", reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True))
        return ESCOLHER_HALL
    elif "2" in texto:
        regras = (
            "*Regras para salas de estudo:*\n"
            "1. Verifique a disponibilidade antecipadamente.\n"
            "2. Reserva por até 2 horas.\n"
            "3. Intervalo máximo de 10 minutos.\n"
            "4. Proibido comer dentro da sala.\n"
            "5. Falar alto ou usar viva-voz é proibido.\n"
            "6. Após 10 minutos de ausência, a reserva pode ser cancelada.\n\n"
            "Respeite o ambiente e colabore para o bom uso coletivo!"
        )
        await update.message.reply_text(regras, parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
        return MENU
    elif "3" in texto:
        await update.message.reply_text("📞 *Contatos da biblioteca:*\nEmail: ecultural@pe.senac.br\nTelefone: (81) 3413-6712", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
        return MENU
    elif "4" in texto:
        await update.message.reply_text("ℹ️ *Informativos:*\nPara assuntos sobre reserva, renovação ou multas de livros, dirija-se ao guichê da biblioteca.", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
        return MENU
    elif "voltar" in texto:
        return await start(update, context)
    else:
        await update.message.reply_text("Não entendi. Por favor, selecione uma opção do menu.")
        return MENU

# Escolha do hall
async def escolher_hall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hall = update.message.text.lower()
    if "norte" in hall:
        context.user_data["hall"] = "Hall Norte"
        salas_disponiveis = random.sample(["Sala 01", "Sala 02", "Sala 03"], k=2)
    elif "sul" in hall:
        context.user_data["hall"] = "Hall Sul"
        salas_disponiveis = random.sample(["Sala 04", "Sala 05", "Sala 06"], k=2)
    elif "voltar" in hall:
        return await start(update, context)
    else:
        await update.message.reply_text("Escolha inválida. Por favor, selecione uma opção do teclado.")
        return ESCOLHER_HALL

    context.user_data["salas_opcoes"] = salas_disponiveis
    teclado = [[sala] for sala in salas_disponiveis] + teclado_voltar()
    await update.message.reply_text("Essas são as salas disponíveis, escolha uma:", reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True))
    return ESCOLHER_SALA

# Escolha da sala
async def escolher_sala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sala = update.message.text
    if sala.lower() == "voltar":
        return await start(update, context)

    if sala not in context.user_data.get("salas_opcoes", []):
        await update.message.reply_text("Escolha inválida. Selecione uma das salas disponíveis.")
        return ESCOLHER_SALA

    context.user_data["sala"] = f"{sala} - {context.user_data['hall']}"
    await update.message.reply_text("Informe seu *Nome e Sobrenome*:", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
    return INFORMAR_NOME

# Nome e sobrenome
async def informar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if texto.lower() == "voltar":
        return await start(update, context)

    context.user_data["nome_completo"] = texto

    teclado_cursos = [[f"{k}. {v}"] for k, v in cursos.items()] + teclado_voltar()
    await update.message.reply_text("Escolha o seu curso:", reply_markup=ReplyKeyboardMarkup(teclado_cursos, resize_keyboard=True))
    return INFORMAR_CURSO

# Curso
async def informar_curso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto.lower() == "voltar":
        return await start(update, context)

    for numero, nome in cursos.items():
        if texto.startswith(numero):
            context.user_data["curso"] = nome
            break
    else:
        await update.message.reply_text("Escolha inválida. Selecione uma opção do teclado.")
        return INFORMAR_CURSO

    regras_finais = (
        "*Orientações para uso da sala:*\n"
        "1. Verifique a disponibilidade antecipadamente.\n"
        "2. Reserva por até 2 horas.\n"
        "3. Intervalo máximo de 10 minutos.\n"
        "4. Proibido comer dentro da sala.\n"
        "5. Falar alto ou viva-voz são proibidos.\n"
        "6. Atrasos maiores que 10 minutos podem cancelar a reserva."
    )
    await update.message.reply_text(regras_finais, parse_mode="Markdown")
    return await confirmar(update, context)

# Confirmação final
async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sala = context.user_data.get("sala")
    nome = context.user_data.get("nome_completo")
    curso = context.user_data.get("curso")

    registrar_reserva_csv(nome, sala, curso)

    mensagem_final = (
        f"✅ Reserva confirmada!\n\n"
        f"Sala: *{sala}*\n"
        f"Nome: *{nome}*\n"
        f"Curso: *{curso}*\n\n"
        "📚 Bons estudos!"
    )
    await update.message.reply_text(mensagem_final, parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
    return MENU

# Cancelar conversa
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Reserva cancelada. Caso precise, é só chamar!", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
    return MENU


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Não entendi. Por favor, escolha uma das opções do menu.", reply_markup=ReplyKeyboardMarkup(teclado_voltar(), resize_keyboard=True))
    return MENU

# Configuração do bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handler para /start — fora do ConversationHandler
    app.add_handler(CommandHandler("start", start))

    # Conversa principal
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, menu)
        ],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            ESCOLHER_HALL: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_hall)],
            ESCOLHER_SALA: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_sala)],
            INFORMAR_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, informar_nome)],
            INFORMAR_CURSO: [MessageHandler(filters.TEXT & ~filters.COMMAND, informar_curso)],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            MessageHandler(filters.TEXT, fallback),
        ],
    )

    app.add_handler(conv_handler)
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
