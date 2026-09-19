<div align="center">

[![AnimeSaturn](https://animesaturn.lawliet.lol/static/img/banner.png)](https://animesaturn.lawliet.lol/)

# AnimeSaturn-API (Italiano)

[![PyPI - Version](https://img.shields.io/pypi/v/animesaturn?logo=pypi&logoColor=white&color=blue)](https://pypi.org/project/animesaturn/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/animesaturn?logo=python&logoColor=white)](https://pypi.org/project/animesaturn/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/animesaturn?color=orange&logo=pypi&logoColor=white)](https://pypi.org/project/animesaturn/)
[![PyPI - Format](https://img.shields.io/pypi/format/animesaturn?logo=pypi&logoColor=white)](https://pypi.org/project/animesaturn/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/LICENSE)
[![Publish to PyPI](https://github.com/hollowfall/AnimeSaturn-API/actions/workflows/publish-pypi.yml/badge.svg)](https://pypi.org/project/animesaturn/)
[![Deploy MkDocs](https://github.com/hollowfall/AnimeSaturn-API/actions/workflows/deploy-mkdocs.yml/badge.svg)](https://animesaturn.lawliet.lol/)

[![Language - English](https://img.shields.io/badge/lang-english-%239FA8DA)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/README.md)
[![Language - Italiano](https://img.shields.io/badge/lang-italiano-%239FA8DA)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/README.it.md)

</div>

**AnimeSaturn-API** e una libreria Python non ufficiale, moderna e ad alte prestazioni per cercare anime, estrarre metadati e scaricare episodi da [AnimeSaturn](https://www.animesaturn.net) e da tutti i suoi domini e mirror ufficiali.

Progettata con la stessa filosofia e semplicita d'uso di [AnimeWorld-API](https://github.com/MainKronos/AnimeWorld-API).

Lingue disponibili:
- [English](README.md)
- [Italiano](README.it.md)

---

## Caratteristiche

- **Ricerca Istantanea**: Query diretta attraverso l'endpoint JSON interno di AnimeSaturn con fallback automatico ai filtri HTML.
- **Risoluzione Smart dello Slug**: Cerca anime sia tramite slug con hash (`solo-leveling-6iHEN`), titolo semplice (`solo-leveling`), sia con link completo.
- **Supporto Multi-Dominio**: Rilevamento e risoluzione automatica dei mirror ufficiali attivi tramite `https://www.animesaturn.me/` (`animesaturn.net`, `animesaturn.tv`, `animesaturn.in`, ecc.).
- **Metadati Completi**: Titolo, titolo alternativo/romaji, trama in italiano, generi, stagione di uscita, anno, studio, lingua, voto, link MyAnimeList/AniList e locandine ad alta risoluzione.
- **Decrittazione Video SaturnCDN**: Algoritmo nativo in Python puro per estrarre lo stream video senza necessita di browser headless (Selenium/Playwright) o Node.js.
- **Scaricatore HLS Concorrente**: Motore multi-thread per il download di playlist `.m3u8` e segmenti video `.ts` con selezione automatica della massima risoluzione disponibile e retry automatici.
- **Interruzione Pulita**: Gestione sicura di `Ctrl+C` o hook di interruzione senza tracebacks o file temporanei orfani.
- **Interfaccia CLI Completa**: Strumento da terminale `animesaturn` per cercare, visualizzare dettagli di anime ed episodi e scaricare file video.

---

## Installazione

Installa la release stabile da PyPI:

```bash
pip install animesaturn
```

Per installare anche le dipendenze per la compilazione della documentazione MkDocs:

```bash
pip install "animesaturn[docs]"
```

---

## Esempi Rapidi

### Ricerca Anime

```python
import animesaturn

# Ricerca titoli per parola chiave
risultati = animesaturn.find("One Piece")
for item in risultati[:5]:
    print(f"{item['name']} ({item['year']}) -> {item['url']}")
```

### Dettagli e Metadati Anime

```python
import animesaturn

# Inizializza l'anime tramite slug, titolo o URL
anime = animesaturn.Anime("solo-leveling")

print(f"Titolo:      {anime.name}")
print(f"Titolo Alt:  {anime.jtitle}")
print(f"Categoria:   {anime.category}")
print(f"Studio:      {anime.studio}")
print(f"Stagione:    {anime.season} ({anime.release})")
print(f"Stato:       {anime.status}")
print(f"Voto:        {anime.rating}/10")
print(f"Generi:      {', '.join(anime.genres)}")
print(f"Episodi:     {anime.episodes_num}")
print(f"Locandina:   {anime.poster}")
print(f"MyAnimeList: {anime.mal_url}")
```

### Accesso agli Episodi ed Estrazione Stream

```python
# Accesso diretto per indice o metodo
primo_ep = anime[1]  # oppure anime.get_episode(1)

print(f"Episodio:  {primo_ep.number} - {primo_ep.title}")
print(f"Watch URL: {primo_ep.url}")

# Ottieni i server di streaming disponibili
server_list = primo_ep.servers
server = server_list[0]  # Server principale (SaturnStream)

print(f"Server:     {server.name}")
print(f"Player:     {server.link}")
print(f"Stream URL: {server.fileLink()}")
```

### Download degli Episodi

```python
# Download con barra di avanzamento
primo_ep.download(folder="./downloads")

# Callback personalizzato di avanzamento
def on_progress(current_bytes, total_bytes, percentage):
    print(f"Avanzamento: {percentage:.1f}% ({current_bytes}/{total_bytes} bytes)", end="\r")
    return True  # Restituisci False per interrompere pulitamente

primo_ep.download(folder="./downloads", hook=on_progress)
```

---

## Gestione Multi-Dominio

```python
import animesaturn

# Mostra il dominio attualmente attivo
print("Dominio attivo:", animesaturn.get_domain())

# Recupera tutti i mirror ufficiali registrati
mirrors = animesaturn.fetch_official_domains()
print("Mirror ufficiali:", mirrors)

# Testa e seleziona il mirror piu veloce
active = animesaturn.discover_active_domain()
print("Mirror piu veloce impostato su:", active)

# Oppure imposta manualmente un dominio custom
animesaturn.set_domain("https://www.animesaturn.tv")
```

---

## Interfaccia a Riga di Comando (CLI)

Il pacchetto fornisce il comando da terminale `animesaturn` (eseguibile anche come `python animesaturn`):

| Comando | Descrizione | Esempio |
| :--- | :--- | :--- |
| `search` | Cerca anime per parola chiave | `animesaturn search "Naruto"` |
| `info` | Mostra dettagli anime e lista episodi | `animesaturn info "solo-leveling"` |
| `episode` / `ep` | Mostra dettagli episodio e link stream | `animesaturn ep "solo-leveling" 1` |
| `download` | Scarica episodio con barra di progresso | `animesaturn download "solo-leveling" -e 1 -o ./downloads` |
| `latest` | Mostra gli ultimi episodi rilasciati | `animesaturn latest --page 1` |
| `domains` | Mostra e testa i mirror ufficiali | `animesaturn domains` |

### Esempi CLI

```bash
# Cerca anime
animesaturn search "Bleach"

# Ispeziona i metadati di un anime
animesaturn info "bleach-sennen-kessen-hen-52Qxu"

# Mostra i link di streaming per l'episodio 1
animesaturn ep "solo-leveling" 1

# Scarica l'episodio 1
animesaturn download "solo-leveling" -e 1 -s 0 -o ./downloads

# Elenco ultime uscite
animesaturn latest -p 1
```

---

## Documentazione

La documentazione completa e consultabile all'indirizzo [https://animesaturn.lawliet.lol/](https://animesaturn.lawliet.lol/).

Per visualizzare la documentazione in locale:

```bash
mkdocs serve
```

---

## Disclaimer

Questo progetto non e ufficiale ed e sviluppato dalla community. Non e in alcun modo affiliato, sponsorizzato o collegato ad AnimeSaturn.

## Licenza

Rilasciato sotto licenza [MIT](LICENSE).

---

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=hollowfall/animesaturn-api&type=Date&legend=bottom-right)](https://star-history.com/#hollowfall/animesaturn-api&Date)

</div>
