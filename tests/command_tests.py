import sys

import distest

collector = distest.TestCollector()


@collector()
async def test_one(interface: distest.TestInterface):
    await interface.send_message("$reload_extension TimeExtension")
    await interface.wait_for_message()
    await interface.send_message("$watch_channel")
    await interface.wait_for_message()
    await interface.send_message("4:20UTC")


if __name__ == "__main__":
    distest.run_dtest_bot(sys.argv, collector)
