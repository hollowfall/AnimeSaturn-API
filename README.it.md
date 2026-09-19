<div align="center">

[![AnimeSaturn](https://animesaturn.lawliet.lol/static/img/banner.png)](https://animesaturn.lawliet.lol/)

# AnimeSaturn-API (Italiano)

[![PyPI](https://img.shields.io/pypi/v/animesaturn?color=blue)](https://pypi.org/project/animesaturn/)
[![Python](https://img.shields.io/pypi/pyversions/animesaturn)](https://pypi.org/project/animesaturn/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/LICENSE)
[![Deploy MkDocs](https://github.com/hollowfall/AnimeSaturn-API/actions/workflows/deploy-mkdocs.yml/badge.svg)](https://animesaturn.lawliet.lol/)

</div>

**AnimeSaturn-API** è una libreria Python non ufficiale, moderna e ad alte prestazioni per cercare anime, estrarre metadati e scaricare episodi da [AnimeSaturn](https://www.animesaturn.net) e da tutti i suoi domini e mirror ufficiali.

Progettata con la stessa filosofia e semplicità d'uso di [AnimeWorld-API](https://github.com/MainKronos/AnimeWorld-API).

Lingue:
- [English](README.md)
- [Italiano](README.it.md)

---

## Caratteristiche

- 🔍 **Ricerca Istantanea**: Accesso diretto all'endpoint JSON interno di AnimeSaturn.
- 🌐 **Supporto Multi-Dominio**: Rilevamento automatico dei mirror ufficiali attivi tramite `https://www.animesaturn.me/` (`animesaturn.net`, `animesaturn.tv`, `animesaturn.in`, ecc.).
- 📑 **Metadati Completi**: Titolo, titolo alternativo/romaji, trama completa in italiano, generi, stagione, lingua, voto, link MyAnimeList/AniList e locandina.
- 🔓 **Decrittazione Video SaturnCDN**: Algoritmo nativo in Python puro per estrarre lo stream `.mp4` diretto senza browser headless (Selenium/Playwright).
- 📥 **Scaricatore Integrato**: Download a blocchi ad alta velocità con supporto resume, barra di avanzamento (`tqdm`) e hook personalizzabili.
- ⌨️ **Interfaccia CLI**: Comando da terminale `animesaturn` per cercare, ispezionare e scaricare direttamente da riga di comando.

---

## Installazione

```bash
pip install animesaturn
```

Per installare anche le dipendenze per la documentazione MkDocs:

```bash
pip install "animesaturn[docs]"
```

---

## Esempi Rapidi

### Ricerca Anime

```python
import animesaturn as asaturn

# Ricerca anime per parola chiave
risultati = asaturn.find("One Piece")
for item in risultati[:5]:
    print(f"{item['name']} ({item['year']}) -> {item['link']}")
```

### Dettagli e Metadati Anime

```python
import animesaturn as asaturn

# Inizializza l'anime tramite link o slug
anime = asaturn.Anime("one-piece-PmTvj")

print(f"Titolo:      {anime.name}")
print(f"Titolo Alt:  {anime.jtitle}")
print(f"Tipo:        {anime.category}")
print(f"Stagione:    {anime.season} ({anime.release})")
print(f"Stato:       {anime.status}")
print(f"Voto:        {anime.rating}/10")
print(f"Generi:      {', '.join(anime.genres)}")
print(f"Trama:       {anime.story}")
```

### Lista Episodi e Link Streaming Diretto

```python
# Ottieni gli episodi rilasciati
episodi = anime.getEpisodes()
print(f"Totale episodi: {len(episodi)}")

primo_ep = episodi[0]
print(f"Episodio: {primo_ep.number}")

# Ottieni i server disponibili
server_list = primo_ep.getServer()
server = server_list[0] # Server principale

# Ottieni il link diretto al video .mp4
link_video = server.fileLink()
print(f"URL video: {link_video}")

# Informazioni sul file
info = server.fileInfo()
print(f"Dimensione: {info['total_bytes'] / (1024*1024):.2f} MB")
```

### Download Episodio

```python
# Download con barra di progresso nel terminale
primo_ep.download(folder="./download")

# Download con hook di callback personalizzato
def progresso(corrente, totale, percentuale):
    print(f"Progresso: {percentuale:.1f}% ({corrente}/{totale} byte)", end="\r")
    return True # Ritorna False per interrompere

primo_ep.download(folder="./download", hook=progresso)
```

---

## Gestione Domini e Mirror

```python
import animesaturn as asaturn

# Dominio attualmente attivo
print("Dominio attivo:", asaturn.get_domain())

# Recupera la lista dei domini ufficiali da animesaturn.me
domini = asaturn.fetch_official_domains()
print("Mirror ufficiali:", domini)

# Trova e imposta automaticamente il dominio più veloce
dominio_veloce = asaturn.discover_active_domain()
print("Dominio attivo impostato su:", dominio_veloce)

# Imposta manualmente un dominio specifico
asaturn.set_domain("https://www.animesaturn.tv")
```

---

## Utilizzo da CLI

```bash
# Cerca un anime
animesaturn search "Naruto"

# Mostra informazioni sull'anime
animesaturn info "naruto-shippuden-ita-PjvU1"

# Mostra gli ultimi episodi usciti
animesaturn latest --page 1

# Scarica l'episodio 1
animesaturn download "naruto-shippuden-ita-PjvU1" --ep 1 --folder ./download

# Mostra i domini ufficiali
animesaturn domains
```

---

## Documentazione

La documentazione completa è consultabile su [https://animesaturn.lawliet.lol/](https://animesaturn.lawliet.lol/) oppure localmente avviando:

```bash
mkdocs serve
```

---

## Licenza

Distribuito sotto licenza [MIT](LICENSE).

---

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=hollowfall/animesaturn-api&type=Date&legend=bottom-right)](https://star-history.com/#hollowfall/animesaturn-api&Date)

</div>

