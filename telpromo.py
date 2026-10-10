import re, os, time, asyncio, unicodedata
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pushbullet import Pushbullet

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
API_KEY_PUSHBULLET = os.environ.get("API_KEY_PUSHBULLET")
TELEGRAM_SESSION = os.environ.get("TELEGRAM_SESSION")

ARQUIVO_HISTORICO = "historico_mensagens.txt"
COOLDOWN = 1800

REGRAS_BUSCA = [["Iclamper"], ["tomada inteligente"]]

CANAIS_RAW = os.environ.get("CANAIS_IDS", "")
CANAIS = [int(x.strip()) for x in CANAIS_RAW.split(",") if x.strip()]

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
            if agora - tempo_salvo < COOLDOWN:
                return True

    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f'{agora}|{clean_text}\n')

    return False

def remover_acentos(texto):
    nfkd = unicodedata.normalize('NFD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def tem_desconto_maior_que_20(texto):
    porcentagens = re.findall(r'(\d+)%', texto)
    for p in porcentagens:
        if int(p) >= 20:
            return True
    return False

async def escutar_mensagens(event):
    if event.chat_id not in CANAIS:
        return

    texto_original = event.text if event.text else ""
    if not texto_original.strip():
        return

    texto_mensagem = remover_acentos(texto_original.lower())
    nome_canal = "Mensagens Salvas" if event.is_private else (event.chat.title if event.chat else f"Canal ID {event.chat_id}")

    
    achou_palavras = False
    if REGRAS_BUSCA:
        achou_palavras = any(
            all(palavra in texto_mensagem for palavra in grupo) 
            for grupo in REGRAS_BUSCA
        )

    achou_desconto = tem_desconto_maior_que_20(texto_mensagem)

    if achou_palavras or achou_desconto:
        if filtros(texto_mensagem):
            return
        
        try:
            motivo = "Boa" if achou_palavras else "Desconto >= 20%"
            titulo = f"Promoção ({motivo}) no {nome_canal}"
            corpo = texto_original[:250] + "..." if len(texto_original) > 250 else texto_original
            pb.push_note(titulo, corpo)
            print(f" Notificação enviada por {motivo}!")
        except Exception as e:
            print(f"Erro ao enviar notificação para o celular: {e}")

async def main():
    await client.start()
    await client.get_dialogs()
    client.add_event_handler(escutar_mensagens, events.NewMessage())
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
