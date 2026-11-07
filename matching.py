import json
import os


def normalizar_acordes(entrada):
    if entrada is None:
        return []
    if isinstance(entrada, str):
        partes = entrada.replace(';', ',').split(',')
    elif isinstance(entrada, (list, tuple)):
        partes = []
        for item in entrada:
            partes.extend(str(item).replace(';', ',').split(','))
    else:
        raise ValueError('acordes deve ser string ou lista')
    return [str(parte).strip() for parte in partes if str(parte).strip() != '']


def lista_canonica(acordes):
    return json.dumps(acordes, ensure_ascii=False, separators=(',', ':'))


def sequencia_aparece(cifra, acordes):
    if not acordes or not cifra:
        return False
    if not set(cifra).issubset(set(acordes)):
        return False
    tamanho = len(acordes)
    return any(
        cifra[i:i + tamanho] == acordes
        for i in range(len(cifra) - tamanho + 1)
    )


def calcular_matches(acordes, musicas):
    return [
        musica.id_unico_musica
        for musica in musicas
        if sequencia_aparece(musica.cifra, acordes)
    ]


def dataset_version(caminho_csv):
    estatistica = os.stat(caminho_csv)
    return '%s:%s' % (estatistica.st_size, estatistica.st_mtime_ns)
