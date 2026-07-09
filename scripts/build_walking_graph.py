from pathlib import Path

import osmnx as ox

from app.core.settings import get_settings


def main() -> None:
    settings = get_settings()
    output = Path(settings.walking_graph_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Santa Cruz de la Sierra - red peatonal OSM
    graph = ox.graph_from_place('Santa Cruz de la Sierra, Bolivia', network_type='walk', simplify=True)
    ox.save_graphml(graph, output)
    print(f'Walking graph saved: {output}')


if __name__ == '__main__':
    main()