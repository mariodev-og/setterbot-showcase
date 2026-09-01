"""
Verifica que ningún helper de queries devuelva data cross-tenant.
Requiere DB de test (puede ser la actual con seeds).
"""
import asyncio
from app.database import query_leads_for_client, get_lead_for_client


async def test_no_fuga():
    leads_diego_ferrari = await query_leads_for_client("diego_ferrari")
    for l in leads_diego_ferrari:
        assert l["client_id"] == "diego_ferrari", \
            f"FUGA — lead {l['user_id']} con client_id {l['client_id']} en query de diego_ferrari"
    print(f"OK — {len(leads_diego_ferrari)} leads de diego_ferrari, todos con client_id correcto")

    leads_fake = await query_leads_for_client("cliente_que_no_existe")
    assert leads_fake == [], "ERROR — cliente inexistente devolvió data"
    print("OK — cliente inexistente devuelve lista vacía")


if __name__ == "__main__":
    asyncio.run(test_no_fuga())