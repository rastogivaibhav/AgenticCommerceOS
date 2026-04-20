🎯 **What:** Added unit tests for the WhatsApp configuration loader (`load_whatsapp_config` and `_coerce_config`) in `integrations/whatsapp/client.py`. These functions parse configuration overrides and read environment variables but were previously untested.

📊 **Coverage:** The new tests cover:
- Loading configuration when environment variables are missing.
- Loading configuration successfully using environment variables.
- Coercing configuration using dictionary overrides.
- Coercing configuration with a mix of dictionary overrides and environment variables.
- Handling whitespace and stripping configuration values.

✨ **Result:** Test coverage for `integrations/whatsapp/client.py` has been significantly improved. The simple config parsing and environment reading logic is now fully verified against regressions.
