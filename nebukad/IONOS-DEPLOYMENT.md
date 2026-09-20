# Kontaktformular bei IONOS

Empfänger und fester Absender: info@nebukad-international.com. Die Besucheradresse wird nur als Reply-To verwendet. Keine SMTP-Zugangsdaten im Repository.

Das Formular benötigt PHP 8 mit OpenSSL und ausgehender SMTP-Verbindung im IONOS-Webhosting. Mail Basic allein stellt keinen PHP-Webspace bereit. Einrichtung der Passwortdatei außerhalb des Webroots: siehe SMTP-SETUP.md.

HTML-Dateien, style.css, site.js, contact.js, contact.php, mail-lib/ und assets/ in das Verzeichnis der Domain hochladen. HTTPS aktivieren. Der Versand ist nur unter https://nebukad-international.com und https://www.nebukad-international.com freigegeben. GitHub Pages zeigt eine Vorschau ohne Versand.

Nach Upload muss ein Zustelltest erfolgen: Formular absenden, Empfang im IONOS-Postfach prüfen, Antwortfunktion auf Besucheradresse prüfen. Eine erfolgreiche SMTP-Antwort bestätigt nur die Annahme durch den Mailserver. Website und HTTPS sind erreichbar; SMTP-Zustellung ist bis zum Test mit dem echten Postfachpasswort noch nicht verifiziert.

Schutz: serverseitige Eingabeprüfung, fester Empfänger und Betreff, keine Anhänge, Origin-Prüfung und eigener Request-Header ohne CORS-Freigabe, Honeypot, maximal fünf Versuche pro IP-Hash und 60 insgesamt je Stunde. Zähler liegen in einer auf 60 Einträge begrenzten, gesperrten Datei im temporären Serververzeichnis außerhalb des Webroots. Alte Einträge werden bei der nächsten Anfrage bereinigt. Kein CAPTCHA und kein zusätzlicher Drittanbieter.

Datenschutzentwurf enthält Formular und Missbrauchsschutz. Produktspezifische Hostingangaben bleiben vor dem finalen Start zu prüfen.
