import unittest
import pandas as pd
from src.etl import parse, tratar_brasil, tratar_uf


class ETLTests(unittest.TestCase):
    def setUp(self):
        self.header = {
            "NC": "Nível Territorial (Código)",
            "NN": "Nível Territorial",
            "MC": "Unidade de Medida (Código)",
            "MN": "Unidade de Medida",
            "V": "Valor",
            "D1C": "Brasil (Código)",
            "D1N": "Brasil",
            "D2C": "Variável (Código)",
            "D2N": "Variável",
            "D3C": "Trimestre Móvel - Fim do Período (Código)",
            "D3N": "Trimestre Móvel - Fim do Período",
        }

    def test_parse_decimal_comma_and_missing_marker(self):
        payload = [
            self.header,
            {"D1C": "1", "D1N": "Brasil", "D3C": "202601", "V": "5,2"},
            {"D1C": "1", "D1N": "Brasil", "D3C": "202602", "V": "X"},
        ]
        df = parse(payload)
        self.assertAlmostEqual(df.loc[0, "taxa"], 5.2)
        self.assertTrue(pd.isna(df.loc[1, "taxa"]))
        self.assertEqual(df.loc[0, "ano"], 2026)
        self.assertEqual(df.loc[0, "sub"], 1)

    def test_brasil_derived_metrics(self):
        rows = [{"ano": 2025, "sub": month, "taxa": float(month)} for month in range(1, 13)]
        result = tratar_brasil(pd.DataFrame(rows))
        self.assertEqual(len(result), 12)
        self.assertAlmostEqual(result.loc[0, "desvio_sazonal_pp"], -5.5)

    def test_uf_region_mapping(self):
        source = pd.DataFrame([{
            "territorio_cod": "33", "territorio": "Rio de Janeiro",
            "ano": 2026, "sub": 1, "taxa": 5.0,
        }])
        result = tratar_uf(source)
        self.assertEqual(result.loc[0, "regiao"], "Sudeste")
        self.assertEqual(result.loc[0, "periodo"], "2026-T1")


if __name__ == "__main__":
    unittest.main()
