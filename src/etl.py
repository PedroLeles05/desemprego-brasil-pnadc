"""ETL didático da taxa de desocupação da PNAD Contínua via API pública do SIDRA.

Na raiz do repositório:
    python -m src.etl            # baixa os dados e gera os arquivos
    python -m src.etl --offline  # usa exclusivamente os JSON já salvos em data/raw
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC, ASSETS = ROOT / "data/raw", ROOT / "data/processed", ROOT / "docs/assets"
API = "https://apisidra.ibge.gov.br/values"
SOURCES = {
    "brasil_movel": "/t/6381/n1/all/v/4099/p/all",
    "uf_trimestral": "/t/4099/n3/all/v/4099/p/all",
}
REGIOES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}


def fetch(path: str) -> list[dict]:
    """Consulta o SIDRA sem autenticação e valida a resposta HTTP/JSON."""
    response = requests.get(
        API + path,
        timeout=(15, 180),
        headers={"User-Agent": "ProjetoAcademico-PNADContinua/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Resposta inesperada do SIDRA para {path}.")
    return payload


def _decimal_sidra(values: pd.Series) -> pd.Series:
    """Converte valores do SIDRA (decimal com vírgula) e preserva marcadores como NaN."""
    normalized = values.astype("string").str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(normalized, errors="coerce")


def parse(payload: list[dict]) -> pd.DataFrame:
    """Converte o JSON do SIDRA (primeira linha = cabeçalho) em DataFrame tipado."""
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Payload do SIDRA vazio ou inválido.")
    header, rows = payload[0], payload[1:]
    codes = {
        key: value for key, value in header.items()
        if isinstance(value, str) and value.endswith("(Código)")
    }
    period_key = next(
        (key for key, value in codes.items() if value.startswith("Trimestre")), None
    )
    territory_key = next(
        (key for key, value in codes.items()
         if value.split(" (")[0] in ("Brasil", "Unidade da Federação")), None
    )
    if period_key is None or territory_key is None:
        raise ValueError(f"Não foi possível identificar período e território: {header}")
    territory_name_key = territory_key[:-1] + "N" if territory_key.endswith("C") else None
    if not rows or not territory_name_key or territory_name_key not in rows[0]:
        raise ValueError("Resposta SIDRA sem linhas ou sem nome do território.")
    if "V" not in rows[0]:
        raise ValueError("Campo de valor ('V') não encontrado na resposta do SIDRA.")

    df = pd.DataFrame(rows)
    period = df[period_key].astype("string")
    if not period.str.fullmatch(r"\d{6}").all():
        raise ValueError("Código de período do SIDRA fora do formato esperado AAAAPP.")
    out = pd.DataFrame({
        "territorio_cod": df[territory_key].astype("string"),
        "territorio": df[territory_name_key].astype("string"),
        "periodo_cod": period,
        "taxa": _decimal_sidra(df["V"]),
        "valor_original": df["V"].astype("string"),
    })
    out["ano"] = out["periodo_cod"].str[:4].astype(int)
    out["sub"] = out["periodo_cod"].str[4:].astype(int)
    if not out["sub"].between(1, 12).all():
        raise ValueError("Código de subperíodo fora do intervalo esperado.")
    return out


def tratar_brasil(df: pd.DataFrame) -> pd.DataFrame:
    """Série nacional: mês final do trimestre móvel e métricas descritivas."""
    df = df.rename(columns={"sub": "mes"}).sort_values(["ano", "mes"]).reset_index(drop=True)
    if df.duplicated(["ano", "mes"]).any():
        raise ValueError("Há períodos nacionais duplicados na resposta do SIDRA.")
    df["data"] = pd.to_datetime(dict(year=df.ano, month=df.mes, day=1))
    df["variacao_12m_pp"] = df["taxa"].diff(12).round(1)
    completo = df.groupby("ano")["taxa"].transform(lambda serie: serie.notna().sum() == 12)
    media_ano = df.groupby("ano")["taxa"].transform("mean")
    df["desvio_sazonal_pp"] = (df["taxa"] - media_ano).where(completo).round(2)
    return df[["data", "ano", "mes", "taxa", "variacao_12m_pp", "desvio_sazonal_pp"]]


def tratar_uf(df: pd.DataFrame) -> pd.DataFrame:
    """Painel por UF e trimestre civil; região derivada do código IBGE da UF."""
    df = df.rename(columns={"sub": "trimestre", "territorio": "uf"}).copy()
    df["regiao"] = df["territorio_cod"].str[0].map(REGIOES)
    if df["regiao"].isna().any():
        codigos = sorted(df.loc[df["regiao"].isna(), "territorio_cod"].unique())
        raise ValueError(f"Código de UF sem correspondência de região: {codigos}")
    if not df["trimestre"].between(1, 4).all():
        raise ValueError("A tabela trimestral contém trimestre fora de 1 a 4.")
    if df.duplicated(["territorio_cod", "ano", "trimestre"]).any():
        raise ValueError("Há períodos duplicados para uma UF na resposta do SIDRA.")
    df["periodo"] = df["ano"].astype(str) + "-T" + df["trimestre"].astype(str)
    cols = ["territorio_cod", "uf", "regiao", "ano", "trimestre", "periodo", "taxa"]
    return df[cols].sort_values(["ano", "trimestre", "territorio_cod"]).reset_index(drop=True)


def salvar(df: pd.DataFrame, nome: str) -> None:
    df.to_csv(PROC / f"{nome}.csv.gz", index=False, compression="gzip", decimal=".")
    # Parquet é exigido no projeto; não ocultar a ausência do motor de escrita.
    df.to_parquet(PROC / f"{nome}.parquet", index=False)


def para_json(df: pd.DataFrame, nome: str, rename: dict) -> None:
    dados = df.rename(columns=rename)[list(rename.values())].astype(object)
    dados = dados.where(pd.notna(dados), None)
    (ASSETS / f"{nome}.json").write_text(
        json.dumps(dados.to_dict("records"), ensure_ascii=False, default=str, allow_nan=False),
        encoding="utf-8",
    )


def resumo_valores(df: pd.DataFrame) -> dict:
    originais = df["valor_original"].fillna("<nulo>").astype(str)
    invalidos = originais[df["taxa"].isna()].value_counts().to_dict()
    return {
        "linhas": int(len(df)),
        "valores_validos": int(df["taxa"].notna().sum()),
        "valores_ausentes_ou_nao_numericos": int(df["taxa"].isna().sum()),
        "marcadores_nao_numericos": {str(k): int(v) for k, v in invalidos.items()},
        "primeiro_periodo": str(df["periodo_cod"].min()),
        "ultimo_periodo": str(df["periodo_cod"].max()),
    }


def main(offline: bool = False) -> None:
    for directory in (RAW, PROC, ASSETS):
        directory.mkdir(parents=True, exist_ok=True)

    executado_em = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    payloads = {}
    log = {"executado_em": executado_em, "modo": "offline" if offline else "online", "fontes": {}}
    for nome, path in SOURCES.items():
        arquivo = RAW / f"{nome}.json"
        if offline:
            if not arquivo.exists():
                raise FileNotFoundError(
                    f"Modo offline: arquivo bruto obrigatório não encontrado: {arquivo}"
                )
            registro = json.loads(arquivo.read_text(encoding="utf-8"))
            payloads[nome] = registro["dados"]
            url = registro.get("url", API + path)
            baixado_em = registro.get("baixado_em")
        else:
            payloads[nome] = fetch(path)
            url, baixado_em = API + path, executado_em
            arquivo.write_text(json.dumps({
                "url": url, "baixado_em": baixado_em, "dados": payloads[nome]
            }, ensure_ascii=False), encoding="utf-8")
        log["fontes"][nome] = {
            "url": url,
            "arquivo_bruto": str(arquivo.relative_to(ROOT)),
            "baixado_em": baixado_em,
            "sha256": hashlib.sha256(arquivo.read_bytes()).hexdigest(),
        }

    brutos = {nome: parse(payload) for nome, payload in payloads.items()}
    for nome, bruto in brutos.items():
        log["fontes"][nome]["qualidade"] = resumo_valores(bruto)

    brasil = tratar_brasil(brutos["brasil_movel"])
    uf = tratar_uf(brutos["uf_trimestral"])
    if brasil["taxa"].notna().sum() == 0 or uf["taxa"].notna().sum() == 0:
        raise ValueError("A extração não contém taxas numéricas válidas. Verifique a resposta do SIDRA.")

    salvar(brasil, "taxa_desocupacao_brasil_trimestre_movel")
    salvar(uf, "taxa_desocupacao_uf_trimestral")
    brasil_json = brasil.assign(d=brasil["data"].dt.strftime("%Y-%m"))
    para_json(brasil_json, "serie_brasil", {
        "d": "d", "taxa": "t", "variacao_12m_pp": "v12", "desvio_sazonal_pp": "s", "ano": "a"
    })
    para_json(uf, "uf_trimestral", {
        "uf": "uf", "regiao": "r", "ano": "a", "trimestre": "q", "taxa": "t"
    })
    log["saidas"] = {
        "brasil_linhas": int(len(brasil)),
        "uf_linhas": int(len(uf)),
        "brasil_periodo": [str(brasil["data"].min().date()), str(brasil["data"].max().date())],
        "uf_periodo": [int(uf["ano"].min()), int(uf["ano"].max())],
    }
    (PROC / "etl_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ETL concluído: {len(brasil)} observações nacionais e {len(uf)} observações por UF.")
    print(f"Período nacional: {log['saidas']['brasil_periodo'][0]} a {log['saidas']['brasil_periodo'][1]}.")
    print(f"Período por UF: {log['saidas']['uf_periodo'][0]} a {log['saidas']['uf_periodo'][1]}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL da PNAD Contínua a partir do SIDRA/IBGE")
    parser.add_argument("--offline", action="store_true", help="usa somente os arquivos JSON já existentes em data/raw")
    main(parser.parse_args().offline)
