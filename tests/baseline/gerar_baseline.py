import json, urllib.request, urllib.parse

SEQUENCIAS = ["Bm,G,D,A", "C,G,Am,F", "Gm,F", "C,C7,F,Fm", "Em,G", "C,A7,Dm,G7"]

for i, seq in enumerate(SEQUENCIAS, start=1):
    musicas = set()
    pagina = 1
    while pagina <= 200:
        url = "http://localhost:8080/similares?" + urllib.parse.urlencode({"sequencia": seq, "pagina": pagina})
        resposta = json.load(urllib.request.urlopen(url))
        if not resposta:
            break
        musicas.update(m["id_unico_musica"] for m in resposta)
        pagina += 1
    with open(f"tests/baseline/seq{i}.json", "w") as f:
        json.dump(sorted(musicas), f, indent=1)
    print(f"seq{i} ({seq}): {len(musicas)} músicas")