import re, os, time, asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pushbullet import Pushbullet



API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
API_KEY_PUSHBULLET = os.environ.get("API_KEY_PUSHBULLET")
TELEGRAM_SESSION = os.environ.get("TELEGRAM_SESSION")


ARQUIVO_HISTORICO = "historico_mensagens.txt"
COOLDOWN = 1800
OQUE_EU_QUERO= ['galaxy', 'buds', 'core', '50%']

CANAIS_RAW = os.environ.get("CANAIS_IDS", "")
CANAIS = [int(x) if x.strip().lstrip('-').isdigit() else x.strip() for x in CANAIS_RAW.split() if x.strip()]

sep = '|'.join(OQUE_EU_QUERO)
pb = Pushbullet(API_KEY_PUSHBULLET)
client = TelegramClient(StringSession(TELEGRAM_SESSION), API_ID, API_HASH)



if not os.path.exists(ARQUIVO_HISTORICO):
    open(ARQUIVO_HISTORICO, "w", encoding="utf-8").close()



def filtros(text):
    agora = time.time()
    no_link_text = re.sub(r'https?://\S+', "", text)
    clean_text = "".join(no_link_text.split())

    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        linhas = f.read().splitlines()
    for linha in linhas:
        if "|" not in linha:
            continue
        tempo_salvo_str, texto_salvo = linha.split("|", 1)
        tempo_salvo = float(tempo_salvo_str)

        if clean_text == texto_salvo:
            return True
        
        if "50%" in clean_text and "50%" in texto_salvo:
            if agora - tempo_salvo < COOLDOWN:
                return True

    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f'{agora}|{clean_text}\n')


    return False



@client.on(events.NewMessage(chats=CANAIS))
async def escutar_mensagens(event):
    texto_original = event.text if event.text else ""
    if not texto_original.strip():
        return

    texto_mensagem = texto_original.lower()
    nome_canal = "Mensagens Salvas" if event.is_private else (event.chat.title 
    if event.chat else f"Canal ID {event.chat_id}")

    rr = re.search(fr'(?<!\S)({sep})(?!\S)', texto_mensagem)
    if rr:
        if filtros(texto_mensagem):
            return
        
        try:
            titulo = f"Promoçao no {nome_canal}"
            corpo = texto_original[:250] + "..." if len(texto_original) > 250 else texto_original
            pb.push_note(titulo, corpo)
        except Exception as e:
            print(f"Erro ao enviar notificação para o celular: {e}")


with client:
    client.run_until_disconnected()
