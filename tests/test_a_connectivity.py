import requests
import inspect
from services.ui_service import config

def get_pings():
    return {
        name: value
        for name, value in inspect.getmembers(config)
        if name.startswith("PING_") and not inspect.ismodule(value) and not inspect.isfunction(value)
    }

def test_main():
    pings = get_pings()
    print(pings)
    for k, v in pings.items():
        try:
            resp = requests.get(v)
            print(v)
            print(resp)
            assert(resp.status_code == 200)
        except:
            assert(False)

if __name__ == "__main__":
    test_main()