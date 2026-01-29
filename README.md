# Ultrahuman Ring

This integration uses the official Ultrahuman Vision API to retrieve Ultrahuman AIR Ring information periodically and expose it in HomeAssistant through various sensors.

## HOW TO USE
1. Download repository via HACS store
2. Go to Integrations -> Add Integration -> Ultrahuman Ring
3. Enter API-KEY (see below for steps)
4. Integration should be fully configured now and a few sensor entities will be available for use in HomeAssistant. 

## Obtaining API-Key
1. Visit https://vision.ultrahuman.com/developer
2. Log in
3. Click on "Generate New Token"
4. Enter any suitable name for token name (ex: "YourName Ultrahuman Air Token")
5. (OPTIONAL) Set token expiry to 10 years
6. Select RING DATA ACCESS checkbox
7. Click Generate Token
8. Copy token as this will be required during integration onboarding

