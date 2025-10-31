# 📄 Summary of Changes

## 🐛 Bug Fixes
- Fixed `docker-compose.yml` to point to the correct image repository for `etcd` (now points to `bitnamilegacy` instead of `bitnami`) - reflected this change in the `README.md`
- `get_request` in `helper.py` no longer returns an `AttributeError` if a key was not found in `etcd`
- `get_request` and `put_request` in `helper.py` now converts error messages into `str`, to prevent subsequent Antithesis assertions failing

## ⚙️ Modifications
- The new Antithesis test command (`parallel_driver_generate_leased_traffic.py`) is copied over into the image
- `reachable` assertion has been added to existing test command (`parallel_driver_generate_traffic.py`), further details in the [Google Doc](https://docs.google.com/document/d/1Yh4SKWs_JxvoF3g1a8psATeBCLBeGjRuw4u9sBoQifA/edit?tab=t.0)
- Exposed the rest of the `etcd3` python API in `put_request` in `helper.py`, to allow for the `lease` functionality to be used

## 🆕 New items
- Added a new Antithesis test command (`parallel_driver_generate_leased_traffic.py`), to test the revoke lease functionality of `etcd`!

## 🗑️ Deleted items
- None
