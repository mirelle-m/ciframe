# deciframe

Descubra as músicas que você já sabe tocar (e ainda não faz ideia). Busque por
título/artista, gênero, pelos acordes que você já manja, ou por sequências de
acordes famosas — o deciframe cruza isso com uma base de cifras e sugere
músicas parecidas.

Stack: backend Flask (Python) servindo uma API JSON + um frontend AngularJS
estático. As músicas e gêneros vêm de um CSV carregado em memória; o catálogo
de sequências de acordes (incluindo as cadastradas pelos visitantes) fica em um
SQLite local.

## Rodando localmente

### Com Docker

```
docker build -t ciframe .
docker run -v deciframe-data:/app/instance -p 8080:8080 ciframe
```

O volume nomeado `deciframe-data` mantém as sequências cadastradas quando o
container é removido e recriado. Sem o volume, o catálogo sobrevive a um
`docker restart`, mas não a um `docker rm`.

Acesse [http://localhost:8080](http://localhost:8080).

### Com virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Acesse [http://localhost:5000](http://localhost:5000).

---

Para convenções de contribuição, veja [CONTRIB.md](CONTRIB.md). Licença: [LICENSE](LICENSE).
