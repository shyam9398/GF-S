import asyncio

from app.bis.bis_web import BISWebProvider


async def main():

    provider = BISWebProvider()

    try:
        results = await provider.search_standards("helmet")

        print("\n========== BIS PROVIDER TEST ==========\n")
        print("Results:", len(results))

        for item in results:
            print(
                f"{item.get('standardNumber')} | "
                f"{item.get('standardName')} | "
                f"withdrawStatus={item.get('withdrawStatus')} | "
                f"validUpto={item.get('validUpto')}"
            )

        print("\n========== END ==========\n")

    finally:
        await provider.close()


asyncio.run(main())