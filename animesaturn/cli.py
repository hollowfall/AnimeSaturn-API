"""
Command-line interface (CLI) for AnimeSaturn library.
"""
import argparse
import sys
from typing import Optional

from .search import find, latest_episodes
from .anime import Anime
from .domains import get_domain, set_domain, fetch_official_domains, discover_active_domain


def main(args: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="animesaturn",
        description="AnimeSaturn CLI - Search, view, and download anime episodes."
    )
    parser.add_argument("--domain", help="Custom base domain to use (e.g. https://www.animesaturn.tv)")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: search
    p_search = subparsers.add_parser("search", help="Search anime by keyword")
    p_search.add_argument("query", help="Anime title or keyword to search")

    # Command: info
    p_info = subparsers.add_parser("info", help="Get anime metadata and episode list")
    p_info.add_argument("link", help="Anime slug or link (e.g. 'one-piece-PmTvj')")

    # Command: download
    p_down = subparsers.add_parser("download", help="Download an episode")
    p_down.add_argument("link", help="Anime slug or link")
    p_down.add_argument("--ep", required=True, help="Episode number to download (e.g. 1)")
    p_down.add_argument("--folder", default=".", help="Output directory folder")
    p_down.add_argument("--server", type=int, default=0, help="Server index (default: 0)")

    # Command: latest
    p_latest = subparsers.add_parser("latest", help="Show latest released episodes")
    p_latest.add_argument("--page", type=int, default=1, help="Page number")

    # Command: domains
    p_domains = subparsers.add_parser("domains", help="List and check official domains")

    parsed = parser.parse_args(args)

    if parsed.domain:
        set_domain(parsed.domain)

    if parsed.command == "search":
        print(f"\nSearching AnimeSaturn for: '{parsed.query}'...")
        results = find(parsed.query)
        if not results:
            print("No anime found matching your search.")
            return 0

        print(f"Found {len(results)} results:\n")
        for i, res in enumerate(results, 1):
            year_str = f" ({res['year']})" if res.get("year") else ""
            type_str = f" [{res['type']}]" if res.get("type") else ""
            print(f"[{i}] {res['name']}{year_str}{type_str}")
            print(f"    Link: {res['link']}")
            if res.get("genres"):
                print(f"    Genres: {', '.join(res['genres'])}")
            print()
        return 0

    elif parsed.command == "info":
        print(f"\nFetching anime details for: '{parsed.link}'...")
        try:
            anime = Anime(parsed.link)
            print("=" * 65)
            print(f"Title:        {anime.name}")
            if anime.jtitle:
                print(f"Alt Title:    {anime.jtitle}")
            print(f"Category:     {anime.category}")
            if anime.studio:
                print(f"Studio:       {anime.studio}")
            if anime.season or anime.release:
                print(f"Season/Year:  {anime.season} ({anime.release})")
            if anime.release_date:
                print(f"Release Date: {anime.release_date}")
            if anime.language:
                print(f"Language:     {anime.language}")
            if anime.status:
                print(f"Status:       {anime.status}")
            if anime.duration:
                print(f"Duration:     {anime.duration}")
            if anime.views:
                print(f"Views:        {anime.views}")
            print(f"Rating:       {anime.rating}/10" if anime.rating else "Rating:       N/A")
            if anime.locandina:
                print(f"Locandina:    {anime.locandina}")
            if anime.copertina:
                print(f"Copertina:    {anime.copertina}")
            if anime.genres:
                print(f"Genres:       {', '.join(anime.genres)}")
            if anime.mal_url:
                print(f"MyAnimeList:  {anime.mal_url}")
            if anime.anilist_url:
                print(f"AniList:      {anime.anilist_url}")
            print(f"Episodes:     {anime.episodes_num}")
            if anime.story:
                print(f"\nSynopsis:\n{anime.story[:300]}...")
            print("=" * 65)

            eps = anime.getEpisodes()
            if eps:
                print(f"\nAvailable Episodes ({len(eps)} total):")
                preview_eps = [e.number for e in eps[:24]]
                print(" " + ", ".join(preview_eps) + ("..." if len(eps) > 24 else ""))
            print()
            return 0
        except Exception as e:
            print(f"Error fetching anime: {e}", file=sys.stderr)
            return 1

    elif parsed.command == "download":
        print(f"\nPreparing to download episode {parsed.ep} for '{parsed.link}'...")
        try:
            anime = Anime(parsed.link)
            episodes = anime.getEpisodes()
            target_ep = None
            for ep in episodes:
                if str(ep.number) == str(parsed.ep):
                    target_ep = ep
                    break

            if not target_ep:
                print(f"Episode {parsed.ep} not found in anime episode list.", file=sys.stderr)
                return 1

            servers = target_ep.getServer()
            if not servers:
                print("No video servers available for this episode.", file=sys.stderr)
                return 1

            chosen_server = servers[parsed.server if parsed.server < len(servers) else 0]
            print(f"Using server: '{chosen_server.name}'")
            print(f"Extracting video stream link...")
            direct_link = chosen_server.fileLink()
            print(f"Direct stream URL: {direct_link[:60]}...")
            print(f"Downloading to folder: {parsed.folder}")

            success = chosen_server.download(folder=parsed.folder)
            if success:
                print("\nDownload completed successfully!")
                return 0
            else:
                print("\nDownload failed.", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Download error: {e}", file=sys.stderr)
            return 1

    elif parsed.command == "latest":
        print(f"\nFetching latest episodes (page {parsed.page})...")
        data = latest_episodes(parsed.page)
        items = data.get("items", [])
        print(f"Page {data.get('page')} of {data.get('pages')} (Total: {data.get('total')} items):\n")
        for item in items:
            ep_lbl = f"Ep. {item.get('episodeLabel', '?')}"
            type_lbl = f"[{item.get('type', 'TV')}]"
            print(f"- {item.get('title')} {ep_lbl} {type_lbl}")
            print(f"  Watch URL: {item.get('url')}")
        return 0

    elif parsed.command == "domains":
        print("\nChecking official AnimeSaturn mirrors and domains...")
        domains = fetch_official_domains()
        print(f"Discovered {len(domains)} official domains:")
        for d in domains:
            print(f"  * {d}")
        print("\nSelecting fastest active domain...")
        active = discover_active_domain()
        print(f"Active domain set to: {active}")
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
