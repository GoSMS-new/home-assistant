# Иконки для home-assistant/brands

Готовые файлы для PR в <https://github.com/home-assistant/brands> —
именно оттуда HACS и Home Assistant берут иконки интеграций
(`brands.home-assistant.io/_/gosms/icon.png`).

Структура повторяет целевую в репозитории brands:

```text
custom_integrations/gosms/icon.png      # 256x256, прозрачные углы
custom_integrations/gosms/icon@2x.png   # 512x512 (hDPI)
```

Как отправить: форкнуть home-assistant/brands, скопировать папку
`custom_integrations/gosms/` в корень форка, открыть PR с заголовком
«Add gosms (GoSMS RU)». После мержа иконка появится в HACS и в
Настройки → Устройства и службы автоматически (кэш CDN — до суток).
