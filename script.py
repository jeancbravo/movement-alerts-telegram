from binance.client import Client
from telegram import Bot
import time
import winsound
import asyncio

variacion = 5  # Variacion en los ultimos 30 minutos en porcentaje
variacion_100 = 7  # Variacion en los ultimos 30 minutos en porcentaje si tiene menos de 100k de volumen
variacionfast = 2  # Variacion en los ultimos 2 minutos en porcentaje

client = Client('','', tld='com')
bot = Bot(token='YOUR_BOT_TOKEN ')  # reemplaza 'YOUR_BOT_TOKEN' con el token de tu bot

async def send_message(text):
    await bot.send_message(chat_id='ID-CHAT', text=text)  # reemplaza 'ID-CHAT' con tu ID de chat

def play_alert_sound():
    winsound.Beep(2500, 1000)  # Beep at 2500 Hz for 1000 ms

def buscarticks():
    ticks = []
    lista_ticks = client.futures_symbol_ticker() # traer todas las monedas de futuros de binace
    print('Numero de monedas encontradas #' + str(len(lista_ticks)))

    for tick in lista_ticks:
        if tick['symbol'][-4:] != 'USDT': # seleccionar todas las monedas en el par USDT
            continue
        ticks.append(tick['symbol'])

    print('Numero de monedas encontradas en el par USDT: #' + str(len(ticks)))

    return ticks

def get_klines(tick):
    klines = client.futures_klines(symbol=tick, interval=Client.KLINE_INTERVAL_1MINUTE, limit=30)
    return klines

def infoticks(tick):
    info = client.futures_ticker(symbol=tick)
    return info

def human_format(volumen):
    magnitude = 0
    while abs(volumen) >= 1000:
        magnitude += 1
        volumen /= 1000.0
    return '%.2f%s' % (volumen, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

async def porcentaje_klines(tick, klines, knumber):
    inicial = float(klines[0][4])
    final = float(klines[knumber][4])

    # LONG
    if inicial > final:
        result = round(((inicial - final) / inicial) * 100, 2)
        if result >= variacion:
            info = infoticks(tick)
            volumen = float(info['quoteVolume'])
            if volumen > 100000000 or result >= variacion_100:
                message = f'LONG: {tick}\nVariacion: {result}%\nVolumen: {human_format(volumen)}\nPrecio max: {info["highPrice"]}\nPrecio min: {info["lowPrice"]}\n'
                print(message)
                await send_message(message)
                play_alert_sound()

    # SHORT
    if final > inicial:
        result = round(((final - inicial) / inicial) * 100, 2)
        if result >= variacion:
            info = infoticks(tick)
            volumen = float(info['quoteVolume'])
            if volumen > 100000000 or result >= variacion_100:
                message = f'SHORT: {tick}\nVariacion: {result}%\nVolumen: {human_format(volumen)}\nPrecio max: {info["highPrice"]}\nPrecio min: {info["lowPrice"]}\n'
                print(message)
                await send_message(message)
                play_alert_sound()

    # FAST
    if knumber >= 3:
        inicial = float(klines[knumber-2][4])
        final = float(klines[knumber][4])
        if inicial < final:
            result = round(((final - inicial) / inicial) * 100, 2)
            if result >= variacionfast:
                info = infoticks(tick)
                volumen = float(info['quoteVolume'])
                message = f'FAST SHORT!: {tick}\nVariacion: {result}%\nVolumen: {human_format(volumen)}\nPrecio max: {info["highPrice"]}\nPrecio min: {info["lowPrice"]}\n'
                print(message)
                await send_message(message)
                play_alert_sound()

async def main():
    while True:
        ticks = buscarticks()
        print('Escaneando monedas...')
        print('')
        for tick in ticks:
            klines = get_klines(tick)
            knumber = len(klines)
            if knumber > 0:
                knumber = knumber - 1
                await porcentaje_klines(tick, klines, knumber)
        print('Esperando 30 segundos...')
        print('')
        await asyncio.sleep(30)

# Ejecuta la función principal
asyncio.run(main())
