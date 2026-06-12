# Иконки бренда

С Home Assistant **2026.3** иконки лежат прямо в интеграции —
`custom_components/gosms/brand/` (icon.png 256x256, icon@2x.png 512x512,
прозрачные углы). HA отдаёт их через локальный proxy-API
`/api/brands/integration/gosms/...`, локальные файлы приоритетнее CDN.
Отдельный PR в home-assistant/brands для установленной интеграции не нужен.

Папка `custom_integrations/gosms/` здесь — те же файлы, подготовленные для
PR в <https://github.com/home-assistant/brands>. Он всё ещё полезен:

- иконка в списке HACS видна ДО установки интеграции (список берёт с CDN);
- на Home Assistant старше 2026.3 локальная папка brand/ игнорируется.

Как отправить: форкнуть home-assistant/brands, скопировать
`custom_integrations/gosms/` в корень форка, PR «Add gosms (GoSMS RU)».
