import re
from config.investors import SUPER_INVESTOR_REGISTRY

HFT_DESKS = {
    "QE SECURITIES", "NK SECURITIES", "MICROCURVES", "GRAVITON",
    "JUMP TRADING", "TOWER RESEARCH", "ESTEE ADVISORS", "KRAKEN", "SHRENI SHARES"
}

DII_RE = r"MUTUAL FUND|\bMF\b|LIFE INSURANCE|GENERAL INSURANCE|TRUSTEE|AXIS.*MF|KOTAK.*MF|ICICI PRU|QUANT MF|360 ONE|SUNDARAM MF"
FII_RE = r"GOLDMAN SACHS|BNP PARIBAS|SOCIETE GENERALE|MORGAN STANLEY|NORGES BANK|ADIA|KUWAIT INVESTMENT|BOFA|FIDELITY|GHISALLO"
PE_RE = r"BIDCO|MEERKAT|SOFTBANK|FOSUN|ALPHA WAVE|PEAK XV|VENTURES|HOLDING APS|CENTELLA|BREP ASIA"

def match_hni(name: str) -> str | None:
    clean = f" {re.sub(r'[^\\w\\s]', ' ', str(name).upper())} "
    for investor, pats in SUPER_INVESTOR_REGISTRY.items():
        if any(re.search(p, clean) for p in pats):
            return investor
    return None

def classify_client(name: str) -> str:
    name_u = str(name).upper()
    if any(hft in name_u for hft in HFT_DESKS):
        return "ARBITRAGE"
    if match_hni(name_u):
        return "SUPER_INVESTOR"
    if re.search(DII_RE, name_u):
        return "DII"
    if re.search(FII_RE, name_u):
        return "FII"
    if re.search(PE_RE, name_u):
        return "PE_VC"
    return "OTHER"
